import cv2
import time
import os
from datetime import datetime
import schedule
import threading
import ffmpeg
from flask import Flask, render_template, request, jsonify, send_from_directory

# Read the RTSP_URL from the Docker secret file
def read_secret(secret_name):
    secret_path = f'/run/secrets/{secret_name}'
    try:
        with open(secret_path, 'r') as secret_file:
            return secret_file.read().strip()
    except FileNotFoundError:
        print(f"Error: Secret {secret_name} not found.")
        return None

# Retrieve the RTSP URL from the Docker secret
RTSP_URL = read_secret('rtsp_url')
if not RTSP_URL:
    raise ValueError("RTSP_URL not found in Docker secrets")

# Directories for frames, videos, and thumbnails
OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'timelapse_frames')
VIDEO_DIR = os.getenv('VIDEO_DIR', 'timelapse_videos')
THUMBNAIL_DIR = os.getenv('THUMBNAIL_DIR', 'timelapse_thumbnails')
CAPTURE_INTERVAL = int(os.getenv('CAPTURE_INTERVAL', 120))  # Time between frame captures
FRAME_WIDTH = int(os.getenv('FRAME_WIDTH', 1280))
FRAME_HEIGHT = int(os.getenv('FRAME_HEIGHT', 720))
FPS = int(os.getenv('FPS', 30))

# Ensure the necessary directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(THUMBNAIL_DIR, exist_ok=True)

app = Flask(__name__)

def generate_thumbnail(video_path, thumbnail_path):
    """Generate a thumbnail for a given video."""
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Error: Unable to open video {video_path}")
        return None

    # Read the first frame
    ret, frame = cap.read()
    
    if ret:
        # Save the frame as the thumbnail
        cv2.imwrite(thumbnail_path, frame)
        print(f"Generated thumbnail for {video_path}")
    
    cap.release()

def create_timelapse(video_output, selected_images, fps=30):
    if len(selected_images) == 0:
        print("No frames to compile into a video.")
        return

    input_images = [os.path.join(OUTPUT_DIR, img) for img in selected_images]

    # Use ffmpeg to create a video from the selected frames
    (
        ffmpeg
        .input('pipe:', format='image2pipe', framerate=fps)
        .output(video_output, vcodec='libx264', pix_fmt='yuv420p')
        .overwrite_output()
        .run(input=bytes().join(open(img, 'rb').read() for img in input_images))
    )
    print(f"Timelapse video created: {video_output}")

    # Generate a thumbnail for the video
    thumbnail_output = os.path.join(THUMBNAIL_DIR, f"{os.path.basename(video_output)}.jpg")
    generate_thumbnail(video_output, thumbnail_output)

# Scheduled job to generate timelapse video at midnight every day
def daily_timelapse():
    today_date = datetime.now().strftime("%Y-%m-%d")
    video_output = os.path.join(VIDEO_DIR, f"{today_date}_timelapse.mp4")

    # Get all images in the directory, sorted by their timestamps
    images = sorted([img for img in os.listdir(OUTPUT_DIR) if img.endswith(".jpg")])

    if len(images) == 0:
        print(f"No images found to create timelapse for {today_date}")
        return

    create_timelapse(video_output, images)

# Flask route to serve thumbnails from the timelapse_thumbnails folder
@app.route('/timelapse_thumbnails/<filename>')
def timelapse_thumbnails(filename):
    return send_from_directory(THUMBNAIL_DIR, filename)

# Flask route to serve the last generated video
@app.route('/download_timelapse/<filename>')
def download_timelapse(filename):
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
    thumbnails = {vid: f"{vid}.jpg" for vid in videos}

    return render_template('index.html', videos=thumbnails)

def capture_frame(rtsp_url):
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        print(f"Error: Unable to open video stream {rtsp_url}")
        return None

    ret, frame = cap.read()

    if ret:
        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(OUTPUT_DIR, f"{timestamp}.jpg")
        cv2.imwrite(filename, frame)
        print(f"Captured frame at {timestamp}")
        cap.release()
        return filename
    else:
        print(f"Error: Unable to read frame from {rtsp_url}")
        cap.release()
        return None
    
def capture_loop():
    print("Capture loop started")
    try:
        while True:
            capture_frame(RTSP_URL)
            time.sleep(CAPTURE_INTERVAL)
    except Exception as e:
        print(f"Capture loop encountered an error: {e}")
    except KeyboardInterrupt:
        print("Stopping the capture loop.")
        
# Start the scheduler in a separate thread
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

def run_flask():
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    # Start the capture loop in a separate thread
    capture_thread = threading.Thread(target=capture_loop, name="CaptureThread")
    capture_thread.daemon = True
    capture_thread.start()

    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=run_scheduler, name="SchedulerThread")
    scheduler_thread.daemon = True
    scheduler_thread.start()

    # Start the Flask server in the main thread
    run_flask()
