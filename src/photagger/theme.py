"""
Photagger — Theme manager.
Handles light/dark/auto theme switching with OS detection and QSettings persistence.
"""
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import QSettings

from .constants import (
    APP_NAME, APP_AUTHOR, DarkPalette, LightPalette,
    FONT_FAMILY, FONT_MONO,
)

# Module-level active palette reference
_active_palette = DarkPalette


def get_palette():
    """Return the currently active color palette class."""
    return _active_palette


def set_palette(palette_cls):
    """Set the active palette globally."""
    global _active_palette
    _active_palette = palette_cls
    # Also update the constants.Colors alias
    import photagger.constants as c
    c.Colors = palette_cls


def detect_os_theme() -> str:
    """Detect the OS-level color scheme preference. Returns 'dark' or 'light'."""
    try:
        app = QApplication.instance()
        if app:
            hints = app.styleHints()
            if hasattr(hints, 'colorScheme'):
                scheme = hints.colorScheme()
                # Qt.ColorScheme.Dark == 2, Light == 1
                if scheme and scheme.value == 2:
                    return "dark"
                elif scheme and scheme.value == 1:
                    return "light"
    except Exception:
        pass

    # Fallback: check Windows registry
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return "light" if value == 1 else "dark"
    except Exception:
        return "dark"


def get_theme_preference() -> str:
    """Read the saved theme preference from QSettings. Returns 'auto', 'dark', or 'light'."""
    s = QSettings(APP_AUTHOR, APP_NAME)
    return s.value("ui/theme_mode", "dark")


def save_theme_preference(mode: str):
    """Save theme preference to QSettings."""
    s = QSettings(APP_AUTHOR, APP_NAME)
    s.setValue("ui/theme_mode", mode)


def resolve_theme(preference: str) -> str:
    """Resolve 'auto' to an actual theme. Returns 'dark' or 'light'."""
    if preference == "auto":
        return detect_os_theme()
    return preference


def apply_theme(mode: str = None):
    """
    Apply a theme to the running application.
    
    Args:
        mode: 'dark', 'light', or 'auto'. If None, reads from QSettings.
    """
    if mode is None:
        mode = get_theme_preference()

    resolved = resolve_theme(mode)
    P = DarkPalette if resolved == "dark" else LightPalette
    set_palette(P)

    app = QApplication.instance()
    if not app:
        return

    # Build Qt QPalette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(P.BG_PRIMARY))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(P.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Base, QColor(P.BG_INPUT))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(P.BG_SURFACE))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(P.BG_ELEVATED))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(P.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Text, QColor(P.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Button, QColor(P.BG_ELEVATED))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(P.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(P.ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(P.TEXT_INVERSE))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(P.TEXT_DIM))
    app.setPalette(palette)


def get_stylesheet() -> str:
    """Generate the full application stylesheet for the active palette."""
    P = get_palette()
    return f"""
        /* ── Global ─────────────────────────────────── */
        QMainWindow, QWidget {{
            background: {P.BG_PRIMARY};
            color: {P.TEXT_PRIMARY};
            font-family: {FONT_FAMILY};
        }}

        /* ── Buttons ────────────────────────────────── */
        QPushButton {{
            background: {P.BG_ELEVATED};
            border: 1px solid {P.BORDER};
            border-radius: 6px;
            padding: 8px 16px;
            color: {P.TEXT_PRIMARY};
            font-weight: 500;
            font-size: 13px;
        }}
        QPushButton:hover {{
            background: {P.BORDER_HOVER};
            border-color: {P.BORDER_HOVER};
        }}
        QPushButton:pressed {{
            background: {P.ACCENT_DIM};
        }}
        QPushButton:disabled {{
            color: {P.TEXT_DIM};
            border-color: {P.BORDER};
            background: {P.BG_SURFACE};
        }}

        /* ── Inputs ─────────────────────────────────── */
        QLineEdit {{
            background: {P.BG_INPUT};
            border: 1px solid {P.BORDER};
            border-radius: 6px;
            padding: 8px 12px;
            color: {P.TEXT_PRIMARY};
            font-size: 13px;
            selection-background-color: {P.ACCENT};
        }}
        QLineEdit:focus {{
            border-color: {P.BORDER_FOCUS};
        }}

        /* ── Text Areas ─────────────────────────────── */
        QTextEdit {{
            background: {P.BG_INPUT};
            border: 1px solid {P.BORDER};
            border-radius: 8px;
            color: {P.SUCCESS};
            font-family: {FONT_MONO};
            font-size: 12px;
            padding: 8px;
            selection-background-color: {P.ACCENT};
        }}

        /* ── Progress Bars ──────────────────────────── */
        QProgressBar {{
            border: none;
            border-radius: 4px;
            background: {P.PROGRESS_BG};
            text-align: center;
            color: {P.TEXT_PRIMARY};
            font-size: 11px;
            height: 8px;
        }}
        QProgressBar::chunk {{
            border-radius: 4px;
            background: {P.GRADIENT_PROGRESS};
        }}

        /* ── Scroll Bars ────────────────────────────── */
        QScrollBar:vertical {{
            background: transparent;
            width: 8px;
            border-radius: 4px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {P.BORDER};
            border-radius: 4px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {P.TEXT_DIM};
        }}
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical,
        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {{
            height: 0;
            background: transparent;
        }}
        QScrollBar:horizontal {{
            background: transparent;
            height: 8px;
            border-radius: 4px;
            margin: 0;
        }}
        QScrollBar::handle:horizontal {{
            background: {P.BORDER};
            border-radius: 4px;
            min-width: 30px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {P.TEXT_DIM};
        }}
        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal,
        QScrollBar::add-page:horizontal,
        QScrollBar::sub-page:horizontal {{
            width: 0;
            background: transparent;
        }}

        /* ── Scroll Areas ───────────────────────────── */
        QScrollArea {{
            border: none;
            background: transparent;
        }}

        /* ── Tooltips ───────────────────────────────── */
        QToolTip {{
            background: {P.BG_ELEVATED};
            color: {P.TEXT_PRIMARY};
            border: 1px solid {P.BORDER};
            border-radius: 4px;
            padding: 6px 10px;
            font-size: 12px;
        }}

        /* ── Menus ──────────────────────────────────── */
        QMenu {{
            background: {P.BG_ELEVATED};
            color: {P.TEXT_PRIMARY};
            border: 1px solid {P.BORDER};
            border-radius: 8px;
            padding: 4px;
        }}
        QMenu::item {{
            padding: 8px 24px 8px 12px;
            border-radius: 4px;
        }}
        QMenu::item:selected {{
            background: {P.ACCENT};
            color: {P.TEXT_INVERSE};
        }}
        QMenu::separator {{
            height: 1px;
            background: {P.BORDER};
            margin: 4px 8px;
        }}

        /* ── Combo Boxes ────────────────────────────── */
        QComboBox {{
            background: {P.BG_INPUT};
            border: 1px solid {P.BORDER};
            border-radius: 6px;
            padding: 6px 12px;
            color: {P.TEXT_PRIMARY};
            font-size: 13px;
        }}
        QComboBox:hover {{
            border-color: {P.BORDER_HOVER};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}
        QComboBox QAbstractItemView {{
            background: {P.BG_ELEVATED};
            border: 1px solid {P.BORDER};
            border-radius: 6px;
            color: {P.TEXT_PRIMARY};
            selection-background-color: {P.ACCENT};
            selection-color: {P.TEXT_INVERSE};
            padding: 4px;
        }}

        /* ── Spin Boxes ─────────────────────────────── */
        QSpinBox {{
            background: {P.BG_INPUT};
            color: {P.TEXT_PRIMARY};
            border: 1px solid {P.BORDER};
            border-radius: 4px;
            padding: 4px 8px;
        }}

        /* ── Check Boxes ────────────────────────────── */
        QCheckBox {{
            color: {P.TEXT_PRIMARY};
            spacing: 8px;
        }}

        /* ── Sliders ────────────────────────────────── */
        QSlider::groove:horizontal {{
            height: 6px;
            background: {P.BORDER};
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: {P.ACCENT};
            width: 16px;
            height: 16px;
            margin: -5px 0;
            border-radius: 8px;
        }}
        QSlider::sub-page:horizontal {{
            background: {P.ACCENT};
            border-radius: 3px;
        }}

        /* ── Dialogs ────────────────────────────────── */
        QDialog {{
            background: {P.BG_PRIMARY};
            color: {P.TEXT_PRIMARY};
        }}

        /* ── Frames ─────────────────────────────────── */
        QFrame[frameShape="4"] {{
            color: {P.BORDER};
        }}
    """
