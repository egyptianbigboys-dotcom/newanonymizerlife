# Use a slim Python base image
FROM python:3.8-slim

# Install system dependencies required by Pillow, Fawkes, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    git build-essential libgl1 libglib2.0-0 libsm6 libxrender1 libxext6 \
 && rm -rf /var/lib/apt/lists/*

# Set working directory inside container
WORKDIR /app

# Avoid pip cache bloat
ENV PIP_NO_CACHE_DIR=1

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy handler script into the image
COPY handler.py .

# Create temp directories for processing images
RUN mkdir -p /tmp/in /tmp/out

# Default command: start the RunPod serverless handler
CMD ["python", "-u", "handler.py"]
