"""
Photagger — Exposure quality analysis via histogram evaluation.
Uses OpenCV to detect overexposed/underexposed images.
"""
import cv2
import numpy as np
from pathlib import Path
from .logger import get_logger

log = get_logger("exposure")


class ExposureResult:
    """Container for exposure analysis results."""
    __slots__ = ("score", "rating", "verdict", "highlights_clipped", "shadows_clipped", "noise_estimate")

    def __init__(self, score: float, rating: int, verdict: str,
                 highlights_clipped: float, shadows_clipped: float, noise_estimate: float = 0.0):
        self.score = score
        self.rating = rating
        self.verdict = verdict
        self.highlights_clipped = highlights_clipped
        self.shadows_clipped = shadows_clipped
        self.noise_estimate = noise_estimate

    def __repr__(self):
        return f"ExposureResult(score={self.score:.1f}, rating={self.rating}★, verdict='{self.verdict}')"


def analyze_exposure(image_path: str | Path, reject_threshold: float = 15.0) -> ExposureResult:
    """
    Analyze image exposure quality using histogram distribution.

    Evaluates:
    - Highlight clipping (% of pixels at max brightness)
    - Shadow clipping (% of pixels at min brightness)
    - Overall histogram balance

    Returns an ExposureResult with a 0-100 score and 1-5 star rating.
    """
    try:
        img = cv2.imread(str(image_path))
        if img is None:
            return ExposureResult(50.0, 3, "unreadable", 0.0, 0.0, 0.0)

        # Convert to grayscale for luminance analysis
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        total_pixels = gray.size

        # Calculate histogram
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()

        # Highlight clipping: pixels in top 5 bins (251-255)
        highlights_clipped = (hist[251:].sum() / total_pixels) * 100

        # Shadow clipping: pixels in bottom 5 bins (0-4)
        shadows_clipped = (hist[:5].sum() / total_pixels) * 100

        # Calculate weighted mean brightness (0-255)
        brightness = np.average(np.arange(256), weights=hist)

        # Calculate standard deviation of the histogram (spread)
        variance = np.average((np.arange(256) - brightness) ** 2, weights=hist)
        std_dev = np.sqrt(variance)
        
        # Noise Estimation (Fast Median filter difference)
        # Using a small center crop for speed
        h, w = gray.shape
        crop = gray[h//4:3*h//4, w//4:3*w//4]
        blurred = cv2.medianBlur(crop, 3)
        diff = cv2.absdiff(crop, blurred)
        noise_estimate = float(np.mean(diff))

        # Score computation (0-100, higher = better exposure)
        score = 100.0

        # Penalize highlight clipping
        if highlights_clipped > 2:
            score -= min(highlights_clipped * 3, 40)

        # Penalize shadow clipping
        if shadows_clipped > 2:
            score -= min(shadows_clipped * 3, 40)

        # Penalize extreme brightness (ideally 100-160 range)
        if brightness < 60:
            score -= min((60 - brightness) * 0.5, 25)
        elif brightness > 200:
            score -= min((brightness - 200) * 0.5, 25)

        # Reward good dynamic range (higher std_dev = more tonal range)
        if std_dev < 30:
            score -= 10  # Very flat / low contrast
            
        # Penalize high noise
        if noise_estimate > 5.0:
            score -= min(noise_estimate * 2.0, 20)

        score = max(0.0, min(100.0, score))

        # Map score to star rating
        if score >= 85:
            rating = 5
        elif score >= 70:
            rating = 4
        elif score >= 50:
            rating = 3
        elif score >= 30:
            rating = 2
        else:
            rating = 1

        # Verdict string
        if highlights_clipped > reject_threshold:
            verdict = "overexposed"
        elif shadows_clipped > reject_threshold:
            verdict = "underexposed"
        elif noise_estimate > 8.0:
            verdict = "noisy"
        elif score >= 70:
            verdict = "well-exposed"
        elif score >= 50:
            verdict = "acceptable"
        else:
            verdict = "poor-exposure"

        log.debug(f"Exposure: {Path(image_path).name} → score={score:.1f}, "
                  f"highlights={highlights_clipped:.1f}%, shadows={shadows_clipped:.1f}%, noise={noise_estimate:.1f}")

        return ExposureResult(score, rating, verdict,
                              round(highlights_clipped, 1), round(shadows_clipped, 1), round(noise_estimate, 1))

    except Exception as e:
        log.warning(f"Exposure analysis failed for {image_path}: {e}")
        return ExposureResult(50.0, 3, "error", 0.0, 0.0, 0.0)
