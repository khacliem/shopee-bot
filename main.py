import time
import requests
import threading
from datetime import datetime, timedelta

# ==========================================
# 1. CẤU HÌNH TÀI KHOẢN & BOT TELEGRAM
# ==========================================
TELEGRAM_TOKEN = "8840187234:AAHCEJ7zW_RJmO-Pz03kBzogEyTP-KLxpHg"
CHAT_ID = "5426059232"

# Cookie Shopee chuẩn (Lấy từ F12 -> Network)
SHOPEE_COOKIE = "SPC_EC=xxxx; SPC_F=xxxx; SPC_SI=xxxx;"

# Danh sách mặc định (Sẽ tự động cập nhật nếu quét được mã mới từ API)
TARGET_VOUCHER_LIST = [
    {"pct": 100, "evcode": "Njc4MjM1UFNODg4SUA", "name": "Voucher 100%"},
    {"pct": 50,  "evcode": "Mjc4OTI1UFNOOTk5SUA", "name": "Voucher 50%"},
    {"pct": 30,  "evcode": "ODc4MTI1UFNOOTk5SUA", "name": "Voucher 30%"},
    {"pct": 25,  "evcode": "SDc4MTI1UFNOMjUxSUA", "name": "Voucher 25%"}
]

HUNT_TARGET_HOURS = ["00:00:00", "09:00:00", "12:00:00", "15:00:00", "18:00:00", "21:00:00"]

# ==========================================
# 2. HÀM GỬI THÔNG BÁO TELEGRAM
# ==========================================
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"-> Lỗi gửi Telegram: {e}")

# ==========================================
# 3. TỰ ĐỘNG CÀO API LẤY EVCODE MỚI NHẤT
# ==========================================
def auto_fetch_evcodes():
    """Tự động cào API Shopee lấy danh sách evcode mới trước giờ săn"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 Đang quét evcode tự động từ Shopee...")
    url = "https://shopee.vn/api/v2/voucher_wallet/get_voucher_tab_list?tab_id=1"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
        "Cookie": SHOPEE_COOKIE
    }
    
    extracted = []
    try:
        res = requests.get(url, headers=headers, timeout=5)
        data = res.json()
        if data.get("error") == 0 and "data" in data:
            for col in data["data"].get("voucher_collections", []):
                for v in col.get("vouchers", []):
                    pct = v.get("discount_percentage", 0)
                    code = v.get("voucher_code") or v.get("signature")
                    name = v.get("title_name", f"Voucher {pct}%")
                    if pct >= 25 and code:
                        extracted.append({"pct": pct, "evcode": code, "name": name})
                        
        if extracted:
            print(f"✅ Đã tự động cập nhật {len(extracted)} evcode mới!")
            return extracted
    except Exception as e:
        print(f"⚠️ Lỗi cào evcode tự động: {e}")
        
    print("⚠️ Không lấy được code mới qua API, giữ nguyên danh sách hiện tại.")
    return TARGET_VOUCHER_LIST

# ==========================================
# 4. LUỒNG PRE-FIRING GIẬT MÃ TỐC ĐỘ CAO
# ==========================================
def claim_task(v_info, success_list, failed_details):
    url = "https://shopee.vn/api/v2/voucher_wallet/save_voucher"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
        "Cookie": SHOPEE_COOKIE,
        "Content-Type": "application/json",
        "Referer": "https://shopee.vn/m/ma-giam-gia"
    }
    payload = {"voucher_code": v_info["evcode"], "signature": "", "source": "vlp"}
    
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=2)
        data = res.json()
        now_str = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        if data.get("error") == 0:
            print(f"[{now_str}] ✅ THÀNH CÔNG: {v_info['name']}")
            success_list.append(v_info['name'])
        else:
            msg = data.get("error_msg", "Hết lượt/Chưa mở")
            print(f"[{now_str}] ❌ THẤT BẠI ({v_info['name']}): {msg}")
            failed_details.append(f"• {v_info['name']}: {msg}")
    except Exception as e:
        failed_details.append(f"• {v_info['name']}: Lỗi kết nối server")

def fast_claim_all_vouchers():
    """Bắn đa luồng song song đè đợt sóng đầu tiên"""
    print(f"\n⚡ [{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] KÍCH HOẠT PRE-FIRING GIẬT MÃ...")
    threads = []
    success_list = []
    failed_details = []

    # Bắn 5 request song song cho mỗi mã
    for v_info in TARGET_VOUCHER_LIST:
        for _ in range(5):
            t = threading.Thread(target=claim_task, args=(v_info, success_list, failed_details))
            threads.append(t)
            t.start()
            time.sleep(0.015)
            
    for t in threads:
        t.join()

    # Báo cáo kết quả về Telegram
    report = f"📊 *KẾT QUẢ SĂN MÃ ({datetime.now().strftime('%H:%M:%S')})*\n\n"
    if success_list:
        report += "🎉 *MÃ ĐÃ GIẬT ĐƯỢC:*\n" + "\n".join([f"✅ {item}" for item in set(success_list)]) + "\n\n"
    else:
        report += "❌ *Chưa giật được mã nào.*\n\n"

    if failed_details:
        report += "⚠️ *Phản hồi từ Shopee:*\n" + "\n".join(list(set(failed_details))[:5])

    send_telegram_alert(report)

# ==========================================
# 5. LUỒNG CANH GIỜ MILI-GIÂY
# ==========================================
def hunter_worker():
    global TARGET_VOUCHER_LIST
    print("=== TOOL HUNTER & TỰ ĐỘNG LẤY EVCODE ĐÃ BẬT ===")
    
    notified_5m = set()
    notified_10s = set()
    hunted_today = set()
    
    send_telegram_alert("🚀 *Tool Hunter Full Auto đã khởi chạy!*\n\n• Tự động cào evcode trước 5 phút.\n• Pre-firing 300ms bù trễ mạng.")

    while True:
        now = datetime.now()
        current_time_str = now.strftime("%H:%M:%S")
        today_date = now.strftime("%Y-%m-%d")

        for target_hour_str in HUNT_TARGET_HOURS:
            target_time = datetime.strptime(f"{today_date} {target_hour_str}", "%Y-%m-%d %H:%M:%S")
            
            if now > target_time + timedelta(seconds=5):
                target_time += timedelta(days=1)

            time_diff = (target_time - now).total_seconds()
            key_id = target_time.strftime("%Y-%m-%d %H:%M:%S")

            # 1. BÁO SỚM & TỰ ĐỘNG CÀO MÃ TRƯỚC 5 PHÚT
            if 295 <= time_diff <= 300 and key_id not in notified_5m:
                TARGET_VOUCHER_LIST = auto_fetch_evcodes()
                send_telegram_alert(
                    f"⏰ *CẢNH BÁO (Còn 5 phút)*\n\n"
                    f"Sắp đến khung giờ: *{target_hour_str}*\n"
                    f"📌 Đã chuẩn bị {len(TARGET_VOUCHER_LIST)} mã để giật."
                )
                notified_5m.add(key_id)

            # 2. BÁO SỚM TRƯỚC 10 GIÂY
            if 9 <= time_diff <= 10 and key_id not in notified_10s:
                send_telegram_alert(f"⚡ *CÒN 10 GIÂY!* Sẵn sàng kích hoạt Pre-firing...")
                notified_10s.add(key_id)

            # 3. PRE-FIRING BẮN SỚM TRƯỚC 300MS (0.3 GIÂY)
            if 0.0 <= time_diff <= 0.35 and key_id not in hunted_today:
                hunted_today.add(key_id)
                fast_claim_all_vouchers()

        if current_time_str == "00:01:00":
            notified_5m.clear()
            notified_10s.clear()
            hunted_today.clear()

        time.sleep(0.01)

if __name__ == "__main__":
    hunter_worker()
