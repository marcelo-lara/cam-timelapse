import cv2
import time
import os
from datetime import datetime
import ffmpeg
from flask import Flask, render_template, request, jsonify, send_from_directory

# Load RTSP_URL secret from Docker secrets
with open('/run/secrets/rtsp_url', 'r') as f:
    RTSP_URL = f.read().strip()

# Retrieve configuration from environment variables with default values
CAPTURE_INTERVAL = int(os.getenv('CAPTURE_INTERVAL', 120))
OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'timelapse_frames')
VIDEO_OUTPUT = os.getenv('VIDEO_OUTPUT', 'timelapse_video.mp4')
FRAME_WIDTH = int(os.getenv('FRAME_WIDTH', 1280))
FRAME_HEIGHT = int(os.getenv('FRAME_HEIGHT', 720))
FPS = int(os.getenv('FPS', 30))

app = Flask(__name__)

# Serve the timelapse frames folder
@app.route('/timelapse_frames/<filename>')
def timelapse_frames(filename):
    return send_from_directory(OUTPUT_DIR, filename)


# Ensure the output directory exists
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def capture_frame(rtsp_url, frame_index):
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        print(f"Error: Unable to open video stream {rtsp_url}")
        return None
    
    ret, frame = cap.read()
    
    if ret:
        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(OUTPUT_DIR, f"frame_{frame_index}_{timestamp}.jpg")
        cv2.imwrite(filename, frame)
        print(f"Captured frame {frame_index} at {timestamp}")
        cap.release()
        return filename
    else:
        print(f"Error: Unable to read frame from {rtsp_url}")
        cap.release()
        return None

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
        .run(input=bytes().join(open(img, 'rb').read() for img in input_images))
    )
    print(f"Timelapse video created: {video_output}")

@app.route('/')
def index():
    # Get list of images in the output directory
    images = sorted([img for img in os.listdir(OUTPUT_DIR) if img.endswith(".jpg")])
    
    # Enumerate the images in the backend
    enumerated_images = list(enumerate(images))

    # Pass the enumerated list to the template
    return render_template('index.html', images=enumerated_images)

@app.route('/generate_timelapse', methods=['POST'])
def generate_timelapse():
    start_idx = int(request.form.get('start_idx'))
    end_idx = int(request.form.get('end_idx'))
    
    images = sorted([img for img in os.listdir(OUTPUT_DIR) if img.endswith(".jpg")])
    
    # Validate indices
    if start_idx < 0 or end_idx >= len(images) or start_idx > end_idx:
        return jsonify({"status": "error", "message": "Invalid indices"}), 400
    
    selected_images = images[start_idx:end_idx + 1]
    
    create_timelapse(VIDEO_OUTPUT, selected_images)
    
    return jsonify({"status": "success", "message": f"Timelapse created: {VIDEO_OUTPUT}"})

def main():
    frame_index = 0
    try:
        while True:
            capture_frame(RTSP_URL, frame_index)
            frame_index += 1
            time.sleep(CAPTURE_INTERVAL)
    except KeyboardInterrupt:
        print("Stopping the image capture loop.")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
