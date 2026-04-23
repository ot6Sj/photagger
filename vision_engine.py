import cv2
import numpy as np
from PIL import Image
import os
import httpx
import onnxruntime as ort

MODEL_URL = "https://github.com/onnx/models/raw/main/validated/vision/classification/mobilenet/model/mobilenetv2-7.onnx"
CLASSES_URL = "https://raw.githubusercontent.com/pytorch/hub/master/imagenet_classes.txt"

class VisionEngine:
    def __init__(self, blur_threshold=100.0):
        self.blur_threshold = blur_threshold
        self.model_path = "mobilenetv2-7.onnx"
        self.classes_path = "imagenet_classes.txt"
        
        self.ort_session = None
        self.categories = []
        
        # Determine if we need to auto-download standard models
        if not os.path.exists(self.model_path) or not os.path.exists(self.classes_path):
            self.download_assets()
            
        try:
            self.ort_session = ort.InferenceSession(self.model_path)
            with open(self.classes_path, "r", encoding="utf-8") as f:
                self.categories = [s.strip() for s in f.readlines()]
        except Exception as e:
            print(f"Failed to load ONNX: {e}")

    def download_assets(self):
        print("Downloading ONNX AI Assets (First time only)...")
        try:
            # Download ImageNet Classes
            if not os.path.exists(self.classes_path):
                response = httpx.get(CLASSES_URL, timeout=30.0)
                response.raise_for_status()
                with open(self.classes_path, "wb") as f:
                    f.write(response.content)
                    
            # Download ONNX Model
            if not os.path.exists(self.model_path):
                # Using stream for large file to avoid memory overload
                with httpx.stream("GET", MODEL_URL, follow_redirects=True, timeout=60.0) as r:
                    r.raise_for_status()
                    with open(self.model_path, "wb") as f:
                        for chunk in r.iter_bytes():
                            f.write(chunk)
            print("ONNX AI Assets downloaded successfully.")
        except Exception as e:
            print(f"Error downloading AI assets: {e}")

    def preprocess(self, img):
        # Equivalent to PyTorch generic transforms for ResNet/MobileNet (ImageNet standard)
        # 1. Resize to 256
        ratio = 256.0 / min(img.width, img.height)
        new_w, new_h = int(img.width * ratio), int(img.height * ratio)
        img = img.resize((new_w, new_h), Image.Resampling.BILINEAR)
        
        # 2. Center crop to 224x224
        left = (new_w - 224) / 2
        top = (new_h - 224) / 2
        right = (new_w + 224) / 2
        bottom = (new_h + 224) / 2
        img = img.crop((left, top, right, bottom))
        
        # 3. To Numpy Float32 Array + Normalize [0, 1]
        img_data = np.array(img).astype(np.float32) / 255.0
        
        # 4. Standard ImageNet Mean/Std Normalize
        mean = np.array([0.485, 0.456, 0.406]).astype(np.float32)
        std = np.array([0.229, 0.224, 0.225]).astype(np.float32)
        img_data = (img_data - mean) / std
        
        # 5. Permute HWC to CHW format needed by ONNX math
        img_data = np.transpose(img_data, [2, 0, 1])
        
        # 6. Add batch dimension (1, C, H, W)
        img_data = np.expand_dims(img_data, axis=0)
        return img_data

    def is_blurry(self, image_path):
        """
        Phase 2 Feature: OpenCV Laplacian variance.
        Returns True if image variance drops below threshold.
        """
        try:
            image = cv2.imread(str(image_path))
            if image is None:
                return False 
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            variance = cv2.Laplacian(gray, cv2.CV_64F).var()
            return (variance < self.blur_threshold), variance
        except Exception as e:
            return False, 0.0

    def get_tags(self, image_path, top_k=3):
        """
        Phase 3 Feature: ONNX Deep Learning tag classification.
        """
        if not self.ort_session or not self.categories:
            return ["tagging_disabled"]
            
        try:
            input_image = Image.open(str(image_path)).convert('RGB')
            input_tensor = self.preprocess(input_image)
            
            # Predict
            ort_inputs = {self.ort_session.get_inputs()[0].name: input_tensor}
            ort_outs = self.ort_session.run(None, ort_inputs)
            scores = ort_outs[0][0] # first batch
            
            # Softmax
            exp_scores = np.exp(scores - np.max(scores))
            probabilities = exp_scores / exp_scores.sum()
            
            # Top K
            top_indices = np.argsort(probabilities)[-top_k:][::-1]
            
            tags = [self.categories[i] for i in top_indices]
            return tags
        except Exception as e:
            print(f"Error during tag extraction: {e}")
            return ["error"]
