"""
Photagger — Centralized constants and configuration defaults.
All magic numbers, paths, and strings live here.
"""
from pathlib import Path

# --- App Identity ---------------------------------------------------------
APP_NAME = "Photagger"
APP_VERSION = "2.0.0"
APP_AUTHOR = "Photagger"
APP_DESCRIPTION = "AI-Powered Photography Culling & Tagging Pipeline"

# --- Package Paths --------------------------------------------------------
PACKAGE_DIR = Path(__file__).parent
RESOURCES_DIR = PACKAGE_DIR / "resources"

# --- Supported Formats ----------------------------------------------------
SUPPORTED_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp',
    '.raw', '.raf', '.dng', '.heic', '.heif',
    '.arw', '.cr2', '.cr3', '.nef', '.orf', '.rw2',
}

# --- AI Model -------------------------------------------------------------
MODEL_FILENAME = "mobilenetv2-7.onnx"
CLASSES_FILENAME = "imagenet_classes.txt"
MODEL_URL = "https://github.com/onnx/models/raw/main/validated/vision/classification/mobilenet/model/mobilenetv2-7.onnx"
CLASSES_URL = "https://raw.githubusercontent.com/pytorch/hub/master/imagenet_classes.txt"

# --- Processing Defaults --------------------------------------------------
DEFAULT_BLUR_THRESHOLD = 100.0
DEFAULT_TOP_K_TAGS = 3
DEFAULT_EXPOSURE_REJECT_THRESHOLD = 15  # percent
FILE_TRANSFER_TIMEOUT = 60  # seconds
FILE_STABLE_CHECKS = 2

# --- Quality Rating Thresholds --------------------------------------------
RATING_5_STAR_MIN_VARIANCE = 300.0
RATING_4_STAR_MIN_VARIANCE = 200.0
RATING_3_STAR_MIN_VARIANCE = 150.0

# --- Typography -----------------------------------------------------------
FONT_FAMILY = "'Segoe UI', 'Inter', system-ui, -apple-system, sans-serif"
FONT_MONO = "'Cascadia Code', 'Consolas', 'SF Mono', monospace"

FONT_SIZE_XS = "10px"
FONT_SIZE_SM = "11px"
FONT_SIZE_MD = "13px"
FONT_SIZE_LG = "15px"
FONT_SIZE_XL = "18px"
FONT_SIZE_2XL = "22px"
FONT_SIZE_3XL = "28px"

# --- Spacing & Sizing -----------------------------------------------------
SIDEBAR_WIDTH = 56
SIDEBAR_EXPANDED_WIDTH = 180
STAT_CARD_HEIGHT = 80
THUMBNAIL_SIZE_SM = 160
THUMBNAIL_SIZE_MD = 200
THUMBNAIL_SIZE_LG = 260
VIEWER_FILMSTRIP_HEIGHT = 80

# --- Animation Durations (ms) --------------------------------------------
ANIM_FAST = 120
ANIM_NORMAL = 250
ANIM_SLOW = 400

# --- UI Color Palettes ----------------------------------------------------

class DarkPalette:
    """Dark mode color tokens."""
    BG_PRIMARY = "#0F0F14"
    BG_SURFACE = "#1A1A24"
    BG_ELEVATED = "#22222E"
    BG_INPUT = "#13131A"
    BG_SIDEBAR = "#111118"
    BG_OVERLAY = "rgba(0, 0, 0, 0.65)"

    BORDER = "#2A2A3A"
    BORDER_HOVER = "#3A3A50"
    BORDER_FOCUS = "#6C63FF"

    ACCENT = "#6C63FF"
    ACCENT_HOVER = "#7B73FF"
    ACCENT_DIM = "#4A4499"
    ACCENT_SUBTLE = "rgba(108, 99, 255, 0.12)"

    SUCCESS = "#4ADE80"
    SUCCESS_DIM = "rgba(74, 222, 128, 0.15)"
    WARNING = "#FBBF24"
    WARNING_DIM = "rgba(251, 191, 36, 0.15)"
    ERROR = "#F87171"
    ERROR_DIM = "rgba(248, 113, 113, 0.15)"

    TEXT_PRIMARY = "#E8E8ED"
    TEXT_SECONDARY = "#8888A0"
    TEXT_DIM = "#555570"
    TEXT_INVERSE = "#0F0F14"

    PROGRESS_BG = "#1E1E2E"
    THUMBNAIL_BG = "#12121A"

    # Semantic status colors
    STATUS_WATCHING = "#4ADE80"
    STATUS_BOOTING = "#FBBF24"
    STATUS_PROCESSING = "#6C63FF"
    STATUS_IDLE = "#555570"
    STATUS_ERROR = "#F87171"

    # Gradients (CSS linear-gradient format)
    GRADIENT_ACCENT = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6C63FF, stop:1 #A78BFA)"
    GRADIENT_SUCCESS = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4ADE80, stop:1 #34D399)"
    GRADIENT_ERROR = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #F87171, stop:1 #FB923C)"
    GRADIENT_PROGRESS = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6C63FF, stop:1 #4ADE80)"


class LightPalette:
    """Light mode color tokens."""
    BG_PRIMARY = "#F8F8FA"
    BG_SURFACE = "#FFFFFF"
    BG_ELEVATED = "#F0F0F5"
    BG_INPUT = "#FFFFFF"
    BG_SIDEBAR = "#F0F0F5"
    BG_OVERLAY = "rgba(255, 255, 255, 0.75)"

    BORDER = "#D8D8E0"
    BORDER_HOVER = "#B0B0C0"
    BORDER_FOCUS = "#5B52E0"

    ACCENT = "#5B52E0"
    ACCENT_HOVER = "#4A42CC"
    ACCENT_DIM = "#8880F0"
    ACCENT_SUBTLE = "rgba(91, 82, 224, 0.08)"

    SUCCESS = "#16A34A"
    SUCCESS_DIM = "rgba(22, 163, 74, 0.10)"
    WARNING = "#D97706"
    WARNING_DIM = "rgba(217, 119, 6, 0.10)"
    ERROR = "#DC2626"
    ERROR_DIM = "rgba(220, 38, 38, 0.10)"

    TEXT_PRIMARY = "#1A1A2E"
    TEXT_SECONDARY = "#6B6B80"
    TEXT_DIM = "#9999AA"
    TEXT_INVERSE = "#FFFFFF"

    PROGRESS_BG = "#E8E8F0"
    THUMBNAIL_BG = "#F0F0F5"

    # Semantic status colors
    STATUS_WATCHING = "#16A34A"
    STATUS_BOOTING = "#D97706"
    STATUS_PROCESSING = "#5B52E0"
    STATUS_IDLE = "#9999AA"
    STATUS_ERROR = "#DC2626"

    # Gradients
    GRADIENT_ACCENT = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #5B52E0, stop:1 #8880F0)"
    GRADIENT_SUCCESS = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #16A34A, stop:1 #22C55E)"
    GRADIENT_ERROR = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #DC2626, stop:1 #F97316)"
    GRADIENT_PROGRESS = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5B52E0, stop:1 #16A34A)"


# Default active palette (used as fallback and by modules that import Colors)
Colors = DarkPalette
