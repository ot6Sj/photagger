"""
Photagger — Centralized keyboard shortcut manager.
Defines all keyboard shortcuts and provides a help overlay listing.
"""
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QWidget


# Shortcut definitions: (action_id, key_sequence, description, category)
SHORTCUT_DEFS = [
    # Engine
    ("toggle_engine",   "Space",      "Start / Stop engine",     "Engine"),
    # Navigation
    ("go_monitor",      "M",          "Switch to Monitor",       "Navigation"),
    ("go_gallery",      "G",          "Switch to Gallery",       "Navigation"),
    ("go_viewer",       "F",          "Open image viewer",       "Navigation"),
    # Gallery / Viewer
    ("nav_prev",        "Left",       "Previous image",          "Gallery"),
    ("nav_next",        "Right",      "Next image",              "Gallery"),
    ("accept_image",    "A",          "Accept image",            "Gallery"),
    ("reject_image",    "X",          "Reject image",            "Gallery"),
    ("undo_action",     "Ctrl+Z",     "Undo last action",        "Gallery"),
    # Ratings
    ("rate_1",          "1",          "Rate 1 star",             "Rating"),
    ("rate_2",          "2",          "Rate 2 stars",            "Rating"),
    ("rate_3",          "3",          "Rate 3 stars",            "Rating"),
    ("rate_4",          "4",          "Rate 4 stars",            "Rating"),
    ("rate_5",          "5",          "Rate 5 stars",            "Rating"),
    ("rate_0",          "0",          "Clear rating",            "Rating"),
    # Viewer
    ("toggle_exif",     "I",          "Toggle EXIF overlay",     "Viewer"),
    ("toggle_compare",  "C",          "Toggle compare mode",     "Viewer"),
    ("zoom_fit",        "Ctrl+0",     "Fit to window",           "Viewer"),
    ("zoom_100",        "Ctrl+1",     "Zoom to 100%",            "Viewer"),
    # App
    ("open_settings",   "Ctrl+,",     "Open settings",           "App"),
    ("generate_report", "Ctrl+R",     "Generate report",         "App"),
    ("toggle_theme",    "Ctrl+T",     "Toggle light/dark theme", "App"),
    ("show_shortcuts",  "?",          "Show keyboard shortcuts",  "App"),
]


class ShortcutManager:
    """Registers and manages keyboard shortcuts for a parent widget."""

    def __init__(self, parent: QWidget):
        self._parent = parent
        self._shortcuts: dict[str, QShortcut] = {}
        self._callbacks: dict[str, callable] = {}

    def register(self, action_id: str, callback: callable):
        """Register a callback for a shortcut action."""
        self._callbacks[action_id] = callback

        # Find the key sequence from definitions
        for aid, key_seq, desc, cat in SHORTCUT_DEFS:
            if aid == action_id:
                shortcut = QShortcut(QKeySequence(key_seq), self._parent)
                shortcut.activated.connect(callback)
                self._shortcuts[action_id] = shortcut
                return shortcut
        return None

    def register_all(self, callback_map: dict[str, callable]):
        """Register multiple shortcuts from a dict of {action_id: callback}."""
        for action_id, cb in callback_map.items():
            self.register(action_id, cb)

    def get_help_text(self) -> list[tuple[str, str, str]]:
        """Return list of (category, key, description) for the help overlay."""
        results = []
        for aid, key_seq, desc, cat in SHORTCUT_DEFS:
            results.append((cat, key_seq, desc))
        return results

    def get_grouped_help(self) -> dict[str, list[tuple[str, str]]]:
        """Return shortcuts grouped by category: {category: [(key, desc), ...]}."""
        groups: dict[str, list[tuple[str, str]]] = {}
        for aid, key_seq, desc, cat in SHORTCUT_DEFS:
            groups.setdefault(cat, []).append((key_seq, desc))
        return groups
