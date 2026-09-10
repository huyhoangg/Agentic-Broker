# Dockerfile Siêu Nhẹ Cho Render Web Service 24/7 (Groq Cloud STT + Supabase + UptimeRobot)
FROM python:3.11-slim

# Cài đặt ffmpeg và các công cụ hệ thống nhẹ
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files
COPY package*.json ./

# Cài đặt các gói Python: vnstock, vnai, pandas, curl-cffi, yt-dlp
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir yt-dlp curl-cffi imageio-ffmpeg soundfile requests psycopg2-binary pandas "vnstock>=4.0.6" "vnai>=2.5.7"

# Copy toàn bộ code vào container
COPY . .

EXPOSE 10000

# Chạy Web Server + Background Monitor Thread
CMD ["python", "python/server.py"]
