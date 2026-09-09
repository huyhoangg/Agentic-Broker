"""
TikTok Official Profile Metadata Fetcher via OEmbed & Stream Status
"""
import os
import sys
import requests

sys.path.append(os.path.dirname(__file__))
from tiktok_live_capture import get_tiktok_live_audio_stream_url

def fetch_tiktok_channel_profile(channel_username: str):
    """
    Lấy tên hiển thị chính thức của kênh TikTok qua TikTok Official OEmbed API
    """
    clean_username = channel_username.replace("@", "").strip()
    profile_url = f"https://www.tiktok.com/@{clean_username}"
    oembed_api = f"https://www.tiktok.com/oembed?url={profile_url}"

    display_name = clean_username
    try:
        res = requests.get(oembed_api, timeout=5).json()
        if "author_name" in res and res["author_name"]:
            display_name = res["author_name"]
    except Exception as e:
        print(f"ℹ️ Note OEmbed fetch for {channel_username}: {e}")

    # Check live status
    live_stream_url = get_tiktok_live_audio_stream_url(clean_username)
    is_live = True if live_stream_url else False

    return {
        "username": f"@{clean_username}",
        "display_name": display_name,
        "profile_url": profile_url,
        "is_live": is_live
    }
