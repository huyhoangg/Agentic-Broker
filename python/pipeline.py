"""
VN Stock TikTok Broker Audio Assistant - Production Pipeline Demo
Processing 10-second overlapping audio frames into actionable stock trading signals.
"""
import os
import json
import time
from typing import List, Dict
from ticker_mapper import extract_vn_tickers

# Sample TikTok Broker Stream Audio Slices (Simulated 10s Frames with 3s Overlap)
SIMULATED_FRAMES = [
    {
        "id": 1,
        "start": 0,
        "end": 10,
        "raw_stt": "Chào anh em nha, hôm nay VN-Index giữ nhịp rất tốt quanh vùng 1280 điểm. Hôm nay dòng thép đang có dấu hiệu mút mạnh đặc biệt là Hòa Phát."
    },
    {
        "id": 2,
        "start": 7,
        "end": 17,
        "raw_stt": "...dấu hiệu mút mạnh đặc biệt là Hòa Phát con HPG giá 28.5 này anh em gom dần vùng này được, mục tiêu ngắn hạn cản 31 nhé."
    },
    {
        "id": 3,
        "start": 14,
        "end": 24,
        "raw_stt": "...gom dần vùng giá này. Tiếp theo về nhóm chứng khoán thì anh chị em chú ý cổ phiếu SSI nhé. Ép-sơ-sơ-y hiện tại đang tạo đáy 2 rất đẹp."
    },
    {
        "id": 4,
        "start": 21,
        "end": 31,
        "raw_stt": "...đang tạo đáy 2 rất đẹp. SSI quanh 34.5 anh em mở vị thế được, kháng cự quanh 37. Còn dòng bất động sản con Đê Y Gê thì thôi ra hàng đi."
    },
    {
        "id": 5,
        "start": 28,
        "end": 38,
        "raw_stt": "...bất động sản con Đê Y Gê con DIG yếu quá, anh em nên hạ tỷ trọng bán chốt lời hoặc hạ margin vùng 26 nhé."
    }
]

class AudioWindowStreamEngine:
    def __init__(self, frame_sec=10, overlap_sec=3):
        self.frame_sec = frame_sec
        self.overlap_sec = overlap_sec
        self.step_sec = frame_sec - overlap_sec  # 7s step
        self.window_buffer = []

    def process_frame(self, frame_data: Dict) -> Dict:
        # 1. Extract stock symbols from STT text
        tickers = extract_vn_tickers(frame_data["raw_stt"])
        
        # 2. Extract action sentiment
        action = "THEO DÕI"
        text = frame_data["raw_stt"].lower()
        if any(w in text for w in ["gom", "mút", "múc", "mở vị thế", "mua"]):
            action = "MUA"
        elif any(w in text for w in ["bán", "ra hàng", "hạ tỷ trọng", "chốt lời"]):
            action = "BÁN"
        elif "cắt lỗ" in text:
            action = "CẮT LỖ"

        frame_result = {
            "frame_id": frame_data["id"],
            "time_range": f"{frame_data['start']}s - {frame_data['end']}s",
            "raw_text": frame_data["raw_stt"],
            "tickers": tickers,
            "signal": action
        }

        # 3. Add to sliding window buffer (keep 5 frames)
        self.window_buffer.append(frame_result)
        if len(self.window_buffer) > 5:
            self.window_buffer.pop(0)

        # 4. Consolidate context across window
        consolidated = self._synthesize_buffer()

        return {
            "current_frame": frame_result,
            "rolling_summary": consolidated
        }

    def _synthesize_buffer(self) -> Dict:
        all_tickers = {}
        for f in self.window_buffer:
            for t in f["tickers"]:
                symbol = t["ticker"]
                if symbol not in all_tickers:
                    all_tickers[symbol] = {
                        "ticker": symbol,
                        "name": t["name"],
                        "signals": []
                    }
                all_tickers[symbol]["signals"].append(f["signal"])

        summary = []
        for symbol, info in all_tickers.items():
            # Majority action
            buy_cnt = info["signals"].count("MUA")
            sell_cnt = info["signals"].count("BÁN")
            final_action = "MUA" if buy_cnt >= sell_cnt else "BÁN"

            summary.append({
                "ticker": symbol,
                "name": info["name"],
                "action": final_action,
                "frame_mentions": len(info["signals"])
            })

        return {
            "active_window_frames": len(self.window_buffer),
            "stock_recommendations": summary
        }

def run_pipeline():
    print("=" * 60)
    print("🚀 TRỢ LÝ BROKER CHỨNG KHOÁN VN - CHẠY DEMO 10S AUDIO OVERLAP")
    print("=" * 60)

    engine = AudioWindowStreamEngine(frame_sec=10, overlap_sec=3)

    for f in SIMULATED_FRAMES:
        print(f"\n[+] Audio Frame #{f['id']} [{f['start']}s -> {f['end']}s]")
        output = engine.process_frame(f)
        
        cur = output["current_frame"]
        print(f"    👉 STT Audio Text: {cur['raw_text']}")
        print(f"    🔍 Mã CK Phát Hiện: {[t['ticker'] for t in cur['tickers']]}")
        print(f"    🎯 Tín Hiệu Frame: {cur['signal']}")
        
        print("    --- [ 📊 Rolling Synthesis (Ghép Context Overlap) ] ---")
        for rec in output["rolling_summary"]["stock_recommendations"]:
            print(f"        • [{rec['ticker']}] - {rec['name']} => Khuyến Nghị: {rec['action']} (Xuất hiện {rec['frame_mentions']} frames)")

        time.sleep(0.5)

if __name__ == "__main__":
    run_pipeline()
