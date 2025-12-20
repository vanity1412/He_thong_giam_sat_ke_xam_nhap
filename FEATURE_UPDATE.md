# CẬP NHẬT TÍNH NĂNG MỚI - HỆ THỐNG CẢNH BÁO EMAIL

## Tính năng đã thêm

Hệ thống giờ đây có 3 chế độ cảnh báo email tự động sau 10 giây:

### 1. ✅ PHÁT HIỆN NGƯỜI AN TOÀN (SAFE)
- **Điều kiện**: Phát hiện người đã đăng ký trong hệ thống liên tục trong 10 giây
- **Email gửi**: 
  - Tiêu đề: "✅ AN TOÀN - Phát hiện người đã đăng ký"
  - Nội dung: Tên và email của người được phát hiện
  - Màu xanh lá, biểu tượng ✅
- **Hiển thị trên màn hình**: "AN TOAN" màu xanh lá + đếm thời gian

### 2. ⚠️ PHÁT HIỆN NGƯỜI LẠ (WARNING)
- **Điều kiện**: Phát hiện người lạ (không có trong hệ thống) liên tục trong 10 giây
- **Email gửi**:
  - Tiêu đề: "⚠️ CẢNH BÁO AN NINH"
  - Nội dung: Cảnh báo phát hiện người lạ
  - Màu đỏ, biểu tượng ⚠️
- **Hiển thị trên màn hình**: "CANH BAO!" màu đỏ + đếm thời gian

### 3. ℹ️ KHÔNG PHÁT HIỆN AI (NO_FACE)
- **Điều kiện**: Không phát hiện khuôn mặt nào trong 10 giây
- **Email gửi**:
  - Tiêu đề: "ℹ️ THÔNG BÁO - Không phát hiện ai trong 10 giây"
  - Nội dung: Thông báo không phát hiện kẻ xâm nhập
  - Màu vàng cam, biểu tượng ℹ️
- **Hiển thị trên màn hình**: "KHONG PHAT HIEN" màu cam + đếm thời gian

## Cách hoạt động

1. **Bật giám sát**: Hệ thống tự động bật khi đăng nhập
2. **Quét liên tục**: Camera quét khuôn mặt mỗi frame (~30 FPS)
3. **Đếm thời gian**: 
   - Khi phát hiện trạng thái (SAFE/WARNING/NO_FACE), bắt đầu đếm
   - Nếu trạng thái thay đổi, reset bộ đếm
   - Nếu trạng thái giữ nguyên 10 giây → gửi email
4. **Cooldown**: Sau khi gửi email, chờ 60 giây trước khi gửi email tiếp theo (tránh spam)

## Thay đổi code

### File `email_alert.py`:
- Thêm tham số `alert_type` và `detected_user` vào hàm `send_alert()`
- Hỗ trợ 3 loại email: "stranger", "safe", "no_detection"
- Tùy chỉnh màu sắc, icon, nội dung theo từng loại

### File `app.py`:
- Thêm tracking cho 3 trạng thái:
  - `safe_detection_start` + `last_safe_email_sent`
  - `no_detection_start` + `last_no_detection_email_sent`
  - `warning_start_time` + `last_email_sent` (đã có)
- Cập nhật `recognize_face()`: Trả về thêm `email` của người được phát hiện
- Cập nhật `process_frame()`: Trả về thêm `detected_user_info`
- Cập nhật `check_and_send_alert()`: Xử lý 3 trạng thái và gửi email tương ứng
- Hiển thị đếm thời gian cho cả 3 trạng thái trên video

## Ví dụ sử dụng

### Kịch bản 1: Chủ nhà về
1. Camera phát hiện khuôn mặt chủ nhà
2. Hiển thị "AN TOAN" màu xanh
3. Đếm: 1s, 2s, 3s... 10s
4. Gửi email: "✅ Phát hiện Nguyễn Văn A (email@example.com)"

### Kịch bản 2: Người lạ xâm nhập
1. Camera phát hiện khuôn mặt không có trong hệ thống
2. Hiển thị "CANH BAO!" màu đỏ
3. Đếm: 1s, 2s, 3s... 10s
4. Gửi email: "⚠️ CẢNH BÁO! Phát hiện người lạ"

### Kịch bản 3: Không có ai
1. Camera không phát hiện khuôn mặt nào
2. Hiển thị "KHONG PHAT HIEN" màu cam
3. Đếm: 1s, 2s, 3s... 10s
4. Gửi email: "ℹ️ Không phát hiện ai - Không có kẻ xâm nhập"

## Lưu ý

- Email chỉ gửi khi **giám sát đang BẬT**
- Mỗi loại email có cooldown riêng 60 giây
- Nếu trạng thái thay đổi trong 10 giây, bộ đếm reset về 0
- Tất cả email đều đính kèm ảnh từ camera (nếu có)
