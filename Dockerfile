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
    && rm -rf /var/lib/apt/lists/*

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
CMD ["python", "app.py"]
