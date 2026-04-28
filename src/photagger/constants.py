"""
Photagger — Centralized constants and configuration defaults.
All magic numbers, paths, and strings live here.
"""
from pathlib import Path

# ─── App Identity ─────────────────────────────────────────────
APP_NAME = "Photagger"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Photagger"
APP_DESCRIPTION = "AI-Powered Photography Culling & Tagging Pipeline"

# ─── Package Paths ────────────────────────────────────────────
PACKAGE_DIR = Path(__file__).parent
RESOURCES_DIR = PACKAGE_DIR / "resources"

# ─── Supported Formats ───────────────────────────────────────
SUPPORTED_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp',
    '.raw', '.raf', '.dng', '.heic', '.heif',
    '.arw', '.cr2', '.cr3', '.nef', '.orf', '.rw2',
}

# ─── AI Model ────────────────────────────────────────────────
MODEL_FILENAME = "mobilenetv2-7.onnx"
CLASSES_FILENAME = "imagenet_classes.txt"
MODEL_URL = "https://github.com/onnx/models/raw/main/validated/vision/classification/mobilenet/model/mobilenetv2-7.onnx"
CLASSES_URL = "https://raw.githubusercontent.com/pytorch/hub/master/imagenet_classes.txt"

# ─── Processing Defaults ─────────────────────────────────────
DEFAULT_BLUR_THRESHOLD = 100.0
DEFAULT_TOP_K_TAGS = 3
DEFAULT_EXPOSURE_REJECT_THRESHOLD = 15  # percent
FILE_TRANSFER_TIMEOUT = 60  # seconds
FILE_STABLE_CHECKS = 2

# ─── Quality Rating Thresholds ───────────────────────────────
RATING_5_STAR_MIN_VARIANCE = 300.0
RATING_4_STAR_MIN_VARIANCE = 200.0
RATING_3_STAR_MIN_VARIANCE = 150.0

# ─── UI Color Palette ────────────────────────────────────────
class Colors:
    BG_PRIMARY = "#0F0F14"
    BG_SURFACE = "#1A1A24"
    BG_ELEVATED = "#22222E"
    BG_INPUT = "#13131A"
    BORDER = "#2A2A3A"
    BORDER_HOVER = "#3A3A50"
    ACCENT = "#6C63FF"
    ACCENT_HOVER = "#7B73FF"
    ACCENT_DIM = "#4A4499"
    SUCCESS = "#4ADE80"
    WARNING = "#FBBF24"
    ERROR = "#F87171"
    TEXT_PRIMARY = "#E8E8ED"
    TEXT_SECONDARY = "#8888A0"
    TEXT_DIM = "#555570"
    PROGRESS_BG = "#1E1E2E"
    THUMBNAIL_BG = "#12121A"
