# BÁO CÁO DỰ ÁN HỆ THỐNG GIÁM SÁT AN NINH THÔNG MINH

## THÔNG TIN CHUNG

**Tên dự án:** Hệ thống giám sát an ninh đa khu vực với truyền thông LoRa và camera ESP32  
**Ngày báo cáo:** 12/12/2025  
**Công nghệ sử dụng:** STM32F103C6, ESP32-CAM, LoRa, GSM/SIM  

---

## TỔNG QUAN HỆ THỐNG

Dự án xây dựng một hệ thống giám sát an ninh hoàn chỉnh bao gồm:

### Các thành phần chính:
1. **CodeTram1** - Module cảm biến khu vực 1 (STM32F103C6)
2. **CodeTram2** - Module cảm biến khu vực 2 (STM32F103C6)
3. **CodeTrungTam** - Trạm trung tâm điều khiển (STM32F103C6 + GSM)
4. **MainCodeFinal** - Camera giám sát ESP32-CAM

### Kiến trúc hệ thống:
```
┌─────────────────────────────────────────────────────────────────┐
│                    HỆ THỐNG GIÁM SÁT AN NINH                    │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────┐                    ┌──────────────┐
    │  KHU VỰC 1   │                    │  KHU VỰC 2   │
    │  (CodeTram1) │                    │  (CodeTram2) │
    │              │                    │              │
    │ STM32F103C6  │                    │ STM32F103C6  │
    │ + Cảm biến   │                    │ + Cảm biến   │
    │ + LED        │                    │ + LED        │
    │ + Buzzer     │                    │ + Buzzer     │
    │ + LoRa TX/RX │                    │ + LoRa TX/RX │
    └──────┬───────┘                    └──────┬───────┘
           │                                   │
           │ LoRa (9600 baud)                 │ LoRa (9600 baud)
           │ 0xA1/0xA2                        │ 0xB1/0xB2
           │                                   │
           └───────────┬───────────────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │   TRẠM TRUNG TÂM     │
            │   (CodeTrungTam)     │
            │                      │
            │  STM32F103C6         │
            │  + LCD I2C 16x2      │
            │  + Buzzer            │
            │  + 2 Nút nhấn        │
            │  + LoRa RX           │
            │  + GSM Module        │
            └──────────┬───────────┘
                       │
                       │ GSM/SMS
                       │ (115200 baud)
                       ▼
            ┌──────────────────────┐
            │   Điện thoại         │
            │   0968046024         │
            └──────────────────────┘

    ┌──────────────────────┐
    │   CAMERA GIÁM SÁT    │
    │   (MainCodeFinal)    │
    │                      │
    │   ESP32-CAM          │
    │   + OV2640 Camera    │
    │   + WiFi AP Mode     │
    │   + Web Server       │
    │   IP: 192.168.4.1    │
    └──────────┬───────────┘
               │
               │ WiFi
               │ SSID: ESP32_CAM_AP
               ▼
    ┌──────────────────────┐
    │   Trình duyệt web    │
    │   (Smartphone/PC)    │
    └──────────────────────┘
```

---

## PHẦN 1: MODULE CẢM BIẾN KHU VỰC 1 (CodeTram1)

### 1.1. Thông số kỹ thuật

**Vi điều khiển:** STM32F103C6 (ARM Cortex-M3)
- Flash: 32KB
- RAM: 10KB
- Tần số: 8MHz (HSE - External Crystal)

**Phần cứng:**
- **Cảm biến:** GPIO PB12 (Input, No Pull)
- **LED báo hiệu:** GPIO PB14 (Output)
- **Buzzer:** GPIO PC14 (Output)
- **LCD I2C:** PB6 (SCL), PB7 (SDA) - Địa chỉ 0x27
- **LoRa Module:** UART2 (PA2-TX, PA3-RX) - 9600 baud
- **Debug UART:** UART1 (PA9-TX, PA10-RX) - 115200 baud

### 1.2. Giao thức truyền thông

**Lệnh gửi đi (TX qua LoRa):**
- `0xA1` (CMDACTIVE1): Phát hiện xâm nhập khu vực 1
- `0xA2` (CMDINACTIVE1): Khu vực 1 an toàn

**Lệnh nhận vào (RX từ LoRa):**
- `0xC1` (CMDOFFKV1): Lệnh tắt buzzer từ trạm trung tâm

### 1.3. Luồng hoạt động

**Khởi động:**
```
1. Khởi tạo HAL, Clock (8MHz), GPIO, I2C, UART
2. Khởi tạo delay với HCLK = 8MHz
3. Bật LED trong 30 giây (thời gian khởi động)
4. Tắt LED
5. Bật Buzzer 1 giây (kiểm tra hoạt động)
6. Tắt Buzzer
7. Vào vòng lặp chính
```

**Vòng lặp chính:**
```c
while(1) {
    // Bước 1: Kiểm tra lệnh từ LoRa
    CheckLora();  // Nếu nhận 0xC1 → Tắt buzzer
    
    // Bước 2: Đọc cảm biến PB12
    if (PB12 == HIGH) {
        delay(500ms);  // Chống dội
        if (PB12 == HIGH) {  // Xác nhận lại
            OnLED();
            if (Arlarm == 0) {
                Arlarm = 1;
                OnBuzzer();
                SendArlarm();  // Gửi 0xA1
            }
        }
    } else {
        OffLED();
        if (Arlarm == 1) {
            Arlarm = 0;
            SendOff();  // Gửi 0xA2
            // Buzzer vẫn kêu, chờ lệnh tắt từ trung tâm
        }
    }
}
```

### 1.4. Các hàm chính

**OnLED() / OffLED():**
- Điều khiển LED báo hiệu tại PB14

**OnBuzzer() / OffBuzzer():**
- Điều khiển còi báo động tại PC14

**SendArlarm():**
- Gửi byte 0xA1 qua UART2 (LoRa)
- Thông báo phát hiện xâm nhập

**SendOff():**
- Gửi byte 0xA2 qua UART2 (LoRa)
- Thông báo khu vực an toàn

**CheckLora():**
- Đọc 1 byte từ UART2 (timeout 10ms)
- Nếu nhận 0xC1 → Gọi OffBuzzer()

### 1.5. Đặc điểm kỹ thuật

**Chống nhiễu:**
- Delay 500ms sau khi phát hiện cảm biến
- Kiểm tra lại trạng thái cảm biến
- Chỉ kích hoạt nếu cảm biến vẫn ở mức HIGH

**Cơ chế cờ trạng thái:**
- Biến `Arlarm` đảm bảo chỉ gửi lệnh 1 lần
- Tránh spam lệnh qua LoRa

**Tính năng đặc biệt:**
- Buzzer không tự động tắt khi cảm biến về LOW
- Phải nhận lệnh 0xC1 từ trung tâm mới tắt
- Đảm bảo người giám sát đã xác nhận cảnh báo

---

## PHẦN 2: MODULE CẢM BIẾN KHU VỰC 2 (CodeTram2)

### 2.1. Thông số kỹ thuật

**Vi điều khiển:** STM32F103C6 (giống CodeTram1)

**Phần cứng:** Giống hệt CodeTram1
- Cảm biến: PB12
- LED: PB14
- Buzzer: PC14
- LCD I2C: PB6/PB7
- LoRa: UART2 (9600 baud)

### 2.2. Giao thức truyền thông

**Lệnh gửi đi (TX qua LoRa):**
- `0xB1` (CMDACTIVE2): Phát hiện xâm nhập khu vực 2
- `0xB2` (CMDINACTIVE2): Khu vực 2 an toàn

**Lệnh nhận vào (RX từ LoRa):**
- `0xC2` (CMDOFFKV2): Lệnh tắt buzzer từ trạm trung tâm

### 2.3. So sánh với CodeTram1

**Giống nhau:**
- Cấu trúc code hoàn toàn giống nhau
- Logic xử lý giống nhau
- Phần cứng giống nhau

**Khác nhau:**
- Mã lệnh gửi: 0xB1/0xB2 thay vì 0xA1/0xA2
- Mã lệnh nhận: 0xC2 thay vì 0xC1
- Đại diện cho khu vực 2 thay vì khu vực 1

### 2.4. Luồng hoạt động

Hoàn toàn giống CodeTram1, chỉ khác mã lệnh:

```c
void SendArlarm() {
    UARTSend[0] = CMDACTIVE2;  // 0xB1 thay vì 0xA1
    HAL_UART_Transmit(&huart2, UARTSend, 1, 100);
}

void SendOff() {
    UARTSend[0] = CMDINACTIVE2;  // 0xB2 thay vì 0xA2
    HAL_UART_Transmit(&huart2, UARTSend, 1, 100);
}

void CheckLora() {
    if (HAL_UART_Receive(&huart2, UARTData, 1, 10) == HAL_OK) {
        if (UARTData[0] == CMDOFFKV2) {  // 0xC2 thay vì 0xC1
            OffBuzzer();
        }
    }
}
```

### 2.5. Ý nghĩa thiết kế

**Tại sao cần 2 module riêng biệt?**
- Giám sát 2 khu vực độc lập
- Mỗi khu vực có cảnh báo riêng
- Trạm trung tâm có thể phân biệt nguồn cảnh báo
- Có thể tắt cảnh báo từng khu vực riêng lẻ

**Khả năng mở rộng:**
- Có thể thêm CodeTram3, CodeTram4...
- Chỉ cần thay đổi mã lệnh (0xD1/0xD2, 0xE1/0xE2...)
- Trạm trung tâm cần cập nhật để xử lý thêm lệnh

---

## PHẦN 3: TRẠM TRUNG TÂM ĐIỀU KHIỂN (CodeTrungTam)

### 3.1. Thông số kỹ thuật

**Vi điều khiển:** STM32F103C6

**Phần cứng:**
- **LCD I2C 16x2:** PB6 (SCL), PB7 (SDA) - Địa chỉ 0x27
- **Buzzer:** PC14 (Output)
- **Nút nhấn KV1:** PB12 (Input Pull-up)
- **Nút nhấn KV2:** PB13 (Input Pull-up)
- **Module GSM/SIM:** UART1 (PA9-TX, PA10-RX) - 115200 baud
- **Module LoRa:** UART2 (PA2-TX, PA3-RX) - 9600 baud

### 3.2. Giao thức truyền thông

**A. Giao thức LoRa (UART2 - 9600 baud)**

**Lệnh nhận vào (RX):**
- `0xA1`: Khu vực 1 phát hiện xâm nhập
- `0xA2`: Khu vực 1 an toàn
- `0xB1`: Khu vực 2 phát hiện xâm nhập
- `0xB2`: Khu vực 2 an toàn

**Lệnh gửi đi (TX):**
- `0xC1`: Tắt buzzer khu vực 1
- `0xC2`: Tắt buzzer khu vực 2

**B. Giao thức GSM/SIM (UART1 - 115200 baud)**

**Lệnh AT cơ bản:**
```
AT                      → Kiểm tra kết nối (return: OK)
ATE0                    → Tắt echo (return: OK)
AT+IPR=9600            → Đặt baudrate (return: OK)
AT+CMGF=1              → Chế độ SMS text (return: OK)
AT&W                   → Lưu cấu hình (return: OK)
AT+CNMI=2,2,0,0        → Không lưu SMS vào SIM (return: OK)
AT+CREG?               → Kiểm tra đăng ký mạng
                         +CREG: 0,1 → Đã đăng ký
                         +CREG: 0,3 → Chưa đăng ký
```

**Lệnh gửi SMS:**
```
AT+CMGS="0968046024"   → Bắt đầu gửi SMS
[Nội dung SMS]         → Nhập nội dung
Ctrl+Z (0x1A)          → Kết thúc và gửi
```

**Lệnh gọi điện:**
```
ATD0968046024          → Gọi điện
ATH                    → Ngắt cuộc gọi
```

### 3.3. Nội dung SMS

```c
SMS1: "Canh bao dot nhap khu vuc 1"
SMS2: "Canh bao dot nhap khu vuc 2"
SMS3: "HT GIAM SAT SAN SANG"
```

**Số điện thoại nhận:** 0968046024

### 3.4. Các hàm chính

**A. InitModuleSIM()**

Khởi tạo module GSM/SIM:
```c
void InitModuleSIM() {
    // 1. Gửi AT → Kiểm tra kết nối
    HAL_UART_Transmit(&huart1, "AT\r\n", ...);
    HAL_Delay(2000);
    
    // 2. Cấu hình không lưu SMS
    HAL_UART_Transmit(&huart1, "AT+CNMI=2,2,0,0\r\n", ...);
    HAL_Delay(2000);
    
    // 3. Chế độ SMS text
    HAL_UART_Transmit(&huart1, "AT+CMGF=1\r\n", ...);
    HAL_Delay(2000);
}
```

**B. SendSMS(uint8_t SMSNum)**

Gửi SMS cảnh báo:
```c
void SendSMS(uint8_t SMSNum) {
    // 1. Gửi lệnh AT+CMGS="0968046024"
    HAL_UART_Transmit(&huart1, "AT+CMGS=\"0968046024\"\r\n", ...);
    HAL_Delay(2000);
    
    // 2. Gửi nội dung SMS
    if (SMSNum == 1) {
        HAL_UART_Transmit(&huart1, SMS1, ...);
    } else if (SMSNum == 2) {
        HAL_UART_Transmit(&huart1, SMS2, ...);
    } else if (SMSNum == 3) {
        HAL_UART_Transmit(&huart1, SMS3, ...);
    }
    HAL_Delay(500);
    
    // 3. Gửi Ctrl+Z (0x1A) để kết thúc
    HAL_UART_Transmit(&huart1, "\x1A", ...);
    HAL_Delay(5000);  // Chờ module gửi SMS
}
```

**C. CheckLora()**

Kiểm tra và xử lý lệnh từ LoRa:
```c
void CheckLora() {
    uint8_t UARTData[1] = {0};
    
    if (HAL_UART_Receive(&huart2, UARTData, 1, 10) == HAL_OK) {
        
        // Khu vực 1 phát hiện xâm nhập
        if (UARTData[0] == CMDACTIVE1) {  // 0xA1
            I2C_LCD_SetCursor(LCDDisplay, 0, 1);
            I2C_LCD_WriteString(LCDDisplay, "CB KV1");
            OnBuzzer();
            SendSMS(1);
            KV1Active = 1;
        }
        
        // Khu vực 1 an toàn
        else if (UARTData[0] == CMDINACTIVE1) {  // 0xA2
            I2C_LCD_SetCursor(LCDDisplay, 0, 1);
            I2C_LCD_WriteString(LCDDisplay, "      ");  // Xóa
            KV1Active = 0;
            if (KV2Active == 0) OffBuzzer();  // Chỉ tắt nếu KV2 cũng an toàn
        }
        
        // Khu vực 2 phát hiện xâm nhập
        else if (UARTData[0] == CMDACTIVE2) {  // 0xB1
            I2C_LCD_SetCursor(LCDDisplay, 8, 1);
            I2C_LCD_WriteString(LCDDisplay, "CB KV2");
            OnBuzzer();
            SendSMS(2);
            KV2Active = 1;
        }
        
        // Khu vực 2 an toàn
        else if (UARTData[0] == CMDINACTIVE2) {  // 0xB2
            I2C_LCD_SetCursor(LCDDisplay, 8, 1);
            I2C_LCD_WriteString(LCDDisplay, "      ");  // Xóa
            KV2Active = 0;
            if (KV1Active == 0) OffBuzzer();  // Chỉ tắt nếu KV1 cũng an toàn
        }
    }
}
```

**D. SendOffKV1() / SendOffKV2()**

Gửi lệnh tắt buzzer đến các khu vực:
```c
void SendOffKV1() {
    uint8_t UARTSend[1] = {CMDOFFKV1};  // 0xC1
    HAL_UART_Transmit(&huart2, UARTSend, 1, 100);
}

void SendOffKV2() {
    uint8_t UARTSend[1] = {CMDOFFKV2};  // 0xC2
    HAL_UART_Transmit(&huart2, UARTSend, 1, 100);
}
```

**E. DisplayMain()**

Hiển thị màn hình chính:
```c
void DisplayMain() {
    I2C_LCD_Clear(LCDDisplay);
    I2C_LCD_WriteString(LCDDisplay, "GIAM SAT AN NINH");
    I2C_LCD_NoBlink(LCDDisplay);
    I2C_LCD_NoCursor(LCDDisplay);
}
```

### 3.5. Luồng hoạt động

**Khởi động:**
```
1. Khởi tạo HAL, Clock, GPIO, I2C, UART
2. Khởi tạo delay (8MHz)
3. Khởi tạo LCD I2C
4. Hiển thị "GIAM SAT AN NINH"
5. Hiển thị "DANG KHOI DONG.." ở dòng 2
6. Chờ 30 giây (module GSM khởi động và đăng ký mạng)
7. Khởi tạo module SIM (gửi lệnh AT)
8. Chờ 2 giây
9. Gửi SMS "HT GIAM SAT SAN SANG"
10. Xóa dòng 2 LCD
11. Bật buzzer 1 giây (báo hiệu sẵn sàng)
12. Tắt buzzer
13. Vào vòng lặp chính
```

**Vòng lặp chính:**
```c
while(1) {
    // 1. Kiểm tra lệnh từ LoRa
    CheckLora();
    
    // 2. Kiểm tra nút nhấn KV1 (PB12)
    if (PB12 == 0) {  // Nhấn (Pull-up, active LOW)
        OffBuzzer();
        SendOffKV1();  // Gửi 0xC1
        HAL_Delay(500);  // Chống dội
    }
    
    // 3. Kiểm tra nút nhấn KV2 (PB13)
    if (PB13 == 0) {  // Nhấn (Pull-up, active LOW)
        OffBuzzer();
        SendOffKV2();  // Gửi 0xC2
        HAL_Delay(500);  // Chống dội
    }
}
```

### 3.6. Hiển thị LCD

**Màn hình chính:**
```
┌────────────────┐
│GIAM SAT AN NINH│  ← Dòng 0
│                │  ← Dòng 1 (hiển thị cảnh báo)
└────────────────┘
```

**Khi có cảnh báo:**
```
┌────────────────┐
│GIAM SAT AN NINH│
│CB KV1  CB KV2  │  ← Hiển thị cảnh báo cả 2 khu vực
└────────────────┘
   ↑       ↑
   Cột 0   Cột 8
```

**Khi khởi động:**
```
┌────────────────┐
│GIAM SAT AN NINH│
│DANG KHOI DONG..│
└────────────────┘
```

### 3.7. Logic xử lý thông minh

**A. Quản lý buzzer:**
- Buzzer chỉ tắt khi CẢ HAI khu vực đều an toàn
- Nếu KV1 an toàn nhưng KV2 còn cảnh báo → Buzzer vẫn kêu
- Người dùng có thể tắt thủ công bằng nút nhấn

**B. Quản lý cờ trạng thái:**
```c
char KV1Active = 0;  // 0: An toàn, 1: Cảnh báo
char KV2Active = 0;  // 0: An toàn, 1: Cảnh báo
```

**C. Gửi SMS:**
- Chỉ gửi SMS khi phát hiện xâm nhập lần đầu
- Không gửi SMS khi khu vực trở về an toàn
- Gửi SMS xác nhận khi hệ thống sẵn sàng

---

## PHẦN 4: CAMERA GIÁM SÁT ESP32-CAM (MainCodeFinal)

### 4.1. Thông số kỹ thuật

**Vi điều khiển:** ESP32 (Dual-core Xtensa LX6)
- Flash: 2MB
- PSRAM: Có (quan trọng cho camera)
- WiFi: 802.11 b/g/n

**Camera Module:** OV2640
- Độ phân giải tối đa: 1600x1200 (UXGA)
- Độ phân giải sử dụng: 640x480 (VGA)
- Định dạng: JPEG
- Giao tiếp: DVP 8-bit parallel

**Phần cứng:**
- **Camera Pins:** D0-D7, VSYNC, HREF, PCLK, XCLK, SIOD, SIOC
- **WiFi:** Built-in (AP Mode)
- **Power:** 5V/500mA minimum

### 4.2. Cấu hình WiFi

**Chế độ:** Access Point (AP)
```c
SSID: "ESP32_CAM_AP"
Password: "12345678"
IP Address: 192.168.4.1
Max Connections: 4
Security: WPA/WPA2-PSK
```

### 4.3. Cấu hình Camera

```c
camera_config_t camera_config = {
    // GPIO Pins (AI-Thinker ESP32-CAM)
    .pin_pwdn  = 32,
    .pin_reset = -1,  // Software reset
    .pin_xclk = 0,
    .pin_sccb_sda = 26,  // I2C Data
    .pin_sccb_scl = 27,  // I2C Clock
    
    // Data pins (8-bit parallel)
    .pin_d7 = 35,
    .pin_d6 = 34,
    .pin_d5 = 39,
    .pin_d4 = 36,
    .pin_d3 = 21,
    .pin_d2 = 19,
    .pin_d1 = 18,
    .pin_d0 = 5,
    
    // Sync pins
    .pin_vsync = 25,
    .pin_href = 23,
    .pin_pclk = 22,
    
    // Camera settings
    .xclk_freq_hz = 20000000,  // 20MHz
    .pixel_format = PIXFORMAT_JPEG,
    .frame_size = FRAMESIZE_VGA,  // 640x480
    .jpeg_quality = 10,  // 0-63, số càng thấp chất lượng càng cao
    .fb_count = 1,  // Single frame buffer
    .grab_mode = CAMERA_GRAB_WHEN_EMPTY
};
```

### 4.4. Giao thức MJPEG Streaming

**MJPEG (Motion JPEG):** Streaming video bằng cách gửi liên tiếp các ảnh JPEG

**Cấu trúc HTTP Response:**
```
HTTP/1.1 200 OK
Content-Type: multipart/x-mixed-replace;boundary=123456789000000000000987654321

--123456789000000000000987654321
Content-Type: image/jpeg
Content-Length: 15234

[JPEG DATA FRAME 1]

--123456789000000000000987654321
Content-Type: image/jpeg
Content-Length: 15891

[JPEG DATA FRAME 2]

--123456789000000000000987654321
...
```

### 4.5. Các hàm chính

**A. init_camera()**

Khởi tạo camera module:
```c
static esp_err_t init_camera(void) {
    // 1. Tạo cấu hình camera
    camera_config_t camera_config = {...};
    
    // 2. Khởi tạo driver camera
    esp_err_t err = esp_camera_init(&camera_config);
    
    // 3. Kiểm tra lỗi
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Camera init failed with error 0x%x", err);
        return err;
    }
    
    return ESP_OK;
}
```

**B. jpg_stream_httpd_handler()**

Handler xử lý HTTP streaming:
```c
esp_err_t jpg_stream_httpd_handler(httpd_req_t *req) {
    // 1. Đặt Content-Type
    httpd_resp_set_type(req, _STREAM_CONTENT_TYPE);
    
    // 2. Vòng lặp vô hạn gửi frame
    while(true) {
        // a. Lấy frame từ camera
        fb = esp_camera_fb_get();
        if (!fb) break;
        
        // b. Chuyển đổi sang JPEG (nếu cần)
        if (fb->format != PIXFORMAT_JPEG) {
            frame2jpg(fb, 80, &_jpg_buf, &_jpg_buf_len);
        } else {
            _jpg_buf = fb->buf;
            _jpg_buf_len = fb->len;
        }
        
        // c. Gửi boundary
        httpd_resp_send_chunk(req, _STREAM_BOUNDARY, ...);
        
        // d. Gửi header của frame
        snprintf(part_buf, 64, _STREAM_PART, _jpg_buf_len);
        httpd_resp_send_chunk(req, part_buf, ...);
        
        // e. Gửi dữ liệu JPEG
        httpd_resp_send_chunk(req, (const char *)_jpg_buf, _jpg_buf_len);
        
        // f. Giải phóng frame buffer
        esp_camera_fb_return(fb);
        
        // g. Tính toán FPS
        frame_time = esp_timer_get_time() - last_frame;
        fps = 1000.0 / (frame_time / 1000);
        ESP_LOGI(TAG, "MJPG: %uKB %ums (%.1ffps)", ...);
    }
    
    return ESP_OK;
}
```

**C. setup_server()**

Khởi tạo HTTP server:
```c
httpd_handle_t setup_server(void) {
    // 1. Tạo cấu hình mặc định
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    
    // 2. Khởi động server
    httpd_handle_t stream_httpd = NULL;
    if (httpd_start(&stream_httpd, &config) == ESP_OK) {
        // 3. Đăng ký URI handler
        httpd_uri_t uri_get = {
            .uri = "/",
            .method = HTTP_GET,
            .handler = jpg_stream_httpd_handler,
            .user_ctx = NULL
        };
        httpd_register_uri_handler(stream_httpd, &uri_get);
    }
    
    return stream_httpd;
}
```

**D. connect_wifi()**

Khởi động WiFi AP mode:
```c
void connect_wifi() {
    // 1. Khởi tạo TCP/IP stack
    esp_netif_init();
    
    // 2. Tạo event loop
    esp_event_loop_create_default();
    
    // 3. Tạo WiFi AP interface
    esp_netif_create_default_wifi_ap();
    
    // 4. Khởi tạo WiFi driver
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    esp_wifi_init(&cfg);
    
    // 5. Cấu hình AP
    wifi_config_t wifi_config = {
        .ap = {
            .ssid = "ESP32_CAM_AP",
            .password = "12345678",
            .max_connection = 4,
            .authmode = WIFI_AUTH_WPA_WPA2_PSK
        }
    };
    
    // 6. Áp dụng cấu hình và khởi động
    esp_wifi_set_mode(WIFI_MODE_AP);
    esp_wifi_set_config(WIFI_IF_AP, &wifi_config);
    esp_wifi_start();
}
```

### 4.6. Luồng hoạt động

**Khởi động:**
```
1. Khởi tạo NVS Flash (lưu cấu hình WiFi)
2. Khởi động WiFi AP Mode
   - SSID: ESP32_CAM_AP
   - IP: 192.168.4.1
3. Khởi tạo Camera
   - Cấu hình GPIO pins
   - Thiết lập VGA, JPEG, quality 10
4. Khởi động Web Server
   - Đăng ký handler cho URI "/"
5. Log: "ESP32 CAM Web Server is up and running"
6. Chờ client kết nối
```

**Khi client truy cập http://192.168.4.1/:**
```
1. HTTP Server nhận request
2. Gọi jpg_stream_httpd_handler()
3. Gửi HTTP header (multipart/x-mixed-replace)
4. Vòng lặp vô hạn:
   a. Lấy frame từ camera
   b. Chuyển sang JPEG (nếu cần)
   c. Gửi boundary
   d. Gửi header frame
   e. Gửi dữ liệu JPEG
   f. Giải phóng frame buffer
   g. Tính FPS và log
   h. Lặp lại
5. Khi client ngắt kết nối → Thoát vòng lặp
```

### 4.7. Hiệu năng

**FPS (Frames Per Second):**
- VGA (640x480): ~15-20 FPS
- QVGA (320x240): ~25-30 FPS
- Phụ thuộc vào: Độ phân giải, chất lượng JPEG, WiFi

**Kích thước frame:**
- VGA JPEG quality 10: ~15-30KB/frame
- Băng thông: ~300-600KB/s (2.4-4.8 Mbps)

**Log ví dụ:**
```
I (15678) esp32-cam Webserver: MJPG: 18KB 65ms (15.4fps)
I (15743) esp32-cam Webserver: MJPG: 18KB 64ms (15.6fps)
I (15808) esp32-cam Webserver: MJPG: 19KB 66ms (15.2fps)
```

### 4.8. Hỗ trợ nhiều loại board

**AI-Thinker ESP32-CAM** (mặc định):
```c
#define CAM_PIN_PWDN 32
#define CAM_PIN_XCLK 0
#define CAM_PIN_SIOD 26
#define CAM_PIN_SIOC 27
// ... (xem camera_pins.h)
```

**Các board khác:**
- Freenove ESP32-WROVER CAM
- Espressif ESP-EYE
- TTGO T-Journal

Chọn board qua: `idf.py menuconfig` → Application Configuration → Select Board

### 4.9. Tính năng đặc biệt

**A. Tự động chuyển đổi định dạng:**
- Nếu camera output không phải JPEG → Tự động chuyển đổi
- Sử dụng thư viện esp_jpeg

**B. Quản lý bộ nhớ:**
- Frame buffer được quản lý tự động
- Phải gọi `esp_camera_fb_return()` sau khi xử lý
- Sử dụng PSRAM để lưu frame buffer

**C. Tính toán FPS real-time:**
- Đo thời gian giữa các frame
- Log FPS, kích thước frame, thời gian xử lý

**D. Streaming liên tục:**
- Không giới hạn thời gian
- Chỉ dừng khi client ngắt kết nối

---

## PHẦN 5: THƯ VIỆN DÙNG CHUNG

### 5.1. Delay Library (delay.c/h)

**Tác giả:** Ceres_Li

**Chức năng:** Tạo độ trễ chính xác sử dụng SysTick Timer

**Các hàm:**

**A. delay_init(uint8_t SYSCLK)**
```c
void delay_init(uint8_t SYSCLK)
```
- **Tham số:** SYSCLK - Tần số HCLK (MHz), ví dụ: 8, 72
- **Chức năng:** Cấu hình SysTick để tính toán delay chính xác
- **Cơ chế:** 
  - Nếu SYSCLK = 8MHz → 8 chu kỳ clock = 1 microsecond
  - `fac_us = SYSCLK` (số chu kỳ cho 1μs)
  - `fac_ms = fac_us * 1000` (số chu kỳ cho 1ms)

**B. delay_us(uint32_t _us)**
```c
void delay_us(uint32_t _us)
```
- **Chức năng:** Delay chính xác đến microsecond
- **Nguyên lý:**
  1. Tính số ticks cần: `ticks = _us * fac_us`
  2. Đọc giá trị SysTick->VAL (đếm xuống)
  3. Tính số ticks đã trôi qua
  4. Xử lý trường hợp SysTick overflow
  5. Lặp cho đến khi đủ số ticks

**C. delay_ms(uint16_t _ms)**
```c
void delay_ms(uint16_t _ms)
```
- **Chức năng:** Delay millisecond
- **Cơ chế:** Gọi `delay_us(1000)` _ms lần

**Ưu điểm:**
- Chính xác cao hơn HAL_Delay()
- Không phụ thuộc vào interrupt
- Có thể delay từ 1μs

**Sử dụng:**
```c
delay_init(8);      // Khởi tạo với HCLK = 8MHz
delay_us(100);      // Delay 100 microseconds
delay_ms(500);      // Delay 500 milliseconds
```

---

### 5.2. I2C LCD Library (I2C_LCD.c/h)

**Tác giả:** Khaled Magdy (www.DeepBlueMbedded.com)

**Chức năng:** Driver hoàn chỉnh cho LCD 16x2/20x4 qua I2C (PCF8574)

**Kiến trúc:**
- **I2C_LCD.c/h:** Driver chính
- **I2C_LCD_cfg.c/h:** File cấu hình

**Cấu hình (I2C_LCD_cfg.c):**
```c
const I2C_LCD_CfgType I2C_LCD_CfgParam[I2C_LCD_MAX] = {
    {
        I2C_LCD_1,      // Instance index
        &hi2c1,         // I2C handle
        0x27,           // Địa chỉ I2C
        16,             // Số cột
        2               // Số hàng
    }
};
```

**Giao tiếp I2C với PCF8574:**

**Sơ đồ bit:**
```
Bit 7 | Bit 6 | Bit 5 | Bit 4 | Bit 3 | Bit 2 | Bit 1 | Bit 0
 D7   |  D6   |  D5   |  D4   |  BL   |  EN   |  RW   |  RS
```
- **D7-D4:** Data bits (4-bit mode)
- **BL:** Backlight control (1=ON, 0=OFF)
- **EN:** Enable signal (tạo xung kích hoạt LCD)
- **RW:** Read/Write (luôn = 0 cho Write)
- **RS:** Register Select (0=Command, 1=Data)

**Quy trình gửi 1 byte:**
```
1. Gửi 4 bit cao + EN=1
2. Delay 2μs
3. Gửi 4 bit cao + EN=0
4. Delay 50μs
5. Gửi 4 bit thấp + EN=1
6. Delay 2μs
7. Gửi 4 bit thấp + EN=0
8. Delay 50μs
```

**Các hàm chính:**

**A. Khởi tạo:**
```c
void I2C_LCD_Init(uint8_t I2C_LCD_InstanceIndex)
```
- Đợi 50ms sau power-up
- Gửi chuỗi khởi tạo theo datasheet HD44780
- Cấu hình: 4-bit mode, 2 dòng, font 5x8
- Xóa màn hình

**B. Điều khiển hiển thị:**
```c
void I2C_LCD_Clear()                    // Xóa màn hình
void I2C_LCD_Home()                     // Về vị trí (0,0)
void I2C_LCD_SetCursor(col, row)        // Đặt con trỏ
void I2C_LCD_WriteChar(char)            // Viết 1 ký tự
void I2C_LCD_WriteString(str)           // Viết chuỗi
```

**C. Điều khiển backlight:**
```c
void I2C_LCD_Backlight()                // Bật đèn nền
void I2C_LCD_NoBacklight()              // Tắt đèn nền
```

**D. Hiệu ứng:**
```c
void I2C_LCD_ShiftLeft()                // Dịch màn hình sang trái
void I2C_LCD_ShiftRight()               // Dịch màn hình sang phải
void I2C_LCD_Cursor()                   // Hiện con trỏ
void I2C_LCD_NoCursor()                 // Ẩn con trỏ
void I2C_LCD_Blink()                    // Nhấp nháy con trỏ
void I2C_LCD_NoBlink()                  // Tắt nhấp nháy
```

**E. Ký tự tùy chỉnh:**
```c
void I2C_LCD_CreateCustomChar(index, charMap)  // Tạo ký tự tùy chỉnh
void I2C_LCD_PrintCustomChar(index)            // In ký tự tùy chỉnh
```

**Sử dụng:**
```c
// Khởi tạo
I2C_LCD_Init(I2C_LCD_1);

// Hiển thị text
I2C_LCD_SetCursor(I2C_LCD_1, 0, 0);
I2C_LCD_WriteString(I2C_LCD_1, "Hello World!");

// Xóa màn hình
I2C_LCD_Clear(I2C_LCD_1);

// Bật đèn nền
I2C_LCD_Backlight(I2C_LCD_1);
```

---

### 5.3. Utility Macros (Util.h)

**Chức năng:** Cung cấp các macro tối ưu cho GPIO và delay

**A. GPIO Direct Access Macros:**
```c
// Bật pin (nhanh hơn HAL_GPIO_WritePin)
#define GPIO_SET_PIN(port, pin) \
    ((port)->BSRR = (pin))

// Tắt pin
#define GPIO_CLEAR_PIN(port, pin) \
    ((port)->BSRR = (uint32_t)(pin) << 16U)

// Đảo trạng thái pin
#define GPIO_TOGGLE_PIN(port, pin) \
    ((port)->ODR ^= (pin))

// Đọc trạng thái pin
#define GPIO_READ_PIN(port, pin) \
    (((port)->IDR & (pin)) != 0U)
```

**Ví dụ sử dụng:**
```c
GPIO_SET_PIN(GPIOB, GPIO_PIN_14);       // Bật LED
GPIO_CLEAR_PIN(GPIOC, GPIO_PIN_14);     // Tắt Buzzer
GPIO_TOGGLE_PIN(GPIOB, GPIO_PIN_14);    // Đảo LED
if (GPIO_READ_PIN(GPIOB, GPIO_PIN_12))  // Đọc cảm biến
```

**B. SysTick Delay Macros:**
```c
// Delay microsecond (không cần khởi tạo)
#define DELAY_US(us) \
    do { \
        uint32_t ticks = (us) * (SystemCoreClock / 1000000); \
        uint32_t start = SysTick->VAL; \
        while ((start - SysTick->VAL) < ticks); \
    } while(0)

// Delay millisecond
#define DELAY_MS(ms) \
    DELAY_US((ms) * 1000)
```

**Ưu điểm:**
- Truy cập trực tiếp thanh ghi → Nhanh hơn HAL functions
- Inline → Không có overhead của function call
- Tự động tính toán dựa trên SystemCoreClock

**So sánh hiệu năng:**
```c
// HAL function (chậm hơn)
HAL_GPIO_WritePin(GPIOB, GPIO_PIN_14, GPIO_PIN_SET);

// Macro (nhanh hơn)
GPIO_SET_PIN(GPIOB, GPIO_PIN_14);
```

---

## PHẦN 6: GIAO THỨC TRUYỀN THÔNG TỔNG THỂ

### 6.1. Sơ đồ giao tiếp

```
┌─────────────┐                           ┌─────────────┐
│  CodeTram1  │                           │  CodeTram2  │
│   (KV1)     │                           │   (KV2)     │
└──────┬──────┘                           └──────┬──────┘
       │                                         │
       │ LoRa UART2 (9600 baud)                 │ LoRa UART2 (9600 baud)
       │                                         │
       │ TX: 0xA1 (Phát hiện)                   │ TX: 0xB1 (Phát hiện)
       │     0xA2 (An toàn)                     │     0xB2 (An toàn)
       │                                         │
       │ RX: 0xC1 (Tắt buzzer)                  │ RX: 0xC2 (Tắt buzzer)
       │                                         │
       └────────────┬────────────────────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │   CodeTrungTam       │
         │   (Trạm trung tâm)   │
         └──────────┬───────────┘
                    │
                    │ GSM UART1 (115200 baud)
                    │
                    │ AT Commands
                    │ SMS: "Canh bao dot nhap khu vuc X"
                    │
                    ▼
         ┌──────────────────────┐
         │   Điện thoại         │
         │   0968046024         │
         └──────────────────────┘


         ┌──────────────────────┐
         │   ESP32-CAM          │
         │   (Camera)           │
         └──────────┬───────────┘
                    │
                    │ WiFi AP Mode
                    │ SSID: ESP32_CAM_AP
                    │ IP: 192.168.4.1
                    │
                    ▼
         ┌──────────────────────┐
         │   Trình duyệt web    │
         │   MJPEG Stream       │
         └──────────────────────┘
```

### 6.2. Bảng mã lệnh LoRa

| Mã lệnh | Giá trị | Nguồn | Đích | Ý nghĩa |
|---------|---------|-------|------|---------|
| CMDACTIVE1 | 0xA1 | CodeTram1 | CodeTrungTam | KV1 phát hiện xâm nhập |
| CMDINACTIVE1 | 0xA2 | CodeTram1 | CodeTrungTam | KV1 trở về an toàn |
| CMDACTIVE2 | 0xB1 | CodeTram2 | CodeTrungTam | KV2 phát hiện xâm nhập |
| CMDINACTIVE2 | 0xB2 | CodeTram2 | CodeTrungTam | KV2 trở về an toàn |
| CMDOFFKV1 | 0xC1 | CodeTrungTam | CodeTram1 | Tắt buzzer KV1 |
| CMDOFFKV2 | 0xC2 | CodeTrungTam | CodeTram2 | Tắt buzzer KV2 |

### 6.3. Định dạng gói tin LoRa

**Đơn giản:** Chỉ 1 byte duy nhất
```
[1 byte] - Mã lệnh
```

**Ví dụ:**
- Gửi cảnh báo KV1: `0xA1`
- Nhận lệnh tắt KV2: `0xC2`

**Ưu điểm:**
- Đơn giản, dễ implement
- Băng thông thấp
- Độ trễ thấp

**Nhược điểm:**
- Không có checksum
- Không có xác nhận (ACK)
- Có thể bị nhiễu

### 6.4. Giao thức GSM/SIM

**Baudrate:** 115200 bps  
**Format:** 8N1 (8 data bits, No parity, 1 stop bit)

**Cấu trúc lệnh AT:**
```
AT<command><CR><LF>
```
- `<CR>` = 0x0D (Carriage Return)
- `<LF>` = 0x0A (Line Feed)

**Ví dụ gửi SMS:**
```
1. AT+CMGS="0968046024"\r\n
2. [Chờ prompt '>']
3. Canh bao dot nhap khu vuc 1
4. \x1A (Ctrl+Z)
5. [Chờ response: +CMGS: <mr>]
```

**Response từ module:**
```
OK\r\n                  → Lệnh thành công
ERROR\r\n              → Lệnh lỗi
+CMGS: 123\r\n         → SMS đã gửi, message reference = 123
```

### 6.5. Giao thức HTTP (ESP32-CAM)

**URL:** `http://192.168.4.1/`  
**Method:** GET  
**Protocol:** HTTP/1.1

**Request:**
```
GET / HTTP/1.1
Host: 192.168.4.1
User-Agent: Mozilla/5.0...
Accept: text/html,application/xhtml+xml...
```

**Response:**
```
HTTP/1.1 200 OK
Content-Type: multipart/x-mixed-replace;boundary=123456789000000000000987654321

--123456789000000000000987654321
Content-Type: image/jpeg
Content-Length: 15234

[JPEG DATA]
--123456789000000000000987654321
...
```

### 6.6. Luồng giao tiếp tổng thể

**Kịch bản 1: Phát hiện xâm nhập KV1**

```
1. CodeTram1: Cảm biến PB12 = HIGH
2. CodeTram1: Delay 500ms (chống dội)
3. CodeTram1: Kiểm tra lại PB12 = HIGH
4. CodeTram1: Bật LED, Bật Buzzer
5. CodeTram1: Gửi 0xA1 qua LoRa
   ↓
6. CodeTrungTam: Nhận 0xA1 từ LoRa
7. CodeTrungTam: Hiển thị "CB KV1" trên LCD
8. CodeTrungTam: Bật Buzzer
9. CodeTrungTam: Gửi SMS "Canh bao dot nhap khu vuc 1"
   ↓
10. Module GSM: Gửi SMS đến 0968046024
11. Điện thoại: Nhận SMS cảnh báo
```

**Kịch bản 2: Người dùng tắt cảnh báo KV1**

```
1. Người dùng: Nhấn nút PB12 trên CodeTrungTam
2. CodeTrungTam: Tắt Buzzer
3. CodeTrungTam: Gửi 0xC1 qua LoRa
   ↓
4. CodeTram1: Nhận 0xC1 từ LoRa
5. CodeTram1: Tắt Buzzer
```

**Kịch bản 3: KV1 trở về an toàn**

```
1. CodeTram1: Cảm biến PB12 = LOW
2. CodeTram1: Tắt LED
3. CodeTram1: Gửi 0xA2 qua LoRa
   (Buzzer vẫn kêu, chờ lệnh tắt)
   ↓
4. CodeTrungTam: Nhận 0xA2 từ LoRa
5. CodeTrungTam: Xóa "CB KV1" trên LCD
6. CodeTrungTam: Kiểm tra KV2Active
   - Nếu KV2Active = 0: Tắt Buzzer
   - Nếu KV2Active = 1: Giữ Buzzer bật
```

**Kịch bản 4: Xem camera**

```
1. Người dùng: Kết nối WiFi "ESP32_CAM_AP"
2. ESP32-CAM: Cấp IP cho client (192.168.4.x)
3. Người dùng: Mở trình duyệt, truy cập 192.168.4.1
4. ESP32-CAM: Nhận HTTP GET request
5. ESP32-CAM: Bắt đầu streaming MJPEG
   - Lấy frame từ camera
   - Chuyển sang JPEG
   - Gửi qua HTTP
   - Lặp lại
6. Trình duyệt: Hiển thị video real-time
```

---

## PHẦN 7: HƯỚNG DẪN SỬ DỤNG HỆ THỐNG

### 7.1. Yêu cầu phần cứng

**Cho mỗi module STM32 (CodeTram1, CodeTram2, CodeTrungTam):**
- STM32F103C6 Development Board
- Module LoRa (SX1278 hoặc tương tự)
- LCD I2C 16x2 (địa chỉ 0x27)
- Buzzer 5V
- LED
- Cảm biến (PIR, cửa từ, hoặc tương tự)
- Nút nhấn (cho CodeTrungTam)
- Nguồn 5V/1A
- ST-Link V2 (để nạp code)

**Cho ESP32-CAM:**
- ESP32-CAM (AI-Thinker hoặc tương tự)
- Camera OV2640 (thường đi kèm)
- Nguồn 5V/500mA
- USB to Serial adapter (để nạp code)

**Cho module GSM (CodeTrungTam):**
- Module GSM/SIM (SIM800L, SIM900A, hoặc tương tự)
- SIM card có sẵn tiền và đăng ký mạng
- Nguồn 5V/2A (GSM tiêu thụ dòng cao)

### 7.2. Kết nối phần cứng

**A. CodeTram1 / CodeTram2:**

```
STM32F103C6:
├─ PB12 ──→ Cảm biến OUT
├─ PB14 ──→ LED Anode (qua điện trở 330Ω)
├─ PC14 ──→ Buzzer + (qua transistor NPN)
├─ PB6  ──→ LCD SCL
├─ PB7  ──→ LCD SDA
├─ PA2  ──→ LoRa RX
├─ PA3  ──→ LoRa TX
├─ PA9  ──→ Debug UART TX (optional)
└─ PA10 ──→ Debug UART RX (optional)

Nguồn:
├─ 5V   ──→ STM32 5V, LCD VCC, LoRa VCC
└─ GND  ──→ Common GND
```

**B. CodeTrungTam:**

```
STM32F103C6:
├─ PB12 ──→ Nút nhấn KV1 (Pull-up, active LOW)
├─ PB13 ──→ Nút nhấn KV2 (Pull-up, active LOW)
├─ PC14 ──→ Buzzer + (qua transistor NPN)
├─ PB6  ──→ LCD SCL
├─ PB7  ──→ LCD SDA
├─ PA2  ──→ LoRa RX
├─ PA3  ──→ LoRa TX
├─ PA9  ──→ GSM RX
└─ PA10 ──→ GSM TX

Module GSM:
├─ TX   ──→ STM32 PA10
├─ RX   ──→ STM32 PA9
├─ VCC  ──→ 5V (nguồn riêng, dòng cao)
└─ GND  ──→ Common GND

Nguồn:
├─ 5V   ──→ STM32 5V, LCD VCC, LoRa VCC
└─ GND  ──→ Common GND
```

**C. ESP32-CAM:**

```
ESP32-CAM:
├─ 5V   ──→ Nguồn 5V
├─ GND  ──→ GND
└─ Camera module đã kết nối sẵn

Để nạp code:
├─ GPIO0 ──→ GND (khi nạp code)
├─ U0TXD ──→ USB-Serial RX
└─ U0RXD ──→ USB-Serial TX
```

### 7.3. Biên dịch và nạp code

**A. Cho STM32 (Keil MDK-ARM):**

```bash
1. Mở Keil MDK-ARM
2. File → Open Project
3. Chọn file .uvprojx trong thư mục MDK-ARM
4. Project → Build Target (F7)
5. Kết nối ST-Link V2
6. Flash → Download (F8)
7. Reset board
```

**B. Cho ESP32-CAM (ESP-IDF):**

```bash
# 1. Cài đặt ESP-IDF
git clone -b v5.5.1 --recursive https://github.com/espressif/esp-idf.git
cd esp-idf
./install.sh
. ./export.sh

# 2. Build dự án
cd MainCodeFinal
idf.py build

# 3. Nạp code (GPIO0 nối GND)
idf.py -p COM3 flash

# 4. Xem log
idf.py -p COM3 monitor
```

### 7.4. Cấu hình hệ thống

**A. Thay đổi số điện thoại (CodeTrungTam):**

Sửa file `CodeTrungTam/MainCode/Core/Src/main.c`:
```c
uint8_t PhoneNumber[] = "0968046024";  // Thay bằng số của bạn
```

**B. Thay đổi WiFi (ESP32-CAM):**

Sửa file `MainCodeFinal/main/connect_wifi.c`:
```c
#define WIFI_AP_SSID "ESP32_CAM_AP"      // Tên WiFi
#define WIFI_AP_PASSWORD "12345678"      // Mật khẩu
```

**C. Thay đổi địa chỉ LCD:**

Nếu LCD của bạn có địa chỉ 0x3F thay vì 0x27:

Sửa file `Core/Src/I2C_LCD_cfg.c`:
```c
const I2C_LCD_CfgType I2C_LCD_CfgParam[I2C_LCD_MAX] = {
    {
        I2C_LCD_1,
        &hi2c1,
        0x3F,  // Thay 0x27 bằng 0x3F
        16,
        2
    }
};
```

**D. Thay đổi độ phân giải camera:**

Sửa file `MainCodeFinal/main/main.c`:
```c
.frame_size = FRAMESIZE_QVGA,  // Thay VGA bằng QVGA (320x240)
```

Các lựa chọn:
- `FRAMESIZE_QQVGA`: 160x120
- `FRAMESIZE_QVGA`: 320x240
- `FRAMESIZE_VGA`: 640x480 (mặc định)
- `FRAMESIZE_SVGA`: 800x600
- `FRAMESIZE_XGA`: 1024x768

### 7.5. Khởi động hệ thống

**Bước 1: Khởi động CodeTram1 và CodeTram2**
```
1. Cấp nguồn cho board
2. LED sáng 30 giây (thời gian khởi động)
3. LED tắt
4. Buzzer kêu 1 giây (kiểm tra hoạt động)
5. Buzzer tắt
6. Hệ thống sẵn sàng
```

**Bước 2: Khởi động CodeTrungTam**
```
1. Cấp nguồn cho board
2. LCD hiển thị "GIAM SAT AN NINH"
3. LCD hiển thị "DANG KHOI DONG.." ở dòng 2
4. Chờ 30 giây (module GSM đăng ký mạng)
5. Gửi SMS "HT GIAM SAT SAN SANG" đến điện thoại
6. Xóa dòng 2 LCD
7. Buzzer kêu 1 giây
8. Buzzer tắt
9. Hệ thống sẵn sàng
```

**Bước 3: Khởi động ESP32-CAM**
```
1. Cấp nguồn cho board
2. Chờ 5-10 giây
3. WiFi AP "ESP32_CAM_AP" xuất hiện
4. Kết nối vào WiFi (password: 12345678)
5. Mở trình duyệt, truy cập: http://192.168.4.1/
6. Video stream hiển thị
```

### 7.6. Sử dụng hệ thống

**A. Khi có xâm nhập:**

**Tại khu vực:**
- LED sáng
- Buzzer kêu

**Tại trạm trung tâm:**
- LCD hiển thị "CB KV1" hoặc "CB KV2"
- Buzzer kêu
- Nhận SMS cảnh báo trên điện thoại

**B. Tắt cảnh báo:**

**Cách 1: Nhấn nút tại trạm trung tâm**
- Nhấn nút PB12 để tắt cảnh báo KV1
- Nhấn nút PB13 để tắt cảnh báo KV2

**Cách 2: Cảm biến trở về bình thường**
- Khi cảm biến không còn phát hiện
- LED tắt
- Gửi lệnh "an toàn" về trung tâm
- Buzzer tại khu vực vẫn kêu (chờ xác nhận)
- Buzzer tại trung tâm tắt (nếu khu vực khác cũng an toàn)

**C. Xem camera:**
1. Kết nối WiFi "ESP32_CAM_AP"
2. Mở trình duyệt
3. Truy cập: http://192.168.4.1/
4. Xem video real-time

### 7.7. Kiểm tra hoạt động

**A. Kiểm tra LoRa:**
```
1. Kích hoạt cảm biến tại CodeTram1
2. Kiểm tra LCD tại CodeTrungTam có hiển thị "CB KV1"
3. Nếu không → Kiểm tra kết nối LoRa, baudrate
```

**B. Kiểm tra GSM:**
```
1. Kết nối UART1 của CodeTrungTam với máy tính
2. Mở Serial Monitor (115200 baud)
3. Gửi lệnh "AT" → Phải nhận "OK"
4. Gửi lệnh "AT+CREG?" → Phải nhận "+CREG: 0,1"
5. Nếu không → Kiểm tra SIM card, anten, nguồn
```

**C. Kiểm tra LCD:**
```
1. Kiểm tra đèn nền LCD có sáng không
2. Điều chỉnh biến trở contrast trên LCD
3. Nếu không hiển thị → Kiểm tra địa chỉ I2C (0x27 hoặc 0x3F)
```

**D. Kiểm tra Camera:**
```
1. Kiểm tra log qua idf.py monitor
2. Tìm dòng "ESP32 CAM Web Server is up and running"
3. Kiểm tra WiFi AP có xuất hiện không
4. Nếu không → Kiểm tra kết nối camera, nguồn
```

---

## PHẦN 8: KHẮC PHỤC SỰ CỐ VÀ TỐI ƯU HÓA

### 8.1. Các vấn đề thường gặp

**A. LoRa không giao tiếp được**

**Triệu chứng:**
- CodeTrungTam không nhận được lệnh từ CodeTram1/2
- LCD không hiển thị cảnh báo

**Nguyên nhân:**
- Baudrate không khớp
- TX/RX bị đảo
- Module LoRa chưa cấu hình
- Khoảng cách quá xa

**Giải pháp:**
```c
// 1. Kiểm tra baudrate (phải giống nhau)
huart2.Init.BaudRate = 9600;

// 2. Kiểm tra kết nối
// STM32 PA2 (TX) → LoRa RX
// STM32 PA3 (RX) → LoRa TX

// 3. Cấu hình LoRa (nếu cần)
// - Tần số: 433MHz hoặc 868MHz
// - Bandwidth: 125kHz
// - Spreading Factor: 7-12
// - Coding Rate: 4/5

// 4. Giảm khoảng cách hoặc thêm anten
```

**B. GSM không gửi được SMS**

**Triệu chứng:**
- Không nhận được SMS cảnh báo
- Module GSM không phản hồi lệnh AT

**Nguyên nhân:**
- SIM card chưa kích hoạt
- Chưa đăng ký mạng
- Hết tiền
- Nguồn không đủ mạnh
- Baudrate sai

**Giải pháp:**
```c
// 1. Kiểm tra kết nối UART
// STM32 PA9 (TX) → GSM RX
// STM32 PA10 (RX) → GSM TX

// 2. Kiểm tra nguồn
// GSM cần nguồn 5V/2A, dòng đột biến có thể lên 2A
// Sử dụng nguồn riêng cho GSM

// 3. Kiểm tra đăng ký mạng
// Gửi: AT+CREG?
// Nhận: +CREG: 0,1 → OK
//       +CREG: 0,3 → Chưa đăng ký

// 4. Tăng thời gian chờ khởi động
HAL_Delay(30000);  // Tăng lên 60000 (60 giây)

// 5. Thêm lệnh kiểm tra
HAL_UART_Transmit(&huart1, "AT+CSQ\r\n", ...);  // Kiểm tra tín hiệu
// Response: +CSQ: 15,0 → Tín hiệu tốt (0-31)
```

**C. LCD không hiển thị**

**Triệu chứng:**
- Màn hình trắng hoặc đen
- Không có chữ

**Nguyên nhân:**
- Địa chỉ I2C sai
- Kết nối SDA/SCL bị đảo
- Chưa bật backlight
- Contrast chưa điều chỉnh

**Giải pháp:**
```c
// 1. Quét địa chỉ I2C
// Sử dụng I2C scanner để tìm địa chỉ
// Thường là 0x27 hoặc 0x3F

// 2. Thay đổi địa chỉ trong I2C_LCD_cfg.c
.I2C_Address = 0x3F,  // Thay 0x27 bằng 0x3F

// 3. Kiểm tra kết nối
// PB6 → SCL (Clock)
// PB7 → SDA (Data)

// 4. Bật backlight
I2C_LCD_Backlight(I2C_LCD_1);

// 5. Điều chỉnh biến trở contrast trên LCD
```

**D. Camera không khởi động**

**Triệu chứng:**
- Log: "Camera init failed"
- WiFi AP không xuất hiện

**Nguyên nhân:**
- Kết nối camera không đúng
- Camera bị hỏng
- Chọn sai board
- Nguồn không đủ

**Giải pháp:**
```bash
# 1. Kiểm tra log
idf.py -p COM3 monitor

# 2. Kiểm tra board selection
idf.py menuconfig
# → Application Configuration → Select Board
# → Chọn đúng board (AI-Thinker ESP32-CAM)

# 3. Kiểm tra nguồn
# ESP32-CAM cần 5V/500mA minimum
# Không cấp nguồn qua USB máy tính

# 4. Kiểm tra kết nối camera
# Camera module phải cắm chặt vào socket

# 5. Giảm XCLK frequency
.xclk_freq_hz = 10000000,  // Giảm từ 20MHz xuống 10MHz
```

**E. Video bị giật, FPS thấp**

**Triệu chứng:**
- Video không mượt
- FPS < 10

**Nguyên nhân:**
- Độ phân giải quá cao
- Chất lượng JPEG quá cao
- WiFi yếu
- Nhiều client kết nối

**Giải pháp:**
```c
// 1. Giảm độ phân giải
.frame_size = FRAMESIZE_QVGA,  // 320x240 thay vì VGA

// 2. Giảm chất lượng JPEG
.jpeg_quality = 20,  // Tăng từ 10 lên 20-30

// 3. Tăng frame buffer
.fb_count = 2,  // Tăng từ 1 lên 2

// 4. Di chuyển gần ESP32-CAM hơn

// 5. Giới hạn số client
#define MAX_STA_CONN 1  // Chỉ cho 1 client
```

**F. Buzzer không tắt**

**Triệu chứng:**
- Buzzer kêu liên tục
- Không tắt được bằng nút nhấn

**Nguyên nhân:**
- Lệnh tắt không được gửi
- LoRa không hoạt động
- Nút nhấn bị lỗi

**Giải pháp:**
```c
// 1. Kiểm tra nút nhấn
// Nút phải kết nối đúng (Pull-up, active LOW)

// 2. Thêm log debug
if (HAL_GPIO_ReadPin(GPIOB, GPIO_PIN_12) == 0) {
    // Thêm log để kiểm tra
    OffBuzzer();
    SendOffKV1();
}

// 3. Tăng timeout UART
HAL_UART_Receive(&huart2, UARTData, 1, 100);  // Tăng từ 10ms lên 100ms

// 4. Thêm nút tắt khẩn cấp
// Tắt buzzer trực tiếp không cần LoRa
```

### 8.2. Tối ưu hóa hệ thống

**A. Tăng tốc độ STM32**

Hiện tại STM32 chạy 8MHz, có thể tăng lên 72MHz:

```c
// Trong SystemClock_Config()
RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL9;  // 8MHz * 9 = 72MHz

// Cập nhật delay
delay_init(72);  // Thay vì 8
```

**B. Sử dụng UART Interrupt**

Thay vì polling, dùng interrupt để nhận dữ liệu:

```c
// Trong main.c
uint8_t UARTRxBuffer[1];

// Khởi động receive interrupt
HAL_UART_Receive_IT(&huart2, UARTRxBuffer, 1);

// Callback function
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart) {
    if (huart->Instance == USART2) {
        // Xử lý dữ liệu
        if (UARTRxBuffer[0] == CMDACTIVE1) {
            // Xử lý cảnh báo KV1
        }
        // Khởi động lại receive
        HAL_UART_Receive_IT(&huart2, UARTRxBuffer, 1);
    }
}
```

**C. Thêm timeout tự động tắt buzzer**

```c
// Trong main.c
unsigned long BuzzerStartTime = 0;
#define BUZZER_TIMEOUT 300000  // 5 phút

// Khi bật buzzer
if (Arlarm == 0) {
    Arlarm = 1;
    OnBuzzer();
    BuzzerStartTime = HAL_GetTick();
    SendArlarm();
}

// Trong vòng lặp
if (Arlarm == 1 && (HAL_GetTick() - BuzzerStartTime > BUZZER_TIMEOUT)) {
    OffBuzzer();
    Arlarm = 0;
}
```

**D. Thêm xác nhận gói tin (ACK)**

```c
// Định nghĩa thêm lệnh ACK
#define CMDACK1 0xD1
#define CMDACK2 0xD2

// Trong CodeTrungTam, sau khi nhận lệnh
if (UARTData[0] == CMDACTIVE1) {
    // Xử lý cảnh báo
    // ...
    
    // Gửi ACK
    uint8_t ACK[1] = {CMDACK1};
    HAL_UART_Transmit(&huart2, ACK, 1, 100);
}

// Trong CodeTram1, sau khi gửi lệnh
SendArlarm();
HAL_Delay(100);

// Kiểm tra ACK
uint8_t ACKData[1];
if (HAL_UART_Receive(&huart2, ACKData, 1, 1000) == HAL_OK) {
    if (ACKData[0] == CMDACK1) {
        // Đã nhận ACK, thành công
    } else {
        // Không nhận ACK, gửi lại
        SendArlarm();
    }
}
```

**E. Lưu log vào EEPROM**

```c
// Lưu thời gian và loại sự kiện
typedef struct {
    uint32_t timestamp;
    uint8_t event_type;  // 1: KV1 active, 2: KV1 inactive, ...
} LogEntry;

// Ghi log
void WriteLog(uint8_t event_type) {
    LogEntry entry;
    entry.timestamp = HAL_GetTick();
    entry.event_type = event_type;
    
    // Ghi vào EEPROM hoặc Flash
    HAL_FLASH_Program(...);
}

// Đọc log
void ReadLog() {
    // Đọc từ EEPROM/Flash
    // Hiển thị lên LCD hoặc gửi qua UART
}
```

**F. Thêm chế độ tiết kiệm năng lượng**

```c
// Khi không có hoạt động, vào Sleep mode
if (idle_time > 60000) {  // 1 phút không hoạt động
    HAL_PWR_EnterSLEEPMode(PWR_MAINREGULATOR_ON, PWR_SLEEPENTRY_WFI);
}

// Cấu hình wake-up từ GPIO interrupt
HAL_NVIC_EnableIRQ(EXTI15_10_IRQn);  // PB12
```

**G. Tăng độ phân giải camera (nếu cần)**

```c
// Trong main.c của ESP32-CAM
.frame_size = FRAMESIZE_SVGA,  // 800x600
.jpeg_quality = 15,  // Tăng quality number để giảm kích thước
.fb_count = 2,  // Sử dụng 2 frame buffer
```

**H. Thêm authentication cho camera**

```c
// Trong jpg_stream_httpd_handler()
// Kiểm tra header Authorization
char *auth_header = NULL;
size_t auth_len = httpd_req_get_hdr_value_len(req, "Authorization");

if (auth_len) {
    auth_header = malloc(auth_len + 1);
    httpd_req_get_hdr_value_str(req, "Authorization", auth_header, auth_len + 1);
    
    // So sánh với "Basic dXNlcjpwYXNz" (user:pass base64)
    if (strcmp(auth_header, "Basic dXNlcjpwYXNz") != 0) {
        httpd_resp_set_status(req, "401 Unauthorized");
        httpd_resp_set_hdr(req, "WWW-Authenticate", "Basic realm=\"ESP32-CAM\"");
        httpd_resp_send(req, NULL, 0);
        free(auth_header);
        return ESP_FAIL;
    }
    free(auth_header);
}
```

---

## PHẦN 9: ĐÁNH GIÁ VÀ KẾT LUẬN

### 9.1. Ưu điểm của hệ thống

**A. Kiến trúc phân tán:**
- Mỗi khu vực có module riêng
- Dễ dàng mở rộng thêm khu vực
- Không phụ thuộc vào một điểm trung tâm duy nhất

**B. Đa kênh cảnh báo:**
- Cảnh báo tại chỗ (LED, Buzzer)
- Cảnh báo từ xa (SMS)
- Giám sát trực quan (Camera)
- Hiển thị trạng thái (LCD)

**C. Truyền thông không dây:**
- LoRa: Khoảng cách xa (vài km)
- WiFi: Xem camera real-time
- GSM: Gửi SMS đến bất kỳ đâu

**D. Giao diện thân thiện:**
- LCD hiển thị trạng thái rõ ràng
- Nút nhấn đơn giản
- Web interface cho camera

**E. Chi phí hợp lý:**
- STM32F103C6: ~$2-3
- ESP32-CAM: ~$5-7
- Module LoRa: ~$3-5
- LCD I2C: ~$2-3
- Tổng: ~$50-70 cho toàn bộ hệ thống

**F. Độ tin cậy cao:**
- Chống nhiễu (delay 500ms)
- Xác nhận cảnh báo (buzzer không tự tắt)
- Quản lý trạng thái chặt chẽ

### 9.2. Nhược điểm và hạn chế

**A. Giao thức LoRa đơn giản:**
- Không có checksum
- Không có ACK
- Có thể bị nhiễu

**Giải pháp:** Thêm checksum và ACK như đã nêu ở phần tối ưu hóa

**B. Phụ thuộc vào mạng GSM:**
- Cần SIM card có tiền
- Phụ thuộc vào vùng phủ sóng
- Chi phí SMS

**Giải pháp:** Thêm kênh thông báo khác (Telegram, Email qua WiFi)

**C. Camera chỉ hoạt động trong phạm vi WiFi:**
- Khoảng cách giới hạn (~50m)
- Không thể xem từ xa qua Internet

**Giải pháp:** 
- Thêm router WiFi để mở rộng phạm vi
- Cấu hình port forwarding để truy cập từ xa
- Sử dụng dịch vụ cloud (AWS, Firebase)

**D. Không có lưu trữ video:**
- Chỉ streaming real-time
- Không ghi lại sự kiện

**Giải pháp:** Thêm thẻ SD card để ghi video khi có cảnh báo

**E. Nguồn điện:**
- Cần nguồn 5V ổn định
- Không có backup battery

**Giải pháp:** Thêm UPS hoặc pin dự phòng

### 9.3. Khả năng mở rộng

**A. Thêm khu vực giám sát:**
```
CodeTram3: Mã lệnh 0xD1/0xD2, nhận 0xC3
CodeTram4: Mã lệnh 0xE1/0xE2, nhận 0xC4
...
```

**B. Thêm loại cảm biến:**
- Cảm biến nhiệt độ
- Cảm biến khói
- Cảm biến gas
- Cảm biến cửa/cửa sổ

**C. Thêm tính năng:**
- Ghi log vào EEPROM/SD card
- Gửi email thay vì SMS
- Kết nối với Home Assistant
- Điều khiển qua app mobile
- Nhận diện khuôn mặt (AI)

**D. Tích hợp IoT:**
- MQTT protocol
- Cloud storage (AWS S3, Google Cloud)
- Dashboard web (Node-RED, Grafana)
- Notification (Telegram Bot, Discord)

**E. Thêm camera:**
- Nhiều ESP32-CAM cho nhiều góc nhìn
- Mỗi camera có IP riêng
- Tích hợp vào một dashboard

### 9.4. Ứng dụng thực tế

**A. Nhà riêng:**
- Giám sát cửa chính, cửa sau
- Phát hiện xâm nhập
- Xem camera từ xa

**B. Kho bãi:**
- Giám sát nhiều khu vực
- Cảnh báo qua SMS
- Ghi lại sự kiện

**C. Văn phòng nhỏ:**
- Giám sát ngoài giờ làm việc
- Phát hiện xâm nhập
- Quản lý ra vào

**D. Cửa hàng:**
- Giám sát khi đóng cửa
- Phát hiện trộm cắp
- Xem camera real-time

**E. Trang trại:**
- Giám sát chuồng trại
- Phát hiện động vật hoang dã
- Cảnh báo từ xa

### 9.5. So sánh với giải pháp thương mại

| Tiêu chí | Hệ thống này | Giải pháp thương mại |
|----------|--------------|----------------------|
| Chi phí | ~$50-70 | $200-500+ |
| Tùy chỉnh | Hoàn toàn | Hạn chế |
| Mở rộng | Dễ dàng | Phụ thuộc nhà cung cấp |
| Bảo trì | Tự bảo trì | Cần hỗ trợ kỹ thuật |
| Phí dịch vụ | Không | $5-20/tháng |
| Độ tin cậy | Tốt | Rất tốt |
| Hỗ trợ | Cộng đồng | Chính thức |

### 9.6. Kết luận

**Hệ thống giám sát an ninh này là một giải pháp hoàn chỉnh, chi phí thấp, dễ tùy chỉnh và mở rộng.**

**Điểm mạnh:**
- Kiến trúc phân tán, dễ mở rộng
- Đa kênh cảnh báo (LED, Buzzer, SMS, Camera)
- Truyền thông không dây (LoRa, WiFi, GSM)
- Chi phí hợp lý (~$50-70)
- Code rõ ràng, dễ hiểu, dễ tùy chỉnh

**Phù hợp cho:**
- Dự án học tập, nghiên cứu
- Nhà riêng, kho bãi nhỏ
- Người muốn tự xây dựng hệ thống
- Người có kiến thức lập trình nhúng cơ bản

**Không phù hợp cho:**
- Hệ thống quy mô lớn, chuyên nghiệp
- Yêu cầu độ tin cậy cực cao (99.99%)
- Cần hỗ trợ kỹ thuật 24/7
- Không có kiến thức kỹ thuật

**Hướng phát triển:**
- Thêm checksum và ACK cho LoRa
- Lưu trữ video vào SD card
- Tích hợp AI nhận diện khuôn mặt
- Kết nối với cloud (AWS, Firebase)
- Xây dựng app mobile
- Thêm nhiều loại cảm biến

**Tổng kết:**
Đây là một dự án giáo dục tuyệt vời, giúp hiểu rõ về:
- Lập trình nhúng (STM32, ESP32)
- Giao tiếp UART, I2C, SPI
- Truyền thông không dây (LoRa, WiFi, GSM)
- Xử lý camera và streaming
- Thiết kế hệ thống IoT

Với kiến thức thu được từ dự án này, có thể phát triển thành các hệ thống phức tạp hơn như:
- Smart Home
- Industrial IoT
- Agricultural Monitoring
- Environmental Monitoring

---

## PHẦN 10: PHỤ LỤC

### 10.1. Bảng chân GPIO tổng hợp

**A. CodeTram1 / CodeTram2:**

| Chân | Chức năng | Loại | Mô tả |
|------|-----------|------|-------|
| PB12 | Cảm biến | Input | Đầu vào cảm biến (No Pull) |
| PB14 | LED | Output | LED báo hiệu |
| PC14 | Buzzer | Output | Còi báo động |
| PB6 | I2C1_SCL | AF | Clock cho LCD I2C |
| PB7 | I2C1_SDA | AF | Data cho LCD I2C |
| PA2 | USART2_TX | AF | TX LoRa |
| PA3 | USART2_RX | AF | RX LoRa |
| PA9 | USART1_TX | AF | TX Debug (optional) |
| PA10 | USART1_RX | AF | RX Debug (optional) |

**B. CodeTrungTam:**

| Chân | Chức năng | Loại | Mô tả |
|------|-----------|------|-------|
| PB12 | Nút KV1 | Input | Nút tắt cảnh báo KV1 (Pull-up) |
| PB13 | Nút KV2 | Input | Nút tắt cảnh báo KV2 (Pull-up) |
| PC14 | Buzzer | Output | Còi báo động |
| PB6 | I2C1_SCL | AF | Clock cho LCD I2C |
| PB7 | I2C1_SDA | AF | Data cho LCD I2C |
| PA2 | USART2_TX | AF | TX LoRa |
| PA3 | USART2_RX | AF | RX LoRa |
| PA9 | USART1_TX | AF | TX GSM |
| PA10 | USART1_RX | AF | RX GSM |

**C. ESP32-CAM (AI-Thinker):**

| Chân | Chức năng | Mô tả |
|------|-----------|-------|
| GPIO0 | XCLK | Master clock cho camera (20MHz) |
| GPIO26 | SIOD | I2C Data (SCCB) |
| GPIO27 | SIOC | I2C Clock (SCCB) |
| GPIO5 | D0 | Data bit 0 |
| GPIO18 | D1 | Data bit 1 |
| GPIO19 | D2 | Data bit 2 |
| GPIO21 | D3 | Data bit 3 |
| GPIO36 | D4 | Data bit 4 |
| GPIO39 | D5 | Data bit 5 |
| GPIO34 | D6 | Data bit 6 |
| GPIO35 | D7 | Data bit 7 |
| GPIO25 | VSYNC | Vertical sync |
| GPIO23 | HREF | Horizontal reference |
| GPIO22 | PCLK | Pixel clock |
| GPIO32 | PWDN | Power down |

### 10.2. Bảng mã lệnh đầy đủ

| Mã lệnh | Giá trị | Nguồn | Đích | Ý nghĩa | Hành động |
|---------|---------|-------|------|---------|-----------|
| CMDACTIVE1 | 0xA1 | CodeTram1 | CodeTrungTam | KV1 phát hiện | Hiển thị "CB KV1", Bật buzzer, Gửi SMS1 |
| CMDINACTIVE1 | 0xA2 | CodeTram1 | CodeTrungTam | KV1 an toàn | Xóa "CB KV1", Tắt buzzer (nếu KV2 OK) |
| CMDACTIVE2 | 0xB1 | CodeTram2 | CodeTrungTam | KV2 phát hiện | Hiển thị "CB KV2", Bật buzzer, Gửi SMS2 |
| CMDINACTIVE2 | 0xB2 | CodeTram2 | CodeTrungTam | KV2 an toàn | Xóa "CB KV2", Tắt buzzer (nếu KV1 OK) |
| CMDOFFKV1 | 0xC1 | CodeTrungTam | CodeTram1 | Tắt buzzer KV1 | Tắt buzzer tại CodeTram1 |
| CMDOFFKV2 | 0xC2 | CodeTrungTam | CodeTram2 | Tắt buzzer KV2 | Tắt buzzer tại CodeTram2 |

### 10.3. Danh sách linh kiện và chi phí ước tính

**A. Cho mỗi module STM32 (x3):**

| Linh kiện | Số lượng | Giá (USD) | Tổng (USD) |
|-----------|----------|-----------|------------|
| STM32F103C6 Board | 1 | $2.50 | $2.50 |
| Module LoRa SX1278 | 1 | $4.00 | $4.00 |
| LCD I2C 16x2 | 1 | $2.50 | $2.50 |
| Buzzer 5V | 1 | $0.50 | $0.50 |
| LED | 1 | $0.10 | $0.10 |
| Cảm biến PIR | 1 | $1.50 | $1.50 |
| Nút nhấn | 2 | $0.20 | $0.40 |
| Điện trở, tụ, dây | - | $1.00 | $1.00 |
| **Tổng mỗi module** | | | **$12.50** |
| **Tổng 3 module** | | | **$37.50** |

**B. Module GSM (cho CodeTrungTam):**

| Linh kiện | Số lượng | Giá (USD) | Tổng (USD) |
|-----------|----------|-----------|------------|
| Module GSM SIM800L | 1 | $5.00 | $5.00 |
| SIM card | 1 | $2.00 | $2.00 |
| **Tổng** | | | **$7.00** |

**C. ESP32-CAM:**

| Linh kiện | Số lượng | Giá (USD) | Tổng (USD) |
|-----------|----------|-----------|------------|
| ESP32-CAM + OV2640 | 1 | $6.00 | $6.00 |
| USB to Serial | 1 | $2.00 | $2.00 |
| **Tổng** | | | **$8.00** |

**D. Nguồn và phụ kiện:**

| Linh kiện | Số lượng | Giá (USD) | Tổng (USD) |
|-----------|----------|-----------|------------|
| Nguồn 5V/2A | 3 | $3.00 | $9.00 |
| Dây nguồn, jack | - | $2.00 | $2.00 |
| Vỏ hộp | 3 | $1.00 | $3.00 |
| **Tổng** | | | **$14.00** |

**TỔNG CHI PHÍ:** $37.50 + $7.00 + $8.00 + $14.00 = **$66.50**

*Lưu ý: Giá có thể thay đổi tùy theo nhà cung cấp và thời điểm mua*

### 10.4. Công cụ và phần mềm cần thiết

**A. Cho STM32:**
- **IDE:** Keil MDK-ARM v5+ (hoặc STM32CubeIDE - miễn phí)
- **Programmer:** ST-Link V2
- **Driver:** ST-Link USB Driver
- **Utility:** STM32CubeMX (tạo code khởi tạo)
- **Terminal:** PuTTY, Tera Term (debug UART)

**B. Cho ESP32:**
- **Framework:** ESP-IDF v5.5.1+
- **Python:** 3.7+
- **Git:** Để clone ESP-IDF
- **Terminal:** CMD, PowerShell, hoặc Git Bash
- **Serial Monitor:** idf.py monitor, PuTTY

**C. Công cụ khác:**
- **I2C Scanner:** Để tìm địa chỉ LCD
- **Logic Analyzer:** Để debug giao tiếp (optional)
- **Multimeter:** Đo điện áp, dòng điện
- **Oscilloscope:** Debug tín hiệu (optional)

### 10.5. Tài liệu tham khảo

**A. Datasheet:**
- [STM32F103C6 Datasheet](https://www.st.com/resource/en/datasheet/stm32f103c6.pdf)
- [ESP32 Datasheet](https://www.espressif.com/sites/default/files/documentation/esp32_datasheet_en.pdf)
- [OV2640 Camera Datasheet](https://www.uctronics.com/download/cam_module/OV2640DS.pdf)
- [HD44780 LCD Controller](https://www.sparkfun.com/datasheets/LCD/HD44780.pdf)
- [PCF8574 I2C Expander](https://www.ti.com/lit/ds/symlink/pcf8574.pdf)
- [SX1278 LoRa Module](https://www.semtech.com/products/wireless-rf/lora-core/sx1278)

**B. Thư viện:**
- [STM32 HAL Library](https://www.st.com/en/embedded-software/stm32cube-mcu-mpu-packages.html)
- [ESP32 Camera Driver](https://github.com/espressif/esp32-camera)
- [ESP-IDF Documentation](https://docs.espressif.com/projects/esp-idf/en/latest/)

**C. Tutorial:**
- [STM32 HAL Tutorial](https://controllerstech.com/stm32-tutorials/)
- [ESP32-CAM Tutorial](https://randomnerdtutorials.com/esp32-cam-video-streaming-web-server-camera-home-assistant/)
- [LoRa Tutorial](https://www.instructables.com/Long-Range-18KM-Arduino-to-Arduino-LoRa-Communica/)

**D. Forum và cộng đồng:**
- [STM32 Community](https://community.st.com/)
- [ESP32 Forum](https://www.esp32.com/)
- [Arduino Forum](https://forum.arduino.cc/)
- [Stack Overflow](https://stackoverflow.com/)

### 10.6. Lịch sử phiên bản

**Version 1.0.0 (2025-01-XX):**
- Phiên bản đầu tiên
- Chức năng cơ bản: Phát hiện xâm nhập, báo động, truyền LoRa, gửi SMS, camera streaming
- Hỗ trợ 2 khu vực giám sát

**Tính năng dự kiến (Future versions):**
- [ ] Thêm checksum và ACK cho LoRa
- [ ] Lưu log vào EEPROM/SD card
- [ ] Tự động tắt buzzer sau timeout
- [ ] Ghi video khi có cảnh báo
- [ ] Nhận diện khuôn mặt (AI)
- [ ] App mobile (Android/iOS)
- [ ] Kết nối cloud (AWS, Firebase)
- [ ] Dashboard web (Node-RED)
- [ ] Notification qua Telegram
- [ ] Chế độ tiết kiệm năng lượng

### 10.7. Giấy phép và tác giả

**Giấy phép:**
- Code STM32: Copyright © 2025 STMicroelectronics. All rights reserved.
- Code ESP32: MIT License
- Delay Library: Ceres_Li
- I2C LCD Driver: Khaled Magdy (www.DeepBlueMbedded.com)

**Tác giả dự án:**
- Main Application: [Tên của bạn]
- Tích hợp hệ thống: [Tên của bạn]
- Tài liệu: [Tên của bạn]

**Đóng góp:**
Mọi đóng góp, báo lỗi, và đề xuất cải tiến đều được hoan nghênh.

**Liên hệ:**
- Email: [Email của bạn]
- GitHub: [GitHub của bạn]

---

## KẾT THÚC BÁO CÁO

**Ngày hoàn thành:** 12/12/2025  
**Tổng số trang:** [Tự động tính]  
**Tổng số dòng code:** ~2000+ dòng  
**Thời gian phát triển:** [Thời gian của bạn]  

**Cảm ơn đã đọc báo cáo này!**

Nếu có thắc mắc hoặc cần hỗ trợ, vui lòng liên hệ qua email hoặc tạo issue trên GitHub repository.

---

**PHỤ LỤC CUỐI:**

### Checklist triển khai hệ thống:

- [ ] Mua đủ linh kiện
- [ ] Cài đặt phần mềm (Keil, ESP-IDF)
- [ ] Hàn mạch và kết nối phần cứng
- [ ] Nạp code cho CodeTram1
- [ ] Nạp code cho CodeTram2
- [ ] Nạp code cho CodeTrungTam
- [ ] Nạp code cho ESP32-CAM
- [ ] Kiểm tra LoRa giữa CodeTram1 và CodeTrungTam
- [ ] Kiểm tra LoRa giữa CodeTram2 và CodeTrungTam
- [ ] Kiểm tra GSM gửi SMS
- [ ] Kiểm tra LCD hiển thị
- [ ] Kiểm tra camera streaming
- [ ] Test toàn bộ hệ thống
- [ ] Lắp đặt tại vị trí thực tế
- [ ] Kiểm tra khoảng cách LoRa
- [ ] Kiểm tra tín hiệu GSM
- [ ] Kiểm tra phạm vi WiFi camera
- [ ] Đào tạo người sử dụng
- [ ] Lập kế hoạch bảo trì

### Bảo trì định kỳ:

**Hàng tuần:**
- Kiểm tra hoạt động của cảm biến
- Kiểm tra buzzer và LED
- Kiểm tra LCD hiển thị

**Hàng tháng:**
- Kiểm tra pin/nguồn
- Kiểm tra kết nối LoRa
- Kiểm tra SIM card (tiền, tín hiệu)
- Vệ sinh camera

**Hàng quý:**
- Kiểm tra toàn bộ hệ thống
- Cập nhật firmware (nếu có)
- Sao lưu log (nếu có)
- Thay thế linh kiện hỏng

**Hàng năm:**
- Đánh giá hiệu quả hệ thống
- Nâng cấp phần cứng/phần mềm
- Mở rộng hệ thống (nếu cần)

---

**HẾT**

