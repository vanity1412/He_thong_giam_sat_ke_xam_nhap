# HỆ THỐNG BÁO ĐỘNG VÀ TRUYỀN THÔNG LORA - STM32F103C6

## TỔNG QUAN DỰ ÁN

Đây là dự án hệ thống báo động thông minh sử dụng vi điều khiển STM32F103C6, tích hợp cảm biến, LED, buzzer và module truyền thông LoRa để giám sát và cảnh báo từ xa.

### Phần cứng sử dụng:
- **Vi điều khiển**: STM32F103C6 (ARM Cortex-M3, 8MHz HSE)
- **Màn hình LCD**: I2C LCD 16x2 (địa chỉ 0x27)
- **Module truyền thông**: LoRa qua UART2 (9600 baud)
- **Cảm biến đầu vào**: GPIO PB12 (cảm biến báo động)
- **Đầu ra**: LED (PB14), Buzzer (PC14)
- **Debug**: UART1 (115200 baud)

---

## CẤU TRÚC DỰ ÁN

```
MainCode/
├── Core/
│   ├── Inc/                      # Thư mục header files
│   │   ├── main.h               # Header chính
│   │   ├── stm32f1xx_hal_conf.h # Cấu hình HAL
│   │   └── stm32f1xx_it.h       # Khai báo interrupt handlers
│   └── Src/                      # Thư mục source files
│       ├── main.c               # Chương trình chính
│       ├── delay.c/h            # Thư viện delay chính xác
│       ├── I2C_LCD.c/h          # Driver màn hình LCD I2C
│       ├── I2C_LCD_cfg.c/h      # Cấu hình LCD
│       ├── Util.c/h             # Các macro tiện ích
│       ├── stm32f1xx_it.c       # Interrupt handlers
│       ├── stm32f1xx_hal_msp.c  # Cấu hình phần cứng HAL
│       └── system_stm32f1xx.c   # Cấu hình hệ thống
├── Drivers/                      # Thư viện HAL và CMSIS
└── MDK-ARM/                      # Project Keil MDK-ARM
```

---

## CHI TIẾT CÁC MODULE

### 1. MAIN.C - CHƯƠNG TRÌNH CHÍNH

#### 1.1. Định nghĩa lệnh giao tiếp LoRa

```c
#define CMDACTIVE1    0xA1    // Lệnh gửi: Báo động kích hoạt
#define CMDINACTIVE1  0xA2    // Lệnh gửi: Báo động tắt
#define CMDACTIVE2    0xB1    // Lệnh nhận: Xác nhận kích hoạt
#define CMDINACTIVE2  0xB2    // Lệnh nhận: Xác nhận tắt
#define CMDOFFKV1     0xC1    // Lệnh nhận: Tắt buzzer từ xa
#define CMDOFFKV2     0xC2    // Lệnh nhận: Tắt buzzer từ xa (dự phòng)
```

#### 1.2. Biến toàn cục

```c
unsigned long TimeCount = 0;  // Bộ đếm thời gian (chưa sử dụng)
char Arlarm = 0;              // Cờ trạng thái báo động (0: tắt, 1: bật)
```

#### 1.3. Các hàm điều khiển phần cứng

**Điều khiển LED (PB14):**
```c
void OnLED()   // Bật LED báo hiệu
void OffLED()  // Tắt LED
```

**Điều khiển Buzzer (PC14):**
```c
void OnBuzzer()   // Bật còi báo động
void OffBuzzer()  // Tắt còi
```

**Giao tiếp LoRa qua UART2:**
```c
void SendArlarm()  // Gửi lệnh CMDACTIVE1 (0xA1) - Báo động kích hoạt
void SendOff()     // Gửi lệnh CMDINACTIVE1 (0xA2) - Báo động tắt
void CheckLora()   // Kiểm tra lệnh từ LoRa, tắt buzzer nếu nhận CMDOFFKV1
```

#### 1.4. Luồng khởi tạo (main function)

```c
int main(void)
{
    // 1. Khởi tạo HAL
    HAL_Init();
    
    // 2. Cấu hình clock hệ thống (8MHz HSE)
    SystemClock_Config();
    
    // 3. Khởi tạo các ngoại vi
    MX_GPIO_Init();      // GPIO cho LED, Buzzer, Sensor
    MX_I2C1_Init();      // I2C cho LCD
    MX_USART1_UART_Init(); // UART1 debug (115200)
    MX_USART2_UART_Init(); // UART2 LoRa (9600)
    
    // 4. Khởi tạo delay chính xác
    delay_init(8);  // 8MHz system clock
    
    // 5. Kiểm tra hoạt động (startup sequence)
    OnLED();
    HAL_Delay(30000);  // LED sáng 30 giây
    OffLED();
    OnBuzzer();
    HAL_Delay(1000);   // Buzzer kêu 1 giây
    OffBuzzer();
    
    // 6. Vòng lặp chính
    while(1) {
        // Xử lý logic báo động
    }
}
```

#### 1.5. Vòng lặp chính - Logic báo động

```c
while (1)
{
    // Bước 1: Kiểm tra lệnh từ LoRa
    CheckLora();  // Nếu nhận CMDOFFKV1 → Tắt buzzer
    
    // Bước 2: Đọc trạng thái cảm biến (PB12)
    if(HAL_GPIO_ReadPin(GPIOB, GPIO_PIN_12) == GPIO_PIN_SET)
    {
        // Chống dội phím: Đợi 500ms và kiểm tra lại
        HAL_Delay(500);
        
        if(HAL_GPIO_ReadPin(GPIOB, GPIO_PIN_12) == GPIO_PIN_SET)
        {
            // Cảm biến vẫn ở mức HIGH → Báo động
            OnLED();  // Bật LED
            
            if(Arlarm == 0)  // Nếu chưa báo động
            {
                Arlarm = 1;        // Đặt cờ báo động
                OnBuzzer();        // Bật còi
                SendArlarm();      // Gửi lệnh 0xA1 qua LoRa
            }
        }
    }
    else  // Cảm biến ở mức LOW
    {
        OffLED();  // Tắt LED
        
        if(Arlarm == 1)  // Nếu đang báo động
        {
            Arlarm = 0;    // Xóa cờ báo động
            SendOff();     // Gửi lệnh 0xA2 qua LoRa
            // Lưu ý: Buzzer KHÔNG tự động tắt, phải nhận lệnh từ LoRa
        }
    }
}
```

---

### 2. DELAY.C/H - THỨ VIỆN DELAY CHÍNH XÁC

Module này cung cấp hàm delay chính xác dựa trên SysTick timer.

#### 2.1. Khởi tạo

```c
void delay_init(uint8_t SYSCLK)
```
- **Tham số**: `SYSCLK` - Tần số HCLK (MHz), ví dụ: 8, 72
- **Chức năng**: Cấu hình SysTick để tính toán delay chính xác
- **Cơ chế**: Nếu SYSCLK = 8MHz → 8 chu kỳ clock = 1 microsecond

#### 2.2. Hàm delay

```c
void delay_us(uint32_t _us)  // Delay microsecond
void delay_ms(uint16_t _ms)  // Delay millisecond
```

**Nguyên lý hoạt động:**
- Sử dụng SysTick counter (đếm xuống từ LOAD)
- Tính toán số chu kỳ cần thiết: `ticks = _us * fac_us`
- Đợi cho đến khi đủ số chu kỳ

---

### 3. I2C_LCD - DRIVER MÀN HÌNH LCD I2C

Driver điều khiển màn hình LCD 16x2 qua giao tiếp I2C với PCF8574 I/O expander.

#### 3.1. Cấu hình (I2C_LCD_cfg.c)

```c
const I2C_LCD_CfgType I2C_LCD_CfgParam[I2C_LCD_MAX] = {
    {
        I2C_LCD_1,    // Instance index
        &hi2c1,       // I2C1 handle
        0x27,         // Địa chỉ I2C của LCD
        16,           // 16 cột
        2             // 2 hàng
    }
};
```

#### 3.2. Các hàm chính

**Khởi tạo:**
```c
void I2C_LCD_Init(uint8_t I2C_LCD_InstanceIndex)
```
- Đợi 50ms sau power-up
- Gửi chuỗi khởi tạo theo datasheet HD44780
- Cấu hình: 4-bit mode, 2 dòng, font 5x8
- Xóa màn hình

**Điều khiển hiển thị:**
```c
void I2C_LCD_Clear()              // Xóa màn hình
void I2C_LCD_Home()               // Về vị trí (0,0)
void I2C_LCD_SetCursor(col, row)  // Đặt con trỏ
void I2C_LCD_WriteChar(char)      // Viết 1 ký tự
void I2C_LCD_WriteString(str)     // Viết chuỗi
```

**Điều khiển backlight:**
```c
void I2C_LCD_Backlight()    // Bật đèn nền
void I2C_LCD_NoBacklight()  // Tắt đèn nền
```

**Hiệu ứng:**
```c
void I2C_LCD_ShiftLeft()   // Dịch màn hình sang trái
void I2C_LCD_ShiftRight()  // Dịch màn hình sang phải
void I2C_LCD_Cursor()      // Hiện con trỏ
void I2C_LCD_NoCursor()    // Ẩn con trỏ
void I2C_LCD_Blink()       // Nhấp nháy con trỏ
void I2C_LCD_NoBlink()     // Tắt nhấp nháy
```

**Ký tự tùy chỉnh:**
```c
void I2C_LCD_CreateCustomChar(index, charMap)  // Tạo ký tự tùy chỉnh
void I2C_LCD_PrintCustomChar(index)            // In ký tự tùy chỉnh
```

#### 3.3. Giao thức I2C với PCF8574

**Định dạng byte gửi:**
```
Bit 7-4: Data (D7-D4)
Bit 3:   Backlight (1=ON, 0=OFF)
Bit 2:   Enable (E)
Bit 1:   Read/Write (RW)
Bit 0:   Register Select (RS)
```

**Quy trình gửi 1 byte:**
1. Gửi 4 bit cao + EN=1
2. Delay 2μs
3. Gửi 4 bit cao + EN=0
4. Delay 50μs
5. Gửi 4 bit thấp + EN=1
6. Delay 2μs
7. Gửi 4 bit thấp + EN=0
8. Delay 50μs

---

### 4. UTIL.H - CÁC MACRO TIỆN ÍCH

#### 4.1. Macro GPIO truy cập trực tiếp

```c
GPIO_SET_PIN(port, pin)      // Bật pin (nhanh hơn HAL)
GPIO_CLEAR_PIN(port, pin)    // Tắt pin
GPIO_TOGGLE_PIN(port, pin)   // Đảo trạng thái pin
GPIO_READ_PIN(port, pin)     // Đọc trạng thái pin
```

**Ví dụ sử dụng:**
```c
GPIO_SET_PIN(GPIOB, GPIO_PIN_14);    // Bật LED
GPIO_TOGGLE_PIN(GPIOC, GPIO_PIN_14); // Đảo buzzer
```

#### 4.2. Macro Delay dựa trên SysTick

```c
DELAY_US(us)  // Delay microsecond (không cần khởi tạo)
DELAY_MS(ms)  // Delay millisecond
```

**Ưu điểm:**
- Không cần gọi `delay_init()`
- Tự động tính toán dựa trên `SystemCoreClock`
- Inline, nhanh hơn function call

---

### 5. CẤU HÌNH PHẦN CỨNG (stm32f1xx_hal_msp.c)

#### 5.1. I2C1 - Giao tiếp LCD

```c
PB6 → I2C1_SCL (Open-Drain, High Speed)
PB7 → I2C1_SDA (Open-Drain, High Speed)
Clock: 100kHz
```

#### 5.2. UART1 - Debug

```c
PA9  → USART1_TX (Push-Pull, High Speed)
PA10 → USART1_RX (Input, No Pull)
Baud: 115200
```

#### 5.3. UART2 - LoRa

```c
PA2 → USART2_TX (Push-Pull, High Speed)
PA3 → USART2_RX (Input, No Pull)
Baud: 9600
```

#### 5.4. GPIO

**Đầu vào:**
```c
PA4  → Input (No Pull)
PB0  → Input (No Pull)
PB12 → Input (No Pull) - CẢM BIẾN BÁO ĐỘNG
PB13 → Input (Pull-Up)
```

**Đầu ra:**
```c
PC13 → Output (Push-Pull, Low Speed)
PC14 → Output (Push-Pull, Low Speed) - BUZZER
PB14 → Output (Push-Pull, Low Speed) - LED
```

---

### 6. CẤU HÌNH CLOCK (SystemClock_Config)

```c
Nguồn clock: HSE (External 8MHz crystal)
SYSCLK: 8MHz (không dùng PLL)
HCLK:   8MHz (AHB prescaler = 1)
PCLK1:  8MHz (APB1 prescaler = 1)
PCLK2:  8MHz (APB2 prescaler = 1)
```

**Lưu ý:** Có thể tăng tốc độ lên 72MHz bằng cách bật PLL.

---

## LUỒNG HOẠT ĐỘNG TỔNG THỂ

### Sơ đồ trạng thái

```
[KHỞI ĐỘNG]
    ↓
[Kiểm tra LED 30s]
    ↓
[Kiểm tra Buzzer 1s]
    ↓
[CHỜ] ←──────────────┐
    ↓                 │
[Kiểm tra LoRa]      │
    ↓                 │
[Đọc cảm biến PB12]  │
    ↓                 │
    ├─ HIGH (500ms) ──┤
    │   ↓             │
    │   [Bật LED]     │
    │   [Bật Buzzer]  │
    │   [Gửi 0xA1]    │
    │   [Arlarm=1]    │
    │                 │
    └─ LOW ───────────┤
        ↓             │
        [Tắt LED]     │
        [Gửi 0xA2]    │
        [Arlarm=0]    │
        └─────────────┘
```

### Chi tiết các trường hợp

#### Trường hợp 1: Phát hiện xâm nhập

1. Cảm biến PB12 = HIGH
2. Đợi 500ms (chống nhiễu)
3. Kiểm tra lại PB12 = HIGH
4. Bật LED (PB14)
5. Nếu `Arlarm == 0`:
   - Đặt `Arlarm = 1`
   - Bật Buzzer (PC14)
   - Gửi `0xA1` qua LoRa
6. Tiếp tục vòng lặp

#### Trường hợp 2: Hết báo động

1. Cảm biến PB12 = LOW
2. Tắt LED (PB14)
3. Nếu `Arlarm == 1`:
   - Đặt `Arlarm = 0`
   - Gửi `0xA2` qua LoRa
   - **Buzzer vẫn kêu** (chờ lệnh từ xa)
4. Tiếp tục vòng lặp

#### Trường hợp 3: Tắt buzzer từ xa

1. Nhận byte `0xC1` từ UART2 (LoRa)
2. Hàm `CheckLora()` phát hiện
3. Gọi `OffBuzzer()`
4. Buzzer tắt

---

## GIAO THỨC TRUYỀN THÔNG LORA

### Lệnh gửi đi (TX)

| Mã lệnh | Giá trị | Ý nghĩa | Khi nào gửi |
|---------|---------|---------|-------------|
| CMDACTIVE1 | 0xA1 | Báo động kích hoạt | Khi phát hiện xâm nhập lần đầu |
| CMDINACTIVE1 | 0xA2 | Báo động tắt | Khi cảm biến trở về bình thường |

### Lệnh nhận vào (RX)

| Mã lệnh | Giá trị | Ý nghĩa | Hành động |
|---------|---------|---------|-----------|
| CMDOFFKV1 | 0xC1 | Tắt buzzer từ xa | Tắt còi báo động |
| CMDOFFKV2 | 0xC2 | Tắt buzzer từ xa (dự phòng) | Chưa sử dụng |
| CMDACTIVE2 | 0xB1 | Xác nhận kích hoạt | Chưa sử dụng |
| CMDINACTIVE2 | 0xB2 | Xác nhận tắt | Chưa sử dụng |

### Định dạng gói tin

```
[1 byte] - Mã lệnh
```

**Ví dụ:**
- Gửi báo động: `0xA1`
- Nhận lệnh tắt: `0xC1`

---

## HƯỚNG DẪN SỬ DỤNG

### 1. Biên dịch và nạp code

```bash
# Sử dụng Keil MDK-ARM
1. Mở file: MDK-ARM/MainCode.uvprojx
2. Build Project (F7)
3. Download to Flash (F8)
```

### 2. Kết nối phần cứng

**I2C LCD:**
- VCC → 5V
- GND → GND
- SDA → PB7
- SCL → PB6

**Module LoRa:**
- VCC → 3.3V
- GND → GND
- TX → PA3 (UART2_RX)
- RX → PA2 (UART2_TX)

**Cảm biến:**
- OUT → PB12
- VCC → 3.3V/5V
- GND → GND

**LED:**
- Anode → PB14
- Cathode → GND (qua điện trở 220Ω)

**Buzzer:**
- Positive → PC14
- Negative → GND

### 3. Kiểm tra hoạt động

1. **Sau khi reset:**
   - LED sáng 30 giây
   - Buzzer kêu 1 giây
   
2. **Kích hoạt cảm biến:**
   - LED sáng
   - Buzzer kêu
   - Gửi 0xA1 qua LoRa
   
3. **Tắt cảm biến:**
   - LED tắt
   - Gửi 0xA2 qua LoRa
   - Buzzer vẫn kêu
   
4. **Gửi 0xC1 từ LoRa:**
   - Buzzer tắt

---

## TỐI ƯU HÓA VÀ MỞ RỘNG

### Các điểm cần cải thiện

1. **Tăng tốc độ xử lý:**
   - Bật PLL để chạy 72MHz
   - Sửa `delay_init(72)` trong main.c

2. **Sử dụng LCD:**
   - Hiện tại LCD được khởi tạo nhưng chưa dùng
   - Có thể hiển thị trạng thái hệ thống

3. **Xử lý UART bằng interrupt:**
   - Thay `HAL_UART_Receive()` bằng `HAL_UART_Receive_IT()`
   - Tránh blocking trong `CheckLora()`

4. **Thêm timeout:**
   - Tự động tắt buzzer sau X phút
   - Sử dụng biến `TimeCount`

5. **Xác nhận gói tin:**
   - Sử dụng `CMDACTIVE2` và `CMDINACTIVE2`
   - Gửi lại nếu không nhận được ACK

### Ví dụ code mở rộng

**Hiển thị trạng thái lên LCD:**
```c
// Trong main(), sau delay_init()
I2C_LCD_Init(I2C_LCD_1);
I2C_LCD_SetCursor(I2C_LCD_1, 0, 0);
I2C_LCD_WriteString(I2C_LCD_1, "System Ready");

// Trong vòng lặp
if(Arlarm == 1) {
    I2C_LCD_Clear(I2C_LCD_1);
    I2C_LCD_WriteString(I2C_LCD_1, "ALARM ACTIVE!");
} else {
    I2C_LCD_Clear(I2C_LCD_1);
    I2C_LCD_WriteString(I2C_LCD_1, "System Normal");
}
```

**Tự động tắt buzzer sau 5 phút:**
```c
unsigned long BuzzerStartTime = 0;

// Khi bật buzzer
if(Arlarm == 0) {
    Arlarm = 1;
    OnBuzzer();
    BuzzerStartTime = HAL_GetTick();
    SendArlarm();
}

// Trong vòng lặp
if(Arlarm == 1 && (HAL_GetTick() - BuzzerStartTime > 300000)) {
    OffBuzzer();  // Tắt sau 5 phút (300000ms)
}
```

---

## TROUBLESHOOTING

### Vấn đề 1: LCD không hiển thị

**Nguyên nhân:**
- Địa chỉ I2C sai (0x27 hoặc 0x3F)
- Kết nối SDA/SCL bị đảo
- Chưa bật backlight

**Giải pháp:**
```c
// Thử địa chỉ khác
#define I2C_LCD_ADDRESS 0x3F  // Trong I2C_LCD_cfg.c

// Bật backlight
I2C_LCD_Backlight(I2C_LCD_1);
```

### Vấn đề 2: LoRa không gửi/nhận

**Nguyên nhân:**
- Baud rate không khớp
- TX/RX bị đảo
- Module chưa cấu hình

**Giải pháp:**
```c
// Kiểm tra baud rate
huart2.Init.BaudRate = 9600;  // Phải khớp với module LoRa

// Kiểm tra kết nối
// STM32 TX (PA2) → LoRa RX
// STM32 RX (PA3) → LoRa TX
```

### Vấn đề 3: Buzzer không tắt từ xa

**Nguyên nhân:**
- Timeout quá ngắn trong `HAL_UART_Receive()`
- Lệnh sai

**Giải pháp:**
```c
// Tăng timeout
HAL_UART_Receive(&huart2, UARTData, 1, 100);  // 100ms

// Kiểm tra lệnh
if(UARTData[0] == CMDOFFKV1 || UARTData[0] == CMDOFFKV2) {
    OffBuzzer();
}
```

### Vấn đề 4: Cảm biến kích hoạt liên tục

**Nguyên nhân:**
- Nhiễu điện
- Delay chống dội chưa đủ

**Giải pháp:**
```c
// Tăng delay chống dội
HAL_Delay(1000);  // 1 giây

// Thêm tụ lọc 0.1μF giữa OUT và GND của cảm biến
```

---

## THÔNG TIN THÊM

### Tài liệu tham khảo

- [STM32F103C6 Datasheet](https://www.st.com/resource/en/datasheet/stm32f103c6.pdf)
- [HD44780 LCD Controller](https://www.sparkfun.com/datasheets/LCD/HD44780.pdf)
- [PCF8574 I2C Expander](https://www.ti.com/lit/ds/symlink/pcf8574.pdf)

### Tác giả

- **Delay Module**: Ceres_Li
- **I2C LCD Driver**: Khaled Magdy (www.DeepBlueMbedded.com)
- **Main Application**: [Tên của bạn]

### Giấy phép

Copyright © 2025 STMicroelectronics. All rights reserved.

---

## CHANGELOG

### Version 1.0 (2025-01-XX)
- Phiên bản đầu tiên
- Chức năng cơ bản: Phát hiện xâm nhập, báo động, truyền LoRa
- Hỗ trợ tắt buzzer từ xa

### Tính năng dự kiến

- [ ] Hiển thị trạng thái lên LCD
- [ ] Xác nhận gói tin (ACK)
- [ ] Tự động tắt buzzer sau timeout
- [ ] Lưu log vào EEPROM
- [ ] Chế độ tiết kiệm năng lượng (Sleep mode)
- [ ] Cấu hình qua UART (AT commands)

---

**Lưu ý:** Đây là tài liệu kỹ thuật chi tiết. Vui lòng đọc kỹ trước khi sử dụng và chỉnh sửa code.
