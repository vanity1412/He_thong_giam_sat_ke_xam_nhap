from flask import Flask, render_template, Response, request, jsonify, session, redirect, url_for
import cv2
import numpy as np
import os
import pickle
from datetime import datetime
import time
from email_alert import EmailAlert
from werkzeug.security import generate_password_hash, check_password_hash
import json
import threading
import asyncio
import queue

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

USERS_FILE = 'users.json'

# Admin account
ADMIN_EMAIL = "vvthong.insec@gmail.com"
ADMIN_PASSWORD = "123321"

class UserManager:
    def __init__(self):
        self.users_file = USERS_FILE
        self._lock = threading.Lock()
        self.load_users()
    
    def load_users(self):
        with self._lock:
            if os.path.exists(self.users_file):
                try:
                    with open(self.users_file, 'r', encoding='utf-8') as f:
                        self.users = json.load(f)
                except:
                    self.users = {}
            else:
                self.users = {}
    
    def save_users(self):
        with self._lock:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
    
    def register(self, email, password, name):
        if email in self.users:
            return False, "Email đã tồn tại!"
        
        self.users[email] = {
            'password': generate_password_hash(password),
            'name': name,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.save_users()
        return True, "Đăng ký thành công!"

    def login(self, email, password):
        # Kiểm tra admin
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            return True, "Đăng nhập Admin thành công!"
        
        if email not in self.users:
            return False, "Email không tồn tại!"
        
        if check_password_hash(self.users[email]['password'], password):
            return True, "Đăng nhập thành công!"
        else:
            return False, "Mật khẩu không đúng!"
    
    def get_user(self, email):
        # Admin user
        if email == ADMIN_EMAIL:
            return {'name': 'Administrator', 'created_at': '2024-01-01'}
        return self.users.get(email)
    
    def get_all_users(self):
        """Lấy danh sách tất cả users"""
        return self.users
    
    def delete_user_face(self, email):
        """Xóa dữ liệu khuôn mặt của user"""
        import shutil
        user_dir = os.path.join("face_data", email)
        if os.path.exists(user_dir):
            shutil.rmtree(user_dir)
            return True
        return False
    
    def is_admin(self, email):
        """Kiểm tra có phải admin không"""
        return email == ADMIN_EMAIL


class FaceRecognitionSystem:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.face_data_dir = "face_data"
        self.models_dir = "models"
        
        # Tạo thư mục cần thiết
        for dir_path in [self.face_data_dir, self.models_dir]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
        
        # Model files - dùng shared model cho tất cả user
        self.model_file = os.path.join(self.models_dir, "shared_model.yml")
        self.labels_file = os.path.join(self.models_dir, "shared_labels.pkl")
        
        # Thread lock
        self._lock = threading.Lock()
        
        # Camera
        self.camera = None
        self.registered_faces = {}
        
        # Current user
        self.current_user_email = None
        
        # Registration state
        self.registration_mode = False
        self.registration_count = 0
        self.registration_target = 30
        self.registration_completed = False
        self._last_capture_time = 0
        self._capture_interval = 0.15  # 150ms giữa các lần chụp
        
        # Email alert
        self.email_alert = EmailAlert()
        self.warning_start_time = None
        self.last_email_sent = 0
        self.email_cooldown = 60
        
        # Tracking cho phát hiện an toàn và không phát hiện
        self.safe_detection_start = None
        self.no_detection_start = None
        self.last_safe_email_sent = 0
        self.last_no_detection_email_sent = 0
        
        # Monitoring
        self.monitoring_active = False
        
        # Camera source
        self.esp32_ip = "192.168.4.1"
        self.use_esp32 = False
        self._esp32_stream = None
        self._esp32_frame_queue = queue.Queue(maxsize=5)
        self._esp32_ws_thread = None
        self._esp32_ws_running = False
        
        # Load model nếu có
        self.load_model()

    def set_current_user(self, email):
        """Thiết lập user hiện tại"""
        with self._lock:
            self.current_user_email = email
            self.load_model()
            print(f"📂 User {email} đã đăng nhập")
    
    def set_camera_source(self, source, ip=None):
        """Chọn nguồn camera"""
        with self._lock:
            # Dừng WebSocket cũ nếu có
            if self._esp32_ws_running:
                self._esp32_ws_running = False
                if self._esp32_ws_thread:
                    self._esp32_ws_thread.join(timeout=2)
            
            # Đóng stream ESP32 cũ nếu có
            if self._esp32_stream:
                try:
                    self._esp32_stream.close()
                except:
                    pass
                self._esp32_stream = None
            
            if source == "esp32":
                if ip:
                    self.esp32_ip = ip
                self.use_esp32 = True
                # Khởi động WebSocket thread
                self._start_esp32_websocket()
                print(f"Đã chuyển sang ESP32-CAM: {self.esp32_ip}")
            else:
                self.use_esp32 = False
                print("Đã chuyển sang camera laptop")
    
    def _start_esp32_websocket(self):
        """Khởi động WebSocket thread cho ESP32-CAM"""
        if not self._esp32_ws_running:
            self._esp32_ws_running = True
            self._esp32_ws_thread = threading.Thread(
                target=self._run_esp32_websocket,
                daemon=True
            )
            self._esp32_ws_thread.start()
    
    def _run_esp32_websocket(self):
        """Chạy WebSocket loop trong thread riêng"""
        try:
            asyncio.run(self._esp32_websocket_loop())
        except Exception as e:
            print(f"❌ Lỗi WebSocket thread: {e}")
            self._esp32_ws_running = False
    
    async def _esp32_websocket_loop(self):
        """WebSocket loop để nhận frames từ ESP32-CAM"""
        uri = f"ws://{self.esp32_ip}:81"
        retry_count = 0
        max_retries = 3
        
        while self._esp32_ws_running and retry_count < max_retries:
            try:
                import websockets
                print(f"🔌 Đang kết nối WebSocket tới ESP32-CAM: {uri}")
                async with websockets.connect(uri, ping_timeout=10) as websocket:
                    print("✅ Đã kết nối WebSocket ESP32-CAM")
                    retry_count = 0  # Reset retry khi kết nối thành công
                    
                    while self._esp32_ws_running:
                        try:
                            frame_data = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                            
                            # Lưu frame vào queue - luôn giữ frame mới nhất
                            try:
                                # Nếu queue đầy, xóa frame cũ nhất
                                if self._esp32_frame_queue.full():
                                    try:
                                        self._esp32_frame_queue.get_nowait()
                                    except:
                                        pass
                                self._esp32_frame_queue.put_nowait(frame_data)
                            except:
                                pass
                        
                        except asyncio.TimeoutError:
                            print("⚠️ WebSocket timeout - đang thử lại...")
                            break
                        except Exception as e:
                            print(f"❌ Lỗi nhận frame: {e}")
                            break
            
            except Exception as e:
                retry_count += 1
                print(f"❌ Lỗi kết nối WebSocket (lần {retry_count}/{max_retries}): {e}")
                if retry_count < max_retries and self._esp32_ws_running:
                    await asyncio.sleep(2)  # Đợi trước khi retry
        
        print("🔌 WebSocket ESP32-CAM đã đóng")
        self._esp32_ws_running = False
    
    def get_frame_from_esp32(self):
        """Lấy frame từ ESP32-CAM qua WebSocket hoặc HTTP"""
        if not self.esp32_ip:
            return None
        
        # Ưu tiên WebSocket - lấy frame mới nhất từ queue
        if hasattr(self, '_esp32_frame_queue') and self._esp32_ws_running:
            try:
                # Xóa các frame cũ, chỉ lấy frame mới nhất
                frame_bytes = None
                while not self._esp32_frame_queue.empty():
                    frame_bytes = self._esp32_frame_queue.get_nowait()
                
                if frame_bytes:
                    img_np = np.frombuffer(frame_bytes, dtype=np.uint8)
                    frame = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
                    if frame is not None:
                        return frame
            except:
                pass
        
        # Fallback: HTTP capture
        try:
            import requests
            url = f"http://{self.esp32_ip}/capture"
            response = requests.get(url, timeout=1)
            
            if response.status_code == 200:
                img_array = np.frombuffer(response.content, dtype=np.uint8)
                frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                return frame
        except:
            pass
        
        # Fallback 2: HTTP stream
        try:
            import requests
            url = f"http://{self.esp32_ip}/"
            response = requests.get(url, stream=True, timeout=1)
            
            if response.status_code == 200:
                bytes_data = b''
                for chunk in response.iter_content(chunk_size=4096):
                    bytes_data += chunk
                    a = bytes_data.find(b'\xff\xd8')
                    b = bytes_data.find(b'\xff\xd9')
                    
                    if a != -1 and b != -1:
                        jpg = bytes_data[a:b+2]
                        frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                        response.close()
                        return frame
                    
                    if len(bytes_data) > 100000:
                        response.close()
                        break
        except:
            pass
        
        return None

    def get_camera(self):
        if self.camera is None or not self.camera.isOpened():
            self.camera = cv2.VideoCapture(0)
            if self.camera.isOpened():
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.camera.set(cv2.CAP_PROP_FPS, 30)
        return self.camera
    
    def get_frame(self):
        if self.use_esp32:
            return self.get_frame_from_esp32()
        else:
            camera = self.get_camera()
            if camera and camera.isOpened():
                success, frame = camera.read()
                return frame if success else None
            return None
    
    def release_camera(self):
        """Giải phóng camera"""
        if self.camera is not None:
            self.camera.release()
            self.camera = None
    
    def register_face(self, user_email, frame):
        """Đăng ký khuôn mặt với rate limiting"""
        current_time = time.time()
        if current_time - self._last_capture_time < self._capture_interval:
            return False, "Đang chờ..."
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5, minSize=(80, 80))
        
        if len(faces) == 0:
            return False, "Không phát hiện khuôn mặt!"
        
        if len(faces) > 1:
            return False, "Phát hiện nhiều hơn 1 khuôn mặt!"
        
        user_dir = os.path.join(self.face_data_dir, user_email)
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        
        for (x, y, w, h) in faces:
            # Resize face về kích thước chuẩn để training tốt hơn
            face_img = gray[y:y+h, x:x+w]
            face_img = cv2.resize(face_img, (200, 200))
            
            existing_images = len([f for f in os.listdir(user_dir) if f.endswith('.jpg')])
            img_path = os.path.join(user_dir, f"face_{existing_images + 1}.jpg")
            cv2.imwrite(img_path, face_img)
            
            self._last_capture_time = current_time
            return True, f"Đã chụp {existing_images + 1}/{self.registration_target}"
        
        return False, "Lỗi khi lưu ảnh"

    def train_model(self):
        """Huấn luyện model với TẤT CẢ user đã đăng ký"""
        faces = []
        labels = []
        label_dict = {}
        current_label = 0
        
        if not os.path.exists(self.face_data_dir):
            return False, "Chưa có dữ liệu khuôn mặt!"
        
        total_images = 0
        for user_email in os.listdir(self.face_data_dir):
            user_dir = os.path.join(self.face_data_dir, user_email)
            
            if not os.path.isdir(user_dir):
                continue
            
            user_images = 0
            for image_name in os.listdir(user_dir):
                if not image_name.endswith('.jpg'):
                    continue
                
                image_path = os.path.join(user_dir, image_name)
                image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
                
                if image is not None:
                    # Resize về kích thước chuẩn
                    image = cv2.resize(image, (200, 200))
                    faces.append(image)
                    labels.append(current_label)
                    user_images += 1
            
            if user_images > 0:
                label_dict[current_label] = user_email
                print(f"  ✓ {user_email}: {user_images} ảnh")
                total_images += user_images
                current_label += 1
        
        if len(faces) == 0:
            return False, "Không có dữ liệu để huấn luyện!"
        
        # Huấn luyện model mới
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.recognizer.train(faces, np.array(labels))
        self.registered_faces = label_dict
        
        # Lưu model
        self.recognizer.save(self.model_file)
        with open(self.labels_file, 'wb') as f:
            pickle.dump(label_dict, f)
        
        print(f"✅ Đã huấn luyện model với {total_images} ảnh từ {len(label_dict)} người")
        return True, f"Huấn luyện thành công với {total_images} ảnh từ {len(label_dict)} người!"
    
    def load_model(self):
        """Load model đã train"""
        if os.path.exists(self.model_file) and os.path.exists(self.labels_file):
            try:
                self.recognizer = cv2.face.LBPHFaceRecognizer_create()
                self.recognizer.read(self.model_file)
                with open(self.labels_file, 'rb') as f:
                    self.registered_faces = pickle.load(f)
                print(f"✅ Đã load model với {len(self.registered_faces)} người")
                return True
            except Exception as e:
                print(f"❌ Lỗi load model: {e}")
                return False
        return False

    def recognize_face(self, frame, current_user_email):
        """Nhận diện khuôn mặt"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5, minSize=(80, 80))
        
        results = []
        
        for (x, y, w, h) in faces:
            face_img = gray[y:y+h, x:x+w]
            face_img = cv2.resize(face_img, (200, 200))
            
            # Nếu chưa có model hoặc chưa train -> tất cả là NGUOI LA
            if len(self.registered_faces) == 0:
                name = "NGUOI LA"
                status = "WARNING"
                confidence = 100
                detected_email = None
            else:
                try:
                    label, confidence = self.recognizer.predict(face_img)
                    detected_email = self.registered_faces.get(label, "Unknown")
                    
                    # Confidence càng thấp càng giống
                    if confidence < 60:
                        status = "SAFE"
                        if detected_email == current_user_email:
                            name = "BAN"
                        else:
                            name = detected_email.split('@')[0].upper()[:12]
                    else:
                        status = "WARNING"
                        name = "NGUOI LA"
                        detected_email = None
                except Exception as e:
                    print(f"❌ Lỗi nhận diện: {e}")
                    name = "NGUOI LA"
                    status = "WARNING"
                    confidence = 100
                    detected_email = None
            
            results.append({
                'bbox': (x, y, w, h),
                'name': name,
                'confidence': confidence,
                'status': status,
                'email': detected_email
            })
        
        return results
    
    def process_frame(self, frame, current_user_email):
        """Xử lý frame và vẽ thông tin"""
        if frame is None:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, "KHONG THE KET NOI CAMERA", (80, 240),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
            return frame, "WARNING", None
        
        display_frame = frame.copy()
        overall_status = "SAFE"
        detected_user_info = None
        h_frame, w_frame = display_frame.shape[:2]
        
        # Hiển thị datetime và email ở góc trên
        current_datetime = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        cv2.putText(display_frame, current_datetime, (w_frame - 200, 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Hiển thị email user hiện tại
        if current_user_email:
            email_short = current_user_email[:25] + "..." if len(current_user_email) > 25 else current_user_email
            cv2.putText(display_frame, f"User: {email_short}", (w_frame - 250, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1)
        
        if self.registration_mode:
            # Chế độ đăng ký
            cv2.putText(display_frame, "CHE DO DANG KY", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
            cv2.putText(display_frame, f"Da chup: {self.registration_count}/{self.registration_target}", 
                       (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            
            # Vẽ khung hướng dẫn
            center_x, center_y = w_frame // 2, h_frame // 2
            box_size = 150
            cv2.rectangle(display_frame, 
                         (center_x - box_size, center_y - box_size),
                         (center_x + box_size, center_y + box_size),
                         (0, 255, 255), 3)
        else:
            # Chế độ nhận diện
            results = self.recognize_face(frame, current_user_email)
            
            # Xác định trạng thái tổng thể
            if len(results) == 0:
                overall_status = "NO_FACE"
            else:
                has_safe = False
                has_warning = False
                
                for result in results:
                    if result['status'] == "SAFE":
                        has_safe = True
                        # Lưu thông tin user được phát hiện
                        if result.get('email'):
                            user_data = user_manager.get_user(result['email'])
                            detected_user_info = {
                                'name': user_data.get('name', result['name']) if user_data else result['name'],
                                'email': result['email']
                            }
                    elif result['status'] == "WARNING":
                        has_warning = True
                
                if has_warning:
                    overall_status = "WARNING"
                elif has_safe:
                    overall_status = "SAFE"
                else:
                    overall_status = "NO_FACE"
            
            for result in results:
                if result['bbox'] is not None:
                    x, y, w, h = result['bbox']
                    name = result['name']
                    status = result['status']
                    
                    if status == "SAFE":
                        color = (0, 255, 0)
                    else:
                        color = (0, 0, 255)
                    
                    cv2.rectangle(display_frame, (x, y), (x+w, y+h), color, 2)
                    cv2.rectangle(display_frame, (x, y-30), (x+w, y), color, -1)
                    cv2.putText(display_frame, name, (x+5, y-8),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Hiển thị trạng thái giám sát
            if self.monitoring_active:
                status_text = "GIAM SAT: BAT"
                status_color = (0, 255, 0)
                
                if overall_status == "WARNING":
                    # Hiển thị CANH BAO lớn ở giữa dưới màn hình
                    text = "CANH BAO!"
                    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3)[0]
                    text_x = (w_frame - text_size[0]) // 2
                    cv2.putText(display_frame, text, (text_x, h_frame - 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
                    
                    # Hiển thị thời gian cảnh báo
                    if self.warning_start_time:
                        duration = int(time.time() - self.warning_start_time)
                        cv2.putText(display_frame, f"Thoi gian: {duration}s", (10, h_frame - 70),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                
                elif overall_status == "SAFE":
                    # Hiển thị AN TOÀN lớn ở giữa dưới màn hình
                    text = "AN TOAN"
                    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3)[0]
                    text_x = (w_frame - text_size[0]) // 2
                    cv2.putText(display_frame, text, (text_x, h_frame - 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
                    
                    # Hiển thị thời gian phát hiện an toàn
                    if self.safe_detection_start:
                        duration = int(time.time() - self.safe_detection_start)
                        cv2.putText(display_frame, f"Thoi gian: {duration}s", (10, h_frame - 70),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                
                elif overall_status == "NO_FACE":
                    # Hiển thị KHÔNG PHÁT HIỆN
                    text = "KHONG PHAT HIEN"
                    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
                    text_x = (w_frame - text_size[0]) // 2
                    cv2.putText(display_frame, text, (text_x, h_frame - 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 165, 0), 3)
                    
                    # Hiển thị thời gian không phát hiện
                    if self.no_detection_start:
                        duration = int(time.time() - self.no_detection_start)
                        cv2.putText(display_frame, f"Thoi gian: {duration}s", (10, h_frame - 70),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 165, 0), 2)
            else:
                status_text = "GIAM SAT: TAT"
                status_color = (128, 128, 128)
            
            cv2.putText(display_frame, status_text, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        return display_frame, overall_status, detected_user_info

    def check_and_send_alert(self, frame, status, detected_user_info=None):
        """Kiểm tra và gửi email cảnh báo
        
        Args:
            frame: Frame hiện tại
            status: Trạng thái - "WARNING" (người lạ), "SAFE" (người an toàn), "NO_FACE" (không phát hiện)
            detected_user_info: Thông tin user được phát hiện (dict với 'name' và 'email')
        """
        if not self.monitoring_active:
            self.warning_start_time = None
            self.safe_detection_start = None
            self.no_detection_start = None
            return
        
        current_time = time.time()
        
        if status == "WARNING":
            # Reset các timer khác
            self.safe_detection_start = None
            self.no_detection_start = None
            
            if self.warning_start_time is None:
                self.warning_start_time = current_time
                print("⚠️ BẮT ĐẦU CẢNH BÁO - Phát hiện người lạ!")
            
            warning_duration = current_time - self.warning_start_time
            
            if warning_duration >= 10:
                if current_time - self.last_email_sent >= self.email_cooldown:
                    print(f"🚨 CẢNH BÁO {int(warning_duration)}s - GỬI EMAIL...")
                    
                    message = f"⚠️ CẢNH BÁO AN NINH!\n\nPhát hiện người lạ trong {int(warning_duration)} giây!"
                    if self.email_alert.send_alert(frame, message, alert_type="stranger"):
                        self.last_email_sent = current_time
                        print(f"✅ ĐÃ GỬI EMAIL CẢNH BÁO NGƯỜI LẠ!")
                    else:
                        print("❌ LỖI GỬI EMAIL!")
        
        elif status == "SAFE":
            # Reset các timer khác
            self.warning_start_time = None
            self.no_detection_start = None
            
            if self.safe_detection_start is None:
                self.safe_detection_start = current_time
                print("✅ BẮT ĐẦU PHÁT HIỆN NGƯỜI AN TOÀN")
            
            safe_duration = current_time - self.safe_detection_start
            
            if safe_duration >= 10:
                if current_time - self.last_safe_email_sent >= self.email_cooldown:
                    print(f"✅ PHÁT HIỆN AN TOÀN {int(safe_duration)}s - GỬI EMAIL...")
                    
                    user_name = detected_user_info.get('name', 'N/A') if detected_user_info else 'N/A'
                    user_email = detected_user_info.get('email', 'N/A') if detected_user_info else 'N/A'
                    
                    message = f"✅ AN TOÀN!\n\nPhát hiện người đã đăng ký: {user_name}"
                    if self.email_alert.send_alert(frame, message, alert_type="safe", detected_user=detected_user_info):
                        self.last_safe_email_sent = current_time
                        print(f"✅ ĐÃ GỬI EMAIL THÔNG BÁO NGƯỜI AN TOÀN: {user_name} ({user_email})")
                    else:
                        print("❌ LỖI GỬI EMAIL!")
        
        elif status == "NO_FACE":
            # Reset các timer khác
            self.warning_start_time = None
            self.safe_detection_start = None
            
            if self.no_detection_start is None:
                self.no_detection_start = current_time
                print("ℹ️ BẮT ĐẦU KHÔNG PHÁT HIỆN AI")
            
            no_detection_duration = current_time - self.no_detection_start
            
            if no_detection_duration >= 10:
                if current_time - self.last_no_detection_email_sent >= self.email_cooldown:
                    print(f"ℹ️ KHÔNG PHÁT HIỆN AI {int(no_detection_duration)}s - GỬI EMAIL...")
                    
                    message = f"ℹ️ THÔNG BÁO!\n\nKhông phát hiện ai trong {int(no_detection_duration)} giây."
                    if self.email_alert.send_alert(frame, message, alert_type="no_detection"):
                        self.last_no_detection_email_sent = current_time
                        print(f"✅ ĐÃ GỬI EMAIL THÔNG BÁO KHÔNG PHÁT HIỆN!")
                    else:
                        print("❌ LỖI GỬI EMAIL!")
    
    def reset_registration(self):
        """Reset trạng thái đăng ký"""
        self.registration_mode = False
        self.registration_count = 0
        self.registration_completed = False
        self._last_capture_time = 0


# Khởi tạo global instances
user_manager = UserManager()
system = FaceRecognitionSystem()


def generate_frames(user_email=None):
    """Generator cho video stream"""
    while True:
        try:
            frame = system.get_frame()
            
            if user_email is None:
                # Chưa đăng nhập
                if frame is not None:
                    overlay = frame.copy()
                    cv2.rectangle(overlay, (0, 0), (frame.shape[1], frame.shape[0]), (0, 0, 0), -1)
                    frame = cv2.addWeighted(frame, 0.3, overlay, 0.7, 0)
                    cv2.putText(frame, "VUI LONG DANG NHAP", (frame.shape[1]//2 - 180, frame.shape[0]//2),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                else:
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(frame, "VUI LONG DANG NHAP", (140, 240),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            else:
                # Đã đăng nhập
                if frame is not None:
                    processed_frame, status, detected_user_info = system.process_frame(frame, user_email)
                    
                    # Xử lý đăng ký tự động
                    if system.registration_mode:
                        if system.registration_count < system.registration_target:
                            success, msg = system.register_face(user_email, frame)
                            if success:
                                system.registration_count += 1
                                print(f"✓ {system.registration_count}/{system.registration_target}")
                        else:
                            # Hoàn thành đăng ký
                            print(f"✅ Hoàn thành đăng ký {system.registration_target} ảnh!")
                            system.registration_mode = False
                            system.registration_completed = True
                            
                            # Tự động train
                            print("🤖 Đang huấn luyện model...")
                            success, msg = system.train_model()
                            if success:
                                print(f"✅ {msg}")
                                system.monitoring_active = True
                                system.email_alert.set_recipient(user_email)
                                print(f"✅ Đã bật giám sát cho {user_email}")
                    else:
                        # Kiểm tra cảnh báo
                        system.check_and_send_alert(frame, status, detected_user_info)
                    
                    frame = processed_frame
                else:
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(frame, "KHONG THE KET NOI CAMERA", (100, 240),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(0.033)  # ~30 FPS
            
        except Exception as e:
            print(f"❌ Lỗi generate_frames: {e}")
            time.sleep(0.1)


# ==================== ROUTES ====================

@app.route('/')
def index():
    if 'user_email' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register_page')
def register_page():
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_email' not in session:
        return redirect(url_for('index'))
    
    user = user_manager.get_user(session['user_email'])
    return render_template('dashboard.html', user=user, user_email=session['user_email'])

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()
    name = data.get('name', '').strip()
    
    if not email or not password or not name:
        return jsonify({'success': False, 'message': 'Vui lòng điền đầy đủ thông tin!'})
    
    if len(password) < 6:
        return jsonify({'success': False, 'message': 'Mật khẩu phải có ít nhất 6 ký tự!'})
    
    success, message = user_manager.register(email, password, name)
    return jsonify({'success': success, 'message': message})

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()
    
    if not email or not password:
        return jsonify({'success': False, 'message': 'Vui lòng điền đầy đủ thông tin!'})
    
    success, message = user_manager.login(email, password)
    
    if success:
        session['user_email'] = email
        user = user_manager.get_user(email)
        session['user_name'] = user['name']
        session['is_admin'] = user_manager.is_admin(email)
        
        # Thiết lập user và load model
        system.set_current_user(email)
        system.email_alert.set_recipient(email)
        
        # Tự động bật giám sát cho tất cả user (admin và user thường)
        system.monitoring_active = True
        
        if user_manager.is_admin(email):
            print(f"👑 Admin {email} đã đăng nhập - Giám sát BẬT")
        else:
            user_dir = os.path.join(system.face_data_dir, email)
            has_face_data = os.path.exists(user_dir) and len([f for f in os.listdir(user_dir) if f.endswith('.jpg')]) >= system.registration_target
            
            if has_face_data:
                print(f"✅ {email} đã đăng ký khuôn mặt - Giám sát BẬT")
            else:
                print(f"ℹ️ {email} chưa đăng ký khuôn mặt - Giám sát BẬT (tất cả là NGƯỜI LẠ)")
    
    return jsonify({'success': success, 'message': message, 'is_admin': user_manager.is_admin(email) if success else False})

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    system.monitoring_active = False
    system.reset_registration()
    system.current_user_email = None
    return jsonify({'success': True, 'message': 'Đăng xuất thành công!'})

@app.route('/video_feed')
def video_feed():
    user_email = session.get('user_email', None)
    return Response(generate_frames(user_email),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/start_registration', methods=['POST'])
def start_registration():
    if 'user_email' not in session:
        return jsonify({'success': False, 'message': 'Chưa đăng nhập!'})
    
    user_email = session['user_email']
    user_dir = os.path.join(system.face_data_dir, user_email)
    
    # Kiểm tra đã đăng ký chưa
    if os.path.exists(user_dir):
        existing = len([f for f in os.listdir(user_dir) if f.endswith('.jpg')])
        if existing >= system.registration_target:
            return jsonify({'success': False, 'message': 'Bạn đã đăng ký khuôn mặt rồi!'})
    
    system.reset_registration()
    system.registration_mode = True
    system.monitoring_active = False
    
    return jsonify({'success': True, 'message': 'Bắt đầu đăng ký khuôn mặt!'})

@app.route('/api/train_model', methods=['POST'])
def train_model():
    if 'user_email' not in session:
        return jsonify({'success': False, 'message': 'Chưa đăng nhập!'})
    
    success, message = system.train_model()
    return jsonify({'success': success, 'message': message})

@app.route('/api/toggle_monitoring', methods=['POST'])
def toggle_monitoring():
    if 'user_email' not in session:
        return jsonify({'success': False, 'message': 'Chưa đăng nhập!'})
    
    # Luôn cho phép bật/tắt giám sát - không cần kiểm tra model
    system.monitoring_active = not system.monitoring_active
    
    if system.monitoring_active:
        system.email_alert.set_recipient(session['user_email'])
        system.reset_registration()
        msg = 'Đã bật giám sát!'
        if len(system.registered_faces) == 0:
            msg += ' (Chưa có model - Tất cả sẽ là NGƯỜI LẠ)'
        return jsonify({'success': True, 'message': msg, 'active': True})
    else:
        system.warning_start_time = None
        return jsonify({'success': True, 'message': 'Đã tắt giám sát!', 'active': False})

@app.route('/api/set_camera', methods=['POST'])
def set_camera():
    if 'user_email' not in session:
        return jsonify({'success': False, 'message': 'Chưa đăng nhập!'})
    
    data = request.json
    source = data.get('source', 'laptop')
    ip = data.get('ip', '192.168.4.1')
    
    system.set_camera_source(source, ip)
    
    if source == 'esp32':
        return jsonify({'success': True, 'message': f'Đã chuyển sang ESP32-CAM ({ip})'})
    else:
        return jsonify({'success': True, 'message': 'Đã chuyển sang camera laptop'})

@app.route('/api/status', methods=['GET'])
def status():
    if 'user_email' not in session:
        return jsonify({'logged_in': False})
    
    user_email = session['user_email']
    is_admin = session.get('is_admin', False)
    user_dir = os.path.join(system.face_data_dir, user_email)
    has_registered = os.path.exists(user_dir) and len([f for f in os.listdir(user_dir) if f.endswith('.jpg')]) >= system.registration_target
    
    return jsonify({
        'logged_in': True,
        'user_email': user_email,
        'user_name': session.get('user_name', ''),
        'is_admin': is_admin,
        'registration_mode': system.registration_mode,
        'registration_count': system.registration_count,
        'registration_target': system.registration_target,
        'registration_completed': system.registration_completed,
        'has_registered': has_registered,
        'monitoring_active': system.monitoring_active,
        'email_enabled': system.email_alert.enabled,
        'warning_duration': int(time.time() - system.warning_start_time) if system.warning_start_time else 0,
        'camera_source': 'ESP32-CAM' if system.use_esp32 else 'Laptop',
        'esp32_ip': system.esp32_ip
    })


# ==================== ADMIN ROUTES ====================

@app.route('/admin')
def admin_page():
    if 'user_email' not in session:
        return redirect(url_for('index'))
    if not session.get('is_admin', False):
        return redirect(url_for('dashboard'))
    return render_template('admin.html', user_email=session['user_email'])

@app.route('/api/admin/users', methods=['GET'])
def admin_get_users():
    if 'user_email' not in session or not session.get('is_admin', False):
        return jsonify({'success': False, 'message': 'Không có quyền truy cập!'})
    
    users = user_manager.get_all_users()
    users_list = []
    
    for email, data in users.items():
        user_dir = os.path.join(system.face_data_dir, email)
        face_count = 0
        if os.path.exists(user_dir):
            face_count = len([f for f in os.listdir(user_dir) if f.endswith('.jpg')])
        
        users_list.append({
            'email': email,
            'name': data.get('name', ''),
            'created_at': data.get('created_at', ''),
            'face_count': face_count,
            'has_face': face_count >= system.registration_target
        })
    
    return jsonify({'success': True, 'users': users_list})

@app.route('/api/admin/delete_face', methods=['POST'])
def admin_delete_face():
    if 'user_email' not in session or not session.get('is_admin', False):
        return jsonify({'success': False, 'message': 'Không có quyền truy cập!'})
    
    data = request.json
    target_email = data.get('email', '').strip()
    
    if not target_email:
        return jsonify({'success': False, 'message': 'Email không hợp lệ!'})
    
    if user_manager.delete_user_face(target_email):
        # Train lại model sau khi xóa để cập nhật
        success, msg = system.train_model()
        
        if not success:
            # Nếu không còn ai để train, xóa model files
            if os.path.exists(system.model_file):
                os.remove(system.model_file)
            if os.path.exists(system.labels_file):
                os.remove(system.labels_file)
            system.registered_faces = {}
            msg = "Đã xóa tất cả dữ liệu - Không còn ai trong hệ thống"
        
        return jsonify({'success': True, 'message': f'Đã xóa dữ liệu khuôn mặt của {target_email}. {msg}'})
    else:
        return jsonify({'success': False, 'message': 'Không tìm thấy dữ liệu khuôn mặt!'})

@app.route('/api/admin/retrain', methods=['POST'])
def admin_retrain():
    if 'user_email' not in session or not session.get('is_admin', False):
        return jsonify({'success': False, 'message': 'Không có quyền truy cập!'})
    
    success, message = system.train_model()
    return jsonify({'success': success, 'message': message})


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎥 HỆ THỐNG NHẬN DIỆN KHUÔN MẶT AI")
    print("="*60)
    print("📱 Truy cập: http://localhost:5000")
    print("🔐 Đăng ký tài khoản để sử dụng")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
