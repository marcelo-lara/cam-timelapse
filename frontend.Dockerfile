# Base image with Python 3.9
FROM python:3.9-slim

# Install dependencies for OpenCV and FFmpeg
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    ffmpeg \
    libx264-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the timezone to America/Argentina/Buenos_Aires (UTC-3)
ENV TZ=America/Argentina/Buenos_Aires

# Set environment variable to ensure print statements are flushed immediately
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy requirements.txt for Python dependencies
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python application code
COPY . .

# Expose port if needed (Not mandatory for this task, but useful if your app expands)
EXPOSE 5000

# Command to run the application
CMD ["python", "frontend.py"]
