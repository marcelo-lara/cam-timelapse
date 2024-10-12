import os
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

if __name__ == '__main__':
    # recreate timelapse videos on startup
    create_timelapse_videos(OUTPUT_DIR, VIDEO_DIR, FPS)
    capture_loop(OUTPUT_DIR, VIDEO_DIR, FPS)
