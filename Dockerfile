# Pinned combo that has prebuilt wheels for TF 2.2.x + numpy, Pillow, etc.
FROM python:3.8-bullseye

# System libs needed by Pillow (JPEG/PNG/WebP) and friends
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git \
    libjpeg-dev zlib1g-dev libpng-dev libtiff5 libopenjp2-7 libwebp-dev \
    libgl1 libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PIP_NO_CACHE_DIR=1 PIP_DEFAULT_TIMEOUT=1000

# Install build tooling and lock the low-level wheels FIRST
RUN python -m pip install --upgrade pip setuptools wheel \
 && python -m pip install -vv --only-binary=:all: \
      "numpy==1.19.5" \
      "Pillow==9.5.0"

# Install TF (CPU) version that plays nicely with Python 3.8 + numpy 1.19.x
RUN python -m pip install -vv "tensorflow==2.2.3"

# Now install the rest (runpod, fawkes, requests)
COPY requirements.txt .
RUN python -m pip install -vv -r requirements.txt

# Copy handler and start
COPY handler.py .
RUN mkdir -p /tmp/in /tmp/out
CMD ["python", "-u", "handler.py"]
