"""
Photagger — ONNX-based computer vision engine.
Handles blur detection (OpenCV Laplacian) and semantic tagging (MobileNetV2).
"""
import cv2
import numpy as np
from pathlib import Path
from PIL import Image
import httpx
import onnxruntime as ort

from .constants import (
    MODEL_FILENAME, CLASSES_FILENAME, MODEL_URL, CLASSES_URL,
    RESOURCES_DIR, DEFAULT_BLUR_THRESHOLD,
)
from .logger import get_logger

log = get_logger("vision")


def _get_model_dir() -> Path:
    """Get the directory for storing downloaded models."""
    import os
    appdata = os.environ.get("APPDATA", Path.home() / ".config")
    model_dir = Path(appdata) / "Photagger" / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    return model_dir


class VisionEngine:
    """Combined blur detection + ONNX semantic tagging engine."""

    def __init__(self, blur_threshold: float = DEFAULT_BLUR_THRESHOLD,
                 progress_callback=None):
        self.blur_threshold = blur_threshold
        self._progress = progress_callback or (lambda msg: None)

        self.model_dir = _get_model_dir()
        self.model_path = self.model_dir / MODEL_FILENAME
        self.classes_path = RESOURCES_DIR / CLASSES_FILENAME

        self.ort_session = None
        self.categories: list[str] = []

        self._ensure_assets()
        self._load_model()

    def _ensure_assets(self):
        """Download model files if not present, with retry logic."""
        if not self.classes_path.exists():
            # Try bundled resources first, then download
            self._download_file(CLASSES_URL, self.classes_path, "ImageNet labels")

        if not self.model_path.exists():
            self._download_file(MODEL_URL, self.model_path, "MobileNetV2 ONNX model", stream=True)

    def _download_file(self, url: str, dest: Path, label: str, stream: bool = False, retries: int = 3):
        """Download a file with retry logic and progress reporting."""
        for attempt in range(1, retries + 1):
            try:
                self._progress(f"Downloading {label} (attempt {attempt}/{retries})...")
                log.info(f"Downloading {label} from {url}")

                if stream:
                    with httpx.stream("GET", url, follow_redirects=True, timeout=120.0) as r:
                        r.raise_for_status()
                        total = int(r.headers.get("content-length", 0))
                        downloaded = 0
                        with open(dest, "wb") as f:
                            for chunk in r.iter_bytes(chunk_size=65536):
                                f.write(chunk)
                                downloaded += len(chunk)
                                if total > 0:
                                    pct = int((downloaded / total) * 100)
                                    self._progress(f"Downloading {label}... {pct}%")
                else:
                    response = httpx.get(url, timeout=30.0, follow_redirects=True)
                    response.raise_for_status()
                    dest.write_bytes(response.content)

                log.info(f"Downloaded {label} → {dest}")
                self._progress(f"Downloaded {label} ✓")
                return
            except Exception as e:
                log.warning(f"Download attempt {attempt} failed for {label}: {e}")
                if attempt == retries:
                    log.error(f"Failed to download {label} after {retries} attempts")
                    self._progress(f"Failed to download {label}")
                else:
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff

    def _load_model(self):
        """Load the ONNX model and class labels."""
        try:
            if self.model_path.exists():
                self.ort_session = ort.InferenceSession(str(self.model_path))
                log.info("ONNX model loaded successfully")
            else:
                log.warning("ONNX model file not found, tagging disabled")

            if self.classes_path.exists():
                with open(self.classes_path, "r", encoding="utf-8") as f:
                    self.categories = [s.strip() for s in f.readlines()]
                log.info(f"Loaded {len(self.categories)} class labels")
            else:
                log.warning("Class labels not found, tagging disabled")
        except Exception as e:
            log.error(f"Failed to load ONNX model: {e}")

    @property
    def is_ready(self) -> bool:
        """Check if the engine is fully loaded and ready."""
        return self.ort_session is not None and len(self.categories) > 0

    def preprocess(self, img: Image.Image) -> np.ndarray:
        """Standard ImageNet preprocessing: resize, center-crop, normalize."""
        # Resize shortest side to 256
        ratio = 256.0 / min(img.width, img.height)
        new_w, new_h = int(img.width * ratio), int(img.height * ratio)
        img = img.resize((new_w, new_h), Image.Resampling.BILINEAR)

        # Center crop 224x224
        left = (new_w - 224) / 2
        top = (new_h - 224) / 2
        img = img.crop((left, top, left + 224, top + 224))

        # To float32 array, normalize
        img_data = np.array(img).astype(np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        img_data = (img_data - mean) / std

        # HWC → CHW, add batch dim
        img_data = np.transpose(img_data, [2, 0, 1])
        return np.expand_dims(img_data, axis=0)

    def is_blurry(self, image_path: str | Path) -> tuple[bool, float]:
        """
        OpenCV Laplacian variance blur detection.
        Returns (is_blurry, variance_score).
        """
        try:
            image = cv2.imread(str(image_path))
            if image is None:
                log.warning(f"Could not read image for blur check: {image_path}")
                return False, 0.0

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            variance = cv2.Laplacian(gray, cv2.CV_64F).var()
            return (variance < self.blur_threshold), float(variance)
        except Exception as e:
            log.warning(f"Blur check failed for {image_path}: {e}")
            return False, 0.0

    def get_tags(self, image_path: str | Path, top_k: int = 3) -> list[str]:
        """
        ONNX MobileNetV2 semantic tagging.
        Returns top-k predicted ImageNet labels.
        """
        if not self.is_ready:
            return ["tagging_disabled"]

        try:
            input_image = Image.open(str(image_path)).convert("RGB")
            input_tensor = self.preprocess(input_image)

            ort_inputs = {self.ort_session.get_inputs()[0].name: input_tensor}
            ort_outs = self.ort_session.run(None, ort_inputs)
            scores = ort_outs[0][0]

            # Softmax
            exp_scores = np.exp(scores - np.max(scores))
            probabilities = exp_scores / exp_scores.sum()

            # Top K indices
            top_indices = np.argsort(probabilities)[-top_k:][::-1]
            return [self.categories[i] for i in top_indices if i < len(self.categories)]
        except Exception as e:
            log.error(f"Tag extraction failed for {image_path}: {e}")
            return ["error"]
