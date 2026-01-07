# QoE Video Tester

A simple, cross-platform tool for conducting video Quality of Experience (QoE) studies. Participants watch videos and rate them on comprehension and comfort.

## 📋 Requirements

- Docker Desktop (Windows/Mac) or Docker (Linux)
- Your video files

**That's it.** No Python, no complex setup.

## 🚀 Quick Start

### 1. Download the Project

Download or clone this repository to your computer:

```bash
git clone <repository-url>
cd video-qoe
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
└── videos/          ← PUT YOUR VIDEOS HERE
```

### 2. Add Your Videos

Place your video files in the `videos/` folder.

**IMPORTANT: Video Naming Format**

Videos must be named like this:
```
{fragment_id} fragment {delay}.mp4
```

Examples:
- `1 fragment 00.mp4` → Fragment 1, delay 0.0 seconds
- `1 fragment 05.mp4` → Fragment 1, delay 0.5 seconds
- `2 fragment 10.mp4` → Fragment 2, delay 1.0 seconds
- `3 fragment 15.mp4` → Fragment 3, delay 1.5 seconds

The program automatically extracts:
- **Fragment ID** (first number)
- **Delay** (last number ÷ 10 = seconds)

Supported formats: `.mp4`, `.mkv`, `.webm`, `.avi`

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
3. Watch each video completely
4. Rate on two scales (1-5):
   - Comprehension: How well you understood what happened
   - Comfort: How comfortable was watching
5. Add optional comments
6. Click "Dalej" (Next) to continue

The system will automatically show all videos and save your ratings.

## 📊 Exporting Results

After testing is complete, download the results:

1. Go to: **http://localhost:8080/export**
2. Or click "Pobierz CSV" on the completion screen

The CSV file includes:
- `participant_id` - Participant identifier
- `video` - Video filename
- `fragment_id` - Fragment number
- `delay_seconds` - Delay in seconds
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

### Problem: "Port 8080 is already in use"

**Solution:** Change the port in `docker-compose.yml`:

```yaml
ports:
  - "9000:8080"  ← Use 9000 instead (or any free port)
```

Then access at: http://localhost:9000

### Problem: Videos don't play

**Solutions:**
1. Check video naming format: `{number} fragment {number}.mp4`
2. Ensure files are in the `videos/` folder
3. Try converting to MP4 format (most compatible)
4. Check browser console (F12) for errors

### Problem: "No videos found"

**Solutions:**
1. Verify videos are in `videos/` folder
2. Check filenames match the required format
3. Restart Docker: `docker-compose down` then `docker-compose up --build`

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

1. Zip the entire folder (including videos)
2. Send to participants
3. They only need Docker installed
4. They run: `docker-compose up --build`

Each person's data is saved independently.

## 🎯 Best Practices

1. **Test first:** Run a trial with 2-3 videos before the real study
2. **Clear instructions:** Tell participants to watch completely before rating
3. **Unique IDs:** Assign unique participant IDs (P01, P02, etc.)
4. **Backup data:** Export CSV after each participant
5. **Browser:** Chrome/Firefox work best; Safari may have issues with some video formats

## 📝 Data Structure

The SQLite database (`data/ratings.db`) stores all ratings. Export to CSV for analysis in Excel, Python, R, etc.

Example CSV output:
```csv
id,participant_id,video,fragment_id,delay_seconds,comprehension_rating,comfort_rating,comments,timestamp
1,P01,1 fragment 00.mp4,1,0.0,4,5,"Good quality",2024-01-07T10:30:00
2,P01,1 fragment 05.mp4,1,0.5,3,3,"Slight delay noticed",2024-01-07T10:32:15
```

## 🔒 Security Note

This tool uses basic HTTP authentication. For public internet deployment, consider adding HTTPS and stronger authentication.

For local network use (recommended), the default setup is sufficient.

## 📧 Support

If you encounter issues:
1. Check this README's Troubleshooting section
2. Verify all files are in the correct folders
3. Check Docker logs: `docker-compose logs`

## 📄 License

Open source - modify as needed for your research.

---

**Ready to start?** Put your videos in `videos/` and run `docker-compose up --build`!