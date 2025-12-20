# 🎥 HỆ THỐNG NHẬN DIỆN KHUÔN MẶT AI
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python ./app.py

Hệ thống nhận diện khuôn mặt thông minh với AI, hỗ trợ đăng ký đa người dùng, giám sát an ninh tự động và cảnh báo email.

## 📋 Mục Lục
- [Tính Năng](#-tính-năng)
- [Kiến Trúc Hệ Thống](#-kiến-trúc-hệ-thống)
- [Cài Đặt](#-cài-đặt)
- [Hướng Dẫn Sử Dụng](#-hướng-dẫn-sử-dụng)
- [Luồng Hoạt Động](#-luồng-hoạt-động)
- [Cấu Trúc Thư Mục](#-cấu-trúc-thư-mục)
- [API Documentation](#-api-documentation)

---

## ✨ Tính Năng

### 🔐 Quản Lý Người Dùng
- ✅ Đăng ký tài khoản với email/password
- ✅ Đăng nhập bảo mật với session
- ✅ Mỗi user có dữ liệu riêng biệt
- ✅ Admin panel để quản lý tất cả users

### 👤 Nhận Diện Khuôn Mặt
- ✅ Đăng ký khuôn mặt tự động (30 ảnh)
- ✅ Huấn luyện AI model (LBPH Face Recognizer)
- ✅ Nhận diện real-time với độ chính xác cao
- ✅ Hiển thị tên người và trạng thái (AN TOAN/CANH BAO)

### 🔍 Giám Sát An Ninh
- ✅ Bật/tắt giám sát linh hoạt
- ✅ Phát hiện người lạ tự động
- ✅ Đếm thời gian cảnh báo
- ✅ Gửi email cảnh báo sau 10 giây
- ✅ Cooldown 60 giây giữa các email

### 📹 Hỗ Trợ Đa Camera
- ✅ Camera laptop tích hợp
- ✅ ESP32-CAM qua WiFi (WebSocket)
- ✅ Chuyển đổi nguồn camera dễ dàng
- ✅ Auto-retry khi mất kết nối

### 👑 Admin Panel
- ✅ Xem danh sách tất cả users
- ✅ Xem số ảnh đã đăng ký
- ✅ Xóa dữ liệu khuôn mặt user
- ✅ Train lại model sau khi xóa

---

## 🏗️ Kiến Trúc Hệ Thống

```
┌─────────────────────────────────────────────────────────────┐
│                    FLASK WEB SERVER                         │
│                    (Port 5000)                              │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌──────▼──────┐  ┌────────▼────────┐
│  UserManager   │  │ FaceRecog   │  │  EmailAlert     │
│                │  │  System     │  │                 │
│ - Register     │  │ - Detect    │  │ - Send Alert    │
│ - Login        │  │ - Train     │  │ - SMTP Gmail    │
│ - Admin        │  │ - Recognize │  │ - Non-blocking  │
└────────────────┘  └──────┬──────┘  └─────────────────┘
                           │
                ┌──────────┼──────────┐
                │          │          │
        ┌───────▼──┐  ┌───▼────┐  ┌──▼──────┐
        │ Laptop   │  │ ESP32  │  │ Model   │
        │ Camera   │  │ CAM    │  │ Storage │
        └──────────┘  └────────┘  └─────────┘
```

---

## 🚀 Cài Đặt

### 1. Yêu Cầu Hệ Thống
- Python 3.8+
- Webcam (hoặc ESP32-CAM)
- Windows/Linux/MacOS

### 2. Clone Repository
```bash
git clone <repository-url>
cd face-recognition-system
```

### 3. Tạo Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 4. Cài Đặt Dependencies
```bash
pip install -r requirements.txt
```

### 5. Chạy Ứng Dụng
```bash
python app.py
```

Truy cập: **http://localhost:5000**

---

## 📖 Hướng Dẫn Sử Dụng

### 🔑 Đăng Ký Tài Khoản

1. Truy cập `http://localhost:5000`
2. Click "Đăng Ký Tài Khoản Mới"
3. Nhập thông tin:
   - Họ và tên
   - Email
   - Mật khẩu (tối thiểu 6 ký tự)
4. Click "Đăng Ký"

### 🔓 Đăng Nhập

1. Nhập email và mật khẩu
2. Click "Đăng Nhập"
3. Hệ thống chuyển đến Dashboard

**Tài khoản Admin:**
- Email: `watershoputetea@gmail.com`
- Password: `123321`

### 📸 Đăng Ký Khuôn Mặt

1. Tại Dashboard, click "Bắt Đầu Đăng Ký"
2. Đặt mặt vào khung màu vàng
3. Di chuyển đầu nhẹ nhàng (trái, phải, lên, xuống)
4. Hệ thống tự động chụp 30 ảnh
5. Sau khi đủ 30 ảnh:
   - ✅ Tự động huấn luyện AI
   - ✅ Tự động bật giám sát
   - ✅ Sẵn sàng nhận diện

### 🔍 Giám Sát An Ninh

**Bật Giám Sát:**
- Click "Bật Giám Sát" tại Dashboard
- Hệ thống bắt đầu phân tích video

**Khi Phát Hiện:**
- **Người quen** (đã đăng ký): Hiển thị "AN TOAN" màu xanh
- **Người lạ** (chưa đăng ký): Hiển thị "CANH BAO!" màu đỏ
- Sau 10 giây cảnh báo: Gửi email tự động

**Tắt Giám Sát:**
- Click "Tắt Giám Sát"

### 📹 Chuyển Đổi Camera

**Sử dụng Camera Laptop:**
1. Click nút "💻 Laptop"
2. Camera laptop sẽ được kích hoạt

**Sử dụng ESP32-CAM:**
1. Kết nối WiFi ESP32-CAM (SSID: `ESP32_CAM_AP`)
2. Nhập IP: `192.168.4.1`
3. Click nút "📡 ESP32-CAM"
4. Hệ thống kết nối qua WebSocket

### 👑 Admin Panel

**Truy cập:**
- Đăng nhập với tài khoản admin
- Click nút "👑 Admin" ở góc phải

**Chức năng:**
- Xem danh sách tất cả users
- Xem số ảnh khuôn mặt đã đăng ký
- Xóa dữ liệu khuôn mặt user (biến thành người lạ)
- Train lại model sau khi xóa

---

## 🔄 Luồng Hoạt Động

### 1️⃣ Luồng Đăng Ký User

```
User nhập thông tin
        ↓
Validate dữ liệu (email, password, name)
        ↓
Hash password (bcrypt)
        ↓
Lưu vào users.json
        ↓
Tạo session
        ↓
Chuyển đến Dashboard
```

### 2️⃣ Luồng Đăng Nhập

```
User nhập email/password
        ↓
Kiểm tra admin? → Yes → Load admin profile
        ↓ No
Kiểm tra user trong DB
        ↓
Verify password hash
        ↓
Tạo session (user_email, user_name, is_admin)
        ↓
Load model shared
        ↓
Bật giám sát tự động
        ↓
Chuyển đến Dashboard
```

### 3️⃣ Luồng Đăng Ký Khuôn Mặt

```
User click "Bắt Đầu Đăng Ký"
        ↓
Set registration_mode = True
        ↓
Loop: Lấy frame từ camera
        ↓
Phát hiện khuôn mặt (Haar Cascade)
        ↓
Kiểm tra: 1 khuôn mặt? → No → Retry
        ↓ Yes
Resize face → 200x200
        ↓
Lưu vào face_data/{email}/face_{n}.jpg
        ↓
registration_count++
        ↓
Đủ 30 ảnh? → No → Continue loop
        ↓ Yes
Tự động train model
        ↓
Tự động bật giám sát
        ↓
Hoàn thành
```

### 4️⃣ Luồng Huấn Luyện Model

```
Quét thư mục face_data/
        ↓
Load tất cả ảnh của tất cả users
        ↓
Resize mỗi ảnh → 200x200
        ↓
Gán label cho mỗi user (0, 1, 2, ...)
        ↓
Train LBPH Recognizer
        ↓
Lưu model → models/shared_model.yml
        ↓
Lưu labels → models/shared_labels.pkl
        ↓
Load model vào memory
```

### 5️⃣ Luồng Nhận Diện Real-time

```
Loop: Lấy frame từ camera (30 FPS)
        ↓
Convert → Grayscale
        ↓
Phát hiện khuôn mặt (Haar Cascade)
        ↓
Với mỗi khuôn mặt:
        ↓
Resize → 200x200
        ↓
Model có sẵn? → No → "NGUOI LA" (WARNING)
        ↓ Yes
Predict với LBPH Recognizer
        ↓
Confidence < 60? → Yes → "AN TOAN" (SAFE)
        ↓ No
"NGUOI LA" (WARNING)
        ↓
Vẽ khung + tên lên frame
        ↓
Hiển thị datetime + email
        ↓
Encode → JPEG
        ↓
Stream qua HTTP (MJPEG)
```

### 6️⃣ Luồng Giám Sát & Cảnh Báo

```
Giám sát BẬT?
        ↓ Yes
Nhận diện khuôn mặt
        ↓
Status = WARNING? → No → Hiển thị "AN TOAN"
        ↓ Yes
Bắt đầu đếm thời gian
        ↓
Hiển thị "CANH BAO!" + thời gian
        ↓
Thời gian >= 10s?
        ↓ Yes
Kiểm tra cooldown (60s)
        ↓
Gửi email (non-blocking thread)
        ↓
Đính kèm ảnh camera
        ↓
Update last_email_sent
        ↓
Continue monitoring
```

### 7️⃣ Luồng ESP32-CAM WebSocket

```
User chọn ESP32-CAM
        ↓
Start WebSocket thread
        ↓
Connect ws://192.168.4.1:81
        ↓
Loop: Nhận frame data
        ↓
Decode JPEG bytes → OpenCV Mat
        ↓
Put vào frame_queue (maxsize=5)
        ↓
Queue đầy? → Xóa frame cũ nhất
        ↓
Main thread lấy frame từ queue
        ↓
Xử lý như camera laptop
        ↓
Mất kết nối? → Auto retry (3 lần)
```

### 8️⃣ Luồng Admin Xóa User Face

```
Admin click "Xóa Face"
        ↓
Confirm dialog
        ↓
DELETE /api/admin/delete_face
        ↓
Xóa thư mục face_data/{email}/
        ↓
Train lại model (không có user đó)
        ↓
Còn user nào? → No → Xóa model files
        ↓ Yes
Lưu model mới
        ↓
User đó trở thành "NGUOI LA"
        ↓
Reload danh sách users
```

---

## 📁 Cấu Trúc Thư Mục

```
face-recognition-system/
│
├── app.py                      # Flask server chính
├── email_alert.py              # Module gửi email
├── requirements.txt            # Dependencies
├── users.json                  # Database users
├── README.md                   # Tài liệu này
│
├── templates/                  # HTML templates
│   ├── login.html             # Trang đăng nhập
│   ├── register.html          # Trang đăng ký
│   ├── dashboard.html         # Dashboard user
│   └── admin.html             # Admin panel
│
├── face_data/                  # Dữ liệu khuôn mặt
│   ├── user1@gmail.com/       # Thư mục user 1
│   │   ├── face_1.jpg
│   │   ├── face_2.jpg
│   │   └── ... (30 ảnh)
│   └── user2@gmail.com/       # Thư mục user 2
│       └── ...
│
├── models/                     # AI models
│   ├── shared_model.yml       # LBPH model (tất cả users)
│   └── shared_labels.pkl      # Labels mapping
│
└── venv/                       # Virtual environment
```

---

## 🔌 API Documentation

### Authentication APIs

#### POST `/api/register`
Đăng ký tài khoản mới

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "name": "Nguyen Van A"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Đăng ký thành công!"
}
```

#### POST `/api/login`
Đăng nhập

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Đăng nhập thành công!",
  "is_admin": false
}
```

#### POST `/api/logout`
Đăng xuất

**Response:**
```json
{
  "success": true,
  "message": "Đăng xuất thành công!"
}
```

### Face Recognition APIs

#### POST `/api/start_registration`
Bắt đầu đăng ký khuôn mặt

**Response:**
```json
{
  "success": true,
  "message": "Bắt đầu đăng ký khuôn mặt!"
}
```

#### POST `/api/toggle_monitoring`
Bật/tắt giám sát

**Response:**
```json
{
  "success": true,
  "message": "Đã bật giám sát!",
  "active": true
}
```

#### POST `/api/set_camera`
Chuyển đổi nguồn camera

**Request:**
```json
{
  "source": "esp32",
  "ip": "192.168.4.1"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Đã chuyển sang ESP32-CAM (192.168.4.1)"
}
```

#### GET `/api/status`
Lấy trạng thái hệ thống

**Response:**
```json
{
  "logged_in": true,
  "user_email": "user@example.com",
  "user_name": "Nguyen Van A",
  "is_admin": false,
  "registration_mode": false,
  "registration_count": 30,
  "registration_target": 30,
  "has_registered": true,
  "monitoring_active": true,
  "warning_duration": 5,
  "camera_source": "Laptop",
  "esp32_ip": "192.168.4.1"
}
```

### Admin APIs

#### GET `/api/admin/users`
Lấy danh sách tất cả users (Admin only)

**Response:**
```json
{
  "success": true,
  "users": [
    {
      "email": "user1@example.com",
      "name": "User 1",
      "created_at": "2024-01-01 10:00:00",
      "face_count": 30,
      "has_face": true
    }
  ]
}
```

#### POST `/api/admin/delete_face`
Xóa dữ liệu khuôn mặt user (Admin only)

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Đã xóa dữ liệu khuôn mặt của user@example.com"
}
```

#### POST `/api/admin/retrain`
Train lại model (Admin only)

**Response:**
```json
{
  "success": true,
  "message": "Huấn luyện thành công với 60 ảnh từ 2 người!"
}
```

---

## 🎯 Thông Số Kỹ Thuật

### AI Model
- **Algorithm:** LBPH (Local Binary Patterns Histograms)
- **Face Detection:** Haar Cascade Classifier
- **Image Size:** 200x200 pixels
- **Training Images:** 30 per user
- **Confidence Threshold:** 60 (0-100)

### Performance
- **FPS:** 25-30 (Laptop), 15-20 (ESP32-CAM)
- **Latency:** 20-50ms (WebSocket), 100-300ms (HTTP)
- **Recognition Time:** <50ms per face
- **Training Time:** ~2-5s per user

### Email Alert
- **SMTP:** Gmail (smtp.gmail.com:587)
- **Trigger:** 10 seconds continuous warning
- **Cooldown:** 60 seconds between emails
- **Attachment:** JPEG image from camera

### ESP32-CAM
- **Connection:** WebSocket (ws://IP:81)
- **Fallback:** HTTP (http://IP/)
- **Resolution:** 640x480 (VGA)
- **Format:** MJPEG
- **Auto-retry:** 3 attempts

---

## 🛠️ Troubleshooting

### Camera không hoạt động
```bash
# Kiểm tra camera
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

### ESP32-CAM không kết nối
1. Kiểm tra WiFi ESP32-CAM đã bật
2. Kết nối đúng SSID: `ESP32_CAM_AP`
3. Ping test: `ping 192.168.4.1`
4. Kiểm tra port 81 mở

### Email không gửi được
1. Kiểm tra internet
2. Verify email/password trong `email_alert.py`
3. Bật "Less secure app access" trong Gmail
4. Hoặc dùng App Password

### Model không nhận diện
1. Đảm bảo đã train model
2. Kiểm tra ánh sáng đủ
3. Khuôn mặt rõ ràng, không bị che
4. Thử train lại với nhiều ảnh hơn

---

## 📝 License

MIT License - Tự do sử dụng và chỉnh sửa

## 👨‍💻 Author

Developed with ❤️ by Your Team

## 🤝 Contributing

Pull requests are welcome!

---

**🎉 Chúc bạn sử dụng hệ thống thành công!**
