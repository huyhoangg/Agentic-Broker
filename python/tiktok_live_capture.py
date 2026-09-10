"""
TikTok Live Stream Audio Extractor & Real-time Stream Pipe
"""
import os
import sys
import subprocess
import time
import imageio_ffmpeg
import shutil

system_ffmpeg = shutil.which("ffmpeg")
if system_ffmpeg:
    ffmpeg_binary = system_ffmpeg
else:
    ffmpeg_binary = imageio_ffmpeg.get_ffmpeg_exe()

def get_tiktok_live_audio_stream_url(tiktok_username: str) -> str:
    """
    Trích xuất trực tiếp URL luồng HLS audio/video từ TikTok Livestream.
    Sử dụng đa tầng (yt-dlp --impersonate chrome + curl_cffi) để vượt qua chặn IP datacenter trên Render.
    """
    clean_username = tiktok_username.replace("@", "").strip()
    tiktok_url = f"https://www.tiktok.com/@{clean_username}/live"
    
    print(f"[+] Đang kết nối tới TikTok Live: {tiktok_url}")
    
    # Method 1: yt-dlp với --impersonate chrome (Vượt bot-check của Cloudflare)
    cmd1 = ["yt-dlp", "--impersonate", "chrome", "-g", tiktok_url]
    try:
        res = subprocess.run(cmd1, capture_output=True, text=True, timeout=18)
        if res.returncode == 0 and res.stdout.strip():
            urls = [u for u in res.stdout.strip().split("\n") if u.startswith("http")]
            if urls:
                print(f"✅ (Method 1: yt-dlp chrome) Đã lấy thành công luồng Stream HLS của @{clean_username}")
                return urls[0]
    except Exception as e:
        print(f"⚠️ Method 1 error: {e}")

    # Method 2: curl_cffi (Trích xuất trực tiếp SIGI_STATE JSON từ HLS payload)
    try:
        from curl_cffi import requests as c_requests
        import json, re
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.tiktok.com/"
        }
        res_curl = c_requests.get(tiktok_url, headers=headers, impersonate="chrome120", timeout=12)
        if res_curl.status_code == 200 and len(res_curl.text) > 10000:
            m = re.search(r'<script id="SIGI_STATE" type="application/json">(.*?)</script>', res_curl.text)
            if m:
                sigi = json.loads(m.group(1))
                cr = sigi.get("CurrentRoom", {})
                room_info = cr.get("roomInfo", {})
                if room_info:
                    status = room_info.get("status")
                    if status in [2, 1, "2", "1"]:  # 2 means LIVE
                        stream_obj = room_info.get("stream_url", {})
                        hls_url = stream_obj.get("hls_pull_url") or stream_obj.get("flv_pull_url", {}).get("FULL_HD1")
                        if hls_url:
                            print(f"✅ (Method 2: curl_cffi SIGI_STATE) Đã lấy thành công luồng HLS của @{clean_username}")
                            return hls_url
    except Exception as e:
        print(f"⚠️ Method 2 (curl_cffi) error: {e}")

    # Method 3: yt-dlp với User-Agent giả lập Chrome & Referer
    cmd3 = [
        "yt-dlp",
        "-g",
        "--user-agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "--referer", "https://www.tiktok.com/",
        tiktok_url
    ]
    try:
        res3 = subprocess.run(cmd3, capture_output=True, text=True, timeout=15)
        if res3.returncode == 0 and res3.stdout.strip():
            urls = [u for u in res3.stdout.strip().split("\n") if u.startswith("http")]
            if urls:
                print(f"✅ (Method 3: yt-dlp custom headers) Đã lấy thành công luồng Stream HLS của @{clean_username}")
                return urls[0]
    except Exception as e:
        print(f"⚠️ Method 3 error: {e}")

    return None

def capture_stream_audio_chunks(stream_url: str, output_dir="chunks", chunk_sec=10):
    os.makedirs(output_dir, exist_ok=True)
    out_pattern = os.path.join(output_dir, "frame_%03d.wav")

    print(f"🎙️ Đang bắt luồng Audio từ Live Stream -> Cắt thành các file {chunk_sec}s vào folder '{output_dir}'...")

    ffmpeg_cmd = [
        ffmpeg_binary,
        "-i", stream_url,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        "-f", "segment",
        "-segment_time", str(chunk_sec),
        "-reset_timestamps", "1",
        out_pattern
    ]

    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return process

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "@chng.khon.cng.win"
    url = get_tiktok_live_audio_stream_url(target)
    if url:
        print(f"Direct Stream URL: {url[:100]}...")
