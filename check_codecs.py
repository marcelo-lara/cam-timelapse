import cv2

def check_codecs():
    build_info = cv2.getBuildInformation()
    print(build_info)

    # Optionally, you can search for codec-related information
    codec_keywords = ['Video I/O', 'FFmpeg', 'GStreamer', 'DirectShow']
    for line in build_info.split('\n'):
        if any(keyword in line for keyword in codec_keywords):
            print(line)

if __name__ == "__main__":
    check_codecs()