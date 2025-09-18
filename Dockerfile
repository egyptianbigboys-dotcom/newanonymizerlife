FROM python:3.8-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git build-essential libgl1 libglib2.0-0 libsm6 libxrender1 libxext6 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY rp_handler.py .

RUN mkdir -p /tmp/in /tmp/out

CMD ["python", "-u", "rp_handler.py"]
