# ==========================================
# LUỒNG CANH GIỜ CẢI TIẾN (CHẮC CHẮN KÍCH HOẠT)
# ==========================================
def hunter_worker():
    global TARGET_VOUCHER_LIST
    print("=== TOOL HUNTER & TỰ ĐỘNG LẤY EVCODE ĐÃ BẬT ===")
    
    notified_5m = set()
    notified_10s = set()
    hunted_today = set()
    
    send_telegram_alert("🚀 *Tool Hunter Full Auto đã khởi chạy thành công!*")

    while True:
        now = datetime.now()
        today_date = now.strftime("%Y-%m-%d")

        for target_hour_str in HUNT_TARGET_HOURS:
            # Tạo mốc thời gian cho khung giờ săn
            target_time = datetime.strptime(f"{today_date} {target_hour_str}", "%Y-%m-%d %H:%M:%S")
            
            # Tính khoảng cách giây (âm tức là đã qua giờ)
            time_diff = (target_time - now).total_seconds()
            key_id = f"{today_date}_{target_hour_str}"

            # 1. BÁO SỚM & CÀO EVCODE TRƯỚC 5 PHÚT
            if 290 <= time_diff <= 300 and key_id not in notified_5m:
                TARGET_VOUCHER_LIST = auto_fetch_evcodes()
                send_telegram_alert(
                    f"⏰ *CẢNH BÁO (Còn 5 phút)*\n\n"
                    f"Khung giờ: *{target_hour_str}*\n"
                    f"📌 Đã chuẩn bị {len(TARGET_VOUCHER_LIST)} mã để giật."
                )
                notified_5m.add(key_id)

            # 2. BÁO SỚM TRƯỚC 10 GIÂY
            if 8 <= time_diff <= 10 and key_id not in notified_10s:
                send_telegram_alert(f"⚡ *CÒN 10 GIÂY!* Chuẩn bị Pre-firing...")
                notified_10s.add(key_id)

            # 3. KÍCH HOẠT PRE-FIRING GIẬT MÃ (Nới rộng lên -1.0s đến 0.5s để chống lag)
            if -1.0 <= time_diff <= 0.5 and key_id not in hunted_today:
                hunted_today.add(key_id)
                
                # Gọi ngay hàm giật mã và gửi báo cáo Telegram
                fast_claim_all_vouchers()

        time.sleep(0.01)
