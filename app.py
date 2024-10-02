import os
from datetime import datetime
import threading
from flask import Flask, render_template, request, jsonify, send_from_directory

from capture import capture_loop
from render import create_timelapse_videos

# Directories for frames, videos, and thumbnails
OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'timelapse_frames')
VIDEO_DIR = os.getenv('VIDEO_DIR', 'timelapse_videos')
THUMBNAIL_DIR = os.getenv('THUMBNAIL_DIR', VIDEO_DIR)
FPS = int(os.getenv('FPS', 30))

# Ensure the necessary directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(THUMBNAIL_DIR, exist_ok=True)

app = Flask(__name__)

# Flask route to serve thumbnails from the timelapse_thumbnails folder
@app.route('/timelapse_thumbnails/<filename>')
def timelapse_thumbnails(filename):
    return send_from_directory(THUMBNAIL_DIR, filename)

# Flask route to serve the last generated video
@app.route('/timelapse_videos/<filename>')
def timelapse_videos(filename):
    video_output = os.path.join(VIDEO_DIR, filename)
    
    if os.path.exists(video_output):
        return send_from_directory(VIDEO_DIR, os.path.basename(video_output), as_attachment=True)
    else:
        return jsonify({"status": "error", "message": "No timelapse video found"}), 404

# Flask route to render the main page with video thumbnails
@app.route('/')
def index():
    # Get all video files and corresponding thumbnails
    videos = sorted([vid for vid in os.listdir(VIDEO_DIR) if vid.endswith(".mp4")])
    thumbnails = {vid: f"{os.path.splitext(vid)[0]}.jpg" for vid in videos}

    return render_template('index.html', videos=thumbnails)

def run_flask():
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    # recreate timelapse videos on startup
    create_timelapse_videos(OUTPUT_DIR, VIDEO_DIR, FPS)

    # Start the capture loop in a separate thread
    capture_thread = threading.Thread(target=capture_loop, args=(OUTPUT_DIR, VIDEO_DIR, FPS,), name="CaptureThread")
    capture_thread.daemon = True
    capture_thread.start()

    # Start the Flask server in the main thread
    run_flask()
