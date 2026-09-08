# Dockerfile cho Render Background Worker (TikTok Live Audio Record & AI Speech-to-Text)
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
COPY python/requirements.txt ./python/

# Cài đặt Python requirements
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir yt-dlp openai-whisper imageio-ffmpeg soundfile requests

# Copy toàn bộ code vào container
COPY . .

# Chạy Background Worker ngầm 24/7
CMD ["python", "python/render_worker.py"]
