import cv2
import os
import time
from datetime import datetime

from render import create_timelapse_videos

# Directories for frames, videos, and thumbnails
OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'timelapse_frames')
VIDEO_DIR = os.getenv('VIDEO_DIR', 'timelapse_videos')
THUMBNAIL_DIR = os.getenv('THUMBNAIL_DIR', VIDEO_DIR)
FPS = int(os.getenv('FPS', 30))

CAPTURE_INTERVAL = int(os.getenv('CAPTURE_INTERVAL', 120))  # Time between frame captures
FRAME_WIDTH = int(os.getenv('FRAME_WIDTH', 1280))
FRAME_HEIGHT = int(os.getenv('FRAME_HEIGHT', 720))
CURRENT_DAY = datetime.now().strftime("%Y%m%d")

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


def capture_frame(rtsp_url, OUTPUT_DIR):
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
        cap.release()
        # print(f"Capture: {filename}")
        return filename
    else:
        print(f"Error: Unable to read frame from {rtsp_url}")
        cap.release()
        return None

def capture_loop(OUTPUT_DIR, VIDEO_DIR, FPS):
    print("Capture loop started")
    global CURRENT_DAY
    try:
        while True:
            capture_frame(RTSP_URL, OUTPUT_DIR)

            if datetime.now().strftime("%Y%m%d") != CURRENT_DAY:
                print("New day, creating new directory")
                CURRENT_DAY = datetime.now().strftime("%Y%m%d")
                create_timelapse_videos(OUTPUT_DIR, VIDEO_DIR, FPS)

            time.sleep(CAPTURE_INTERVAL)
    except Exception as e:
        print(f"Capture loop encountered an error: {e}")
    except KeyboardInterrupt:
        print("Stopping the capture loop.")



if __name__ == '__main__':

    # Ensure the necessary directories exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(VIDEO_DIR, exist_ok=True)
    os.makedirs(THUMBNAIL_DIR, exist_ok=True)

    # recreate timelapse videos on startup
    create_timelapse_videos(OUTPUT_DIR, VIDEO_DIR, FPS)
    capture_loop(OUTPUT_DIR, VIDEO_DIR, FPS)