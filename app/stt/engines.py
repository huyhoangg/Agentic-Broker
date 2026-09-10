"""Groq Whisper cloud STT + Groq LLM transcript analysis."""
import logging
import os
import re
import time

import requests

from .. import config

log = logging.getLogger("stt")

HALLUCINATION_RE = re.compile(r"(?:\b[a-zA-Z]{1,2}\s+){3,}[a-zA-Z]{1,2}\b")

PROMPT_HINT = "Chứng khoán Việt Nam, HCM, HPG, SSI, DIG, stop loss, break"

ANALYSIS_SYSTEM_PROMPT = (
    "Bạn là Chuyên gia Phân tích Tài chính & Đầu tư Chứng khoán Việt Nam.\n"
    "Đọc đoạn transcript trích từ livestream broker và lọc bỏ hoàn toàn tán gẫu, "
    "chào hỏi, tên nick khán giả. Chỉ giữ lại nội dung đầu tư: mã cổ phiếu được nhắc tới, "
    "xu hướng (Tăng/Giảm/Sideway/Tích lũy), khuyến nghị & mốc giá (Mua/Bán/Giữ/Stop-loss/"
    "Hỗ trợ/Kháng cự), nhận định thị trường. Nếu không có nội dung đầu tư, trả về đúng "
    "chuỗi: 'Không có thông tin giao dịch.' Trình bày ngắn gọn bằng tiếng Việt."
)


def clean_text(raw: str) -> str:
    if not raw:
        return ""
    cleaned = HALLUCINATION_RE.sub("", raw)
    return re.sub(r"\s+", " ", cleaned).strip()


def transcribe(audio_path: str) -> str | None:
    """Groq Whisper STT with retry. Returns cleaned text or None."""
    if not config.GROQ_API_KEY:
        log.warning("GROQ_API_KEY missing, cannot transcribe")
        return None

    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    for attempt in range(1, 4):
        try:
            with open(audio_path, "rb") as f:
                res = requests.post(
                    url,
                    headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
                    files={"file": (os.path.basename(audio_path), f, "audio/mpeg")},
                    data={
                        "model": config.WHISPER_MODEL,
                        "language": "vi",
                        "temperature": "0.0",
                        "prompt": PROMPT_HINT,
                        "response_format": "verbose_json",
                    },
                    timeout=300,
                )
            if res.status_code == 200:
                text = clean_text(res.json().get("text", ""))
                log.info("groq stt ok: %s", text[:80])
                return text
            log.warning("groq stt %s: %s", res.status_code, res.text[:200])
            if res.status_code == 429:
                time.sleep(5 * attempt)
        except Exception as e:
            log.warning("groq stt error (attempt %s/3): %s", attempt, e)
            time.sleep(2)
    return None


def analyze(text: str) -> str | None:
    """Groq LLM analysis: filter gossip, extract tickers/levels/advices."""
    if not config.GROQ_API_KEY or not text or len(text.strip()) < 10:
        return None

    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": config.LLM_MODEL,
        "messages": [
            {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
            {"role": "user", "content": f"Transcript:\n\"{text}\""},
        ],
        "temperature": 0.1,
    }
    try:
        res = requests.post(
            url,
            headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
            json=payload,
            timeout=60,
        )
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]
        # model fallback
        fallback = dict(payload, model="openai/gpt-oss-20b")
        res = requests.post(
            url,
            headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
            json=fallback,
            timeout=60,
        )
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]
        log.warning("groq llm %s: %s", res.status_code, res.text[:200])
    except Exception as e:
        log.warning("groq llm error: %s", e)
    return None
