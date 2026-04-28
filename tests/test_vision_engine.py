"""Tests for the vision engine."""
import os
import sys
import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from photagger.vision_engine import VisionEngine


class TestVisionEnginePreprocess:
    """Tests for image preprocessing pipeline."""

    def test_output_shape(self):
        """Preprocessing should produce (1, 3, 224, 224) tensor."""
        engine = VisionEngine.__new__(VisionEngine)
        img = Image.new("RGB", (640, 480), color=(128, 128, 128))
        result = engine.preprocess(img)
        assert result.shape == (1, 3, 224, 224)
        assert result.dtype == np.float32

    def test_normalized_range(self):
        """Output values should be roughly in ImageNet normalized range."""
        engine = VisionEngine.__new__(VisionEngine)
        img = Image.new("RGB", (300, 300), color=(128, 128, 128))
        result = engine.preprocess(img)
        # After normalization, values should be around -2 to +3 range
        assert result.min() > -5.0
        assert result.max() < 5.0


class TestBlurDetection:
    """Tests for Laplacian blur detection."""

    def test_sharp_image(self, tmp_path):
        """A high-contrast sharp image should not be detected as blurry."""
        engine = VisionEngine.__new__(VisionEngine)
        engine.blur_threshold = 100.0

        # Create a sharp checkerboard pattern
        img = np.zeros((200, 200), dtype=np.uint8)
        for i in range(0, 200, 10):
            for j in range(0, 200, 10):
                if (i // 10 + j // 10) % 2 == 0:
                    img[i:i+10, j:j+10] = 255

        # Save as file
        import cv2
        path = str(tmp_path / "sharp.png")
        cv2.imwrite(path, img)

        is_blur, variance = engine.is_blurry(path)
        assert bool(is_blur) is False
        assert variance > 100.0

    def test_blurry_image(self, tmp_path):
        """A uniform/blurred image should be detected as blurry."""
        engine = VisionEngine.__new__(VisionEngine)
        engine.blur_threshold = 100.0

        # Create a nearly uniform (blurry) image
        img = np.full((200, 200), 128, dtype=np.uint8)
        img += np.random.randint(0, 3, (200, 200), dtype=np.uint8)

        import cv2
        path = str(tmp_path / "blurry.png")
        cv2.imwrite(path, img)

        is_blur, variance = engine.is_blurry(path)
        assert bool(is_blur) is True
        assert variance < 100.0

    def test_nonexistent_file(self):
        """Should handle missing files gracefully."""
        engine = VisionEngine.__new__(VisionEngine)
        engine.blur_threshold = 100.0
        is_blur, variance = engine.is_blurry("nonexistent.jpg")
        assert is_blur is False
        assert variance == 0.0
