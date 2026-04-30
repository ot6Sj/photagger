"""
Photagger — CLIP-based semantic tagging engine.
Uses HuggingFace Transformers and PyTorch isolated in a separate process.
"""
import os
from pathlib import Path
from PIL import Image

# Import torch and transformers. This module MUST only be imported inside a 
# multiprocessing.Process to avoid WinError 1114 DLL conflicts with PyQt6.
import torch
from transformers import CLIPProcessor, CLIPModel

from .logger import get_logger
from .constants import DEFAULT_BLUR_THRESHOLD
import cv2

log = get_logger("vision")


class VisionEngine:
    """Full CLIP semantic tagging + OpenCV blur detection engine."""

    def __init__(self, blur_threshold: float = DEFAULT_BLUR_THRESHOLD,
                 progress_callback=None):
        self.blur_threshold = blur_threshold
        self._progress = progress_callback or (lambda msg: None)
        self.model = None
        self.processor = None
        self.device = "cpu"
        
        # Hardcode some photography categories for zero-shot text matching
        self.categories = [
            "landscape", "wildlife", "portrait", "architecture", 
            "street", "macro", "food", "sports", "astrophotography", "abstract"
        ]
        
        self.text_prompts = [f"a professional photo of {cat}" for cat in self.categories]

        self._load_model()

    def _load_model(self):
        """Download and load the HuggingFace CLIP model."""
        self._progress("[DOWNLOAD] Initializing CLIP ViT-B/32 model (~600MB)...")
        try:
            # We use openai/clip-vit-base-patch32
            # It will download automatically via huggingface_hub on first run.
            self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            self.model.to(self.device)
            self.model.eval()
            self._progress("[READY] CLIP Model loaded successfully.")
            log.info("CLIP model loaded successfully")
        except Exception as e:
            log.error(f"Failed to load CLIP model: {e}")
            self._progress(f"[ERROR] CLIP load failed: {e}")

    @property
    def is_ready(self) -> bool:
        """Check if the engine is fully loaded and ready."""
        return self.model is not None and self.processor is not None

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
        Full open-vocabulary CLIP semantic tagging.
        Returns top-k predicted labels.
        """
        if not self.is_ready:
            return ["tagging_disabled"]

        try:
            image = Image.open(str(image_path)).convert("RGB")
            
            # Prepare inputs
            inputs = self.processor(
                text=self.text_prompts, 
                images=image, 
                return_tensors="pt", 
                padding=True
            ).to(self.device)
            
            # Forward pass
            with torch.no_grad():
                outputs = self.model(**inputs)
                
            # Get image-text similarity score
            logits_per_image = outputs.logits_per_image # this is the image-text similarity score
            probs = logits_per_image.softmax(dim=1).cpu().numpy()[0]
            
            # Top K indices
            top_indices = probs.argsort()[-top_k:][::-1]
            return [self.categories[i] for i in top_indices]
            
        except Exception as e:
            log.error(f"Tag extraction failed for {image_path}: {e}")
            return ["error"]


def _run_ai_process(cmd_q, res_q, blur_threshold):
    """
    Multiprocessing target function. This runs in a completely separate Python 
    process to isolate PyTorch/Transformers DLLs from the PyQt6 main thread.
    """
    def on_progress(msg):
        res_q.put(("progress", msg))
        
    try:
        engine = VisionEngine(blur_threshold=blur_threshold, progress_callback=on_progress)
        res_q.put(("init_done", True))
    except Exception as e:
        res_q.put(("init_done", e))
        return
        
    while True:
        try:
            cmd = cmd_q.get()
            if cmd is None:
                break
            
            action = cmd[0]
            if action == "blur":
                file_path = cmd[1]
                res = engine.is_blurry(file_path)
                res_q.put((action, res))
            elif action == "tag":
                file_path, top_k = cmd[1], cmd[2]
                res = engine.get_tags(file_path, top_k=top_k)
                res_q.put((action, res))
        except Exception as e:
            res_q.put(("error", e))
