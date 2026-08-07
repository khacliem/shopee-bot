import os
import time
from datetime import datetime
import pytz
import requests
from flask import Flask

app = Flask(__name__)

# Lấy biến môi trường từ Render
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")

def send_telegram(message):
    """Hàm gửi thông báo qua Telegram"""
    if TELEGRAM_TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print(f"Lỗi gửi Telegram: {e}")

def run_san_ma():
    """Hàm xử lý săn mã Shopee"""
    tz_vn = pytz.timezone('Asia/Ho_Chi_Minh')
    now = datetime.now(tz_vn)
    print(f"[{now.strftime('%H:%M:%S %d/%m/%Y')}] Bắt đầu chạy luồng săn mã Shopee...")
    
    # --- Dán logic giật voucher / request Shopee của bạn vào đây ---
    
    msg = f"🔥 <b>THÔNG BÁO SẮN MÃ</b> 🔥\n⏰ Thời gian: {now.strftime('%H:%M:%S')}\nStatus: Đã kích hoạt luồng giật mã thành công!"
    send_telegram(msg)

@app.route('/')
@app.route('/health')
def health_check():
    """Endpoint giữ nhịp cho UptimeRobot"""
    return {"status": "ok", "message": "Shopee Bot is running!"}, 200

if __name__ == "__main__":
    # Khai báo múi giờ Việt Nam
    tz_vn = pytz.timezone('Asia/Ho_Chi_Minh')
    print("=== TOOL AUTO GIẶT VOUCHER SHOPEE STARTED ===")
    
    # Khởi chạy Flask Server trên Thread riêng hoặc chạy trực tiếp
    import threading
    server_thread = threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8080))
    server_thread.daemon = True
    server_thread.start()

    # Vòng lặp kiểm tra thời gian thực (Precision Loop)
    target_hours = [0, 9, 12, 15, 18, 21]  # Các khung giờ săn mã phổ biến
    has_run = False

    while True:
        now_vn = datetime.now(tz_vn)
        
        # Kiểm tra đúng giờ và phút 00
        if now_vn.hour in target_hours and now_vn.minute == 0 and not has_run:
            run_san_ma()
            has_run = True  # Đánh dấu đã chạy trong phút này
            time.sleep(50)  # Chờ hết phút 00 để tránh chạy lặp lại
            
        if now_vn.minute != 0:
            has_run = False  # Reset trạng thái khi sang phút mới
            
        time.sleep(1)  # Quét mỗi giây 1 lần
