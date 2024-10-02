import cv2
from glob import glob
import os
import subprocess
from datetime import datetime

def create_timelapse_videos(FRAMES_DIR, VIDEO_DIR, FPS = 30):
    print("Creating timelapse videos...")

    # Get all the images in the FRAMES_DIR directory
    image_files = glob(os.path.join(FRAMES_DIR, "*.jpg"))
    
    # Get today's date string
    today_date_str = datetime.now().strftime("%Y%m%d")

    # Group images by date
    images_by_date = {}
    for image_file in image_files:
        date_str = os.path.basename(image_file).split('_')[0]
        if date_str == today_date_str:
            continue  # Skip images with today's timestamp
                
        if date_str not in images_by_date:
            images_by_date[date_str] = []
        images_by_date[date_str].append(image_file)
    
    # Create a timelapse video for each day
    for date_str, images in images_by_date.items():
        images.sort()  # Ensure images are in chronological order
        frame = cv2.imread(images[0])
        height, width, layers = frame.shape
        video_filename = os.path.join(VIDEO_DIR, f"{date_str}.mp4")
        print(f"Rendering: {video_filename}")

        # Generate a file list for FFmpeg input
        file_list = os.path.join(FRAMES_DIR, f"{date_str}_file_list.txt")
        with open(file_list, 'w') as f:
            for image in images:
                f.write(f"file '{image}'\n")

        # Use FFmpeg to create the video
        ffmpeg_command = [
            'ffmpeg', '-y', '-r', str(FPS), '-f', 'concat', '-safe', '0',
            '-i', file_list, '-vcodec', 'libx264', '-preset', 'slower', '-crf', '24', '-pix_fmt', 'yuv420p', video_filename
        ]
        subprocess.run(ffmpeg_command)

        # Infer the thumbnail path based on the video path
        thumbnail_path = os.path.splitext(video_filename)[0] + ".jpg"

        # Save the middle frame as the thumbnail
        if images:
            thumb_frame = int(len(images) / 2)
            thumb_image = cv2.imread(images[thumb_frame])
            cv2.imwrite(thumbnail_path, thumb_image)

        # Remove the file list after video creation
        os.remove(file_list)

        # Remove the source images
        for image in images:
            os.remove(image)


    print("Timelapse videos created.")
