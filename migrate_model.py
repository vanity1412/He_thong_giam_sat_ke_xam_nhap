"""
Script để migrate model cũ sang model shared mới.
Chạy một lần sau khi cập nhật code.
"""
import os
import cv2
import numpy as np
import pickle

def migrate():
    face_data_dir = "face_data"
    models_dir = "models"
    model_file = os.path.join(models_dir, "shared_model.yml")
    labels_file = os.path.join(models_dir, "shared_labels.pkl")
    
    if not os.path.exists(face_data_dir):
        print("❌ Không có thư mục face_data")
        return
    
    faces = []
    labels = []
    label_dict = {}
    current_label = 0
    total_images = 0
    
    print("🔄 Đang quét dữ liệu khuôn mặt...")
    
    for user_email in os.listdir(face_data_dir):
        user_dir = os.path.join(face_data_dir, user_email)
        
        if not os.path.isdir(user_dir):
            continue
        
        user_images = 0
        for image_name in os.listdir(user_dir):
            if not image_name.endswith('.jpg'):
                continue
            
            image_path = os.path.join(user_dir, image_name)
            image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            
            if image is not None:
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
        print("❌ Không có dữ liệu để huấn luyện!")
        return
    
    print(f"\n🤖 Đang huấn luyện model với {total_images} ảnh từ {len(label_dict)} người...")
    
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(labels))
    
    recognizer.save(model_file)
    with open(labels_file, 'wb') as f:
        pickle.dump(label_dict, f)
    
    print(f"✅ Đã tạo model shared mới!")
    print(f"   - Model: {model_file}")
    print(f"   - Labels: {labels_file}")

if __name__ == '__main__':
    migrate()
