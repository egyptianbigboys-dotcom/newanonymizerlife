# Stable base for TF 1.15.x wheels
FROM python:3.7-bullseye

# System libs for Pillow and image IO
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git \
    libjpeg-dev zlib1g-dev libpng-dev libtiff5 libopenjp2-7 libwebp-dev \
    libgl1 libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PIP_NO_CACHE_DIR=1 PIP_DEFAULT_TIMEOUT=1000

# --- Pin the low-level stack FIRST (avoid source builds) ---
# numpy 1.19.5 is the last manylinux wheel that plays well with TF1.x on Py3.7
RUN python -m pip install --upgrade pip "setuptools<60" wheel \
 && python -m pip install -vv --only-binary=:all: \
      "numpy==1.19.5" \
      "Pillow==9.5.0" \
      "scipy==1.4.1" \
      "h5py==2.10.0"

# --- TensorFlow 1.x + Keras 2.2.x + compat deps ---
RUN python -m pip install -vv \
      "tensorflow==1.15.5" \
      "keras==2.2.5" \
      "gast==0.2.2" \
      "protobuf==3.20.*" \
      "wrapt==1.14.1" \
      "termcolor==1.1.0" \
      "absl-py==0.9.0"

# Now install ONLY your lightweight app deps from requirements.txt
COPY requirements.txt .
RUN python -m pip install -vv -r requirements.txt

# Copy handler
COPY handler.py .

# Runtime temp dirs
RUN mkdir -p /tmp/in /tmp/out

CMD ["python", "-u", "handler.py"]
