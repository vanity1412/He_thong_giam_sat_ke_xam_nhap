# HỆ THỐNG BÁO ĐỘNG VỚI STM32F103C6

## TỔNG QUAN DỰ ÁN

Đây là một hệ thống báo động thông minh sử dụng vi điều khiển STM32F103C6 với khả năng giao tiếp không dây qua module LoRa. Hệ thống có thể phát hiện tín hiệu từ cảm biến, kích hoạt cảnh báo bằng LED và còi, đồng thời gửi thông báo qua giao tiếp UART đến module LoRa.

## PHẦN CỨNG

### Vi điều khiển
- **STM32F103C6**: ARM Cortex-M3, 32KB Flash, 10KB RAM
- **Tần số hoạt động**: 8MHz (HSE - High Speed External oscillator)

### Các ngoại vi được sử dụng

#### GPIO (General Purpose Input/Output)
- **PB12**: Đầu vào cảm biến (INPUT, NO PULL)
- **PB13**: Đầu vào dự phòng (INPUT, PULL-UP)
- **PB14**: Điều khiển LED (OUTPUT)
- **PC13**: Đầu ra dự phòng (OUTPUT)
- **PC14**: Điều khiển còi Buzzer (OUTPUT)

#### I2C1 (Inter-Integrated Circuit)
- **PB6**: I2C1_SCL (Clock)
- **PB7**: I2C1_SDA (Data)
- **Tốc độ**: 100kHz
- **Chức năng**: Giao tiếp với màn hình LCD I2C (địa chỉ 0x27)

#### UART (Universal Asynchronous Receiver-Transmitter)
- **USART1**: 
  - PA9 (TX), PA10 (RX)
  - Baudrate: 115200
  - Chức năng: Debug/Communication
  
- **USART2**:
  - PA2 (TX), PA3 (RX)
  - Baudrate: 9600
  - Chức năng: Giao tiếp với module LoRa

## CẤU TRÚC DỰ ÁN

```
MainCode/
├── Core/
│   ├── Inc/                    # Thư mục header files
│   │   ├── main.h             # Header chính
│   │   ├── stm32f1xx_hal_conf.h  # Cấu hình HAL
│   │   └── stm32f1xx_it.h     # Interrupt handlers
│   │
│   └── Src/                    # Thư mục source files
│       ├── main.c             # Chương trình chính
│       ├── delay.c/h          # Thư viện delay chính xác
│       ├── I2C_LCD.c/h        # Driver màn hình LCD I2C
│       ├── I2C_LCD_cfg.c/h    # Cấu hình LCD
│       ├── Util.c/h           # Các macro tiện ích
│       ├── stm32f1xx_it.c     # Xử lý ngắt
│       ├── stm32f1xx_hal_msp.c # Cấu hình phần cứng
│       └── system_stm32f1xx.c  # Cấu hình hệ thống
│
├── Drivers/                    # STM32 HAL Drivers
│   ├── CMSIS/                 # CMSIS core
│   └── STM32F1xx_HAL_Driver/  # HAL library
│
└── MDK-ARM/                    # Keil MDK project files
    └── MainCode.uvprojx       # Keil project
```

## CHI TIẾT CÁC MODULE

### 1. MAIN.C - CHƯƠNG TRÌNH CHÍNH

#### Các lệnh điều khiển (Protocol Commands)
```c
#define CMDACTIVE1 0xA1      // Lệnh kích hoạt thiết bị 1
#define CMDINACTIVE1 0xA2    // Lệnh tắt thiết bị 1
#define CMDACTIVE2 0xB1      // Lệnh kích hoạt thiết bị 2
#define CMDINACTIVE2 0xB2    // Lệnh tắt thiết bị 2
#define CMDOFFKV1 0xC1       // Lệnh tắt từ xa 1
#define CMDOFFKV2 0xC2       // Lệnh tắt từ xa 2
```

#### Biến toàn cục
- `TimeCount`: Bộ đếm thời gian (unsigned long)
- `Arlarm`: Cờ trạng thái báo động (0: tắt, 1: bật)

#### Các hàm điều khiển

**Điều khiển LED:**
```c
void OnLED()   // Bật LED (PB14 = HIGH)
void OffLED()  // Tắt LED (PB14 = LOW)
```

**Điều khiển Buzzer:**
```c
void OnBuzzer()   // Bật còi (PC14 = HIGH)
void OffBuzzer()  // Tắt còi (PC14 = LOW)
```

**Giao tiếp LoRa:**
```c
void SendArlarm()  // Gửi lệnh báo động (0xB1) qua UART2
void SendOff()     // Gửi lệnh tắt (0xB2) qua UART2
void CheckLora()   // Kiểm tra lệnh từ LoRa, tắt còi nếu nhận 0xC2
```

#### Luồng hoạt động chính (main function)

**1. Khởi tạo hệ thống:**
```c
HAL_Init();              // Khởi tạo HAL library
SystemClock_Config();    // Cấu hình clock 8MHz
MX_GPIO_Init();          // Khởi tạo GPIO
MX_I2C1_Init();          // Khởi tạo I2C
MX_USART1_UART_Init();   // Khởi tạo UART1
MX_USART2_UART_Init();   // Khởi tạo UART2
delay_init(8);           // Khởi tạo delay với clock 8MHz
```

**2. Chuỗi khởi động (Startup Sequence):**
```c
OnLED();                 // Bật LED
HAL_Delay(30000);        // Chờ 30 giây (thời gian khởi động)
OffLED();                // Tắt LED
OnBuzzer();              // Bật còi
HAL_Delay(1000);         // Còi kêu 1 giây
OffBuzzer();             // Tắt còi
```

**3. Vòng lặp chính (Main Loop):**

```
┌─────────────────────────────────────┐
│     Bắt đầu vòng lặp chính          │
└──────────────┬──────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  CheckLora()                         │
│  - Kiểm tra lệnh từ module LoRa      │
│  - Nếu nhận 0xC2 → Tắt còi          │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  Đọc trạng thái cảm biến (PB12)      │
└──────────────┬───────────────────────┘
               │
        ┌──────┴──────┐
        │             │
        ▼             ▼
    PB12 = 1      PB12 = 0
    (Phát hiện)   (Không phát hiện)
        │             │
        ▼             ▼
┌───────────────┐  ┌──────────────────┐
│ Delay 500ms   │  │  OffLED()        │
│ Kiểm tra lại  │  │                  │
└───────┬───────┘  │  Nếu Arlarm==1:  │
        │          │  - Arlarm = 0    │
    PB12 = 1?      │  - SendOff()     │
        │          └──────────────────┘
        ▼
    ┌───────┐
    │  Có   │
    └───┬───┘
        │
        ▼
┌──────────────────────┐
│  OnLED()             │
│                      │
│  Nếu Arlarm == 0:    │
│  - Arlarm = 1        │
│  - OnBuzzer()        │
│  - SendArlarm()      │
└──────────────────────┘
        │
        ▼
    Lặp lại
```

### 2. DELAY.C/H - THƯ VIỆN DELAY CHÍNH XÁC

Module này cung cấp các hàm delay chính xác sử dụng SysTick timer.

#### Nguyên lý hoạt động:
- Sử dụng SysTick timer của ARM Cortex-M3
- SysTick đếm ngược từ giá trị LOAD về 0
- Tính toán số chu kỳ cần thiết dựa trên tần số HCLK

#### Các hàm:

**delay_init(uint8_t SYSCLK):**
- Khởi tạo hệ thống delay
- Tham số: Tần số HCLK (MHz), ví dụ: 8 cho 8MHz
- Cấu hình SysTick sử dụng HCLK làm nguồn clock

**delay_us(uint32_t _us):**
- Delay chính xác đến mức microsecond
- Tính toán số ticks = _us × fac_us
- Đếm số chu kỳ SysTick đã trôi qua
- Xử lý cả trường hợp SysTick overflow

**delay_ms(uint16_t _ms):**
- Delay millisecond
- Gọi delay_us(1000) _ms lần

### 3. I2C_LCD - DRIVER MÀN HÌNH LCD I2C

Driver hoàn chỉnh cho màn hình LCD 16x2 hoặc 20x4 sử dụng giao tiếp I2C qua PCF8574.

#### Kiến trúc:
- **I2C_LCD.c/h**: Driver chính
- **I2C_LCD_cfg.c/h**: File cấu hình

#### Cấu hình LCD (I2C_LCD_cfg.c):
```c
I2C_LCD_1:
- I2C Handle: &hi2c1
- Địa chỉ I2C: 0x27
- Số cột: 16
- Số hàng: 2
```

#### Các lệnh LCD (Internal Commands):
```c
LCD_CLEARDISPLAY    0x01  // Xóa màn hình
LCD_RETURNHOME      0x02  // Về vị trí đầu
LCD_ENTRYMODESET    0x04  // Cài đặt chế độ nhập
LCD_DISPLAYCONTROL  0x08  // Điều khiển hiển thị
LCD_FUNCTIONSET     0x20  // Cài đặt chức năng
LCD_SETCGRAMADDR    0x40  // Đặt địa chỉ CGRAM
LCD_SETDDRAMADDR    0x80  // Đặt địa chỉ DDRAM
```

#### Giao tiếp I2C với PCF8574:

**Sơ đồ bit PCF8574:**
```
Bit 7 | Bit 6 | Bit 5 | Bit 4 | Bit 3 | Bit 2 | Bit 1 | Bit 0
 D7   |  D6   |  D5   |  D4   |  BL   |  EN   |  RW   |  RS
```
- D7-D4: Data bits (4-bit mode)
- BL: Backlight control
- EN: Enable signal
- RW: Read/Write (luôn = 0 cho Write)
- RS: Register Select (0=Command, 1=Data)

#### Các hàm chính:

**I2C_LCD_Init():**
- Chờ 50ms sau power-up
- Gửi chuỗi khởi tạo theo datasheet HD44780
- Cấu hình: 4-bit mode, 2 lines, 5x8 dots
- Bật hiển thị, tắt cursor, tắt blink
- Xóa màn hình

**I2C_LCD_SetCursor(Col, Row):**
- Đặt vị trí con trỏ
- Row offsets: [0x00, 0x40, 0x14, 0x54]

**I2C_LCD_WriteString(char* Str):**
- Ghi chuỗi ký tự lên LCD

**I2C_LCD_Clear():**
- Xóa toàn bộ màn hình

**Các hàm điều khiển:**
- `I2C_LCD_Backlight()` / `I2C_LCD_NoBacklight()`
- `I2C_LCD_Display()` / `I2C_LCD_NoDisplay()`
- `I2C_LCD_Cursor()` / `I2C_LCD_NoCursor()`
- `I2C_LCD_Blink()` / `I2C_LCD_NoBlink()`

### 4. UTIL.H - CÁC MACRO TIỆN ÍCH

#### GPIO Direct Access Macros:
```c
GPIO_SET_PIN(port, pin)     // Bật pin
GPIO_CLEAR_PIN(port, pin)   // Tắt pin
GPIO_TOGGLE_PIN(port, pin)  // Đảo trạng thái pin
GPIO_READ_PIN(port, pin)    // Đọc trạng thái pin
```

#### SysTick Delay Macros:
```c
DELAY_US(us)  // Delay microsecond (sử dụng SysTick)
DELAY_MS(ms)  // Delay millisecond
```

Các macro này truy cập trực tiếp thanh ghi, nhanh hơn HAL functions.

### 5. INTERRUPT HANDLERS (stm32f1xx_it.c)

Xử lý các ngắt hệ thống:

**SysTick_Handler():**
- Được gọi mỗi 1ms
- Cập nhật HAL_IncTick() cho HAL_Delay()

**Các Exception Handlers:**
- NMI_Handler()
- HardFault_Handler()
- MemManage_Handler()
- BusFault_Handler()
- UsageFault_Handler()

### 6. HAL MSP (stm32f1xx_hal_msp.c)

Cấu hình phần cứng cho các ngoại vi:

**HAL_I2C_MspInit():**
- Enable clock cho GPIOB và I2C1
- Cấu hình PB6, PB7 là chế độ Alternate Function Open-Drain
- Tốc độ HIGH

**HAL_UART_MspInit():**
- USART1: PA9 (TX - AF Push-Pull), PA10 (RX - Input)
- USART2: PA2 (TX - AF Push-Pull), PA3 (RX - Input)

## LUỒNG XỬ LÝ TỔNG THỂ

### Sơ đồ trạng thái hệ thống:

```
┌─────────────────┐
│   POWER ON      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  KHỞI TẠO       │
│  - HAL Init     │
│  - Clock Config │
│  - GPIO Init    │
│  - I2C Init     │
│  - UART Init    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  STARTUP        │
│  - LED ON       │
│  - Delay 30s    │
│  - LED OFF      │
│  - Beep 1s      │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│      TRẠNG THÁI IDLE            │
│  - Arlarm = 0                   │
│  - LED OFF                      │
│  - Buzzer OFF                   │
│  - Lắng nghe LoRa               │
│  - Quét cảm biến PB12           │
└────────┬────────────────────────┘
         │
         │ PB12 = HIGH (phát hiện)
         │ + delay 500ms
         │ + kiểm tra lại = HIGH
         ▼
┌─────────────────────────────────┐
│    TRẠNG THÁI ALARM             │
│  - Arlarm = 1                   │
│  - LED ON                       │
│  - Buzzer ON                    │
│  - Gửi CMDACTIVE2 qua LoRa      │
└────────┬────────────────────────┘
         │
         │ PB12 = LOW hoặc
         │ Nhận CMDOFFKV2 từ LoRa
         ▼
┌─────────────────────────────────┐
│   TRỞ VỀ IDLE                   │
│  - Arlarm = 0                   │
│  - LED OFF                      │
│  - Buzzer OFF (nếu nhận lệnh)   │
│  - Gửi CMDINACTIVE2 qua LoRa    │
└─────────────────────────────────┘
```

## GIAO THỨC TRUYỀN THÔNG

### UART2 - LoRa Communication

**Baudrate**: 9600 bps  
**Format**: 8 data bits, 1 stop bit, no parity

**Các lệnh gửi đi (TX):**
- `0xB1` (CMDACTIVE2): Thông báo phát hiện xâm nhập
- `0xB2` (CMDINACTIVE2): Thông báo hết cảnh báo

**Các lệnh nhận vào (RX):**
- `0xC2` (CMDOFFKV2): Lệnh tắt còi từ xa

**Timeout**: 10ms cho mỗi lần nhận

## TÍNH NĂNG CHỐNG NHIỄU

### Debouncing cảm biến:
```c
if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_12)==1)
{
    HAL_Delay(500);  // Chờ 500ms
    if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_12)==1)  // Kiểm tra lại
    {
        // Xác nhận phát hiện thật
    }
}
```

### Cơ chế cờ trạng thái:
- Biến `Arlarm` đảm bảo chỉ gửi lệnh 1 lần khi chuyển trạng thái
- Tránh spam lệnh qua LoRa

## BIÊN DỊCH VÀ NẠP CODE

### Yêu cầu:
- **IDE**: Keil MDK-ARM v5 trở lên
- **Compiler**: ARM Compiler v6
- **Debugger**: ST-Link V2

### Các bước:
1. Mở file `MDK-ARM/MainCode.uvprojx` trong Keil
2. Chọn target: STM32F103C6
3. Build project (F7)
4. Nạp code qua ST-Link (F8)

### Cấu hình Flash:
- Flash Size: 32KB
- RAM Size: 10KB
- Start Address: 0x08000000

## HƯỚNG DẪN SỬ DỤNG

1. **Kết nối phần cứng:**
   - Cảm biến → PB12
   - LED → PB12 (qua điện trở 330Ω)
   - Buzzer → PC14 (qua transistor)
   - LCD I2C → PB6 (SCL), PB7 (SDA)
   - Module LoRa → PA2 (TX), PA3 (RX)

2. **Cấp nguồn:**
   - 3.3V cho STM32
   - 5V cho LCD và module LoRa (nếu cần)

3. **Khởi động:**
   - LED sáng 30 giây (thời gian khởi động)
   - Còi kêu 1 giây để xác nhận
   - Hệ thống sẵn sàng

4. **Hoạt động:**
   - Khi cảm biến phát hiện: LED sáng, còi kêu, gửi cảnh báo
   - Tắt từ xa: Gửi lệnh 0xC2 qua LoRa

## KHẮC PHỤC SỰ CỐ

### LED không sáng:
- Kiểm tra kết nối PB14
- Kiểm tra nguồn cấp
- Kiểm tra điện trở hạn dòng

### Còi không kêu:
- Kiểm tra kết nối PC14
- Kiểm tra transistor driver
- Kiểm tra nguồn cấp cho buzzer

### Không giao tiếp được LoRa:
- Kiểm tra baudrate (9600)
- Kiểm tra kết nối TX/RX
- Kiểm tra nguồn module LoRa

### LCD không hiển thị:
- Kiểm tra địa chỉ I2C (0x27 hoặc 0x3F)
- Kiểm tra kết nối SDA/SCL
- Điều chỉnh biến trở contrast trên LCD

## TÍNH NĂNG MỞ RỘNG

Có thể thêm:
- Hiển thị thông tin lên LCD
- Thêm nhiều cảm biến
- Lưu log vào EEPROM
- Thêm RTC để ghi thời gian sự kiện
- Kết nối WiFi/GSM để gửi SMS

## TÁC GIẢ VÀ GIẤY PHÉP

- **Delay Module**: Ceres_Li
- **I2C LCD Driver**: Khaled Magdy (www.DeepBlueMbedded.com)
- **Main Application**: Custom implementation
- **HAL Library**: STMicroelectronics

## LIÊN HỆ HỖ TRỢ

Nếu có thắc mắc hoặc cần hỗ trợ, vui lòng tạo issue trên repository.
