"""
Multi-Channel Manager for TikTok Live Broker Assistant
"""
import os
import json

CHANNELS_FILE = os.path.join(os.path.dirname(__file__), "..", "monitored_channels.json")
DEFAULT_CHANNELS = ["@vtv24", "@chungkhoanssi", "@hsc_securities"]

def load_monitored_channels():
    if os.path.exists(CHANNELS_FILE):
        try:
            with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return data
        except Exception:
            pass

    # Read from environment variable TIKTOK_CHANNEL if set (comma separated: "@kenh1, @kenh2")
    env_channels = os.getenv("TIKTOK_CHANNEL", "")
    if env_channels:
        channels = [c.strip() for c in env_channels.split(",") if c.strip()]
        if channels:
            return channels

    return DEFAULT_CHANNELS

def save_monitored_channels(channels_list):
    try:
        with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
            json.dump(channels_list, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Lỗi lưu channels list: {e}")
        return False

def add_channel(channel_name: str):
    clean = channel_name.strip()
    if not clean.startswith("@"):
        clean = "@" + clean
    
    channels = load_monitored_channels()
    if clean.lower() not in [c.lower() for c in channels]:
        channels.append(clean)
        save_monitored_channels(channels)
        return True, clean, channels
    return False, clean, channels

def remove_channel(channel_name: str):
    clean = channel_name.strip()
    if not clean.startswith("@"):
        clean = "@" + clean
        
    channels = load_monitored_channels()
    new_list = [c for c in channels if c.lower() != clean.lower()]
    if len(new_list) < len(channels):
        save_monitored_channels(new_list)
        return True, clean, new_list
    return False, clean, channels
