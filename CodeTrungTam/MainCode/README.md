# HỆ THỐNG GIÁM SÁT AN NINH - STM32F103

## TỔNG QUAN DỰ ÁN

Đây là hệ thống giám sát an ninh sử dụng vi điều khiển STM32F103C6, tích hợp:
- **Module GSM/SIM**: Gửi SMS cảnh báo qua UART1 (115200 baud)
- **Module LoRa**: Nhận tín hiệu từ các cảm biến từ xa qua UART2 (9600 baud)
- **LCD I2C 16x2**: Hiển thị trạng thái hệ thống (địa chỉ 0x27)
- **Buzzer**: Cảnh báo âm thanh khi phát hiện xâm nhập
- **2 Nút nhấn**: Tắt cảnh báo cho từng khu vực

## CẤU TRÚC PHẦN CỨNG

### Chân GPIO được sử dụng:
- **PC13**: LED (Output)
- **PC14**: Buzzer (Output)
- **PB14**: Output dự phòng
- **PB12**: Nút nhấn tắt cảnh báo Khu vực 1 (Input Pull-up)
- **PB13**: Nút nhấn tắt cảnh báo Khu vực 2 (Input Pull-up)
- **PB6, PB7**: I2C1 (SCL, SDA) - Kết nối LCD
- **PA9, PA10**: USART1 (TX, RX) - Module GSM/SIM
- **PA2, PA3**: USART2 (TX, RX) - Module LoRa

### Clock Configuration:
- HSE: 8MHz (External Crystal)
- System Clock: 8MHz (không sử dụng PLL)
- I2C Clock: 100kHz

## CẤU TRÚC CODE

### 1. DRIVER DELAY (delay.c/h)

**Chức năng**: Tạo độ trễ chính xác dựa trên SysTick Timer

**Các hàm chính**:
- `delay_init(uint8_t SYSCLK)`: Khởi tạo delay với tần số HCLK (8MHz)
- `delay_us(uint32_t _us)`: Delay chính xác đến từng microsecond
- `delay_ms(uint16_t _ms)`: Delay theo millisecond

**Nguyên lý hoạt động**:
- Sử dụng SysTick timer đếm ngược từ giá trị LOAD
- Tính toán số chu kỳ cần thiết: `ticks = _us * fac_us`
- Vòng lặp kiểm tra giá trị VAL cho đến khi đủ số chu kỳ

### 2. DRIVER LCD I2C (I2C_LCD.c/h, I2C_LCD_cfg.c/h)

**Chức năng**: Điều khiển màn hình LCD 16x2 qua giao tiếp I2C với PCF8574

**Cấu hình** (I2C_LCD_cfg.c):
- Instance: I2C_LCD_1
- I2C Handle: hi2c1
- Địa chỉ I2C: 0x27
- Kích thước: 16 cột x 2 hàng

**Các hàm chính**:
- `I2C_LCD_Init()`: Khởi tạo LCD theo chuẩn HD44780 (4-bit mode)
- `I2C_LCD_Clear()`: Xóa màn hình
- `I2C_LCD_SetCursor(col, row)`: Đặt vị trí con trỏ
- `I2C_LCD_WriteString(str)`: Hiển thị chuỗi ký tự
- `I2C_LCD_Backlight()` / `NoBacklight()`: Bật/tắt đèn nền
- `I2C_LCD_Cursor()` / `NoCursor()`: Hiển thị/ẩn con trỏ
- `I2C_LCD_Blink()` / `NoBlink()`: Nhấp nháy con trỏ

**Nguyên lý hoạt động**:
1. **Gửi dữ liệu qua I2C Expander (PCF8574)**:
   - 4 bit cao: Dữ liệu/lệnh
   - Bit EN (Enable): Tạo xung kích hoạt LCD
   - Bit RS (Register Select): 0=Lệnh, 1=Dữ liệu
   - Bit RW (Read/Write): Luôn = 0 (Write)
   - Bit Backlight: Điều khiển đèn nền

2. **Quy trình khởi tạo LCD**:
   - Chờ 50ms sau power-up
   - Gửi lệnh 0x30 ba lần (chuyển sang 8-bit mode)
   - Gửi lệnh 0x02 (chuyển sang 4-bit mode)
   - Cấu hình: 4-bit, 2 dòng, font 5x8
   - Bật hiển thị, tắt con trỏ

3. **Gửi dữ liệu 4-bit**:
   - Gửi 4 bit cao trước
   - Tạo xung EN (high → low)
   - Gửi 4 bit thấp
   - Tạo xung EN

### 3. UTILITY MACROS (Util.h)

**Chức năng**: Cung cấp các macro tối ưu cho GPIO và delay

**GPIO Macros**:
- `GPIO_SET_PIN(port, pin)`: Set pin = 1
- `GPIO_CLEAR_PIN(port, pin)`: Clear pin = 0
- `GPIO_TOGGLE_PIN(port, pin)`: Đảo trạng thái pin
- `GPIO_READ_PIN(port, pin)`: Đọc trạng thái pin

**Delay Macros**:
- `DELAY_US(us)`: Delay microsecond (sử dụng SysTick)
- `DELAY_MS(ms)`: Delay millisecond

**Ưu điểm**: Truy cập trực tiếp thanh ghi, nhanh hơn HAL functions

### 4. CHƯƠNG TRÌNH CHÍNH (main.c)

#### 4.1. ĐỊNH NGHĨA LỆNH GIAO TIẾP

**Lệnh LoRa** (qua UART2):
- `CMDACTIVE1 (0xA1)`: Khu vực 1 phát hiện xâm nhập
- `CMDINACTIVE1 (0xA2)`: Khu vực 1 an toàn
- `CMDACTIVE2 (0xB1)`: Khu vực 2 phát hiện xâm nhập
- `CMDINACTIVE2 (0xB2)`: Khu vực 2 an toàn
- `CMDOFFKV1 (0xC1)`: Lệnh tắt cảnh báo KV1
- `CMDOFFKV2 (0xC2)`: Lệnh tắt cảnh báo KV2

**Lệnh AT cho Module GSM/SIM**:
- `AT`: Kiểm tra kết nối
- `ATE0`: Tắt echo
- `AT+IPR=9600`: Đặt baudrate
- `AT+CMGF=1`: Chế độ SMS text
- `AT&W`: Lưu cấu hình
- `AT+CNMI=2,2,0,0`: Không lưu SMS vào SIM
- `AT+CREG?`: Kiểm tra đăng ký mạng
- `AT+CMGS=`: Gửi SMS
- `ATD`: Gọi điện
- `ATH`: Ngắt cuộc gọi

**Số điện thoại nhận cảnh báo**: `0968046024`

**Nội dung SMS**:
- SMS1: "Canh bao dot nhap khu vuc 1"
- SMS2: "Canh bao dot nhap khu vuc 2"
- SMS3: "HT GIAM SAT SAN SANG" (Hệ thống sẵn sàng)

#### 4.2. CÁC HÀM CHỨC NĂNG

**1. OnBuzzer() / OffBuzzer()**
- Bật/tắt buzzer (PC14)
- Sử dụng HAL_GPIO_WritePin()

**2. DisplayMain()**
- Xóa màn hình LCD
- Hiển thị "GIAM SAT AN NINH" ở dòng 1
- Tắt con trỏ và nhấp nháy

**3. InitModuleSIM()**

**Chức năng**: Khởi tạo module GSM/SIM

**Quy trình**:
1. Gửi lệnh `AT` → Kiểm tra kết nối (chờ 2s)
2. Gửi `AT+CNMI=2,2,0,0` → Cấu hình không lưu SMS (chờ 2s)
3. Gửi `AT+CMGF=1` → Chế độ SMS text (chờ 2s)

**Lưu ý**: Mỗi lệnh AT kết thúc bằng `\r\n` (0x0D, 0x0A)

**4. SendSMS(uint8_t SMSNum)**

**Chức năng**: Gửi SMS cảnh báo

**Quy trình**:
1. Gửi lệnh: `AT+CMGS="0968046024"`
2. Chờ 2 giây
3. Gửi nội dung SMS (SMS1, SMS2 hoặc SMS3)
4. Chờ 500ms
5. Gửi ký tự `Ctrl+Z` (0x1A) để kết thúc
6. Chờ 5 giây để module gửi SMS

**Tham số**:
- SMSNum = 1: Gửi SMS cảnh báo KV1
- SMSNum = 2: Gửi SMS cảnh báo KV2
- SMSNum = 3: Gửi SMS hệ thống sẵn sàng

**5. CheckLora()**

**Chức năng**: Kiểm tra dữ liệu từ module LoRa

**Quy trình**:
1. Đọc 1 byte từ UART2 (timeout 10ms)
2. Phân tích mã lệnh nhận được:

   **Nếu nhận 0xA1 (CMDACTIVE1)**:
   - Hiển thị "CB KV1" tại cột 0, dòng 1
   - Bật buzzer
   - Gửi SMS cảnh báo KV1
   - Đặt cờ KV1Active = 1

   **Nếu nhận 0xA2 (CMDINACTIVE1)**:
   - Xóa hiển thị "CB KV1" (6 khoảng trắng)
   - Đặt cờ KV1Active = 0
   - Tắt buzzer nếu KV2Active = 0

   **Nếu nhận 0xB1 (CMDACTIVE2)**:
   - Hiển thị "CB KV2" tại cột 8, dòng 1
   - Bật buzzer
   - Gửi SMS cảnh báo KV2
   - Đặt cờ KV2Active = 1

   **Nếu nhận 0xB2 (CMDINACTIVE2)**:
   - Xóa hiển thị "CB KV2"
   - Đặt cờ KV2Active = 0
   - Tắt buzzer nếu KV1Active = 0

**6. SendOffKV1() / SendOffKV2()**

**Chức năng**: Gửi lệnh tắt cảnh báo đến module LoRa

- SendOffKV1(): Gửi byte 0xC1 qua UART2
- SendOffKV2(): Gửi byte 0xC2 qua UART2

**Mục đích**: Thông báo cho các node LoRa từ xa biết đã xác nhận cảnh báo

## LUỒNG HOẠT ĐỘNG CHÍNH

### 1. KHỞI ĐỘNG HỆ THỐNG (main function)

```
START
  ↓
HAL_Init() - Khởi tạo HAL library
  ↓
SystemClock_Config() - Cấu hình clock 8MHz từ HSE
  ↓
MX_GPIO_Init() - Khởi tạo GPIO
  ↓
MX_I2C1_Init() - Khởi tạo I2C1 (100kHz)
  ↓
MX_USART1_UART_Init() - Khởi tạo UART1 (115200 baud - GSM)
  ↓
MX_USART2_UART_Init() - Khởi tạo UART2 (9600 baud - LoRa)
  ↓
delay_init(8) - Khởi tạo delay với HCLK = 8MHz
  ↓
I2C_LCD_Init() - Khởi tạo LCD I2C
  ↓
DisplayMain() - Hiển thị "GIAM SAT AN NINH"
  ↓
Hiển thị "DANG KHOI DONG.." ở dòng 2
  ↓
HAL_Delay(30000) - Chờ 30 giây (module GSM khởi động)
  ↓
InitModuleSIM() - Cấu hình module GSM
  ↓
HAL_Delay(2000) - Chờ 2 giây
  ↓
SendSMS(3) - Gửi SMS "HT GIAM SAT SAN SANG"
  ↓
Xóa dòng 2 LCD
  ↓
Bật buzzer 1 giây (báo hiệu sẵn sàng)
  ↓
Tắt buzzer
  ↓
Vào vòng lặp chính (while(1))
```

### 2. VÒNG LẶP CHÍNH (Infinite Loop)

```
while(1) {
    ↓
  CheckLora() - Kiểm tra tín hiệu từ LoRa
    ↓
  Kiểm tra nút PB12 (Nút tắt KV1)
    ├─ Nếu nhấn (= 0):
    │   ├─ Tắt buzzer
    │   ├─ SendOffKV1() - Gửi lệnh 0xC1
    │   └─ Delay 500ms (chống dội)
    ↓
  Kiểm tra nút PB13 (Nút tắt KV2)
    ├─ Nếu nhấn (= 0):
    │   ├─ Tắt buzzer
    │   ├─ SendOffKV2() - Gửi lệnh 0xC2
    │   └─ Delay 500ms (chống dội)
    ↓
  Lặp lại
}
```

### 3. XỬ LÝ CẢNH BÁO (CheckLora function)

**Kịch bản 1: Phát hiện xâm nhập KV1**
```
LoRa nhận byte 0xA1
  ↓
LCD hiển thị "CB KV1" (cột 0, dòng 1)
  ↓
Bật buzzer (PC14 = HIGH)
  ↓
SendSMS(1) - Gửi "Canh bao dot nhap khu vuc 1"
  ↓
Đặt cờ KV1Active = 1
```

**Kịch bản 2: KV1 trở lại an toàn**
```
LoRa nhận byte 0xA2
  ↓
LCD xóa "CB KV1" (hiển thị 6 khoảng trắng)
  ↓
Đặt cờ KV1Active = 0
  ↓
Kiểm tra KV2Active
  ├─ Nếu KV2Active = 0: Tắt buzzer
  └─ Nếu KV2Active = 1: Giữ buzzer bật
```

**Kịch bản 3: Người dùng nhấn nút tắt cảnh báo KV1**
```
Nhấn nút PB12
  ↓
Tắt buzzer ngay lập tức
  ↓
SendOffKV1() - Gửi 0xC1 đến LoRa
  ↓
Node LoRa KV1 nhận lệnh và reset trạng thái
  ↓
Delay 500ms (chống dội nút)
```

## SƠ ĐỒ GIAO TIẾP

```
                    STM32F103C6
                   ┌─────────────┐
                   │             │
    LCD I2C ───────┤ PB6/PB7     │
    (0x27)         │ (I2C1)      │
                   │             │
    Module GSM ────┤ PA9/PA10    │
    (115200)       │ (UART1)     │
                   │             │
    Module LoRa ───┤ PA2/PA3     │
    (9600)         │ (UART2)     │
                   │             │
    Buzzer ────────┤ PC14        │
                   │             │
    Nút KV1 ───────┤ PB12        │
    Nút KV2 ───────┤ PB13        │
                   │             │
    LED ───────────┤ PC13        │
                   └─────────────┘
```

## TÍNH NĂNG NỔI BẬT

1. **Giám sát 2 khu vực độc lập**: Mỗi khu vực có cảnh báo riêng
2. **Cảnh báo đa kênh**: 
   - Hiển thị LCD
   - Buzzer âm thanh
   - SMS qua GSM
3. **Tắt cảnh báo linh hoạt**: Có thể tắt từng khu vực mà không ảnh hưởng khu vực khác
4. **Giao tiếp không dây**: Sử dụng LoRa cho khoảng cách xa
5. **Thông báo trạng thái**: Gửi SMS khi hệ thống sẵn sàng

## THÔNG SỐ KỸ THUẬT

- **Vi điều khiển**: STM32F103C6 (ARM Cortex-M3)
- **Tần số hoạt động**: 8MHz (HSE)
- **Flash**: 32KB
- **RAM**: 10KB
- **Giao tiếp**:
  - I2C1: 100kHz (LCD)
  - UART1: 115200 baud (GSM)
  - UART2: 9600 baud (LoRa)

## HƯỚNG DẪN SỬ DỤNG

### Khởi động lần đầu:
1. Cấp nguồn cho hệ thống
2. LCD hiển thị "GIAM SAT AN NINH" và "DANG KHOI DONG.."
3. Chờ 30 giây để module GSM kết nối mạng
4. Hệ thống gửi SMS xác nhận "HT GIAM SAT SAN SANG"
5. Buzzer kêu 1 giây báo hiệu sẵn sàng

### Khi có cảnh báo:
1. LCD hiển thị "CB KV1" hoặc "CB KV2"
2. Buzzer kêu liên tục
3. Nhận SMS cảnh báo trên điện thoại
4. Nhấn nút tương ứng (PB12 hoặc PB13) để tắt cảnh báo

### Lưu ý:
- Thay đổi số điện thoại trong biến `PhoneNumber[]`
- Module GSM cần SIM card có sẵn tiền và đăng ký mạng
- Khoảng cách LoRa phụ thuộc vào môi trường (tối đa vài km)

## TÁC GIẢ VÀ CREDIT

- **Delay Driver**: Ceres_Li
- **I2C LCD Driver**: Khaled Magdy (www.DeepBlueMbedded.com)
- **Main Application**: Tích hợp hệ thống giám sát an ninh

## PHIÊN BẢN

- **Version**: 1.0.0
- **Date**: 2025
- **Platform**: STM32F103C6
- **IDE**: Keil MDK-ARM
- **HAL Version**: STM32F1xx HAL Driver

## KẾT LUẬN

Hệ thống giám sát an ninh này cung cấp giải pháp hoàn chỉnh với khả năng:
- Giám sát từ xa qua LoRa
- Cảnh báo tức thì qua SMS
- Giao diện trực quan qua LCD
- Điều khiển dễ dàng qua nút nhấn
- Hoạt động ổn định với STM32F103

Phù hợp cho các ứng dụng: nhà riêng, kho bãi, văn phòng nhỏ, hoặc các khu vực cần giám sát an ninh cơ bản.
