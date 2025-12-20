# Hướng Dẫn Cấu Hình Email Cảnh Báo

## Tính năng
- Tự động gửi email khi phát hiện người lạ **quá 10 giây**
- Đính kèm ảnh chụp người lạ
- Cooldown 60 giây giữa các email để tránh spam
- Gửi từ Gmail: watershoputetea@gmail.com

## Cách sử dụng

### 1. Trên Web Interface
1. Mở trình duyệt: `http://localhost:5000`
2. Tìm phần **"📧 Cảnh Báo Email"**
3. Nhập email của bạn (ví dụ: yourname@gmail.com)
4. Click **"✉️ Bật Email"**
5. Click **"🧪 Test"** để kiểm tra

### 2. Kiểm tra hoạt động
1. Đảm bảo đã huấn luyện model AI
2. Để người lạ xuất hiện trước camera
3. Sau 10 giây, email sẽ được gửi tự động
4. Kiểm tra hộp thư đến của bạn

## Nội dung Email

Email cảnh báo bao gồm:
- **Tiêu đề:** ⚠️ CẢNH BÁO AN NINH - [Thời gian]
- **Nội dung:** 
  - Thông báo phát hiện người lạ
  - Thời gian phát hiện
  - Trạng thái cảnh báo
- **Đính kèm:** Ảnh chụp từ camera (nếu có)

## Cấu hình Gmail gửi

Hệ thống sử dụng Gmail SMTP với cấu hình:
```
Host: smtp.gmail.com
Port: 587
Email: watershoputetea@gmail.com
Password: ibdjgggydrtteqxg (App Password)
```

## Lưu ý quan trọng

### Bảo mật
- ⚠️ **KHÔNG chia sẻ App Password** với người khác
- Email gửi đi từ watershoputetea@gmail.com
- Chỉ bạn nhận được email cảnh báo

### Giới hạn
- **Cooldown:** 60 giây giữa các email
- **Ngưỡng:** Phải cảnh báo liên tục 10 giây
- **Kích thước ảnh:** ~15-30KB

### Khắc phục sự cố

**Email không gửi được:**
1. Kiểm tra kết nối internet
2. Click "🧪 Test" để kiểm tra kết nối
3. Kiểm tra email nhận có đúng không
4. Xem console log để biết lỗi chi tiết

**Email vào Spam:**
1. Kiểm tra thư mục Spam/Junk
2. Đánh dấu "Not Spam" cho email từ watershoputetea@gmail.com
3. Thêm vào danh sách liên hệ

**Nhận quá nhiều email:**
- Hệ thống có cooldown 60 giây
- Chỉ gửi khi cảnh báo kéo dài >10 giây
- Có thể tắt email bất cứ lúc nào

## Tắt cảnh báo email

Click nút **"❌ Tắt Email"** trong phần Cảnh Báo Email

## Ví dụ sử dụng

### Kịch bản 1: Giám sát nhà
```
1. Đăng ký khuôn mặt gia đình
2. Huấn luyện model
3. Bật email cảnh báo với email của bạn
4. Khi có người lạ vào nhà >10s → Nhận email ngay
```

### Kịch bản 2: Văn phòng
```
1. Đăng ký khuôn mặt nhân viên
2. Huấn luyện model
3. Bật email cho bảo vệ/quản lý
4. Phát hiện người lạ → Gửi cảnh báo tự động
```

### Kịch bản 3: Cửa hàng
```
1. Đăng ký khuôn mặt nhân viên
2. Huấn luyện model
3. Bật email cho chủ cửa hàng
4. Theo dõi khách hàng lạ xuất hiện lâu
```

## Thông số kỹ thuật

- **Thời gian phát hiện:** 10 giây
- **Cooldown:** 60 giây
- **Timeout kết nối:** 10 giây
- **Định dạng:** HTML email với ảnh đính kèm
- **Giao thức:** SMTP với STARTTLS

## Mã nguồn

File liên quan:
- `email_alert.py` - Class xử lý email
- `main.py` - Tích hợp vào hệ thống
- `templates/esp32_index.html` - Giao diện web

## Hỗ trợ

Nếu gặp vấn đề, kiểm tra:
1. Console log trong terminal
2. Trạng thái email trong web interface
3. Kết nối internet
4. Cấu hình email đúng chưa
