# Dockerfile cho Render Web Service 24/7 (TikTok Seamless Live Audio Streamer + UptimeRobot Keep-Alive)
FROM python:3.11-slim

# Cài đặt ffmpeg và các công cụ hệ thống
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files
COPY package*.json ./

# Cài đặt Python requirements
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir yt-dlp openai-whisper imageio-ffmpeg soundfile requests

# Copy toàn bộ code vào container
COPY . .

EXPOSE 10000

# Chạy Web Server + Background Monitor Thread
CMD ["python", "python/server.py"]
