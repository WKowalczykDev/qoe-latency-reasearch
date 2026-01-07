import os
import sqlite3
import json
import csv
import random
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, session
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)

DB_PATH = "data/ratings.db"
CONFIG_PATH = "config.json"


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
                        fragment_id
                        TEXT
                        NOT
                        NULL,
                        delay_seconds
                        REAL
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


def parse_video_filename(filename):
    # Format: "3 fragment 05.mp4" -> id=3, delay=0.5
    parts = filename.replace('.mp4', '').replace('.mkv', '').replace('.webm', '').split()
    if len(parts) >= 3:
        fragment_id = parts[0]
        delay_str = parts[2]
        delay_seconds = float(delay_str) / 10.0  # "05" -> 0.5
        return fragment_id, delay_seconds
    return None, None


def load_videos(shuffle=False):
    videos = []
    video_dir = "videos"

    if not os.path.exists(video_dir):
        return videos

    for filename in os.listdir(video_dir):
        if filename.lower().endswith(('.mp4', '.mkv', '.webm', '.avi')):
            fragment_id, delay = parse_video_filename(filename)
            if fragment_id and delay is not None:
                videos.append({
                    'filename': filename,
                    'fragment_id': fragment_id,
                    'delay_seconds': delay
                })

    if shuffle:
        random.shuffle(videos)

    return videos


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

    config = load_config()
    videos = load_videos(shuffle=config.get('shuffle', True))

    if not videos:
        return jsonify({'error': 'No videos found'}), 400

    session['participant_id'] = participant_id
    session['playlist'] = videos
    session['current_index'] = 0

    return jsonify({'success': True, 'total_videos': len(videos)})


@app.route('/next_video')
def next_video():
    if 'participant_id' not in session:
        return jsonify({'error': 'No active session'}), 400

    idx = session.get('current_index', 0)
    playlist = session.get('playlist', [])

    if idx >= len(playlist):
        return jsonify({'completed': True})

    video = playlist[idx]
    config = load_config()

    return jsonify({
        'filename': video['filename'],
        'fragment_id': video['fragment_id'],
        'delay_seconds': video['delay_seconds'],
        'index': idx + 1,
        'total': len(playlist),
        'questions': config['questions']
    })


@app.route('/submit_rating', methods=['POST'])
def submit_rating():
    if 'participant_id' not in session:
        return jsonify({'error': 'No active session'}), 400

    data = request.get_json()
    idx = session.get('current_index', 0)
    playlist = session.get('playlist', [])

    if idx >= len(playlist):
        return jsonify({'error': 'No more videos'}), 400

    video = playlist[idx]

    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
                    INSERT INTO ratings(participant_id, video, fragment_id, delay_seconds,
                                        comprehension_rating, comfort_rating, comments, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        session['participant_id'],
                        video['filename'],
                        video['fragment_id'],
                        video['delay_seconds'],
                        data['comprehension_rating'],
                        data['comfort_rating'],
                        data.get('comments', ''),
                        datetime.utcnow().isoformat()
                    ))

    session['current_index'] = idx + 1

    return jsonify({'success': True})


@app.route('/videos/<path:filename>')
def serve_video(filename):
    return send_from_directory('videos', filename)


@app.route('/export')
@require_auth
def export_csv():
    csv_path = "data/ratings_export.csv"

    with sqlite3.connect(DB_PATH) as con:
        rows = con.execute("""
                           SELECT id,
                                  participant_id,
                                  video,
                                  fragment_id,
                                  delay_seconds,
                                  comprehension_rating,
                                  comfort_rating,
                                  comments, timestamp
                           FROM ratings
                           ORDER BY timestamp
                           """).fetchall()

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'id', 'participant_id', 'video', 'fragment_id', 'delay_seconds',
            'comprehension_rating', 'comfort_rating', 'comments', 'timestamp'
        ])
        writer.writerows(rows)

    return send_from_directory('data', 'ratings_export.csv', as_attachment=True)


if __name__ == '__main__':
    init_db()
    config = load_config()
    app.run(host='0.0.0.0', port=config['http_port'], debug=False)