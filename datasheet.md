# DATASHEET
# HỆ THỐNG GIÁM SÁT AN NINH THÔNG MINH
## SMART SECURITY MONITORING SYSTEM

---

**Mã sản phẩm:** SSMS-2025-V1.0  
**Nhà sản xuất:** [Tên công ty/Trường]  
**Ngày phát hành:** 21/12/2025  
**Phiên bản:** 1.0.0  
**Trạng thái:** Production Ready  

---

## 1. MÔ TẢ CHUNG (GENERAL DESCRIPTION)

### 1.1. Tổng quan sản phẩm

Hệ thống giám sát an ninh thông minh tích hợp đa công nghệ IoT, bao gồm:
- **3x Module cảm biến không dây** (STM32F103C6 + LoRa)
- **1x Trạm điều khiển trung tâm** (STM32F103C6 + GSM + LCD)
- **1x Camera giám sát** (ESP32-CAM + OV2640)
- **1x Hệ thống AI nhận diện** (Python Flask + OpenCV)

### 1.2. Tính năng chính

✓ Giám sát đa khu vực (mở rộng được)  
✓ Truyền thông không dây LoRa (1-5km)  
✓ Cảnh báo đa kênh (LED, Buzzer, SMS, Email)  
✓ Streaming video real-time (MJPEG)  
✓ Nhận diện khuôn mặt AI (LBPH)  
✓ Quản lý người dùng web-based  
✓ Giao diện LCD 16x2 hiển thị trạng thái  

### 1.3. Ứng dụng

- Giám sát an ninh nhà riêng
- Hệ thống báo động kho bãi
- Kiểm soát ra vào văn phòng
- Giám sát trang trại/chuồng trại
- Dự án nghiên cứu IoT/AI

---

## 2. SƠ ĐỒ KHỐI HỆ THỐNG (BLOCK DIAGRAM)

```
┌─────────────────────────────────────────────────────────────┐
│                    SYSTEM ARCHITECTURE                       │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐         LoRa          ┌──────────────┐
│   SENSOR     │      9600 baud        │   CENTRAL    │
│   MODULE 1   ├──────────────────────►│   STATION    │
│ STM32F103C6  │◄──────────────────────┤ STM32F103C6  │
└──────────────┘                       │   + GSM      │
                                       │   + LCD      │
┌──────────────┐         LoRa          └──────┬───────┘
│   SENSOR     │      9600 baud               │
│   MODULE 2   ├──────────────────────►       │ GSM
│ STM32F103C6  │◄──────────────────────┤      │ 115200
└──────────────┘                       │      │
                                       │      ▼
┌──────────────┐         WiFi          │  ┌────────┐
│  ESP32-CAM   │      192.168.4.1      │  │  SMS   │
│   + OV2640   ├───────────┐           │  │ Alert  │
└──────────────┘           │           │  └────────┘
                           │           │
                           ▼           ▼
                    ┌──────────────────────┐
                    │   AI FACE RECOG      │
                    │   Flask + OpenCV     │
                    │   Port 5000          │
                    └──────────────────────┘
```

---

## 3. THÔNG SỐ KỸ THUẬT TUYỆT ĐỐI (ABSOLUTE MAXIMUM RATINGS)

### 3.1. Module STM32F103C6

| Thông số | Ký hiệu | Min | Typ | Max | Đơn vị | Ghi chú |
|----------|---------|-----|-----|-----|--------|---------|
| Điện áp nguồn | VDD | 2.0 | 3.3 | 3.6 | V | Logic supply |
| Điện áp I/O | VIO | -0.3 | - | VDD+0.3 | V | GPIO pins |
| Dòng GPIO | IGPIO | - | - | 25 | mA | Per pin |
| Nhiệt độ hoạt động | TOP | -40 | 25 | 85 | °C | Industrial |
| Tần số CPU | FCPU | 0 | 8 | 72 | MHz | Configurable |

**⚠️ CẢNH BÁO:** Vượt quá giá trị tuyệt đối có thể gây hỏng vĩnh viễn linh kiện.

### 3.2. Module ESP32-CAM

| Thông số | Ký hiệu | Min | Typ | Max | Đơn vị | Ghi chú |
|----------|---------|-----|-----|-----|--------|---------|
| Điện áp nguồn | VIN | 4.5 | 5.0 | 5.5 | V | USB power |
| Dòng tiêu thụ (idle) | IDD_IDLE | - | 50 | 100 | mA | WiFi off |
| Dòng tiêu thụ (streaming) | IDD_STREAM | 200 | 350 | 500 | mA | WiFi + Camera |
| Dòng đột biến | IDD_PEAK | - | - | 800 | mA | WiFi TX burst |
| Nhiệt độ hoạt động | TOP | -40 | 25 | 85 | °C | Industrial |

**⚠️ CẢNH BÁO:** Nguồn phải cung cấp tối thiểu 500mA. Nguồn yếu gây brownout reset.

### 3.3. Module GSM (SIM800L)

| Thông số | Ký hiệu | Min | Typ | Max | Đơn vị | Ghi chú |
|----------|---------|-----|-----|-----|--------|---------|
| Điện áp nguồn | VIN | 3.4 | 4.0 | 4.4 | V | Regulated |
| Dòng tiêu thụ (idle) | IDD_IDLE | - | 10 | 50 | mA | Registered |
| Dòng tiêu thụ (SMS) | IDD_SMS | 300 | 500 | 800 | mA | Transmitting |
| Dòng đột biến | IDD_PEAK | - | - | 2000 | mA | Call/GPRS |
| Nhiệt độ hoạt động | TOP | -30 | 25 | 80 | °C | Commercial |

**⚠️ CẢNH BÁO:** Dòng đột biến lên đến 2A. Phải dùng nguồn riêng với tụ lọc lớn (470-1000µF).

---

## 4. SƠ ĐỒ CHÂN (PINOUT DIAGRAM)

### 4.1. Module Cảm Biến (CodeTram1/2) - STM32F103C6

```
                    STM32F103C6
                  ┌─────────────┐
        SENSOR ──►│PB12      5V │◄── VIN (5V)
           LED ──►│PB14     GND │◄── GND
        BUZZER ──►│PC14     3V3 │
                  │             │
     LCD_SCL ────►│PB6      PA9 │──► UART1_TX (Debug)
     LCD_SDA ────►│PB7     PA10 │◄── UART1_RX (Debug)
                  │             │
    LoRa_TX  ────►│PA2      PA3 │◄── LoRa_RX
                  │             │
                  │         RST │◄── RESET
                  │        BOOT │◄── BOOT0
                  └─────────────┘
```

**Bảng chức năng chân:**

| Chân | Tên | Loại | Chức năng | Cấu hình | Ghi chú |
|------|-----|------|-----------|----------|---------|
| PB12 | SENSOR_IN | Input | Đầu vào cảm biến | No Pull | Active HIGH |
| PB14 | LED_OUT | Output | LED báo hiệu | Push-Pull | Active HIGH |
| PC14 | BUZZER_OUT | Output | Còi báo động | Push-Pull | Qua transistor |
| PB6 | I2C1_SCL | AF | Clock LCD I2C | Open-Drain | Pull-up 4.7kΩ |
| PB7 | I2C1_SDA | AF | Data LCD I2C | Open-Drain | Pull-up 4.7kΩ |
| PA2 | USART2_TX | AF | TX LoRa | Push-Pull | 9600 baud |
| PA3 | USART2_RX | AF | RX LoRa | Input | 9600 baud |
| PA9 | USART1_TX | AF | TX Debug | Push-Pull | 115200 baud |
| PA10 | USART1_RX | AF | RX Debug | Input | 115200 baud |

### 4.2. Trạm Trung Tâm (CodeTrungTam) - STM32F103C6

```
                    STM32F103C6
                  ┌─────────────┐
     BUTTON1 ────►│PB12      5V │◄── VIN (5V)
     BUTTON2 ────►│PB13     GND │◄── GND
      BUZZER ────►│PC14     3V3 │
                  │             │
     LCD_SCL ────►│PB6      PA9 │──► GSM_RX
     LCD_SDA ────►│PB7     PA10 │◄── GSM_TX
                  │             │
    LoRa_TX  ────►│PA2      PA3 │◄── LoRa_RX
                  │             │
                  │         RST │◄── RESET
                  │        BOOT │◄── BOOT0
                  └─────────────┘
```

**Bảng chức năng chân:**

| Chân | Tên | Loại | Chức năng | Cấu hình | Ghi chú |
|------|-----|------|-----------|----------|---------|
| PB12 | BTN_KV1 | Input | Nút tắt KV1 | Pull-up | Active LOW |
| PB13 | BTN_KV2 | Input | Nút tắt KV2 | Pull-up | Active LOW |
| PC14 | BUZZER_OUT | Output | Còi báo động | Push-Pull | Qua transistor |
| PB6 | I2C1_SCL | AF | Clock LCD | Open-Drain | Pull-up 4.7kΩ |
| PB7 | I2C1_SDA | AF | Data LCD | Open-Drain | Pull-up 4.7kΩ |
| PA2 | USART2_TX | AF | TX LoRa | Push-Pull | 9600 baud |
| PA3 | USART2_RX | AF | RX LoRa | Input | 9600 baud |
| PA9 | USART1_TX | AF | TX GSM | Push-Pull | 115200 baud |
| PA10 | USART1_RX | AF | RX GSM | Input | 115200 baud |


### 4.3. Camera ESP32-CAM (AI-Thinker) - ESP32 + OV2640

```
                    ESP32-CAM
                  ┌─────────────┐
          5V ────►│VIN      GND │◄── GND
         GND ────►│GND      IO0 │◄── BOOT (GND khi flash)
                  │             │
    CAM_XCLK ────►│IO0      IO2 │──► LED Flash
    CAM_SIOD ────►│IO26     IO4 │──► LED Status
    CAM_SIOC ────►│IO27    IO12 │
                  │             │
      CAM_D0 ────►│IO5     IO13 │
      CAM_D1 ────►│IO18    IO15 │
      CAM_D2 ────►│IO19    IO14 │
      CAM_D3 ────►│IO21    IO16 │
      CAM_D4 ────►│IO36     RST │◄── RESET
      CAM_D5 ────►│IO39   U0TXD │──► Serial TX
      CAM_D6 ────►│IO34   U0RXD │◄── Serial RX
      CAM_D7 ────►│IO35         │
                  │             │
   CAM_VSYNC ────►│IO25    IO22 │──► CAM_PCLK
    CAM_HREF ────►│IO23    IO32 │──► CAM_PWDN
                  └─────────────┘
```

**Bảng chức năng chân Camera:**

| Chân ESP32 | Tên Camera | Chức năng | Tốc độ | Ghi chú |
|------------|------------|-----------|--------|---------|
| IO0 | XCLK | Master Clock | 20MHz | Cấp clock cho camera |
| IO26 | SIOD | I2C Data | 100kHz | Cấu hình camera (SCCB) |
| IO27 | SIOC | I2C Clock | 100kHz | Cấu hình camera (SCCB) |
| IO5 | D0 | Data bit 0 | - | 8-bit parallel data |
| IO18 | D1 | Data bit 1 | - | 8-bit parallel data |
| IO19 | D2 | Data bit 2 | - | 8-bit parallel data |
| IO21 | D3 | Data bit 3 | - | 8-bit parallel data |
| IO36 | D4 | Data bit 4 | - | 8-bit parallel data |
| IO39 | D5 | Data bit 5 | - | 8-bit parallel data |
| IO34 | D6 | Data bit 6 | - | 8-bit parallel data |
| IO35 | D7 | Data bit 7 | - | 8-bit parallel data |
| IO25 | VSYNC | Vertical Sync | - | Báo frame mới |
| IO23 | HREF | Horizontal Ref | - | Báo dòng hợp lệ |
| IO22 | PCLK | Pixel Clock | - | Đồng bộ đọc data |
| IO32 | PWDN | Power Down | - | Tắt camera (Active HIGH) |

---

## 5. ĐẶC TÍNH ĐIỆN (ELECTRICAL CHARACTERISTICS)

### 5.1. Nguồn cấp hệ thống

| Module | Điện áp | Dòng Idle | Dòng Active | Dòng Peak | Nguồn khuyến nghị |
|--------|---------|-----------|-------------|-----------|-------------------|
| STM32 Module | 5V | 50mA | 100mA | 150mA | 5V/500mA |
| ESP32-CAM | 5V | 100mA | 350mA | 800mA | 5V/1A |
| GSM Module | 5V | 50mA | 500mA | 2000mA | 5V/2A (riêng) |
| **Tổng hệ thống** | **5V** | **300mA** | **1.5A** | **3A** | **5V/3A** |

**Lưu ý:** Module GSM cần nguồn riêng với tụ lọc 1000µF gần chân nguồn.

### 5.2. Mức logic I/O

**STM32F103C6:**
| Thông số | Ký hiệu | Min | Typ | Max | Đơn vị |
|----------|---------|-----|-----|-----|--------|
| Điện áp logic HIGH input | VIH | 2.0 | - | VDD | V |
| Điện áp logic LOW input | VIL | VSS | - | 0.8 | V |
| Điện áp logic HIGH output | VOH | 2.4 | 3.0 | - | V |
| Điện áp logic LOW output | VOL | - | 0.4 | 0.4 | V |
| Dòng source/sink | IOL/IOH | - | - | 25 | mA |

**ESP32:**
| Thông số | Ký hiệu | Min | Typ | Max | Đơn vị |
|----------|---------|-----|-----|-----|--------|
| Điện áp logic HIGH input | VIH | 2.0 | - | 3.6 | V |
| Điện áp logic LOW input | VIL | -0.3 | - | 0.8 | V |
| Điện áp logic HIGH output | VOH | 2.4 | 3.0 | - | V |
| Điện áp logic LOW output | VOL | - | 0.1 | 0.4 | V |
| Dòng source/sink | IOL/IOH | - | - | 40 | mA |

### 5.3. Thông số UART

**LoRa Communication (UART2):**
| Thông số | Giá trị | Đơn vị | Ghi chú |
|----------|---------|--------|---------|
| Baudrate | 9600 | bps | Fixed |
| Data bits | 8 | bit | - |
| Parity | None | - | - |
| Stop bits | 1 | bit | - |
| Flow control | None | - | - |
| Timeout RX | 10 | ms | Configurable |

**GSM Communication (UART1):**
| Thông số | Giá trị | Đơn vị | Ghi chú |
|----------|---------|--------|---------|
| Baudrate | 115200 | bps | AT commands |
| Data bits | 8 | bit | - |
| Parity | None | - | - |
| Stop bits | 1 | bit | - |
| Flow control | None | - | - |
| Timeout RX | 2000 | ms | AT response |

### 5.4. Thông số I2C (LCD)

| Thông số | Ký hiệu | Min | Typ | Max | Đơn vị |
|----------|---------|-----|-----|-----|--------|
| Clock frequency | fSCL | 10 | 100 | 400 | kHz |
| Địa chỉ LCD | ADDR | - | 0x27 | 0x3F | hex |
| Pull-up resistor | RPU | 2.2 | 4.7 | 10 | kΩ |
| Setup time | tSU | 250 | - | - | ns |
| Hold time | tHD | 0 | - | - | ns |

---

## 6. GIAO THỨC TRUYỀN THÔNG (COMMUNICATION PROTOCOLS)

### 6.1. Giao thức LoRa

**Thông số RF:**
| Thông số | Giá trị | Đơn vị | Ghi chú |
|----------|---------|--------|---------|
| Tần số | 433 / 868 / 915 | MHz | Tùy khu vực |
| Công suất TX | 20 | dBm | 100mW |
| Độ nhạy RX | -148 | dBm | SF12, BW125 |
| Khoảng cách | 1-5 | km | Line of sight |
| Bandwidth | 125 | kHz | Configurable |
| Spreading Factor | 7-12 | - | Configurable |
| Coding Rate | 4/5 | - | Error correction |

**Bảng mã lệnh:**

| Mã lệnh | Hex | Binary | Nguồn | Đích | Chức năng |
|---------|-----|--------|-------|------|-----------|
| CMDACTIVE1 | 0xA1 | 10100001 | Tram1 | TrungTam | KV1 phát hiện |
| CMDINACTIVE1 | 0xA2 | 10100010 | Tram1 | TrungTam | KV1 an toàn |
| CMDACTIVE2 | 0xB1 | 10110001 | Tram2 | TrungTam | KV2 phát hiện |
| CMDINACTIVE2 | 0xB2 | 10110010 | Tram2 | TrungTam | KV2 an toàn |
| CMDOFFKV1 | 0xC1 | 11000001 | TrungTam | Tram1 | Tắt buzzer KV1 |
| CMDOFFKV2 | 0xC2 | 11000010 | TrungTam | Tram2 | Tắt buzzer KV2 |

**Format gói tin:** 1 byte đơn (không header, không checksum)

### 6.2. Giao thức GSM/SMS

**AT Commands sử dụng:**

| Lệnh | Chức năng | Response | Timeout |
|------|-----------|----------|---------|
| AT | Test connection | OK | 1s |
| ATE0 | Disable echo | OK | 1s |
| AT+CMGF=1 | SMS text mode | OK | 1s |
| AT+CNMI=2,2,0,0 | No save SMS | OK | 1s |
| AT+CREG? | Check network | +CREG: 0,1 | 2s |
| AT+CMGS="phone" | Send SMS | > | 2s |
| Ctrl+Z (0x1A) | End SMS | +CMGS: xxx | 5s |

**SMS Content:**
- SMS1: "Canh bao dot nhap khu vuc 1" (30 ký tự)
- SMS2: "Canh bao dot nhap khu vuc 2" (30 ký tự)
- SMS3: "HT GIAM SAT SAN SANG" (21 ký tự)

**Chi phí:** ~500đ/SMS (Viettel/Vinaphone/Mobifone)

### 6.3. Giao thức WiFi (ESP32-CAM)

**Access Point Mode:**
| Thông số | Giá trị | Ghi chú |
|----------|---------|---------|
| SSID | ESP32_CAM_AP | Configurable |
| Password | 12345678 | Min 8 chars |
| Security | WPA2-PSK | - |
| IP Address | 192.168.4.1 | Fixed |
| Subnet Mask | 255.255.255.0 | - |
| Gateway | 192.168.4.1 | - |
| DHCP Range | 192.168.4.2-254 | - |
| Max Clients | 4 | Configurable |
| Channel | 1 | Auto |
| Bandwidth | 20MHz | 802.11n |

### 6.4. Giao thức HTTP (MJPEG Streaming)

**HTTP Request:**
```
GET / HTTP/1.1
Host: 192.168.4.1
User-Agent: Mozilla/5.0
Accept: text/html,image/jpeg
Connection: keep-alive
```

**HTTP Response:**
```
HTTP/1.1 200 OK
Content-Type: multipart/x-mixed-replace;boundary=123456789000000000000987654321
Cache-Control: no-cache
Connection: close

--123456789000000000000987654321
Content-Type: image/jpeg
Content-Length: 15234

[JPEG Binary Data]
--123456789000000000000987654321
...
```

**Performance:**
| Thông số | VGA (640x480) | QVGA (320x240) | Đơn vị |
|----------|---------------|----------------|--------|
| FPS | 15-20 | 25-30 | fps |
| Frame Size | 15-30 | 8-15 | KB |
| Bandwidth | 300-600 | 200-450 | KB/s |
| Latency | 50-100 | 30-60 | ms |
| JPEG Quality | 10 | 10 | 0-63 |

---

## 7. BIỂU ĐỒ THỜI GIAN (TIMING DIAGRAMS)

### 7.1. Timing LoRa Communication

```
Transmitter (CodeTram1):
         ┌─────┐
SENSOR ──┘     └────────────────────
         
         ┌──────────────────────┐
LED    ──┘                      └───
         
         ┌──────────────────────┐
BUZZER ──┘                      └───
         
TX(LoRa) ────┐ 0xA1 ┌─────────────
             └───────┘
         
         ├─500ms─┤
         (debounce)

Receiver (CodeTrungTam):
         
RX(LoRa) ────┐ 0xA1 ┌─────────────
             └───────┘
         
         ┌──────────────────────┐
BUZZER ──┘                      └───
         
LCD      ────┤ "CB KV1" ├──────────
         
GSM_TX   ────┤ AT+CMGS ├──────────
         
         ├─10ms─┤
         (process)
```

### 7.2. Timing I2C LCD Communication

```
SCL  ────┐   ┌───┐   ┌───┐   ┌───┐   ┌───┐   ┌───┐   ┌───┐   ┌───┐   ┌───┐
         └───┘   └───┘   └───┘   └───┘   └───┘   └───┘   └───┘   └───┘
         
SDA  ──┐ S ├─A6─┤─A5─┤─A4─┤─A3─┤─A2─┤─A1─┤─A0─┤─R/W┤─ACK┤─D7─┤...
       └───┘   └───┘   └───┘   └───┘   └───┘   └───┘   └───┘   └───┘
       
       ├─────────────────────────────────────────────────────────┤
                        ~100 kHz (10µs per bit)
       
       S = Start condition
       A6-A0 = Address (0x27 = 0100111)
       R/W = Read(1) / Write(0)
       ACK = Acknowledge
       D7-D0 = Data byte
```

### 7.3. Timing Camera DVP Interface

```
XCLK  ──┐   ┌───┐   ┌───┐   ┌───┐   ┌───┐   ┌───┐   ┌───┐   ┌───┐
        └───┘   └───┘   └───┘   └───┘   └───┘   └───┘   └───┘
        20MHz (50ns period)

VSYNC ──┐                                                       ┌───
        └───────────────────────────────────────────────────────┘
        ├───────────────── Frame period ─────────────────────────┤
        
HREF  ────┐       ┌───┐       ┌───┐       ┌───┐       ┌───────────
          └───────┘   └───────┘   └───────┘   └───────┘
          ├─ Line ─┤   ├─ Line ─┤   ├─ Line ─┤
          
PCLK  ──┐   ┌───┐   ┌───┐   ┌───┐   ┌───┐   ┌───┐   ┌───┐   ┌───
        └───┘   └───┘   └───┘   └───┘   └───┘   └───┘   └───┘
        
D[7:0]  ──┤ P0 ├───┤ P1 ├───┤ P2 ├───┤ P3 ├───┤ P4 ├───┤ P5 ├───
          └────┘   └────┘   └────┘   └────┘   └────┘   └────┘
          
VGA 640x480: ~33ms per frame (30fps)
```


---

## 8. BIỂU ĐỒ HIỆU NĂNG (PERFORMANCE CHARACTERISTICS)

### 8.1. Đồ thị FPS vs Resolution (ESP32-CAM)

```
FPS
 │
30├─────────────────────────────────────────────────────────
  │                                    ●
25├────────────────────────────────●
  │                            ●
20├────────────────────────●
  │                    ●
15├────────────────●
  │            ●
10├────────●
  │    ●
 5├●
  │
 0└────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬──► Resolution
     QQVGA QVGA CIF  VGA SVGA XGA SXGA HD UXGA
     160x  320x 352x 640x 800x 1024 1280 1280 1600
     120   240  288  480  600  x768 x1024 x720 x1200

● = Measured FPS (JPEG Quality 10)
```

### 8.2. Đồ thị Dòng tiêu thụ vs Trạng thái (ESP32-CAM)

```
Current (mA)
 │
800├─────────────────────────────────────────────────────────
   │                                              ▲
   │                                              │ Peak
600├──────────────────────────────────────────────┼─────────
   │                                    ┌─────────┴─────┐
   │                                    │  WiFi TX      │
400├────────────────────────────────────┤  Streaming    ├───
   │                          ┌─────────┴───────────────┘
   │                          │  Camera Active
200├──────────────────────────┤  WiFi Connected
   │                ┌─────────┴─────┐
   │                │  WiFi Idle    │
100├────────────────┴───────────────┘
   │      ┌─────┐
   │      │Sleep│
 50├──────┴─────┘
   │
  0└──────┬──────┬──────┬──────┬──────┬──────┬──────┬──► Time
       Sleep  WiFi  Camera Stream Peak
              Init  Init   Active Burst
```

### 8.3. Đồ thị Khoảng cách vs RSSI (LoRa)

```
RSSI (dBm)
 │
-40├─────────────────────────────────────────────────────────
   │●
   │ ●
-60├─  ●
   │    ●
   │     ●
-80├─      ●
   │        ●
   │         ●
-100├─        ●
    │          ●
    │           ●
-120├─           ●
    │             ●
    │              ●
-140├─              ●
    │                ●
    │                 ●
-160└────┬────┬────┬────┬────┬────┬────┬────┬────┬──► Distance (km)
        0.1  0.5  1.0  1.5  2.0  2.5  3.0  3.5  4.0  5.0

● = Measured RSSI (SF7, BW125, Outdoor)
Minimum sensitivity: -148dBm (SF12)
```

### 8.4. Bảng hiệu năng AI Face Recognition

| Metric | Value | Unit | Condition |
|--------|-------|------|-----------|
| Training Time | 2-5 | s | 30 images/person |
| Recognition Time | 30-50 | ms | Per face |
| Detection Rate | 95-98 | % | Good lighting |
| False Positive | 2-5 | % | Confidence < 60 |
| False Negative | 3-7 | % | Poor lighting |
| Max Faces/Frame | 10 | faces | Performance degrades |
| Processing FPS | 25-30 | fps | Laptop camera |
| Processing FPS | 15-20 | fps | ESP32-CAM |
| Model Size | 50-200 | KB | Depends on users |
| RAM Usage | 200-500 | MB | Python process |

---

## 9. MẠCH ỨNG DỤNG ĐIỂN HÌNH (TYPICAL APPLICATION CIRCUITS)

### 9.1. Mạch Module Cảm Biến

```
                    +5V
                     │
                     ├──────────┐
                     │          │
                    ┌┴┐        ┌┴┐
                    │ │ 10kΩ   │ │ 4.7kΩ (Pull-up I2C)
                    └┬┘        └┬┘
                     │          │
    PIR Sensor       │          ├─────── I2C_SCL (PB6)
    ┌─────────┐      │          │
    │   VCC   ├──────┤          ├─────── I2C_SDA (PB7)
    │   OUT   ├──────┼─────── PB12 (Sensor Input)
    │   GND   ├──┐   │
    └─────────┘  │   │
                 │   │      STM32F103C6
                GND  │    ┌──────────────┐
                     │    │              │
                     ├────┤ VDD      PB14├───┬───[R330Ω]───[LED]───GND
                     │    │              │   │
                     │    │          PC14├───┼───[R1kΩ]───┐
                     │    │              │   │            │
                     │    │          PA2 ├───┼────────────┼─── LoRa_RX
                     │    │          PA3 ├───┼────────────┼─── LoRa_TX
                     │    │              │   │            │
                     └────┤ GND          │   │            │
                          └──────────────┘   │            │
                                             │            │
                                            ┌▼┐          ┌┴┐
                                         Q1 │ │ 2N2222   │ │ LoRa Module
                                            │E│          │ │ SX1278
                                            └┬┘          └─┘
                                             │
                                            GND
                                             │
                                        [Buzzer 5V]
                                             │
                                            GND

Lưu ý:
- Tụ lọc 100nF gần chân VDD của STM32
- Tụ lọc 10µF gần chân nguồn PIR
- Điện trở pull-up I2C: 4.7kΩ
- Transistor Q1: 2N2222 hoặc tương đương
```

### 9.2. Mạch Trạm Trung Tâm với GSM

```
                    +5V (3A minimum)
                     │
                     ├──────────┬──────────┬──────────┐
                     │          │          │          │
                    ┌┴┐        ┌┴┐        │         ┌┴┐
                    │ │ 10kΩ   │ │ 4.7kΩ  │         │ │ 1000µF
                    └┬┘        └┬┘         │         └┬┘
                     │          │          │          │
                     │          ├─────── I2C_SCL     ┌┴┐ 100nF
                     │          ├─────── I2C_SDA     └┬┘
                     │          │                     │
    Button KV1       │          │                     │
    ┌────────┐       │          │                     │
    │  SW1   ├───────┼─────── PB12                    │
    └────────┘       │          │                     │
                     │          │      STM32F103C6    │
    Button KV2       │          │    ┌──────────────┐ │
    ┌────────┐       │          │    │              │ │
    │  SW2   ├───────┼──────────┼────┤ VDD      PA9 ├─┼─── GSM_RX
    └────────┘       │          │    │          PA10├─┼─── GSM_TX
                     │          │    │              │ │
                     │          │    │          PA2 ├─┼─── LoRa_RX
                     │          │    │          PA3 ├─┼─── LoRa_TX
                     │          │    │              │ │
                     └──────────┴────┤ GND          │ │
                                     └──────────────┘ │
                                                      │
                                     GSM Module       │
                                     SIM800L          │
                                   ┌──────────────┐   │
                                   │ VCC      TX  ├───┘
                                   │ GND      RX  ├───┐
                                   │ RST      GND ├───┤
                                   └──────────────┘   │
                                                     GND

Lưu ý:
- Tụ 1000µF bắt buộc gần chân nguồn GSM
- Nguồn riêng cho GSM, dòng tối thiểu 2A
- Nút nhấn có điện trở pull-up 10kΩ
- Anten GSM phải kết nối đúng
```

### 9.3. Mạch Nguồn ESP32-CAM

```
                    USB 5V
                     │
                     ├──────────┐
                     │          │
                    ┌┴┐        ┌┴┐
                    │ │ 470µF  │ │ 100nF
                    └┬┘        └┬┘
                     │          │
                     ├──────────┼──────── VIN (ESP32-CAM)
                     │          │
                    ┌▼┐        ┌▼┐
                    │ │ 100µF  │ │ 10nF (Ceramic)
                    └┬┘        └┬┘
                     │          │
                    GND        GND

ESP32-CAM Module:
┌────────────────────────────────┐
│  ┌──────────────────────────┐  │
│  │      ESP32-WROOM-32      │  │
│  │                          │  │
│  └──────────────────────────┘  │
│                                 │
│  ┌──────────────────────────┐  │
│  │      OV2640 Camera       │  │
│  │      (Socket mount)      │  │
│  └──────────────────────────┘  │
│                                 │
│  VIN ○                          │
│  GND ○                          │
│  IO0 ○ (BOOT - GND khi flash)  │
│  RST ○                          │
│ U0TX ○ ──── USB-Serial RX       │
│ U0RX ○ ──── USB-Serial TX       │
└─────────────────────────────────┘

Lưu ý:
- Tụ lọc 470µF bắt buộc
- Nguồn tối thiểu 5V/500mA
- Không dùng nguồn USB máy tính (yếu)
- IO0 nối GND khi nạp code, ngắt khi chạy
```

---

## 10. THÔNG TIN ĐÓI GÓI VÀ KÍCH THƯỚC (PACKAGE INFORMATION)

### 10.1. Kích thước Module STM32F103C6

```
STM32F103C6 Development Board
┌─────────────────────────────────────┐
│  ○                             ○    │
│                                     │ 53mm
│  ┌───────────────────────────┐     │
│  │   STM32F103C6 (LQFP48)    │     │
│  │   ARM Cortex-M3           │     │
│  └───────────────────────────┘     │
│                                     │
│  [USB]  [RESET] [BOOT0] [BOOT1]    │
│                                     │
│  ○                             ○    │
└─────────────────────────────────────┘
              72mm

Trọng lượng: ~10g
Vật liệu: PCB FR4, 1.6mm
```

### 10.2. Kích thước ESP32-CAM

```
ESP32-CAM Module (AI-Thinker)
┌─────────────────────────────┐
│  ┌───────────────────────┐  │
│  │   ESP32-WROOM-32      │  │ 40mm
│  └───────────────────────┘  │
│                              │
│  ┌───────────────────────┐  │
│  │   OV2640 Camera       │  │
│  │   [Lens]              │  │
│  └───────────────────────┘  │
│                              │
│  [Pins 16x2]                 │
└──────────────────────────────┘
            27mm

Trọng lượng: ~8g (không camera)
Trọng lượng: ~12g (có camera)
Vật liệu: PCB FR4, 1.0mm
```

### 10.3. Kích thước LCD I2C 16x2

```
LCD 16x2 with I2C Backpack
┌─────────────────────────────────────┐
│ ┌─────────────────────────────────┐ │
│ │  ████████████████████████████   │ │ 36mm
│ │  ████████████████████████████   │ │
│ └─────────────────────────────────┘ │
│                                     │
│  [I2C Module]  [Contrast Pot]       │
│  GND VCC SDA SCL                    │
└─────────────────────────────────────┘
              80mm

Trọng lượng: ~35g
Điện áp: 5V
Dòng: 50-100mA (backlight on)
```

---

## 11. ĐIỀU KIỆN VẬN HÀNH VÀ BẢO QUẢN (OPERATING CONDITIONS)

### 11.1. Điều kiện môi trường

| Thông số | Min | Typ | Max | Đơn vị | Ghi chú |
|----------|-----|-----|-----|--------|---------|
| Nhiệt độ hoạt động | -10 | 25 | 60 | °C | Indoor use |
| Nhiệt độ bảo quản | -20 | 25 | 70 | °C | - |
| Độ ẩm hoạt động | 10 | 50 | 85 | %RH | Non-condensing |
| Độ ẩm bảo quản | 5 | 50 | 95 | %RH | Non-condensing |
| Độ cao | 0 | - | 2000 | m | Above sea level |

**⚠️ CẢNH BÁO:**
- Không sử dụng trong môi trường ẩm ướt
- Tránh ánh nắng trực tiếp lên camera
- Không để gần nguồn nhiệt (>60°C)
- Tránh bụi và hơi ăn mòn

### 11.2. Yêu cầu nguồn điện

| Module | Điện áp | Dòng | Nguồn khuyến nghị | Ghi chú |
|--------|---------|------|-------------------|---------|
| STM32 Module | 5V ±5% | 100-150mA | 5V/500mA | Adapter hoặc USB |
| ESP32-CAM | 5V ±5% | 350-800mA | 5V/1A | Adapter (không dùng USB PC) |
| GSM Module | 5V ±5% | 500-2000mA | 5V/2A | Adapter riêng + tụ lọc |
| **Tổng hệ thống** | **5V** | **1-3A** | **5V/3A** | **Adapter chất lượng tốt** |

**Khuyến nghị:**
- Dùng adapter 5V/3A chất lượng tốt (có chứng nhận)
- Tụ lọc 1000µF gần chân nguồn GSM
- Tụ lọc 100nF gần chân VDD của mỗi IC
- Dây nguồn ngắn, tiết diện đủ lớn (≥0.5mm²)

### 11.3. Yêu cầu lắp đặt

**Khoảng cách:**
- LoRa: 1-5km (line of sight, outdoor)
- WiFi: 50-100m (indoor, tùy vật cản)
- GSM: Phụ thuộc vùng phủ sóng

**Vị trí:**
- Module cảm biến: Gắn tại vị trí cần giám sát
- Trạm trung tâm: Vị trí dễ quan sát LCD
- ESP32-CAM: Góc nhìn rộng, ánh sáng đủ
- Anten LoRa: Thẳng đứng, không bị che

---

## 12. HƯỚNG DẪN SỬ DỤNG AN TOÀN (SAFETY INSTRUCTIONS)

### 12.1. Cảnh báo an toàn

⚠️ **NGUY HIỂM - ĐIỆN ÁP:**
- Luôn ngắt nguồn trước khi lắp đặt/sửa chữa
- Không chạm vào mạch khi đang cấp nguồn
- Sử dụng nguồn có chứng nhận an toàn

⚠️ **CẢNH BÁO - NHIỆT ĐỘ:**
- Module GSM có thể nóng (>50°C) khi hoạt động
- ESP32-CAM có thể nóng (>45°C) khi streaming
- Đảm bảo thông gió tốt

⚠️ **CHÚ Ý - TĨNH ĐIỆN:**
- Chạm vào vật dẫn điện trước khi cầm module
- Sử dụng vòng đeo tay chống tĩnh điện
- Bảo quản trong túi chống tĩnh điện

### 12.2. Bảo trì định kỳ

**Hàng tuần:**
- Kiểm tra hoạt động của cảm biến
- Kiểm tra LED và Buzzer
- Kiểm tra LCD hiển thị

**Hàng tháng:**
- Kiểm tra nguồn điện
- Kiểm tra kết nối LoRa
- Kiểm tra SIM card (tiền, tín hiệu)
- Vệ sinh camera (lau ống kính)

**Hàng quý:**
- Kiểm tra toàn bộ hệ thống
- Cập nhật firmware (nếu có)
- Thay thế linh kiện hỏng

---

## 13. THÔNG TIN ĐẶT HÀNG (ORDERING INFORMATION)

### 13.1. Mã sản phẩm

| Mã sản phẩm | Mô tả | Bao gồm |
|-------------|-------|---------|
| SSMS-FULL-KIT | Bộ đầy đủ | 3x STM32 Module, 1x GSM, 1x ESP32-CAM, Nguồn, Dây |
| SSMS-STM32-MOD | Module STM32 | STM32F103C6, LoRa, LCD, Cảm biến, LED, Buzzer |
| SSMS-CENTRAL | Trạm trung tâm | STM32F103C6, LoRa, LCD, GSM, Nút nhấn |
| SSMS-CAM | Camera module | ESP32-CAM, OV2640, USB-Serial |
| SSMS-AI-SW | Phần mềm AI | Python source code, Documentation |

### 13.2. Phụ kiện tùy chọn

| Mã phụ kiện | Mô tả | Giá (USD) |
|-------------|-------|-----------|
| SSMS-PSU-3A | Nguồn 5V/3A | $5.00 |
| SSMS-ANT-LORA | Anten LoRa 433MHz | $3.00 |
| SSMS-ANT-GSM | Anten GSM | $2.00 |
| SSMS-CASE | Vỏ hộp nhựa | $3.00 |
| SSMS-CABLE | Bộ dây kết nối | $2.00 |

---

## 14. HỖ TRỢ KỸ THUẬT (TECHNICAL SUPPORT)

### 14.1. Thông tin liên hệ

**Email:** support@example.com  
**Website:** www.example.com/ssms  
**Forum:** forum.example.com  
**GitHub:** github.com/example/ssms  

### 14.2. Tài liệu tham khảo

- User Manual: SSMS-UM-001
- Quick Start Guide: SSMS-QSG-001
- Application Notes: SSMS-AN-xxx
- Firmware Update Guide: SSMS-FUG-001

### 14.3. Bảo hành

- Thời gian bảo hành: 12 tháng
- Điều kiện: Lỗi do nhà sản xuất
- Không bảo hành: Hỏng do người dùng, thiên tai

---

## 15. THÔNG TIN PHÁP LÝ (LEGAL INFORMATION)

### 15.1. Chứng nhận

- CE: Đạt chuẩn EU (nếu xuất khẩu)
- FCC: Đạt chuẩn US (nếu xuất khẩu)
- RoHS: Không chứa chất độc hại

### 15.2. Giấy phép phần mềm

- STM32 HAL: © STMicroelectronics
- ESP-IDF: Apache License 2.0
- OpenCV: Apache License 2.0
- Flask: BSD License
- Application Code: MIT License

### 15.3. Tuyên bố từ chối trách nhiệm

Sản phẩm này được cung cấp "nguyên trạng" không có bảo đảm nào. Nhà sản xuất không chịu trách nhiệm về thiệt hại trực tiếp hoặc gián tiếp phát sinh từ việc sử dụng sản phẩm.

---

## 16. LỊCH SỬ PHIÊN BẢN (REVISION HISTORY)

| Phiên bản | Ngày | Thay đổi | Người thực hiện |
|-----------|------|----------|-----------------|
| 1.0.0 | 21/12/2025 | Phát hành ban đầu | [Tên] |
| - | - | - | - |

---

**KẾT THÚC DATASHEET**

© 2025 [Tên công ty/Trường]. All rights reserved.

Tài liệu này có thể thay đổi mà không cần thông báo trước.
Vui lòng kiểm tra phiên bản mới nhất tại website.

