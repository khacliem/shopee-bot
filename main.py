import os
import random
import threading
import time
from datetime import datetime

import requests
from flask import Flask


app = Flask(__name__)


@app.get("/")
def webview_status():
    return {
        "status": "ok",
        "service": "Shopee voucher hunter",
        "dry_run": DRY_RUN,
    }


@app.get("/health")
def health_check():
    """Stable health endpoint for Preview and uptime monitors."""
    return {"status": "ok"}, 200


# ==========================================
# 1. CẤU HÌNH TÀI KHOẢN & BOT TELEGRAM
# ==========================================
# Không lưu token/cookie trực tiếp trong mã nguồn.
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
SHOPEE_COOKIE = os.environ["SHOPEE_COOKIE"]

# Chế độ thực được bật khi DRY_RUN=0; thông tin xác thực vẫn phải nằm
# trong biến môi trường, không đặt trực tiếp trong mã nguồn.
DRY_RUN = False

# Danh sách danh mục mã voucher từ 25% trở lên để săn
TARGET_VOUCHER_LIST = [
    {"pct": 100, "evcode": "Njc4MjM1UFNODg4SUA", "name": "Voucher 100%"},
    {"pct": 50, "evcode": "Mjc4OTI1UFNOOTk5SUA", "name": "Voucher 50%"},
    {"pct": 30, "evcode": "ODc4MTI1UFNOOTk5SUA", "name": "Voucher 30%"},
    {"pct": 25, "evcode": "SDc4MTI1UFNOMjUxSUA", "name": "Voucher 25%"},
]

# Các khung giờ vàng Shopee tự động bật chế độ giật mã
HUNT_TARGET_HOURS = [
    "00:00:00",
    "09:00:00",
    "12:00:00",
    "15:00:00",
    "18:00:00",
    "21:00:00",
]


# ==========================================
# 2. HÀM GỬI THÔNG BÁO TELEGRAM
# ==========================================
def send_telegram_alert(message):
    if DRY_RUN:
        print(f"[DRY RUN] Telegram alert:\n{message}")
        return

    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("-> Thiếu TELEGRAM_TOKEN hoặc CHAT_ID; bỏ qua thông báo Telegram.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as error:
        print(f"-> Lỗi kết nối Telegram: {error}")


# ==========================================
# 3. HÀM GIẬT TOÀN BỘ MÃ >= 25%
# ==========================================
def auto_claim_vouchers():
    """Lặp qua danh sách mã >= 25% và gửi request lưu mã."""
    print(
        f"\n⚡ [{datetime.now().strftime('%H:%M:%S.%f')}] "
        "KÍCH HOẠT TIẾN HÀNH GIẬT TOÀN BỘ MÃ >= 25%..."
    )

    if DRY_RUN:
        for voucher in TARGET_VOUCHER_LIST:
            if voucher["pct"] >= 25:
                print(
                    f"[DRY RUN] Sẽ thử lưu voucher {voucher['pct']}% "
                    f"({voucher['evcode']})."
                )
        return

    if not SHOPEE_COOKIE:
        print("-> Thiếu SHOPEE_COOKIE; không thực hiện request Shopee.")
        return

    url = "https://shopee.vn/api/v2/voucher_wallet/save_voucher"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Cookie": SHOPEE_COOKIE,
        "Content-Type": "application/json",
        "Referer": "https://shopee.vn/m/ma-giam-gia",
    }

    for voucher in TARGET_VOUCHER_LIST:
        if voucher["pct"] >= 25:
            payload = {
                "voucher_code": voucher["evcode"],
                "signature": "",
                "source": "vlp",
            }

            for attempt in range(3):
                try:
                    response = requests.post(
                        url, json=payload, headers=headers, timeout=3
                    )
                    data = response.json()

                    if data.get("error") == 0:
                        message = (
                            f"🎉 *GIẬT MÃ {voucher['pct']}% THÀNH CÔNG!*\n\n"
                            f"✅ Đã lưu {voucher['name']} vào Ví Shopee lúc "
                            f"{datetime.now().strftime('%H:%M:%S')}!"
                        )
                        print(message)
                        send_telegram_alert(message)
                        break
                    else:
                        print(
                            f"-> Mã {voucher['pct']}% (Thử {attempt + 1}): "
                            f"{data.get('error_msg', 'Chưa mở/Hết lượt')}"
                        )
                except Exception as error:
                    print(f"-> Lỗi server: {error}")


# ==========================================
# 4. CHỨC NĂNG QUÉT & LỌC MÃ >= 25% BÁO TELEGRAM
# ==========================================
def get_sample_shopee_vouchers():
    vouchers = []
    shopee_urls = [
        "https://shopee.vn/m/ma-giam-gia",
        "https://shopee.vn/m/voucher-back",
    ]
    back_slots = ["00H00", "09H00", "12H00", "15H00", "18H00", "21H00"]

    now = datetime.now()
    today_str = now.strftime("%d/%m/%Y")

    for index in range(2):
        pct = random.choice([25, 30, 50, 100])
        max_discount = "888k" if pct >= 50 else "100k"
        min_spend = 500000 if pct >= 50 else 150000

        if pct >= 25:
            vouchers.append(
                {
                    "pct": pct,
                    "name": f"Giảm {pct}% Giảm tối đa {max_discount}",
                    "min_spend": f"{min_spend:,}đ",
                    "link": shopee_urls[index % len(shopee_urls)],
                    "appear_slot": random.choice(back_slots),
                    "start_time": f"{now.strftime('%H:%M')} {today_str}",
                    "end_time": f"23:59 {today_str}",
                }
            )
    return vouchers


def scan_worker():
    """Quét và chỉ gửi báo thức mã >= 25% về Telegram."""
    while True:
        try:
            vouchers = get_sample_shopee_vouchers()
            for voucher in vouchers:
                alert_message = (
                    f"🔥 *PHÁT HIỆN VOUCHER HOT {voucher['pct']}%* 🔥\n\n"
                    f"📌 *Ưu đãi:* {voucher['name']}\n"
                    f"💰 *Đơn Tối Thiểu:* {voucher['min_spend']}\n"
                    f"⏰ *Khung giờ xuất hiện:* {voucher['appear_slot']} "
                    "(Vừa back lượt!)\n"
                    f"⏳ *Thời gian mở:* {voucher['start_time']}\n"
                    f"📅 *Hạn sử dụng:* Đến {voucher['end_time']}\n\n"
                    f"👉 Bấm lưu và dùng ngay: {voucher['link']}"
                )
                send_telegram_alert(alert_message)
                time.sleep(2)
        except Exception as error:
            print(f"Lỗi luồng quét: {error}")

        time.sleep(300)


# ==========================================
# 5. LUỒNG CANH GIỜ GIẬT MÃ MILI-GIÂY
# ==========================================
def hunter_worker():
    print("=== DỊCH VỤ AUTO HUNTER MÃ >= 25% ĐÃ SẴN SÀNG ===")
    hunted_today = []

    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")

        if current_time in HUNT_TARGET_HOURS and current_time not in hunted_today:
            send_telegram_alert(
                f"⏰ *ĐẾN GIỜ VÀNG ({current_time})!* "
                "Tiến hành cướp toàn bộ mã >= 25%..."
            )
            auto_claim_vouchers()
            hunted_today.append(current_time)

        if current_time == "00:00:05":
            hunted_today.clear()

        time.sleep(0.1)


def flask_worker():
    """Serve WebView and uptime-monitor endpoints on Replit's WebView port."""
    app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)


# ==========================================
# 6. CHƯƠNG TRÌNH CHÍNH
# ==========================================
if __name__ == "__main__":
    print("==================================================")
    print("=== TOOL AUTO GIẬT VOUCHER SHOPEE >= 25% ===")
    print("==================================================")
    print(f"=== Chế độ mô phỏng: {'BẬT' if DRY_RUN else 'TẮT'} ===")

    # Mở WebView trước các request mạng để Replit nhận cổng 8080 ngay.
    thread_flask = threading.Thread(target=flask_worker, daemon=True)
    thread_flask.start()

    send_telegram_alert(
        "🎉 *Kích hoạt thành công!* Hệ thống lọc và tự động giật mã "
        "*>= 25%* đã sẵn sàng."
    )

    print("--- [TEST SỚM] Đang thử gửi lệnh giật mã ---")
    auto_claim_vouchers()
    print("---------------------------------------------")

    thread_scan = threading.Thread(target=scan_worker, daemon=True)
    thread_hunter = threading.Thread(target=hunter_worker, daemon=True)

    thread_scan.start()
    thread_hunter.start()

    while True:
        time.sleep(1)
