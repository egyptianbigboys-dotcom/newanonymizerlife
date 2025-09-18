# Small Python base just to run the handler
FROM python:3.10-slim

# System deps for the Fawkes binary + image IO
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl unzip ca-certificates \
    libglib2.0-0 libgl1 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PIP_NO_CACHE_DIR=1

# --- Download Fawkes linux binary v0.3 ---
# If the mirror ever changes, grab the link from the official release page.
# We place the binary in /opt/fawkes and make it executable.
RUN mkdir -p /opt/fawkes \
 && curl -L -o /tmp/fawkes_linux.zip \
      https://mirror.cs.uchicago.edu/fawkes/files/fawkes_binary_linux-v0.3.zip \
 && unzip /tmp/fawkes_linux.zip -d /opt/fawkes \
 && chmod +x /opt/fawkes/protection \
 && rm -f /tmp/fawkes_linux.zip

# Python deps: ONLY what your handler needs (no tensorflow, no fawkes)
COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel \
 && python -m pip install -r requirements.txt

# App code
COPY handler.py .

# Runtime work dirs
RUN mkdir -p /tmp/in /tmp/out

# Default: start handler
CMD ["python", "-u", "handler.py"]
