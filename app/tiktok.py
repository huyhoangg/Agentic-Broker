"""TikTok live stream URL resolution.

Multi-layer strategy to beat Cloudflare bot-check on datacenter IPs:
  1. yt-dlp with --impersonate chrome
  2. curl_cffi scraping SIGI_STATE json from the live page
  3. yt-dlp with manual chrome headers
"""
import json
import re
import subprocess

import requests

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def fetch_display_name(handle: str) -> str:
    clean = handle.replace("@", "").strip()
    try:
        res = requests.get(
            f"https://www.tiktok.com/oembed?url=https://www.tiktok.com/@{clean}", timeout=5
        ).json()
        if res.get("author_name"):
            return res["author_name"]
    except Exception:
        pass
    return clean


def resolve_live_stream_url(handle: str) -> str | None:
    clean = handle.replace("@", "").strip()
    url = f"https://www.tiktok.com/@{clean}/live"

    # Method 1: yt-dlp chrome impersonation
    try:
        res = subprocess.run(
            ["yt-dlp", "--impersonate", "chrome", "-g", url],
            capture_output=True,
            text=True,
            timeout=18,
        )
        if res.returncode == 0:
            urls = [u for u in res.stdout.strip().split("\n") if u.startswith("http")]
            if urls:
                return urls[0]
    except Exception:
        pass

    # Method 2: curl_cffi SIGI_STATE extraction
    try:
        from curl_cffi import requests as c_requests

        res = c_requests.get(
            url,
            headers={"User-Agent": USER_AGENT, "Referer": "https://www.tiktok.com/"},
            impersonate="chrome120",
            timeout=12,
        )
        if res.status_code == 200 and len(res.text) > 10000:
            m = re.search(
                r'<script id="SIGI_STATE" type="application/json">(.*?)</script>', res.text
            )
            if m:
                room = json.loads(m.group(1)).get("CurrentRoom", {}).get("roomInfo", {})
                if room.get("status") in (2, 1, "2", "1"):
                    stream = room.get("stream_url", {})
                    hls = stream.get("hls_pull_url") or stream.get("flv_pull_url", {}).get("FULL_HD1")
                    if hls:
                        return hls
    except Exception:
        pass

    # Method 3: yt-dlp with manual headers
    try:
        res = subprocess.run(
            [
                "yt-dlp", "-g",
                "--user-agent", USER_AGENT,
                "--referer", "https://www.tiktok.com/",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if res.returncode == 0:
            urls = [u for u in res.stdout.strip().split("\n") if u.startswith("http")]
            if urls:
                return urls[0]
    except Exception:
        pass

    return None
