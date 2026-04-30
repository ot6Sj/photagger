"""
Photagger — Fast Face Detector using UltraFace ONNX.
Downloads the model dynamically and provides bounding box and count detection.
"""
import os
from pathlib import Path
import httpx
import numpy as np
import cv2
import onnxruntime as ort

from .logger import get_logger

log = get_logger("face_detector")

# UltraFace RFB-320 ONNX Model
MODEL_URL = "https://github.com/onnx/models/raw/main/validated/vision/body_analysis/ultraface/models/version-RFB-320.onnx"
MODEL_FILENAME = "version-RFB-320.onnx"


class FaceDetector:
    """Lightweight face detector using ONNX Runtime."""

    def __init__(self, confidence_threshold: float = 0.7, progress_callback=None):
        self.confidence_threshold = confidence_threshold
        self.progress_callback = progress_callback
        self.session = None
        self.is_ready = False
        
        # Hardcoded anchors and priors for UltraFace 320x240
        self.image_size = (320, 240) # W, H
        
        self._initialize()

    def _initialize(self):
        """Download model if needed and load ONNX session."""
        app_data = Path(os.getenv('APPDATA', os.path.expanduser('~'))) / "Photagger" / "models"
        app_data.mkdir(parents=True, exist_ok=True)
        model_path = app_data / MODEL_FILENAME

        if not model_path.exists():
            if self.progress_callback:
                self.progress_callback(f"[DOWNLOAD] Fetching Face Detection model ({MODEL_FILENAME})...")
            try:
                with httpx.stream("GET", MODEL_URL, follow_redirects=True) as response:
                    response.raise_for_status()
                    total = int(response.headers.get("content-length", 0))
                    downloaded = 0
                    with open(model_path, "wb") as f:
                        for chunk in response.iter_bytes(chunk_size=8192):
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total > 0 and self.progress_callback:
                                pct = int((downloaded / total) * 100)
                                if pct % 10 == 0:
                                    self.progress_callback(f"[DOWNLOAD] {pct}%")
            except Exception as e:
                log.error(f"Failed to download face model: {e}")
                if self.progress_callback:
                    self.progress_callback(f"[ERROR] Face detection disabled: {e}")
                return

        try:
            self.session = ort.InferenceSession(str(model_path), providers=['CPUExecutionProvider'])
            self.is_ready = True
            log.info("Face detector initialized successfully.")
        except Exception as e:
            log.error(f"Failed to load ONNX face model: {e}")

    def detect_faces(self, image_path: Path | str) -> int:
        """
        Detect faces in an image and return the count.
        For Phase 2, we just return the count of detected faces.
        """
        if not self.is_ready or not self.session:
            return 0

        try:
            img = cv2.imread(str(image_path))
            if img is None:
                return 0

            # Preprocess
            image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            image = cv2.resize(image, self.image_size)
            image_mean = np.array([127, 127, 127])
            image = (image - image_mean) / 128
            image = np.transpose(image, [2, 0, 1])
            image = np.expand_dims(image, axis=0)
            image = image.astype(np.float32)

            # Inference
            input_name = self.session.get_inputs()[0].name
            confidences, boxes = self.session.run(None, {input_name: image})

            # Process output
            # Confidences output shape is (1, N, 2) where class 1 is face
            # We just count anchors where face confidence > threshold
            # UltraFace outputs need Non-Maximum Suppression (NMS) for accurate bounding boxes,
            # but for a fast simple count, we can do a rough count or simple NMS.
            # Given the scope, we will do a basic thresholding for now.
            face_probs = confidences[0, :, 1]
            detections = face_probs[face_probs > self.confidence_threshold]
            
            # Very rough estimate of faces (since multiple anchors might trigger per face).
            # To be accurate, we'd implement NMS, but for tagging "portrait" or getting a general presence,
            # even > 0 detections is enough to say "contains face".
            # Let's do a fast distance-based grouping (simple NMS).
            
            valid_boxes = boxes[0, face_probs > self.confidence_threshold]
            count = self._simple_nms(valid_boxes)
            return count

        except Exception as e:
            log.error(f"Face detection failed for {image_path}: {e}")
            return 0

    def _simple_nms(self, boxes: np.ndarray, threshold: float = 0.5) -> int:
        """Extremely simplified NMS just to count distinct face regions."""
        if len(boxes) == 0:
            return 0
        
        # Format: xmin, ymin, xmax, ymax
        # Convert to center points
        centers = []
        for box in boxes:
            cx = (box[0] + box[2]) / 2
            cy = (box[1] + box[3]) / 2
            centers.append((cx, cy))
            
        # Group centers that are close to each other
        groups = []
        for cx, cy in centers:
            merged = False
            for group in groups:
                # If distance is small relative to image normalized coordinates (0-1)
                dist = ((group[0] - cx)**2 + (group[1] - cy)**2)**0.5
                if dist < 0.1:  # 10% of image size
                    group[0] = (group[0] + cx) / 2
                    group[1] = (group[1] + cy) / 2
                    merged = True
                    break
            if not merged:
                groups.append([cx, cy])
                
        return len(groups)
