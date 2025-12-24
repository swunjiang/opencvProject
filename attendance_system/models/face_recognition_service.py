import cv2
import numpy as np
from typing import List, Tuple, Optional
import base64
import json

class FaceRecognitionService:
    def __init__(self):
        # 使用OpenCV的Haar级联分类器进行人脸检测
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        # 使用LBPH人脸识别器
        try:
            self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        except AttributeError:
            # 如果没有opencv-contrib-python，则使用简化版本
            self.recognizer = None
        self.known_faces = {}  # 存储已知人脸特征和对应的学号
        self.face_samples = []  # 存储人脸样本
        self.ids = []  # 存储对应的标签
        self.trained = False
    
    def detect_faces(self, image) -> List[Tuple[int, int, int, int]]:
        """
        检测图像中的人脸
        :param image: 输入图像
        :return: 人脸边界框列表 (x, y, w, h)
        """
        try:
            # 检查图像
            if image is None:
                print("Error: Image is None")
                return []
            
            print(f"Image shape: {image.shape if hasattr(image, 'shape') else 'Unknown'}")
            print(f"Image dtype: {image.dtype if hasattr(image, 'dtype') else 'Unknown'}")
            
            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            print(f"Gray image shape: {gray.shape}")
            
            # 检测人脸
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            print(f"Detected {len(faces)} faces")
            return faces
        except Exception as e:
            print(f"Error in detect_faces: {e}")
            return []
    
    def extract_face(self, image, face_coords) -> np.ndarray:
        """
        从图像中提取人脸区域
        :param image: 输入图像
        :param face_coords: 人脸坐标 (x, y, w, h)
        :return: 人脸区域图像
        """
        (x, y, w, h) = face_coords
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        face_roi = gray[y:y+h, x:x+w]
        # 调整尺寸以统一处理
        face_roi = cv2.resize(face_roi, (100, 100))
        return face_roi
    
    def extract_face_from_base64(self, base64_image: str) -> Optional[np.ndarray]:
        """
        从Base64编码的图片中提取人脸区域
        :param base64_image: Base64编码的图片
        :return: 人脸区域图像
        """
        try:
            # 移除Base64头部信息（如果有的话）
            if base64_image.startswith('data:image'):
                base64_image = base64_image.split(',')[1]
            
            # 解码Base64字符串
            image_data = base64.b64decode(base64_image)
            
            # 转换为numpy数组
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # 检测人脸
            faces = self.detect_faces(img)
            
            if len(faces) > 0:
                # 取第一张人脸
                face_roi = self.extract_face(img, faces[0])
                return face_roi
            
            return None
        except Exception as e:
            print(f"Error extracting face from base64: {e}")
            return None
    
    def add_face(self, image_data: bytes, student_id: str) -> bool:
        """
        添加学生人脸数据到已知人脸库
        :param image_data: 图片数据
        :param student_id: 学生ID
        :return: 是否添加成功
        """
        try:
            print(f"Adding face for student: {student_id}")
            
            # 将字节数据转换为numpy数组
            nparr = np.frombuffer(image_data, np.uint8)
            print(f"Numpy array shape: {nparr.shape}")
            
            # 解码图像
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # 检查图像是否成功解码
            if img is None:
                print("Error: Failed to decode image")
                return False
            
            print(f"Decoded image shape: {img.shape}")
            
            # 检测人脸
            faces = self.detect_faces(img)
            
            if len(faces) > 0:
                print(f"Found {len(faces)} faces, using the first one")
                # 取第一张人脸
                face_roi = self.extract_face(img, faces[0])
                print(f"Extracted face ROI shape: {face_roi.shape}")
                
                # 存储人脸数据用于训练
                self.face_samples.append(face_roi)
                label = hash(student_id) % 10000  # 简化的标签生成
                self.ids.append(label)
                self.known_faces[label] = student_id
                print(f"Added face sample. Total samples: {len(self.face_samples)}")
                
                return True
            else:
                print("No faces detected in the image")
                return False
        except Exception as e:
            print(f"Error adding face: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def train_model(self) -> bool:
        """
        训练人脸识别模型
        :return: 是否训练成功
        """
        try:
            if self.recognizer and len(self.face_samples) > 0 and len(self.ids) > 0:
                self.recognizer.train(self.face_samples, np.array(self.ids))
                self.trained = True
                return True
            return False
        except Exception as e:
            print(f"Error training model: {e}")
            return False
    
    def recognize_face(self, image_data: bytes) -> Optional[str]:
        """
        识别人脸
        :param image_data: 图片数据
        :return: 匹配的学生ID，如果没有匹配则返回None
        """
        try:
            # 将字节数据转换为numpy数组
            nparr = np.frombuffer(image_data, np.uint8)
            # 解码图像
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # 检测人脸
            faces = self.detect_faces(img)
            
            if len(faces) > 0 and self.recognizer and self.trained:
                # 取第一张人脸
                face_roi = self.extract_face(img, faces[0])
                
                # 识别
                label, confidence = self.recognizer.predict(face_roi)
                
                print(f"Recognized label: {label}, confidence: {confidence}")  # 调试信息
                
                # 置信度阈值
                if confidence < 100:  # 置信度越低越好
                    if label in self.known_faces:
                        return self.known_faces[label]
            
            return None
        except Exception as e:
            print(f"Error recognizing face: {e}")
            return None
    
    def load_face_data(self, face_data: str, student_id: str) -> bool:
        """
        从数据库加载的人脸数据中恢复人脸信息
        :param face_data: 数据库中存储的人脸数据（JSON格式）
        :param student_id: 学生ID
        :return: 是否加载成功
        """
        try:
            # 解析存储的人脸数据
            face_info = json.loads(face_data)
            face_array = np.array(face_info['face'], dtype=np.uint8)
            
            # 重塑数组
            shape = face_info.get('shape', (100, 100))  # 默认形状
            face_roi = face_array.reshape(shape)
            
            # 添加到样本中
            self.face_samples.append(face_roi)
            label = hash(student_id) % 10000
            self.ids.append(label)
            self.known_faces[label] = student_id
            
            return True
        except Exception as e:
            print(f"Error loading face data: {e}")
            return False
    
    def serialize_face(self, face_roi: np.ndarray) -> str:
        """
        将人脸数据序列化为可存储的字符串
        :param face_roi: 人脸图像数据
        :return: 序列化后的人脸数据
        """
        try:
            # 确保face_roi是numpy数组
            if not isinstance(face_roi, np.ndarray):
                print(f"Error: face_roi is not numpy array, type: {type(face_roi)}")
                return ""
            
            # 将人脸数据转换为列表并存储
            face_info = {
                'shape': face_roi.shape,
                'face': face_roi.flatten().tolist()
            }
            serialized = json.dumps(face_info)
            print(f"Serialized face data length: {len(serialized)}")
            return serialized
        except Exception as e:
            print(f"Error serializing face: {e}")
            return ""