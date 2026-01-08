# QoE Video Tester

A simple, cross-platform tool for conducting video Quality of Experience (QoE) studies. Participants watch videos with WebVTT subtitles and rate them on comprehension and comfort.

## 📋 Requirements

- Docker Desktop (Windows/Mac) or Docker (Linux)
- Your video files
- Your WebVTT subtitle files

**That's it.** No Python, no complex setup.

## 🚀 Quick Start

### 1. Download the Project

Download or clone this repository to your computer:

```bash
git clone https://github.com/WKowalczykDev/qoe-latency-reasearch.git
cd qoe-latency-research
```

Or manually create this folder structure:

```
video-qoe/
├── docker-compose.yml
├── Dockerfile
├── app.py
├── requirements.txt
├── config.json
├── templates/
│   └── rating.html
├── videos/          ← PUT YOUR VIDEOS HERE
└── subtitles/       ← PUT YOUR VTT SUBTITLES HERE
```

### 2. Add Your Videos and Subtitles

Place your video files in the `videos/` folder and matching WebVTT subtitle files in the `subtitles/` folder.

**IMPORTANT: File Pairing**

The system matches videos and subtitles **by index** when sorted alphabetically. For best results, use matching numbered filenames:

**Videos folder:**
```
01_video.mp4
02_video.mp4
03_video.mp4
...
15_video.mp4
```

**Subtitles folder:**
```
01_subtitle.vtt
02_subtitle.vtt
03_subtitle.vtt
...
15_subtitle.vtt
```

The system will automatically pair:
- `01_video.mp4` with `01_subtitle.vtt`
- `02_video.mp4` with `02_subtitle.vtt`
- etc.

**Requirements:**
- Exactly **15 video-subtitle pairs** are needed
- Videos: `.mp4`, `.mkv`, `.webm`, or `.avi` format
- Subtitles: `.vtt` format (WebVTT)
- Files are matched by alphabetical sort order

**About WebVTT Format:**

WebVTT (Web Video Text Tracks) is the standard subtitle format for HTML5 video. Example VTT file:

```
WEBVTT

00:00:00.000 --> 00:00:02.500
First subtitle line

00:00:02.500 --> 00:00:05.000
Second subtitle line
```

### 3. Start the Application

Open terminal/command prompt in the project folder and run:

```bash
docker-compose up --build
```

Wait for the message:
```
* Running on http://0.0.0.0:8080
```

### 4. Open in Browser

Go to: **http://localhost:8080**

Login credentials (change in `config.json`):
- **Username:** admin
- **Password:** test123

## 👤 For Participants

1. Enter your participant ID (e.g., "P01", "John")
2. Click "Start"
3. Watch each video completely with subtitles
4. Rate on two scales (1-5):
   - Comprehension: How well you understood what happened
   - Comfort: How comfortable was watching
5. Add optional comments
6. Click "Dalej" (Next) to continue

The system will automatically:
- Show all 15 videos in randomized order
- Apply random subtitle delays (0ms, 500ms, 800ms, 1200ms, 2500ms)
- Each delay value is used exactly 3 times across the 15 videos
- Save all ratings

## 🎬 How Subtitle Delays Work

The system automatically applies different subtitle timing delays to test synchronization quality:

**Delay Values:**
- **0ms** - Perfect sync (3 videos)
- **500ms** - Subtitles 0.5 seconds early (3 videos)
- **800ms** - Subtitles 0.8 seconds early (3 videos)
- **1200ms** - Subtitles 1.2 seconds early (3 videos)
- **2500ms** - Subtitles 2.5 seconds early (3 videos)

Each participant sees the same 15 videos but with:
- Randomized order
- Randomly assigned delays (each delay used exactly 3 times)

The subtitle timing is shifted in real-time by the server, so you only need one VTT file per video.

## 📊 Exporting Results

After testing is complete, download the results:

1. Go to: **http://localhost:8080/export**
2. Or click "Pobierz CSV" on the completion screen

The CSV file includes:
- `participant_id` - Participant identifier
- `video` - Video filename
- `subtitle` - Subtitle filename
- `delay_ms` - Delay applied in milliseconds
- `comprehension_rating` - Rating 1-5
- `comfort_rating` - Rating 1-5
- `comments` - Optional text comments
- `timestamp` - When the rating was submitted

## ⚙️ Configuration

Edit `config.json` to customize:

```json
{
  "http_user_name": "admin",        <- Change login username
  "http_user_password": "test123",  <- Change login password
  "http_port": 8080,                <- Change port if 8080 is busy
  "shuffle": true,                  <- true = random order, false = sequential
  "questions": {
    "comprehension": "Your question here",
    "comfort": "Your question here"
  }
}
```

## 🛠️ Troubleshooting

### Problem: "Need exactly 15 video-subtitle pairs"

**Solutions:**
1. Count files: You need exactly 15 videos AND 15 VTT subtitles
2. Check file extensions: `.vtt` for subtitles (not `.srt`)
3. Verify files are in correct folders: `videos/` and `subtitles/`
4. Check debug endpoint: http://localhost:8080/debug/files

### Problem: "Port 8080 is already in use"

**Solution:** Change the port in `docker-compose.yml`:

```yaml
ports:
  - "9000:8080"  ← Use 9000 instead (or any free port)
```

Then access at: http://localhost:9000

### Problem: Subtitles don't show

**Solutions:**
1. Check VTT file format - must start with `WEBVTT`
2. Ensure UTF-8 encoding
3. Verify file pairing (check alphabetical order)
4. Click "Napisy ON/OFF" button to toggle subtitles
5. Check browser console (F12) for errors

### Problem: Subtitles out of sync

**Expected Behavior:** This is intentional! The system applies delays (0-2500ms) for testing purposes. Each video shows the applied delay in the progress bar.

### Problem: Videos don't play

**Solutions:**
1. Ensure files are in the `videos/` folder
2. Try converting to MP4 format (most compatible)
3. Check browser console (F12) for errors
4. Try different browser (Chrome/Firefox recommended)

### Problem: Can't login

**Solutions:**
1. Check credentials in `config.json`
2. Default is username: `admin`, password: `test123`
3. Restart after changing config: `docker-compose restart`

### Problem: Docker build fails

**Solutions:**
1. Ensure Docker Desktop is running
2. Check internet connection (downloads Python image)
3. Try: `docker-compose down -v` then `docker-compose up --build`

### Problem: Ratings not saved

**Solution:** Check that `data/` folder was created automatically. If not:
```bash
mkdir data
```

## 🔄 Converting SRT to VTT

If you have SRT subtitle files, you can convert them to VTT:

**Online Tools:**
- https://subtitletools.com/convert-to-vtt-online
- https://gotranscript.com/subtitle-converter

**Command Line (ffmpeg):**
```bash
ffmpeg -i input.srt output.vtt
```

**Python Script:**
```python
def srt_to_vtt(srt_file, vtt_file):
    with open(srt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace comma with period in timestamps
    content = content.replace(',', '.')
    
    with open(vtt_file, 'w', encoding='utf-8') as f:
        f.write('WEBVTT\n\n')
        f.write(content)
```

## 🔄 Stopping the Application

Press `Ctrl+C` in the terminal where Docker is running.

Or run:
```bash
docker-compose down
```

## 🗑️ Reset Everything

To start fresh (deletes all ratings):

```bash
docker-compose down -v
rm -rf data/
docker-compose up --build
```

**Warning:** This deletes all collected data!

## 📦 Sharing with Others

To share this tool:

1. Zip the entire folder (including videos and subtitles)
2. Send to participants
3. They only need Docker installed
4. They run: `docker-compose up --build`

Each person's data is saved independently.

## 🎯 Best Practices

1. **Test first:** Run a trial with 2-3 video pairs before the real study
2. **Clear instructions:** Tell participants to watch completely before rating
3. **Unique IDs:** Assign unique participant IDs (P01, P02, etc.)
4. **Backup data:** Export CSV after each participant
5. **Browser:** Chrome/Firefox work best
6. **Subtitle quality:** Ensure VTT files are properly formatted and encoded in UTF-8

## 📝 Data Structure

The SQLite database (`data/ratings.db`) stores all ratings. Export to CSV for analysis in Excel, Python, R, etc.

Example CSV output:
```csv
id,participant_id,video,subtitle,delay_ms,comprehension_rating,comfort_rating,comments,timestamp
1,P01,01_video.mp4,01_subtitle.vtt,0,4,5,"Perfect sync",2024-01-07T10:30:00
2,P01,02_video.mp4,02_subtitle.vtt,500,4,4,"Slight delay",2024-01-07T10:32:15
3,P01,03_video.mp4,03_subtitle.vtt,1200,3,2,"Noticeable delay",2024-01-07T10:34:30
```

## 🔒 Security Note

This tool uses basic HTTP authentication. For public internet deployment, consider adding HTTPS and stronger authentication.

For local network use (recommended), the default setup is sufficient.

## 📧 Support

If you encounter issues:
1. Check this README's Troubleshooting section
2. Verify all files are in the correct folders
3. Check Docker logs: `docker-compose logs`
4. Visit debug endpoint: http://localhost:8080/debug/files

## 📄 License

Open source - modify as needed for your research.

---

**Ready to start?** 
1. Put 15 videos in `videos/`
2. Put 15 matching VTT subtitles in `subtitles/`
3. Run `docker-compose up --build`