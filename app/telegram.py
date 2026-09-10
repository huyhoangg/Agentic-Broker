import logging

import requests

from . import config

log = logging.getLogger("telegram")


def send_message(text: str) -> bool:
    if not config.NOTIFY_TELEGRAM or not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        log.info("telegram disabled: %s", text[:120].replace("\n", " "))
        return False
    try:
        res = requests.post(
            f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": config.TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
        if res.status_code != 200:
            log.warning("telegram error %s: %s", res.status_code, res.text[:200])
            return False
        return True
    except Exception as e:
        log.warning("telegram failed: %s", e)
        return False
