"""
VN Stock Market Hourly Price Digest Notifier
Fetches real-time market prices for user watchlists & sends hourly Telegram updates during VN stock trading hours.
Trading hours (VN ICT): Mon-Fri, 09:00 - 11:30 and 13:00 - 15:00.
"""
import os
import time
import threading
from datetime import datetime, timedelta, timezone
import requests

from vnstock import Trading
from telegram_notifier import send_telegram_message, TELEGRAM_CHAT_ID
from watchlist_manager import get_user_watchlist, SUPABASE_URL, SUPABASE_KEY

# VN Timezone (UTC+7)
VN_TZ = timezone(timedelta(hours=7))

def is_vn_stock_market_open(dt: datetime = None) -> bool:
    """
    Kiểm tra xem hiện tại có thuộc giờ giao dịch Thị Trường Chứng Khoán Việt Nam hay không:
    - Thứ 2 đến Thứ 6 (Không tính Thứ 7, Chủ Nhật và ngày lễ)
    - Khung giờ Sáng: 09:00 - 11:30 (GMT+7)
    - Khung giờ Chiều: 13:00 - 15:00 (GMT+7)
    """
    if dt is None:
        dt = datetime.now(VN_TZ)
    elif dt.tzinfo is None:
        dt = dt.astimezone(VN_TZ)

    # Kiểm tra Ngày trong tuần (0: Thứ 2 ... 4: Thứ 6, 5: T7, 6: CN)
    if dt.weekday() >= 5:
        return False

    h = dt.hour
    m = dt.minute
    total_minutes = h * 60 + m

    # Sáng: 09:00 (540 phút) -> 11:30 (690 phút)
    in_morning = (540 <= total_minutes <= 690)
    # Chiều: 13:00 (780 phút) -> 15:00 (900 phút)
    in_afternoon = (780 <= total_minutes <= 900)

    return in_morning or in_afternoon

def fetch_price_digest_for_tickers(tickers: list) -> str:
    """
    Lấy giá chứng khoán realtime từ vnstock cho danh sách tickers & tạo bản tin định dạng Telegram
    """
    if not tickers:
        return "⚠️ Danh mục của bạn chưa có mã cổ phiếu nào."

    clean_tickers = [t.upper().strip() for t in tickers if t.strip()]
    if not clean_tickers:
        return "⚠️ Danh mục không có mã hợp lệ."

    try:
        t = Trading(source="vci")
        df = t.price_board(clean_tickers)
        if df is None or df.empty:
            return "⚠️ Chưa lấy được dữ liệu bảng giá từ thị trường."

        blocks = []
        now_str = datetime.now(VN_TZ).strftime("%H:%M %d/%m/%Y")

        for idx in range(len(df)):
            row = df.iloc[idx]
            
            # Helper to extract value safely from MultiIndex or single index
            def get_val(key1, key2=None, default=0):
                if isinstance(df.columns, pd.MultiIndex):
                    val = row.get((key1, key2))
                else:
                    val = row.get(key1) or row.get(key2)
                return val if val is not None and not pd.isna(val) else default

            import pandas as pd
            tk = str(get_val("listing", "symbol", clean_tickers[min(idx, len(clean_tickers)-1)])).upper()
            
            raw_match_price = float(get_val("match", "match_price", 0))
            raw_ref_price = float(get_val("match", "reference_price", get_val("listing", "ref_price", 0)))
            raw_high = float(get_val("match", "highest", 0))
            raw_low = float(get_val("match", "lowest", 0))
            raw_vol = float(get_val("match", "accumulated_volume", 0))
            raw_ceiling = float(get_val("match", "ceiling_price", get_val("listing", "ceiling", 0)))
            raw_floor = float(get_val("match", "floor_price", get_val("listing", "floor", 0)))

            # If price is in thousands (e.g., 20850), convert to standard (20.85)
            price = raw_match_price / 1000.0 if raw_match_price > 500 else raw_match_price
            ref_price = raw_ref_price / 1000.0 if raw_ref_price > 500 else raw_ref_price
            high = raw_high / 1000.0 if raw_high > 500 else raw_high
            low = raw_low / 1000.0 if raw_low > 500 else raw_low
            ceiling = raw_ceiling / 1000.0 if raw_ceiling > 500 else raw_ceiling
            floor = raw_floor / 1000.0 if raw_floor > 500 else raw_floor

            change = price - ref_price if ref_price > 0 else 0.0
            change_pc = (change / ref_price * 100.0) if ref_price > 0 else 0.0

            # Emojis for Ceiling / Floor / Up / Down / Ref
            if price >= ceiling and ceiling > 0:
                status_emoji = "🟣" # Tím Trần
            elif price <= floor and floor > 0 and price > 0:
                status_emoji = "🔵" # Xanh Sàn
            elif change > 0:
                status_emoji = "🟢" # Xanh Tăng
            elif change < 0:
                status_emoji = "🔴" # Đỏ Giảm
            else:
                status_emoji = "🟡" # Vàng Tham chiếu

            sign = "+" if change > 0 else ""
            vol_str = f"{round(raw_vol / 1_000_000, 2)}M" if raw_vol >= 1_000_000 else f"{int(raw_vol):,}"

            blocks.append(
                f"{status_emoji} <b>{tk}</b>: <b>{price:.2f}</b> ({sign}{change:.2f} / {sign}{change_pc:.2f}%)\n"
                f"• Ref: <code>{ref_price:.2f}</code> | High: <code>{high:.2f}</code> | Low: <code>{low:.2f}</code>\n"
                f"• Khối lượng GD: <b>{vol_str} CP</b>"
            )

        msg = (
            f"📊 <b>BẢN TIN GIÁ CỔ PHIẾU HÀNG GIỜ (WATCHLIST)</b>\n"
            f"⏰ <i>Thời điểm: {now_str} (Giờ giao dịch TTCK)</i>\n\n"
            + "\n--------------------\n".join(blocks) +
            f"\n\n🛡️ <i>Tự động cập nhật mỗi 1 tiếng trong giờ giao dịch (09:00-11:30 & 13:00-15:00).</i>"
        )
        return msg

    except Exception as e:
        print(f"⚠️ Lỗi lấy bảng giá cổ phiếu vnstock: {e}")
        return f"⚠️ Không thể lấy bảng giá chứng khoán lúc này: {e}"

def get_all_users_with_watchlists() -> dict:
    """
    Lấy toàn bộ danh sách users và watchlist của họ từ Supabase DB table 'user_watchlist'
    Returns: dict { chat_id: [ticker1, ticker2] }
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        # Fallback to default TELEGRAM_CHAT_ID if available
        if TELEGRAM_CHAT_ID:
            watchlist = get_user_watchlist(TELEGRAM_CHAT_ID)
            return {TELEGRAM_CHAT_ID: watchlist} if watchlist else {}
        return {}

    db_url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/user_watchlist?select=chat_id,ticker"
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apiKey": SUPABASE_KEY
    }

    user_map = {}
    try:
        res = requests.get(db_url, headers=headers, timeout=5)
        if res.status_code == 200:
            rows = res.json()
            for r in rows:
                c_id = str(r.get("chat_id"))
                tk = r.get("ticker")
                if c_id and tk:
                    if c_id not in user_map:
                        user_map[c_id] = []
                    if tk not in user_map[c_id]:
                        user_map[c_id].append(tk)
    except Exception as e:
        print(f"⚠️ Lỗi lấy user_watchlist tổng hợp: {e}")

    # Ensure fallback chat ID is included if present
    if TELEGRAM_CHAT_ID and TELEGRAM_CHAT_ID not in user_map:
        w = get_user_watchlist(TELEGRAM_CHAT_ID)
        if w:
            user_map[TELEGRAM_CHAT_ID] = w

    return user_map

def send_hourly_price_updates_to_all_users():
    """
    Quét và gửi bản tin tổng hợp giá cổ phiếu hàng giờ cho tất cả users có Watchlist
    """
    user_map = get_all_users_with_watchlists()
    if not user_map:
        print("ℹ️ Chưa có user nào khởi tạo Watchlist để gửi tin giá hàng giờ.")
        return

    print(f"📈 [Hourly Price Alert] Đang gửi thông báo giá cổ phiếu cho {len(user_map)} users...")
    for chat_id, tickers in user_map.items():
        if tickers:
            msg = fetch_price_digest_for_tickers(tickers)
            send_telegram_message(msg, chat_id=chat_id)

def hourly_stock_price_notifier_loop():
    """
    Thread chạy ngầm: Mỗi 1 tiếng kiểm tra giờ giao dịch & gửi thông báo giá cổ phiếu
    """
    print("⏰ [Hourly Price Notifier Loop Started] Đã khởi chạy tiến trình báo giá cổ phiếu 1 tiếng/lần...")
    
    last_sent_hour = -1

    while True:
        try:
            now_vn = datetime.now(VN_TZ)
            current_hour = now_vn.hour

            # Kiểm tra xem có trong giờ giao dịch & chưa gửi bản tin cho giờ này
            if is_vn_stock_market_open(now_vn):
                if current_hour != last_sent_hour:
                    last_sent_hour = current_hour
                    print(f"🔔 [TTCK Mở Cửa - {now_vn.strftime('%H:%M %d/%m')}] Tiến hành gửi bản tin giá cổ phiếu hàng giờ...")
                    send_hourly_price_updates_to_all_users()
            else:
                # Ngoài giờ giao dịch -> reset tracker để sẵn sàng cho phiên kế tiếp
                if last_sent_hour != -1 and (current_hour < 9 or current_hour > 15 or now_vn.weekday() >= 5):
                    last_sent_hour = -1

        except Exception as e:
            print(f"⚠️ Lỗi trong vòng lặp hourly_stock_price_notifier: {e}")

        # Sleep 60 seconds before next check
        time.sleep(60)

def start_hourly_price_notifier_thread():
    t = threading.Thread(target=hourly_stock_price_notifier_loop, daemon=True)
    t.start()
    return t

if __name__ == "__main__":
    print("Testing Hourly Stock Price Digest:")
    print("Is VN Stock Market Open right now?", is_vn_stock_market_open())
    test_msg = fetch_price_digest_for_tickers(["SSI", "CEO", "HPG"])
    print("\n--- SAMPLE DIGEST MESSAGE ---")
    print(test_msg)
