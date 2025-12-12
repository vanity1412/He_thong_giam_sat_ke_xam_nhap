# DỰ ÁN ESP32-CAM WEB STREAMING SERVER

## TỔNG QUAN DỰ ÁN

Đây là dự án xây dựng một web server streaming video trực tiếp (live streaming) sử dụng ESP32-CAM. Dự án cho phép ESP32-CAM hoạt động như một Access Point (AP) và phát video trực tiếp qua giao thức MJPEG (Motion JPEG) mà người dùng có thể xem trực tiếp trên trình duyệt web.

### Tính năng chính:
- **Chế độ Access Point (AP)**: ESP32-CAM tạo một mạng WiFi riêng
- **Live Streaming**: Phát video trực tiếp định dạng MJPEG
- **Web Server**: Cung cấp giao diện web để xem video
- **Hỗ trợ nhiều loại board**: AI-Thinker ESP32-CAM, ESP-EYE, WROVER-KIT, TTGO T-Journal

---

## CẤU TRÚC DỰ ÁN

```
esp32-cam-streaming/
├── main/                          # Thư mục mã nguồn chính
│   ├── main.c                     # File chính của ứng dụng
│   ├── connect_wifi.c             # Xử lý kết nối WiFi (AP mode)
│   ├── connect_wifi.h             # Header file cho WiFi
│   ├── camera_pins.h              # Định nghĩa chân GPIO cho các board khác nhau
│   ├── CMakeLists.txt             # Cấu hình build cho thư mục main
│   ├── component.mk               # Makefile cho component
│   └── Kconfig.projbuild          # Menu cấu hình dự án
├── components/                    # Thư viện bên ngoài
│   └── esp32-camera/              # Driver camera ESP32 chính thức
├── managed_components/            # Component được quản lý tự động
│   └── espressif__esp_jpeg/       # Thư viện xử lý JPEG
├── CMakeLists.txt                 # Cấu hình build chính
├── sdkconfig                      # File cấu hình SDK
└── README.md                      # File này

```

---

## PHÂN TÍCH CHI TIẾT CÁC FILE


### 1. FILE `main/main.c` - TIM CHÍNH CỦA ỨNG DỤNG

Đây là file quan trọng nhất, chứa toàn bộ logic chính của ứng dụng.

#### **Các thành phần chính:**

##### A. Định nghĩa hằng số MJPEG Stream
```c
#define PART_BOUNDARY "123456789000000000000987654321"
static const char* _STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=" PART_BOUNDARY;
static const char* _STREAM_BOUNDARY = "\r\n--" PART_BOUNDARY "\r\n";
static const char* _STREAM_PART = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";
```
- **Mục đích**: Định nghĩa các header HTTP cho MJPEG streaming
- **PART_BOUNDARY**: Chuỗi phân cách giữa các frame ảnh
- **_STREAM_CONTENT_TYPE**: Loại nội dung multipart để browser hiểu đây là video stream
- **_STREAM_BOUNDARY**: Chuỗi ranh giới giữa các frame
- **_STREAM_PART**: Header cho mỗi frame JPEG

##### B. Hàm `init_camera()` - Khởi tạo Camera
```c
static esp_err_t init_camera(void)
```
**Chức năng**: Cấu hình và khởi tạo camera module

**Các tham số cấu hình quan trọng:**
- **GPIO pins**: Cấu hình các chân kết nối với camera (từ file camera_pins.h)
- **xclk_freq_hz**: Tần số clock 20MHz cho camera
- **pixel_format**: PIXFORMAT_JPEG - định dạng ảnh JPEG
- **frame_size**: FRAMESIZE_VGA (640x480 pixels)
- **jpeg_quality**: 10 (0-63, số càng thấp chất lượng càng cao)
- **fb_count**: 1 (số lượng frame buffer)
- **grab_mode**: CAMERA_GRAB_WHEN_EMPTY (chế độ lấy frame)

**Luồng xử lý:**
1. Tạo cấu trúc `camera_config_t` với các thông số
2. Gọi `esp_camera_init()` để khởi tạo driver camera
3. Kiểm tra lỗi và trả về kết quả


##### C. Hàm `jpg_stream_httpd_handler()` - Xử lý HTTP Stream
```c
esp_err_t jpg_stream_httpd_handler(httpd_req_t *req)
```
**Chức năng**: Đây là handler chính xử lý request HTTP và gửi video stream

**Luồng xử lý chi tiết:**

1. **Thiết lập HTTP Response Header**
   ```c
   res = httpd_resp_set_type(req, _STREAM_CONTENT_TYPE);
   ```
   - Đặt Content-Type là multipart/x-mixed-replace để browser hiểu đây là stream

2. **Vòng lặp vô hạn gửi frame**
   ```c
   while(true) {
   ```
   - Liên tục lấy và gửi frame cho đến khi client ngắt kết nối

3. **Lấy frame từ camera**
   ```c
   fb = esp_camera_fb_get();
   ```
   - Lấy một frame buffer từ camera
   - Nếu thất bại, thoát vòng lặp

4. **Xử lý chuyển đổi định dạng (nếu cần)**
   ```c
   if(fb->format != PIXFORMAT_JPEG) {
       bool jpeg_converted = frame2jpg(fb, 80, &_jpg_buf, &_jpg_buf_len);
   }
   ```
   - Nếu frame không phải JPEG, chuyển đổi sang JPEG
   - Chất lượng nén: 80%

5. **Gửi boundary**
   ```c
   res = httpd_resp_send_chunk(req, _STREAM_BOUNDARY, strlen(_STREAM_BOUNDARY));
   ```
   - Gửi chuỗi phân cách giữa các frame

6. **Gửi header của frame**
   ```c
   size_t hlen = snprintf(part_buf, 64, _STREAM_PART, _jpg_buf_len);
   res = httpd_resp_send_chunk(req, part_buf, hlen);
   ```
   - Gửi Content-Type và Content-Length cho frame

7. **Gửi dữ liệu ảnh JPEG**
   ```c
   res = httpd_resp_send_chunk(req, (const char *)_jpg_buf, _jpg_buf_len);
   ```
   - Gửi dữ liệu ảnh thực tế

8. **Giải phóng bộ nhớ**
   ```c
   esp_camera_fb_return(fb);
   ```
   - Trả frame buffer về cho driver để tái sử dụng

9. **Tính toán và log FPS**
   ```c
   int64_t frame_time = fr_end - last_frame;
   ESP_LOGI(TAG, "MJPG: %uKB %ums (%.1ffps)", ...);
   ```
   - Tính thời gian xử lý mỗi frame
   - Tính FPS (frames per second)
   - Log thông tin ra console


##### D. Hàm `setup_server()` - Khởi tạo HTTP Server
```c
httpd_handle_t setup_server(void)
```
**Chức năng**: Tạo và cấu hình HTTP server

**Luồng xử lý:**
1. Tạo cấu hình mặc định cho HTTP server
2. Khởi động server với `httpd_start()`
3. Đăng ký URI handler cho đường dẫn "/" (root)
4. Trả về handle của server

**URI Configuration:**
```c
httpd_uri_t uri_get = {
    .uri = "/",                          // Đường dẫn root
    .method = HTTP_GET,                  // Phương thức GET
    .handler = jpg_stream_httpd_handler, // Handler xử lý
    .user_ctx = NULL
};
```

##### E. Hàm `app_main()` - Điểm khởi đầu ứng dụng
```c
void app_main()
```
**Chức năng**: Hàm main của ESP-IDF, được gọi khi khởi động

**Luồng thực thi tuần tự:**

1. **Khởi tạo NVS (Non-Volatile Storage)**
   ```c
   esp_err_t ret = nvs_flash_init();
   ```
   - Khởi tạo bộ nhớ flash để lưu cấu hình WiFi
   - Nếu lỗi, xóa và khởi tạo lại

2. **Khởi động WiFi AP Mode**
   ```c
   connect_wifi();
   ```
   - Gọi hàm từ connect_wifi.c
   - Tạo Access Point với SSID và password

3. **Khởi tạo Camera**
   ```c
   err = init_camera();
   ```
   - Cấu hình và khởi động camera module
   - Kiểm tra lỗi, nếu thất bại thì dừng

4. **Khởi động Web Server**
   ```c
   setup_server();
   ```
   - Tạo HTTP server
   - Đăng ký handler cho streaming

5. **Log thông báo hoàn tất**
   ```c
   ESP_LOGI(TAG, "ESP32 CAM Web Server is up and running (AP mode: 192.168.4.1)");
   ```
   - Thông báo server đã sẵn sàng
   - IP mặc định của AP: 192.168.4.1


---

### 2. FILE `main/connect_wifi.c` - XỬ LÝ KẾT NỐI WIFI

#### **Chức năng**: Cấu hình ESP32 hoạt động ở chế độ Access Point (AP)

#### **Các hằng số cấu hình:**
```c
#define WIFI_AP_SSID "ESP32_CAM_AP"      // Tên WiFi
#define WIFI_AP_PASSWORD "12345678"      // Mật khẩu (tối thiểu 8 ký tự)
#define MAX_STA_CONN 4                   // Số client tối đa có thể kết nối
```

#### **Hàm `connect_wifi()` - Luồng xử lý chi tiết:**

1. **Khởi tạo TCP/IP Stack**
   ```c
   ESP_ERROR_CHECK(esp_netif_init());
   ```
   - Khởi tạo network interface layer
   - Cần thiết cho mọi kết nối mạng

2. **Tạo Event Loop**
   ```c
   ESP_ERROR_CHECK(esp_event_loop_create_default());
   ```
   - Tạo vòng lặp xử lý sự kiện hệ thống
   - Xử lý các event như WiFi connect/disconnect

3. **Tạo WiFi AP Interface**
   ```c
   esp_netif_create_default_wifi_ap();
   ```
   - Tạo network interface cho chế độ AP
   - Cấu hình IP mặc định: 192.168.4.1

4. **Khởi tạo WiFi Driver**
   ```c
   wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
   ESP_ERROR_CHECK(esp_wifi_init(&cfg));
   ```
   - Khởi tạo WiFi với cấu hình mặc định
   - Cấp phát bộ nhớ cho WiFi driver

5. **Cấu hình WiFi AP**
   ```c
   wifi_config_t wifi_config = {0};
   strcpy((char *)wifi_config.ap.ssid, WIFI_AP_SSID);
   wifi_config.ap.ssid_len = strlen(WIFI_AP_SSID);
   strcpy((char *)wifi_config.ap.password, WIFI_AP_PASSWORD);
   wifi_config.ap.max_connection = MAX_STA_CONN;
   wifi_config.ap.authmode = WIFI_AUTH_WPA_WPA2_PSK;
   ```
   - Thiết lập SSID và password
   - Giới hạn số lượng client
   - Chế độ bảo mật: WPA/WPA2-PSK

6. **Áp dụng cấu hình và khởi động**
   ```c
   ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_AP));
   ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_AP, &wifi_config));
   ESP_ERROR_CHECK(esp_wifi_start());
   ```
   - Đặt chế độ WiFi là AP
   - Áp dụng cấu hình
   - Khởi động WiFi

7. **Log thông tin**
   ```c
   ESP_LOGI(TAG, "Wi-Fi AP started. SSID:%s password:%s", WIFI_AP_SSID, WIFI_AP_PASSWORD);
   ESP_LOGI(TAG, "AP IP address: 192.168.4.1");
   ```


---

### 3. FILE `main/camera_pins.h` - ĐỊNH NGHĨA CHÂN GPIO

#### **Chức năng**: Định nghĩa mapping GPIO cho các loại board ESP32-CAM khác nhau

#### **Các board được hỗ trợ:**

##### A. **AI-Thinker ESP32-CAM** (CONFIG_BOARD_ESP32CAM_AITHINKER)
```c
#define CAM_PIN_PWDN 32      // Power down pin
#define CAM_PIN_RESET -1     // Reset (software reset)
#define CAM_PIN_XCLK 0       // External clock
#define CAM_PIN_SIOD 26      // I2C Data (SCCB)
#define CAM_PIN_SIOC 27      // I2C Clock (SCCB)

// Data pins (8-bit parallel interface)
#define CAM_PIN_D7 35
#define CAM_PIN_D6 34
#define CAM_PIN_D5 39
#define CAM_PIN_D4 36
#define CAM_PIN_D3 21
#define CAM_PIN_D2 19
#define CAM_PIN_D1 18
#define CAM_PIN_D0 5

// Sync pins
#define CAM_PIN_VSYNC 25     // Vertical sync
#define CAM_PIN_HREF 23      // Horizontal reference
#define CAM_PIN_PCLK 22      // Pixel clock
```

**Giải thích các chân:**
- **PWDN (Power Down)**: Điều khiển nguồn camera (GPIO 32)
- **RESET**: Reset camera (-1 = không sử dụng, dùng software reset)
- **XCLK**: Tín hiệu clock cung cấp cho camera (GPIO 0)
- **SIOD/SIOC**: Giao tiếp I2C (SCCB) để cấu hình camera
- **D0-D7**: 8 chân dữ liệu song song từ camera
- **VSYNC**: Đồng bộ dọc (báo hiệu bắt đầu frame mới)
- **HREF**: Đồng bộ ngang (báo hiệu dòng dữ liệu hợp lệ)
- **PCLK**: Clock cho việc đọc dữ liệu pixel

##### B. **Freenove ESP32-WROVER CAM** (CONFIG_BOARD_WROVER_KIT)
- Mapping GPIO khác cho board WROVER
- XCLK ở GPIO 21 thay vì GPIO 0

##### C. **ESP-EYE** (CONFIG_BOARD_CAMERA_MODEL_ESP_EYE)
- Board chính thức của Espressif
- Có mapping GPIO riêng

##### D. **TTGO T-Journal** (CONFIG_BOARD_CAMERA_MODEL_TTGO_T_JOURNAL)
- Board của TTGO
- Mapping GPIO khác biệt

**Lưu ý**: Chỉ một trong các define CONFIG_BOARD_* được kích hoạt thông qua menuconfig


---

### 4. FILE `main/CMakeLists.txt` - CẤU HÌNH BUILD

```cmake
set(srcs "main.c"
         "connect_wifi.c")
idf_component_register(SRCS ${srcs}
                    INCLUDE_DIRS ".")
```

**Chức năng**: 
- Khai báo các file source cần biên dịch
- Đăng ký component với ESP-IDF build system
- Thiết lập thư mục include

---

### 5. FILE `CMakeLists.txt` (Root) - CẤU HÌNH DỰ ÁN

```cmake
cmake_minimum_required(VERSION 3.16)

set(EXTRA_COMPONENT_DIRS
    ${CMAKE_CURRENT_SOURCE_DIR}/components
)

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(esp32_cam_http_stream)
```

**Chức năng**:
- Yêu cầu CMake phiên bản tối thiểu 3.16
- Thêm thư mục `components` vào đường dẫn tìm kiếm component
- Include build system của ESP-IDF
- Đặt tên dự án: `esp32_cam_http_stream`

---

### 6. FILE `main/Kconfig.projbuild` - MENU CẤU HÌNH

#### **Chức năng**: Tạo menu cấu hình trong `idf.py menuconfig`

#### **Các tùy chọn cấu hình:**

##### A. WiFi Setting (Hiện không sử dụng trong code)
```
config ESPCAM_WIFI_SSID
    string "WiFi SSID"
    default "myssid"

config ESPCAM_WIFI_PASSWORD
    string "WiFi Password"
    default "mypassword"

config ESPCAM_MAXIMUM_RETRY
    int "Maximum retry"
    default 5
```
**Lưu ý**: Các config này được định nghĩa nhưng code hiện tại không sử dụng (dùng hardcode trong connect_wifi.c)

##### B. Board Selection
```
choice BOARD
    bool "Select Board"
    default BOARD_ESP32CAM_AITHINKER
```

**Các lựa chọn:**
- `BOARD_WROVER_KIT`: Freenove ESP32-WROVER CAM
- `BOARD_CAMERA_MODEL_ESP_EYE`: Espressif ESP-EYE
- `BOARD_ESP32CAM_AITHINKER`: AI-Thinker ESP32-CAM (mặc định)
- `BOARD_CAMERA_MODEL_TTGO_T_JOURNAL`: TTGO T-Journal

**Cách sử dụng**: Chạy `idf.py menuconfig` → Application Configuration → Select Board


---

### 7. COMPONENT `esp32-camera` - DRIVER CAMERA

#### **Vị trí**: `components/esp32-camera/`

#### **Chức năng**: Thư viện driver chính thức của Espressif cho camera module

#### **Các sensor được hỗ trợ:**
- **OV2640**: 1600x1200, phổ biến nhất trên ESP32-CAM
- **OV3660**: 2048x1536
- **OV5640**: 2592x1944
- **OV7670**: 640x480
- **OV7725**: 640x480
- **NT99141**: 1280x720
- **GC032A, GC0308, GC2145**: Các sensor GalaxyCore
- **BF3005, BF20A6**: Các sensor BYD
- **SC101IOT, SC030IOT, SC031GS**: Các sensor SmartSens
- **HM0360, HM1055**: Các sensor Himax

#### **Các định dạng đầu ra:**
- **JPEG**: Nén, tiết kiệm băng thông (được dùng trong dự án này)
- **RGB565/555**: RGB 16-bit
- **YUV422/420**: Format video
- **RAW**: Dữ liệu thô từ sensor
- **Grayscale**: Ảnh xám

#### **Các file quan trọng:**
- `driver/esp_camera.c`: Driver chính
- `driver/sensor.c`: Xử lý sensor
- `conversions/to_jpg.cpp`: Chuyển đổi sang JPEG
- `sensors/ov2640.c`: Driver cho OV2640 (sensor phổ biến nhất)

---

### 8. COMPONENT `espressif__esp_jpeg` - THƯ VIỆN JPEG

#### **Vị trí**: `managed_components/espressif__esp_jpeg/`

#### **Chức năng**: 
- Thư viện xử lý JPEG encoding/decoding
- Được quản lý tự động bởi ESP-IDF component manager
- Hỗ trợ nén và giải nén ảnh JPEG
- Sử dụng trong hàm `frame2jpg()` để chuyển đổi frame sang JPEG


---

## LUỒNG XỬ LÝ TỔNG THỂ CỦA HỆ THỐNG

### **Sơ đồ luồng hoạt động:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    1. KHỞI ĐỘNG HỆ THỐNG                        │
│                         app_main()                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    2. KHỞI TẠO NVS FLASH                        │
│                      nvs_flash_init()                            │
│  - Khởi tạo bộ nhớ flash để lưu cấu hình                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                 3. KHỞI ĐỘNG WIFI AP MODE                       │
│                      connect_wifi()                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ a. Khởi tạo TCP/IP stack                                 │  │
│  │ b. Tạo event loop                                        │  │
│  │ c. Tạo WiFi AP interface                                 │  │
│  │ d. Khởi tạo WiFi driver                                  │  │
│  │ e. Cấu hình AP (SSID: ESP32_CAM_AP, Pass: 12345678)    │  │
│  │ f. Khởi động WiFi → IP: 192.168.4.1                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    4. KHỞI TẠO CAMERA                           │
│                      init_camera()                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ a. Cấu hình GPIO pins (từ camera_pins.h)                │  │
│  │ b. Thiết lập thông số:                                   │  │
│  │    - Độ phân giải: VGA (640x480)                        │  │
│  │    - Format: JPEG                                        │  │
│  │    - Chất lượng: 10                                      │  │
│  │    - Clock: 20MHz                                        │  │
│  │ c. Gọi esp_camera_init()                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  5. KHỞI ĐỘNG WEB SERVER                        │
│                      setup_server()                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ a. Tạo HTTP server với cấu hình mặc định                │  │
│  │ b. Đăng ký URI handler cho "/"                          │  │
│  │ c. Handler: jpg_stream_httpd_handler                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              6. HỆ THỐNG SẴN SÀNG - CHỜ CLIENT                 │
│         Log: "ESP32 CAM Web Server is up and running"          │
└─────────────────────────────────────────────────────────────────┘
```


### **Luồng xử lý khi Client truy cập:**

```
┌─────────────────────────────────────────────────────────────────┐
│          CLIENT MỞ TRÌNH DUYỆT: http://192.168.4.1/            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│            HTTP SERVER NHẬN REQUEST TẠI URI "/"                 │
│              Gọi: jpg_stream_httpd_handler()                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│         1. GỬI HTTP HEADER (Content-Type: multipart)           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    2. BẮT ĐẦU VÒNG LẶP STREAM                   │
│                         while(true)                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  a. LẤY FRAME TỪ CAMERA                                  │  │
│  │     fb = esp_camera_fb_get()                             │  │
│  │     - Đợi camera capture một frame                       │  │
│  │     - Nhận frame buffer                                  │  │
│  │                                                           │  │
│  │  b. KIỂM TRA VÀ CHUYỂN ĐỔI ĐỊNH DẠNG                    │  │
│  │     if (fb->format != PIXFORMAT_JPEG)                    │  │
│  │        frame2jpg() → chuyển sang JPEG                    │  │
│  │                                                           │  │
│  │  c. GỬI BOUNDARY                                         │  │
│  │     httpd_resp_send_chunk("\r\n--BOUNDARY\r\n")         │  │
│  │                                                           │  │
│  │  d. GỬI HEADER CỦA FRAME                                 │  │
│  │     "Content-Type: image/jpeg"                           │  │
│  │     "Content-Length: [size]"                             │  │
│  │                                                           │  │
│  │  e. GỬI DỮ LIỆU JPEG                                     │  │
│  │     httpd_resp_send_chunk(jpeg_data, jpeg_size)          │  │
│  │                                                           │  │
│  │  f. GIẢI PHÓNG FRAME BUFFER                              │  │
│  │     esp_camera_fb_return(fb)                             │  │
│  │                                                           │  │
│  │  g. TÍNH TOÁN FPS                                        │  │
│  │     frame_time = current_time - last_frame_time          │  │
│  │     fps = 1000 / frame_time                              │  │
│  │     Log: "MJPG: XXkB XXms (XX.Xfps)"                     │  │
│  │                                                           │  │
│  │  h. LẶP LẠI (quay về bước a)                             │  │
│  │                                                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │ (Lặp liên tục cho đến khi...)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│         CLIENT ĐÓNG TRÌNH DUYỆT HOẶC MẤT KẾT NỐI              │
│              httpd_resp_send_chunk() trả về lỗi                 │
│                    Thoát vòng lặp while                         │
│                    Kết thúc stream                              │
└─────────────────────────────────────────────────────────────────┘
```


---

## CHI TIẾT KỸ THUẬT

### **1. Giao thức MJPEG Streaming**

MJPEG (Motion JPEG) là phương pháp streaming video bằng cách gửi liên tiếp các ảnh JPEG.

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

**Ưu điểm:**
- Đơn giản, dễ implement
- Tương thích tốt với browser
- Không cần codec phức tạp
- Mỗi frame độc lập

**Nhược điểm:**
- Băng thông cao hơn H.264/H.265
- Không có nén inter-frame
- FPS thấp hơn các codec hiện đại

### **2. Camera Interface**

ESP32 sử dụng giao diện **DVP (Digital Video Port)** 8-bit song song:

**Các tín hiệu:**
- **D0-D7**: 8 bit dữ liệu song song
- **PCLK**: Pixel clock - đồng bộ đọc dữ liệu
- **VSYNC**: Vertical sync - báo bắt đầu frame mới
- **HREF**: Horizontal reference - báo dòng dữ liệu hợp lệ
- **XCLK**: Master clock cấp cho camera (20MHz)
- **SIOD/SIOC**: I2C (SCCB) để cấu hình camera

**Quy trình capture:**
1. Camera sensor capture ảnh
2. Sensor xử lý và output qua 8-bit parallel
3. ESP32 đọc dữ liệu theo PCLK
4. VSYNC báo hiệu frame mới
5. HREF báo hiệu dữ liệu hợp lệ
6. Dữ liệu được lưu vào frame buffer

### **3. Quản lý bộ nhớ**

**Frame Buffer:**
- Mỗi frame VGA JPEG ≈ 15-30KB
- Sử dụng PSRAM (nếu có) để lưu frame buffer
- `fb_count = 1`: Chế độ single buffer (tiết kiệm RAM)
- `fb_count = 2+`: Chế độ continuous (FPS cao hơn)

**Chu trình bộ nhớ:**
```
Camera → Frame Buffer → HTTP Send → Return Buffer → Camera
```

**Lưu ý quan trọng:**
- Phải gọi `esp_camera_fb_return(fb)` sau khi xử lý xong
- Không return sẽ gây memory leak
- PSRAM cần thiết cho độ phân giải > CIF (không dùng JPEG)


### **4. Hiệu năng và FPS**

**Các yếu tố ảnh hưởng đến FPS:**

1. **Độ phân giải:**
   - QVGA (320x240): ~25-30 FPS
   - VGA (640x480): ~15-20 FPS (dự án này)
   - SVGA (800x600): ~10-15 FPS
   - XGA (1024x768): ~5-10 FPS

2. **Chất lượng JPEG:**
   - Quality 10 (high): Frame lớn hơn, FPS thấp hơn
   - Quality 30 (medium): Cân bằng
   - Quality 50 (low): Frame nhỏ, FPS cao hơn

3. **WiFi:**
   - Băng thông WiFi ảnh hưởng trực tiếp
   - AP mode thường ổn định hơn STA mode
   - Khoảng cách và nhiễu ảnh hưởng

4. **Frame Buffer Count:**
   - `fb_count = 1`: FPS thấp hơn nhưng ổn định
   - `fb_count = 2`: FPS cao hơn, tốn RAM hơn

**Tối ưu hóa:**
- Giảm độ phân giải nếu cần FPS cao
- Tăng jpeg_quality (số lớn hơn) để giảm kích thước frame
- Sử dụng PSRAM
- Tắt các tính năng không cần thiết (Bluetooth, etc.)

### **5. Cấu hình sdkconfig quan trọng**

Từ file `sdkconfig`, các cấu hình quan trọng:

```ini
# Board và chip
CONFIG_IDF_TARGET="esp32"
CONFIG_BOARD_ESP32CAM_AITHINKER=y

# Flash
CONFIG_ESPTOOLPY_FLASHSIZE="2MB"
CONFIG_ESPTOOLPY_FLASHFREQ_40M=y
CONFIG_ESPTOOLPY_FLASHMODE_DIO=y

# WiFi
CONFIG_ESP_WIFI_SSID="myssid"           # Không dùng trong code
CONFIG_ESP_WIFI_PASSWORD="mypassword"   # Không dùng trong code

# Compiler
CONFIG_COMPILER_OPTIMIZATION_DEBUG=y    # Tối ưu cho debug

# PSRAM (quan trọng cho camera)
CONFIG_ESP32_SPIRAM_SUPPORT=y           # Bật PSRAM nếu có

# Partition
CONFIG_PARTITION_TABLE_SINGLE_APP=y     # Single app partition
```

**Lưu ý:**
- PSRAM rất quan trọng cho độ phân giải cao
- Flash 2MB đủ cho ứng dụng cơ bản
- Optimization debug giúp dễ debug nhưng chậm hơn


---

## HƯỚNG DẪN SỬ DỤNG

### **Yêu cầu phần cứng:**
- ESP32-CAM (AI-Thinker hoặc tương tự)
- Camera module OV2640 (thường đi kèm)
- Nguồn 5V ổn định (tối thiểu 500mA)
- USB to Serial adapter (để nạp code)

### **Yêu cầu phần mềm:**
- ESP-IDF v5.5.1 hoặc mới hơn
- Python 3.7+
- Git

### **Các bước cài đặt và chạy:**

#### **1. Cài đặt ESP-IDF**
```bash
# Clone ESP-IDF
git clone -b v5.5.1 --recursive https://github.com/espressif/esp-idf.git
cd esp-idf
./install.sh

# Kích hoạt môi trường
. ./export.sh
```

#### **2. Clone dự án**
```bash
git clone <repository-url>
cd esp32-cam-streaming
```

#### **3. Cấu hình dự án**
```bash
idf.py menuconfig
```

**Các cấu hình cần kiểm tra:**
- `Application Configuration` → `Select Board` → Chọn board của bạn
- `Component config` → `ESP32-specific` → `Support for external, SPI-connected RAM` (nếu có PSRAM)
- `Serial flasher config` → Cấu hình port và baudrate

#### **4. Build dự án**
```bash
idf.py build
```

#### **5. Nạp code vào ESP32-CAM**

**Kết nối phần cứng:**
- GPIO0 → GND (để vào chế độ flash)
- 5V → 5V
- GND → GND
- U0TXD → RX của USB-Serial
- U0RXD → TX của USB-Serial

```bash
idf.py -p /dev/ttyUSB0 flash
```
(Thay `/dev/ttyUSB0` bằng port của bạn, Windows: `COM3`, `COM4`, etc.)

#### **6. Xem log**
```bash
idf.py -p /dev/ttyUSB0 monitor
```

**Sau khi nạp xong:**
- Ngắt kết nối GPIO0 khỏi GND
- Reset ESP32-CAM
- Xem log để kiểm tra


#### **7. Kết nối và xem video**

**Bước 1: Kết nối WiFi**
- Mở danh sách WiFi trên điện thoại/laptop
- Tìm mạng WiFi: `ESP32_CAM_AP`
- Mật khẩu: `12345678`
- Kết nối vào mạng này

**Bước 2: Mở trình duyệt**
- Mở trình duyệt web (Chrome, Firefox, Safari, etc.)
- Truy cập: `http://192.168.4.1/`
- Video stream sẽ hiển thị tự động

**Bước 3: Kiểm tra log**
```
I (12345) Connect_WiFi_AP: Wi-Fi AP started. SSID:ESP32_CAM_AP password:12345678
I (12346) Connect_WiFi_AP: AP IP address: 192.168.4.1
I (12456) esp32-cam Webserver: ESP32 CAM Web Server is up and running (AP mode: 192.168.4.1)
I (15678) esp32-cam Webserver: MJPG: 18KB 65ms (15.4fps)
I (15743) esp32-cam Webserver: MJPG: 18KB 64ms (15.6fps)
```

---

## TROUBLESHOOTING (XỬ LÝ LỖI)

### **1. Camera init failed**
**Nguyên nhân:**
- Kết nối camera không đúng
- Camera bị hỏng
- Chọn sai board trong menuconfig

**Giải pháp:**
- Kiểm tra lại kết nối camera
- Đảm bảo chọn đúng board: `idf.py menuconfig` → Application Configuration → Select Board
- Thử reset camera bằng cách ngắt nguồn

### **2. Brownout detector triggered**
**Nguyên nhân:**
- Nguồn cung cấp không đủ mạnh
- Dòng điện không ổn định

**Giải pháp:**
- Sử dụng nguồn 5V/1A trở lên
- Không cấp nguồn qua USB của máy tính (thường yếu)
- Thêm tụ lọc 100-470uF gần chân nguồn

### **3. WiFi không xuất hiện**
**Nguyên nhân:**
- Code chưa chạy đến phần WiFi
- Lỗi khởi tạo WiFi

**Giải pháp:**
- Kiểm tra log qua `idf.py monitor`
- Đảm bảo không có lỗi trước khi khởi tạo WiFi
- Reset ESP32-CAM

### **4. Không kết nối được vào 192.168.4.1**
**Nguyên nhân:**
- Chưa kết nối vào WiFi ESP32_CAM_AP
- Firewall chặn
- IP không đúng

**Giải pháp:**
- Đảm bảo đã kết nối vào WiFi `ESP32_CAM_AP`
- Tắt VPN nếu đang bật
- Kiểm tra IP trong log
- Thử ping: `ping 192.168.4.1`

### **5. Video bị giật, FPS thấp**
**Nguyên nhân:**
- Độ phân giải quá cao
- Chất lượng JPEG quá cao
- WiFi yếu

**Giải pháp:**
- Giảm độ phân giải: `FRAMESIZE_VGA` → `FRAMESIZE_QVGA`
- Tăng jpeg_quality: `10` → `20` hoặc `30`
- Di chuyển gần ESP32-CAM hơn


### **6. Lỗi "Camera capture failed"**
**Nguyên nhân:**
- Camera không phản hồi
- Lỗi I2C communication
- Camera bị treo

**Giải pháp:**
- Reset ESP32-CAM
- Kiểm tra kết nối SIOD/SIOC (I2C)
- Thử giảm XCLK frequency: `20000000` → `10000000`

### **7. Lỗi "JPEG compression failed"**
**Nguyên nhân:**
- Không đủ RAM
- Lỗi thư viện JPEG

**Giải pháp:**
- Đảm bảo PSRAM được bật (nếu có)
- Giảm độ phân giải
- Kiểm tra component esp_jpeg đã được cài đúng

---

## TÙY CHỈNH VÀ MỞ RỘNG

### **1. Thay đổi SSID và Password WiFi**

Sửa file `main/connect_wifi.c`:
```c
#define WIFI_AP_SSID "TenWiFiCuaBan"
#define WIFI_AP_PASSWORD "MatKhauCuaBan"  // Tối thiểu 8 ký tự
```

### **2. Thay đổi độ phân giải**

Sửa file `main/main.c`, hàm `init_camera()`:
```c
.frame_size = FRAMESIZE_QVGA,  // Thay VGA bằng QVGA (320x240)
```

**Các lựa chọn:**
- `FRAMESIZE_QQVGA`: 160x120
- `FRAMESIZE_QVGA`: 320x240
- `FRAMESIZE_CIF`: 352x288
- `FRAMESIZE_VGA`: 640x480 (mặc định)
- `FRAMESIZE_SVGA`: 800x600
- `FRAMESIZE_XGA`: 1024x768
- `FRAMESIZE_SXGA`: 1280x1024
- `FRAMESIZE_UXGA`: 1600x1200

### **3. Thay đổi chất lượng JPEG**

Sửa file `main/main.c`, hàm `init_camera()`:
```c
.jpeg_quality = 20,  // 0-63, số càng cao chất lượng càng thấp
```

**Gợi ý:**
- `10`: Chất lượng cao, file lớn, FPS thấp
- `20`: Chất lượng tốt, cân bằng (khuyến nghị)
- `30`: Chất lượng trung bình, FPS cao hơn
- `40-50`: Chất lượng thấp, FPS cao

### **4. Thêm authentication (bảo mật)**

Thêm vào `main/main.c`, trong hàm `jpg_stream_httpd_handler()`:
```c
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


### **5. Thêm LED flash control**

Thêm vào `main/main.c`:
```c
#define LED_PIN 4  // GPIO4 là LED flash trên AI-Thinker

// Trong app_main(), sau init_camera():
gpio_set_direction(LED_PIN, GPIO_MODE_OUTPUT);
gpio_set_level(LED_PIN, 0);  // Tắt LED

// Tạo handler mới để bật/tắt LED:
esp_err_t led_control_handler(httpd_req_t *req) {
    char buf[100];
    int ret = httpd_req_recv(req, buf, sizeof(buf));
    
    if (strstr(buf, "on")) {
        gpio_set_level(LED_PIN, 1);
    } else {
        gpio_set_level(LED_PIN, 0);
    }
    
    httpd_resp_send(req, "OK", 2);
    return ESP_OK;
}

// Đăng ký URI:
httpd_uri_t uri_led = {
    .uri = "/led",
    .method = HTTP_GET,
    .handler = led_control_handler,
    .user_ctx = NULL
};
httpd_register_uri_handler(stream_httpd, &uri_led);
```

**Sử dụng:**
- Bật LED: `http://192.168.4.1/led?on`
- Tắt LED: `http://192.168.4.1/led?off`

### **6. Chuyển sang Station Mode (kết nối WiFi có sẵn)**

Sửa file `main/connect_wifi.c`:
```c
void connect_wifi(void) {
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    
    // Tạo STA interface thay vì AP
    esp_netif_create_default_wifi_sta();
    
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    
    wifi_config_t wifi_config = {
        .sta = {
            .ssid = "TenWiFiNhaBan",
            .password = "MatKhauWiFi",
        },
    };
    
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());
    ESP_ERROR_CHECK(esp_wifi_connect());
    
    // Đợi kết nối và lấy IP
    // (Cần thêm event handler để xử lý)
}
```

### **7. Lưu ảnh snapshot**

Thêm handler mới để chụp ảnh tĩnh:
```c
esp_err_t capture_handler(httpd_req_t *req) {
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
        httpd_resp_send_500(req);
        return ESP_FAIL;
    }
    
    httpd_resp_set_type(req, "image/jpeg");
    httpd_resp_set_hdr(req, "Content-Disposition", "inline; filename=capture.jpg");
    httpd_resp_send(req, (const char *)fb->buf, fb->len);
    
    esp_camera_fb_return(fb);
    return ESP_OK;
}

// Đăng ký:
httpd_uri_t uri_capture = {
    .uri = "/capture",
    .method = HTTP_GET,
    .handler = capture_handler,
    .user_ctx = NULL
};
```

**Sử dụng:** `http://192.168.4.1/capture` để lấy ảnh tĩnh


---

## THÔNG TIN KỸ THUẬT BỔ SUNG

### **Thông số kỹ thuật ESP32-CAM:**
- **SoC**: ESP32-DOWDQ6 (dual-core 240MHz)
- **Flash**: 4MB (thường)
- **PSRAM**: 4MB (nếu có)
- **WiFi**: 802.11 b/g/n (2.4GHz)
- **Bluetooth**: BLE 4.2 (không dùng trong dự án này)
- **Camera Interface**: DVP 8-bit
- **GPIO**: Hạn chế do camera chiếm nhiều pin

### **Tiêu thụ điện:**
- **Idle**: ~50mA
- **WiFi active**: ~150-200mA
- **Camera + WiFi streaming**: ~300-400mA
- **Peak**: ~500mA

**Khuyến nghị nguồn:** 5V/1A trở lên

### **Nhiệt độ hoạt động:**
- **Bình thường**: 40-60°C
- **Cảnh báo**: >70°C
- **Giải pháp**: Thêm tản nhiệt nếu chạy liên tục

### **Khoảng cách WiFi:**
- **Indoor**: 10-30m (tùy vật cản)
- **Outdoor**: 50-100m (tầm nhìn thẳng)
- **Khuyến nghị**: <20m cho streaming ổn định

### **Băng thông:**
- **VGA JPEG (quality 10)**: ~1.5-2 Mbps
- **VGA JPEG (quality 20)**: ~1-1.5 Mbps
- **QVGA JPEG**: ~0.5-1 Mbps

### **Độ trễ (Latency):**
- **Tối thiểu**: 100-200ms
- **Trung bình**: 200-500ms
- **Phụ thuộc**: WiFi, độ phân giải, chất lượng JPEG

---

## CẤU TRÚC DỮ LIỆU QUAN TRỌNG

### **1. camera_config_t**
```c
typedef struct {
    int pin_pwdn;              // Power down pin
    int pin_reset;             // Reset pin
    int pin_xclk;              // XCLK pin
    int pin_sccb_sda;          // I2C data
    int pin_sccb_scl;          // I2C clock
    int pin_d7;                // Data bit 7
    int pin_d6;                // Data bit 6
    int pin_d5;                // Data bit 5
    int pin_d4;                // Data bit 4
    int pin_d3;                // Data bit 3
    int pin_d2;                // Data bit 2
    int pin_d1;                // Data bit 1
    int pin_d0;                // Data bit 0
    int pin_vsync;             // VSYNC pin
    int pin_href;              // HREF pin
    int pin_pclk;              // PCLK pin
    int xclk_freq_hz;          // XCLK frequency
    ledc_timer_t ledc_timer;   // LEDC timer
    ledc_channel_t ledc_channel; // LEDC channel
    pixformat_t pixel_format;  // Pixel format
    framesize_t frame_size;    // Frame size
    int jpeg_quality;          // JPEG quality (0-63)
    int fb_count;              // Frame buffer count
    camera_grab_mode_t grab_mode; // Grab mode
} camera_config_t;
```

### **2. camera_fb_t (Frame Buffer)**
```c
typedef struct {
    uint8_t *buf;              // Pointer to frame buffer
    size_t len;                // Length of buffer
    size_t width;              // Image width
    size_t height;             // Image height
    pixformat_t format;        // Pixel format
    struct timeval timestamp;  // Timestamp
} camera_fb_t;
```


---

## CÁC API QUAN TRỌNG

### **Camera APIs:**

```c
// Khởi tạo camera
esp_err_t esp_camera_init(const camera_config_t *config);

// Lấy frame buffer
camera_fb_t *esp_camera_fb_get();

// Trả frame buffer
void esp_camera_fb_return(camera_fb_t *fb);

// Deinitialize camera
esp_err_t esp_camera_deinit();

// Lấy sensor handle
sensor_t *esp_camera_sensor_get();
```

### **HTTP Server APIs:**

```c
// Khởi động server
esp_err_t httpd_start(httpd_handle_t *handle, const httpd_config_t *config);

// Đăng ký URI handler
esp_err_t httpd_register_uri_handler(httpd_handle_t hd, const httpd_uri_t *uri_handler);

// Gửi response
esp_err_t httpd_resp_send(httpd_req_t *r, const char *buf, ssize_t buf_len);

// Gửi chunk (cho streaming)
esp_err_t httpd_resp_send_chunk(httpd_req_t *r, const char *buf, ssize_t buf_len);

// Set response type
esp_err_t httpd_resp_set_type(httpd_req_t *r, const char *type);

// Set response header
esp_err_t httpd_resp_set_hdr(httpd_req_t *r, const char *field, const char *value);
```

### **WiFi APIs:**

```c
// Khởi tạo WiFi
esp_err_t esp_wifi_init(const wifi_init_config_t *config);

// Set WiFi mode
esp_err_t esp_wifi_set_mode(wifi_mode_t mode);

// Set WiFi config
esp_err_t esp_wifi_set_config(wifi_interface_t interface, wifi_config_t *conf);

// Start WiFi
esp_err_t esp_wifi_start();

// Stop WiFi
esp_err_t esp_wifi_stop();
```

### **Conversion APIs:**

```c
// Convert frame to JPEG
bool frame2jpg(camera_fb_t *fb, int quality, uint8_t **out, size_t *out_len);

// Convert frame to BMP
bool frame2bmp(camera_fb_t *fb, uint8_t **out, size_t *out_len);

// Convert JPEG to RGB888
bool jpg2rgb888(const uint8_t *src, size_t src_len, uint8_t *out, jpg_scale_t scale);
```

---

## TÀI LIỆU THAM KHẢO

### **ESP-IDF Documentation:**
- ESP-IDF Programming Guide: https://docs.espressif.com/projects/esp-idf/en/latest/
- ESP32 Technical Reference: https://www.espressif.com/sites/default/files/documentation/esp32_technical_reference_manual_en.pdf

### **ESP32-Camera:**
- GitHub Repository: https://github.com/espressif/esp32-camera
- Component Registry: https://components.espressif.com/components/espressif/esp32-camera

### **Camera Sensors:**
- OV2640 Datasheet: https://www.uctronics.com/download/cam_module/OV2640DS.pdf
- Camera Interface Guide: https://www.espressif.com/sites/default/files/documentation/esp32_camera_sensor_guide_en.pdf

### **HTTP Server:**
- ESP HTTP Server: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/protocols/esp_http_server.html

### **WiFi:**
- ESP32 WiFi Driver: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/network/esp_wifi.html

---

## GIẤY PHÉP (LICENSE)

Dự án này sử dụng các component với giấy phép:
- **ESP-IDF**: Apache License 2.0
- **esp32-camera**: Apache License 2.0
- **esp_jpeg**: Apache License 2.0

---

## LIÊN HỆ VÀ HỖ TRỢ

### **Nguồn tham khảo gốc:**
- Tutorial: https://esp32tutorials.com/esp32-cam-esp-idf-live-streaming-web-server/

### **Community Support:**
- ESP32 Forum: https://esp32.com/
- ESP-IDF GitHub Issues: https://github.com/espressif/esp-idf/issues
- ESP32-Camera GitHub Issues: https://github.com/espressif/esp32-camera/issues

---

## KẾT LUẬN

Dự án ESP32-CAM Web Streaming Server này cung cấp một giải pháp đơn giản nhưng hiệu quả để streaming video từ ESP32-CAM. Với kiến trúc rõ ràng và code dễ hiểu, dự án có thể được mở rộng cho nhiều ứng dụng khác nhau như:

- **Camera giám sát**: Theo dõi nhà cửa, văn phòng
- **Robot điều khiển từ xa**: FPV camera cho robot
- **IoT projects**: Tích hợp với các hệ thống IoT
- **Học tập**: Hiểu về camera interface, HTTP streaming, WiFi

**Ưu điểm:**
✅ Code đơn giản, dễ hiểu
✅ Không cần thư viện phức tạp
✅ Hoạt động độc lập (AP mode)
✅ Dễ tùy chỉnh và mở rộng
✅ Chi phí thấp

**Hạn chế:**
⚠️ FPS không cao (15-20 fps)
⚠️ Độ trễ 200-500ms
⚠️ Chỉ hỗ trợ MJPEG (không phải H.264)
⚠️ Băng thông cao hơn các codec hiện đại

Dự án phù hợp cho các ứng dụng không yêu cầu độ trễ thấp và FPS cao, nhưng cần tính đơn giản và dễ triển khai.

---

**Phiên bản:** 1.0  
**Ngày cập nhật:** 2024  
**ESP-IDF Version:** 5.5.1  
**Board:** ESP32-CAM (AI-Thinker)
