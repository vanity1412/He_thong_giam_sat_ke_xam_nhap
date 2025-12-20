import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
import cv2
import os
import threading

class EmailAlert:
    def __init__(self):
        # Cấu hình Gmail
        self.smtp_host = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = "watershoputetea@gmail.com"
        self.sender_password = "ibdjgggydrtteqxg"
        self.recipient_email = None
        self.enabled = False
        self._lock = threading.Lock()
        
    def set_recipient(self, email):
        """Thiết lập email người nhận"""
        with self._lock:
            self.recipient_email = email
            self.enabled = True if email else False
        print(f"Đã thiết lập email cảnh báo: {email}")
    
    def disable(self):
        """Tắt cảnh báo email"""
        with self._lock:
            self.enabled = False
        print("Đã tắt cảnh báo email")
    
    def send_alert(self, frame=None, message="Phát hiện người lạ!", alert_type="stranger", detected_user=None):
        """Gửi email cảnh báo (non-blocking)
        
        Args:
            frame: Ảnh đính kèm
            message: Nội dung cảnh báo
            alert_type: Loại cảnh báo - "stranger" (người lạ), "safe" (người an toàn), "no_detection" (không phát hiện)
            detected_user: Thông tin user được phát hiện (dict với 'name' và 'email')
        """
        if not self.enabled or not self.recipient_email:
            return False
        
        # Gửi email trong thread riêng để không block
        def _send():
            try:
                msg = MIMEMultipart()
                msg['From'] = self.sender_email
                msg['To'] = self.recipient_email
                
                # Tùy chỉnh subject và body theo loại cảnh báo
                if alert_type == "safe":
                    msg['Subject'] = f"✅ AN TOÀN - Phát hiện người đã đăng ký - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
                    status_color = "#28a745"
                    status_text = "NGƯỜI ĐÃ ĐĂNG KÝ"
                    icon = "✅"
                    bg_gradient = "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)"
                    
                    user_info = ""
                    if detected_user:
                        user_info = f"""
                        <p><strong>👤 Tên:</strong> {detected_user.get('name', 'N/A')}</p>
                        <p><strong>📧 Email:</strong> {detected_user.get('email', 'N/A')}</p>
                        """
                    
                elif alert_type == "no_detection":
                    msg['Subject'] = f"ℹ️ THÔNG BÁO - Không phát hiện ai trong 10 giây - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
                    status_color = "#ffc107"
                    status_text = "KHÔNG PHÁT HIỆN KẺ XÂM NHẬP"
                    icon = "ℹ️"
                    bg_gradient = "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"
                    user_info = ""
                    
                else:  # stranger
                    msg['Subject'] = f"⚠️ CẢNH BÁO AN NINH - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
                    status_color = "#dc3545"
                    status_text = "NGƯỜI LẠ PHÁT HIỆN"
                    icon = "⚠️"
                    bg_gradient = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
                    user_info = ""
                
                body = f"""
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <div style="background: {bg_gradient}; padding: 20px; border-radius: 10px;">
                        <h1 style="color: white; text-align: center;">{icon} THÔNG BÁO AN NINH</h1>
                    </div>
                    
                    <div style="padding: 20px; background: #f8f9fa; margin-top: 20px; border-radius: 10px;">
                        <h2 style="color: {status_color};">{icon} {message}</h2>
                        <p><strong>Thời gian:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                        <p><strong>Trạng thái:</strong> <span style="color: {status_color}; font-weight: bold;">{status_text}</span></p>
                        {user_info}
                    </div>
                    
                    <div style="padding: 20px; margin-top: 20px;">
                        <p style="color: #666;">Đây là email tự động từ Hệ Thống Nhận Diện Khuôn Mặt AI.</p>
                    </div>
                </body>
                </html>
                """
                
                msg.attach(MIMEText(body, 'html'))
                
                # Đính kèm ảnh nếu có
                if frame is not None:
                    try:
                        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                        if ret:
                            image = MIMEImage(buffer.tobytes(), name="canh_bao.jpg")
                            msg.attach(image)
                    except Exception as img_err:
                        print(f"⚠️ Không thể đính kèm ảnh: {img_err}")
                
                # Kết nối và gửi email
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=15)
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
                server.quit()
                
                print(f"✅ Đã gửi email cảnh báo đến {self.recipient_email}")
                
            except Exception as e:
                print(f"❌ Lỗi gửi email: {e}")
        
        # Chạy trong thread riêng
        thread = threading.Thread(target=_send, daemon=True)
        thread.start()
        return True
    
    def test_connection(self):
        """Kiểm tra kết nối email"""
        try:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.quit()
            return True, "Kết nối email thành công!"
        except Exception as e:
            return False, f"Lỗi kết nối: {str(e)}"
