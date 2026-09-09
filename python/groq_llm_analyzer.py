"""
Groq Cloud LLM Financial Analysis Helper (GPT-OSS-120B / GPT-OSS-20B)
Extracts actionable stock insights, trends, stop loss & targets, while filtering gossip.
"""
import os
import requests

# Auto-load .env file
env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_file):
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ[k.strip()] = v.strip()

def analyze_transcript_with_groq_llm(transcript_text: str) -> dict:
    """
    Sử dụng Groq Cloud LLM (openai/gpt-oss-120b) để phân tích chuyên sâu:
    - Loại bỏ hoàn toàn tán gẫu, trò chuyện cá nhân, nickname.
    - Trích xuất mã cổ phiếu, xu hướng (Tăng/Giảm/Sideway), điểm Mua/Bán/Cắt lỗ.
    """
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    if not groq_key or not transcript_text or len(transcript_text.strip()) < 10:
        return {
            "summary": "Không có đủ dữ liệu văn bản để phân tích.",
            "clean_analysis": "Chưa phát hiện thông tin giao dịch.",
            "tickers_detail": []
        }

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json"
    }

    system_prompt = (
        "Bạn là Chuyên gia Phân tích Tài chính & Đầu tư Chứng khoán Việt Nam.\n"
        "Nhiệm vụ của bạn là đọc đoạn văn bản trích xuất từ livestream và tạo BÁO CÁO PHÂN TÍCH CHUYÊN SÂU:\n\n"
        "BẮT BUỘC LỌC BỎ:\n"
        "- Loại bỏ hoàn toàn trò chuyện cá nhân, tán gẫu, chào hỏi, tên nick khán giả (như Tiramisu, Bạc Xỉu Đá...).\n\n"
        "TẬP TRUNG NỘI DUNG:\n"
        "1. Mã Cổ Phiếu được nhắc tới (SSI, HPG, DIG, VHM...)\n"
        "2. Xu hướng (Tăng / Giảm / Sideway / Tích lũy)\n"
        "3. Khuyến nghị & Mốc giá (Mua / Bán / Giữ / Stop-loss / Hỗ trợ / Kháng cự)\n"
        "4. Thời sự / Nhận định thị trường chung (nếu có)\n\n"
        "Trình bày ngắn gọn, súc tích bằng Tiếng Việt theo cấu trúc rõ ràng."
    )

    payload = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Đoạn văn bản bóc tách âm thanh:\n\"{transcript_text}\""}
        ],
        "temperature": 0.1
    }

    for attempt in range(1, 3):
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                result_text = res.json()["choices"][0]["message"]["content"]
                return {
                    "clean_analysis": result_text
                }
            elif res.status_code in [404, 400]:
                # Fallback to gpt-oss-20b if 120b unavailable
                payload["model"] = "openai/gpt-oss-20b"
                res2 = requests.post(url, headers=headers, json=payload, timeout=30)
                if res2.status_code == 200:
                    return {"clean_analysis": res2.json()["choices"][0]["message"]["content"]}
        except Exception as e:
            print(f"⚠️ Groq LLM Analysis error: {e}")

    return {"clean_analysis": "Chưa thể kết nối tới Groq AI LLM."}

if __name__ == "__main__":
    sample = "iramisu ơi, bạn cầm giá nào Thụ nói cả nhà mấy con này chả chết đâu anh em hâm tâm nha Giữ đi cả nhà, nay anh mua vĩ không hả SSI với HPG nay đà tăng tốt gãy 30 thì bán nha Rồi, ghê LED 26 giữ không bạn hả, tạm giữ đi anh Bạc Xỉu Đá"
    res = analyze_transcript_with_groq_llm(sample)
    print("ANALYSIS RESULT:\n", res["clean_analysis"])
