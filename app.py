import cv2
import time
import os
from datetime import datetime
import ffmpeg
import threading
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

# Other configurations
CAPTURE_INTERVAL = int(os.getenv('CAPTURE_INTERVAL', 120))
OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'timelapse_frames')
VIDEO_OUTPUT = os.getenv('VIDEO_OUTPUT', 'timelapse_video.mp4')
FRAME_WIDTH = int(os.getenv('FRAME_WIDTH', 1280))
FRAME_HEIGHT = int(os.getenv('FRAME_HEIGHT', 720))
FPS = int(os.getenv('FPS', 30))

# Ensure the output directory exists
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

app = Flask(__name__)

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

# Flask route to serve images from the timelapse_frames folder
@app.route('/timelapse_frames/<filename>')
def timelapse_frames(filename):
    return send_from_directory(OUTPUT_DIR, filename)

# Flask route to serve the last generated video
@app.route('/download_timelapse')
def download_timelapse():
    if os.path.exists(VIDEO_OUTPUT):
        return send_from_directory(os.path.dirname(VIDEO_OUTPUT), os.path.basename(VIDEO_OUTPUT), as_attachment=True)
    else:
        return jsonify({"status": "error", "message": "No timelapse video found"}), 404

# Flask route to render the main page with image list
@app.route('/')
def index():
    images = sorted([img for img in os.listdir(OUTPUT_DIR) if img.endswith(".jpg")])
    enumerated_images = list(enumerate(images))
    video_exists = os.path.exists(VIDEO_OUTPUT)
    return render_template('index.html', images=enumerated_images, video_exists=video_exists)

# Flask route to generate a timelapse for a selected range of images
@app.route('/generate_timelapse', methods=['POST'])
def generate_timelapse():
    start_idx = int(request.form.get('start_idx'))
    end_idx = int(request.form.get('end_idx'))

    images = sorted([img for img in os.listdir(OUTPUT_DIR) if img.endswith(".jpg")])

    if start_idx < 0 or end_idx >= len(images) or start_idx > end_idx:
        return jsonify({"status": "error", "message": "Invalid indices"}), 400

    selected_images = images[start_idx:end_idx + 1]
    create_timelapse(VIDEO_OUTPUT, selected_images)

    return jsonify({"status": "success", "message": f"Timelapse created: {VIDEO_OUTPUT}"})

# Flask route to generate a timelapse using all images
@app.route('/generate_full_timelapse', methods=['POST'])
def generate_full_timelapse():
    images = sorted([img for img in os.listdir(OUTPUT_DIR) if img.endswith(".jpg")])

    if len(images) == 0:
        return jsonify({"status": "error", "message": "No images found"}), 400

    create_timelapse(VIDEO_OUTPUT, images)

    return jsonify({"status": "success", "message": f"Full timelapse created: {VIDEO_OUTPUT}"})

def create_timelapse(video_output, selected_images, fps=FPS):
    if len(selected_images) == 0:
        print("No frames to compile into a video.")
        return

    input_images = [os.path.join(OUTPUT_DIR, img) for img in selected_images]

    # Use ffmpeg to create a video from the selected frames
    (
        ffmpeg
        .input('pipe:', format='image2pipe', framerate=fps)
        .output(video_output, vcodec='libx264', pix_fmt='yuv420p')
        .overwrite_output()  # This tells ffmpeg to overwrite the output file if it exists
        .run(input=bytes().join(open(img, 'rb').read() for img in input_images))
    )
    print(f"Timelapse video created: {video_output}")

def run_flask():
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    # Start the capture loop in a separate thread
    capture_thread = threading.Thread(target=capture_loop, name="CaptureThread")
    capture_thread.daemon = True
    capture_thread.start()

    # Wait for the capture thread to ensure it's running
    time.sleep(1)

    # Start the Flask server in the main thread
    run_flask()
