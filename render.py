import cv2
import time
import os
from datetime import datetime
import schedule
import threading
import ffmpeg
from glob import glob

# Directories for frames, videos, and thumbnails
OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'timelapse_frames')
VIDEO_DIR = os.getenv('VIDEO_DIR', 'timelapse_videos')
THUMBNAIL_DIR = os.getenv('THUMBNAIL_DIR', VIDEO_DIR)
FPS = int(os.getenv('FPS', 30))

# Ensure the necessary directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(THUMBNAIL_DIR, exist_ok=True)

def create_timelapse_videos():
    print("Creating timelapse videos...")

    # Get all the images in the OUTPUT_DIR directory
    image_files = glob(os.path.join(OUTPUT_DIR, "*.jpg"))
    
    # Group images by date
    images_by_date = {}
    for image_file in image_files:
        date_str = os.path.basename(image_file).split('_')[0]
        if date_str not in images_by_date:
            images_by_date[date_str] = []
        images_by_date[date_str].append(image_file)
    
    # Create a timelapse video for each day
    for date_str, images in images_by_date.items():
        images.sort()  # Ensure images are in chronological order
        frame = cv2.imread(images[0])
        height, width, layers = frame.shape
        video_filename = os.path.join(VIDEO_DIR, f"{date_str}.mp4")
        print(f"rendering: {video_filename}")

        video = cv2.VideoWriter(video_filename, cv2.VideoWriter_fourcc(*'avc1'), FPS, (width, height))

        for image in images:
            frame = cv2.imread(image)
            video.write(frame)
        
        video.release()

        # Infer the thumbnail path based on the video path
        thumbnail_path = os.path.splitext(video_filename)[0] + ".jpg"

        # Save the first frame as the thumbnail
        if images:
            thumb_frame = int(len(images) / 2 )
            thumb_image = cv2.imread(images[thumb_frame])
            cv2.imwrite(thumbnail_path, thumb_image)

    print("Timelapse videos created.")

if __name__ == '__main__':
    # recreate timelapse videos on startup
    create_timelapse_videos()
