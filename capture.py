import cv2
import os
import time
from datetime import datetime

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

CAPTURE_INTERVAL = int(os.getenv('CAPTURE_INTERVAL', 120))  # Time between frame captures
FRAME_WIDTH = int(os.getenv('FRAME_WIDTH', 1280))
FRAME_HEIGHT = int(os.getenv('FRAME_HEIGHT', 720))

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
        return filename
    else:
        print(f"Error: Unable to read frame from {rtsp_url}")
        cap.release()
        return None

def capture_loop(OUTPUT_DIR):
    print("Capture loop started")
    try:
        while True:
            capture_frame(RTSP_URL, OUTPUT_DIR)
            time.sleep(CAPTURE_INTERVAL)
    except Exception as e:
        print(f"Capture loop encountered an error: {e}")
    except KeyboardInterrupt:
        print("Stopping the capture loop.")