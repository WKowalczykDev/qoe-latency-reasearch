import os
import sqlite3
import json
import csv
import random
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, session, Response
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)

DB_PATH = "data/ratings.db"
CONFIG_PATH = "config.json"

# Fixed delays in milliseconds
DELAYS = [0, 500, 800, 1200, 2500]


def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def init_db():
    os.makedirs("data", exist_ok=True)
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
                    CREATE TABLE IF NOT EXISTS ratings
                    (
                        id
                        INTEGER
                        PRIMARY
                        KEY
                        AUTOINCREMENT,
                        participant_id
                        TEXT
                        NOT
                        NULL,
                        video
                        TEXT
                        NOT
                        NULL,
                        subtitle
                        TEXT
                        NOT
                        NULL,
                        delay_ms
                        INTEGER
                        NOT
                        NULL,
                        comprehension_rating
                        INTEGER
                        NOT
                        NULL,
                        comfort_rating
                        INTEGER
                        NOT
                        NULL,
                        comments
                        TEXT,
                        timestamp
                        TEXT
                        NOT
                        NULL
                    )
                    """)


def get_video_pairs():
    """Get matched video-subtitle pairs based on numbering"""
    video_dir = "videos"
    subtitle_dir = "subtitles"

    if not os.path.exists(video_dir) or not os.path.exists(subtitle_dir):
        return []

    videos = sorted([f for f in os.listdir(video_dir) if f.lower().endswith(('.mp4', '.mkv', '.webm', '.avi'))])
    subtitles = sorted([f for f in os.listdir(subtitle_dir) if f.lower().endswith('.srt')])

    # Match by index: video[i] -> subtitle[i]
    pairs = []
    for i in range(min(len(videos), len(subtitles))):
        pairs.append({
            'video': videos[i],
            'subtitle': subtitles[i]
        })

    return pairs


def create_playlist():
    """Create playlist: 15 videos with random delays, each video shown once"""
    pairs = get_video_pairs()

    if len(pairs) != 15:
        return [], f"Need exactly 15 video-subtitle pairs, found {len(pairs)}"

    # Assign delays: each delay (0,500,800,1200,2500) used 3 times
    delays = DELAYS * 3  # [0,500,800,1200,2500, 0,500,800,1200,2500, 0,500,800,1200,2500]
    random.shuffle(delays)

    playlist = []
    for i, pair in enumerate(pairs):
        playlist.append({
            'video': pair['video'],
            'subtitle': pair['subtitle'],
            'delay_ms': delays[i],
            'part_number': i + 1
        })

    return playlist, None


def shift_subtitle_timing(srt_content, delay_ms):
    """Shift all subtitle timings by delay_ms milliseconds"""
    if delay_ms == 0:
        return srt_content

    lines = srt_content.split('\n')
    result = []

    for line in lines:
        if '-->' in line:
            parts = line.split('-->')
            start = parts[0].strip()
            end = parts[1].strip()

            new_start = shift_time(start, delay_ms)
            new_end = shift_time(end, delay_ms)

            result.append(f"{new_start} --> {new_end}")
        else:
            result.append(line)

    return '\n'.join(result)


def shift_time(time_str, delay_ms):
    """Shift a single SRT timestamp by delay_ms"""
    try:
        time_part, ms_part = time_str.split(',')
        h, m, s = map(int, time_part.split(':'))
        ms = int(ms_part)

        total_ms = (h * 3600000) + (m * 60000) + (s * 1000) + ms
        total_ms += delay_ms

        if total_ms < 0:
            total_ms = 0

        h = total_ms // 3600000
        total_ms %= 3600000
        m = total_ms // 60000
        total_ms %= 60000
        s = total_ms // 1000
        ms = total_ms % 1000

        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    except:
        return time_str


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        config = load_config()
        auth = request.authorization
        if not auth or auth.username != config['http_user_name'] or auth.password != config['http_user_password']:
            return ('Authentication required', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
        return f(*args, **kwargs)

    return decorated


@app.route('/')
@require_auth
def index():
    return render_template('rating.html')


@app.route('/start', methods=['POST'])
def start_session():
    data = request.get_json()
    participant_id = data.get('participant_id', '').strip()

    if not participant_id:
        return jsonify({'error': 'Participant ID required'}), 400

    playlist, error = create_playlist()

    if error:
        return jsonify({'error': error}), 400

    session['participant_id'] = participant_id
    session['playlist'] = playlist
    session['current_index'] = 0

    return jsonify({'success': True, 'total_videos': len(playlist)})


@app.route('/next_video')
def next_video():
    if 'participant_id' not in session:
        return jsonify({'error': 'No active session'}), 400

    idx = session.get('current_index', 0)
    playlist = session.get('playlist', [])

    if idx >= len(playlist):
        return jsonify({'completed': True})

    item = playlist[idx]
    config = load_config()

    return jsonify({
        'video': item['video'],
        'subtitle': item['subtitle'],
        'delay_ms': item['delay_ms'],
        'part_number': item['part_number'],
        'index': idx + 1,
        'total': len(playlist),
        'questions': config['questions']
    })


@app.route('/submit_rating', methods=['POST'])
def submit_rating():
    if 'participant_id' not in session:
        print("ERROR: No active session")
        return jsonify({'error': 'No active session'}), 400

    data = request.get_json()
    print(f"Received rating data: {data}")

    idx = session.get('current_index', 0)
    playlist = session.get('playlist', [])

    if idx >= len(playlist):
        print(f"ERROR: Index {idx} >= playlist length {len(playlist)}")
        return jsonify({'error': 'No more videos'}), 400

    item = playlist[idx]
    print(f"Saving rating for: {item}")

    try:
        with sqlite3.connect(DB_PATH) as con:
            con.execute("""
                        INSERT INTO ratings(participant_id, video, subtitle, delay_ms,
                                            comprehension_rating, comfort_rating, comments, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            session['participant_id'],
                            item['video'],
                            item['subtitle'],
                            item['delay_ms'],
                            data['comprehension_rating'],
                            data['comfort_rating'],
                            data.get('comments', ''),
                            datetime.utcnow().isoformat()
                        ))

        session['current_index'] = idx + 1
        print(f"Rating saved successfully. Next index: {idx + 1}")
        return jsonify({'success': True})

    except Exception as e:
        print(f"ERROR saving rating: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/videos/<path:filename>')
def serve_video(filename):
    # Explicit MIME types for video
    mimetype = None
    if filename.lower().endswith('.mp4'):
        mimetype = 'video/mp4'
    elif filename.lower().endswith('.mkv'):
        mimetype = 'video/x-matroska'
    elif filename.lower().endswith('.webm'):
        mimetype = 'video/webm'
    elif filename.lower().endswith('.avi'):
        mimetype = 'video/x-msvideo'

    return send_from_directory('videos', filename, mimetype=mimetype)


@app.route('/subtitles/<path:filename>')
def serve_subtitle(filename):
    delay_ms = request.args.get('delay', 0, type=int)

    subtitle_path = os.path.join('subtitles', filename)
    if not os.path.exists(subtitle_path):
        return "Subtitle not found", 404

    with open(subtitle_path, 'r', encoding='utf-8') as f:
        content = f.read()

    shifted_content = shift_subtitle_timing(content, delay_ms)

    return Response(shifted_content, mimetype='text/plain; charset=utf-8')


@app.route('/debug/files')
@require_auth
def debug_files():
    """Debug endpoint to check available files"""
    pairs = get_video_pairs()
    return jsonify({
        'video_count': len([f for f in os.listdir('videos') if
                            f.lower().endswith(('.mp4', '.mkv', '.webm', '.avi'))]) if os.path.exists('videos') else 0,
        'subtitle_count': len([f for f in os.listdir('subtitles') if f.lower().endswith('.srt')]) if os.path.exists(
            'subtitles') else 0,
        'pairs': pairs
    })


@app.route('/export')
@require_auth
def export_csv():
    csv_path = "data/ratings_export.csv"

    with sqlite3.connect(DB_PATH) as con:
        rows = con.execute("""
                           SELECT id,
                                  participant_id,
                                  video,
                                  subtitle,
                                  delay_ms,
                                  comprehension_rating,
                                  comfort_rating,
                                  comments, timestamp
                           FROM ratings
                           ORDER BY timestamp
                           """).fetchall()

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'id', 'participant_id', 'video', 'subtitle', 'delay_ms',
            'comprehension_rating', 'comfort_rating', 'comments', 'timestamp'
        ])
        writer.writerows(rows)

    return send_from_directory('data', 'ratings_export.csv', as_attachment=True)


if __name__ == '__main__':
    init_db()
    config = load_config()
    print(f"Starting server on port {config['http_port']}")
    print(f"Videos directory exists: {os.path.exists('videos')}")
    print(f"Subtitles directory exists: {os.path.exists('subtitles')}")
    if os.path.exists('videos'):
        print(
            f"Video files: {[f for f in os.listdir('videos') if f.lower().endswith(('.mp4', '.mkv', '.webm', '.avi'))]}")
    if os.path.exists('subtitles'):
        print(f"Subtitle files: {[f for f in os.listdir('subtitles') if f.lower().endswith('.srt')]}")
    app.run(host='0.0.0.0', port=config['http_port'], debug=True)