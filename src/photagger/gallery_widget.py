"""
Photagger — Thumbnail gallery widget for processed images.
Displays a scrollable grid of processed photos with metadata overlays.
"""
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QLabel, QFrame, QMenu, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QAction, QDesktopServices
from PyQt6.QtCore import Qt, QSize, QUrl, pyqtSignal
from .constants import Colors


class ThumbnailCard(QFrame):
    """A single image thumbnail card with metadata."""
    clicked = pyqtSignal(dict)

    def __init__(self, entry: dict, parent=None):
        super().__init__(parent)
        self.entry = entry
        self.setFixedSize(180, 210)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("thumbnail_card")

        status = entry.get("status", "accepted")
        border_color = Colors.SUCCESS if status == "accepted" else Colors.ERROR
        self.setStyleSheet(f"""
            #thumbnail_card {{
                background: {Colors.BG_SURFACE};
                border: 2px solid {border_color};
                border-radius: 8px;
            }}
            #thumbnail_card:hover {{
                border-color: {Colors.ACCENT};
                background: {Colors.BG_ELEVATED};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # Thumbnail image
        self.img_label = QLabel()
        self.img_label.setFixedSize(168, 130)
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_label.setStyleSheet(f"background: {Colors.THUMBNAIL_BG}; border-radius: 4px;")

        final_path = entry.get("final_path", "")
        if final_path and Path(final_path).exists():
            pixmap = QPixmap(final_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(168, 130,
                                       Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
                self.img_label.setPixmap(pixmap)
            else:
                self.img_label.setText("⚠️")
        else:
            self.img_label.setText("📷")

        layout.addWidget(self.img_label)

        # Filename
        name_label = QLabel(entry.get("filename", "Unknown")[:24])
        name_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 11px; font-weight: 500;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)

        # Category + rating
        cat = entry.get("category", "")
        rating = entry.get("star_rating", 0)
        info_label = QLabel(f"{cat.capitalize()} · {'⭐' * rating}")
        info_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 10px;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.entry)
        super().mousePressEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {Colors.BG_ELEVATED};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                padding: 4px;
            }}
            QMenu::item:selected {{
                background: {Colors.ACCENT};
                border-radius: 4px;
            }}
        """)

        open_action = QAction("Open in Explorer", self)
        open_action.triggered.connect(self._open_in_explorer)
        menu.addAction(open_action)
        menu.exec(event.globalPos())

    def _open_in_explorer(self):
        path = self.entry.get("final_path", "")
        if path and Path(path).exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(path).parent)))


class GalleryWidget(QWidget):
    """Scrollable thumbnail grid showing all processed images."""
    card_selected = pyqtSignal(dict)

    COLS = 4

    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries: list[dict] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QHBoxLayout()
        self.count_label = QLabel("No images processed yet")
        self.count_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 13px; padding: 8px;")
        header.addWidget(self.count_label)
        header.addStretch()
        layout.addLayout(header)

        # Scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: {Colors.BG_PRIMARY};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {Colors.BORDER};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {Colors.TEXT_DIM};
            }}
        """)

        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(12)
        self.grid_layout.setContentsMargins(8, 8, 8, 8)
        self.scroll.setWidget(self.grid_widget)
        layout.addWidget(self.scroll)

    def add_entry(self, entry: dict):
        """Add a new processed image entry to the gallery."""
        self._entries.insert(0, entry)
        self._rebuild_grid()

    def _rebuild_grid(self):
        """Clear and rebuild the grid layout."""
        # Clear existing
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, entry in enumerate(self._entries[:200]):  # Cap at 200 for performance
            card = ThumbnailCard(entry, self.grid_widget)
            card.clicked.connect(self.card_selected.emit)
            row, col = divmod(i, self.COLS)
            self.grid_layout.addWidget(card, row, col)

        accepted = sum(1 for e in self._entries if e.get("status") == "accepted")
        rejected = sum(1 for e in self._entries if e.get("status") == "rejected")
        self.count_label.setText(
            f"📷 {len(self._entries)} images  ·  "
            f"✅ {accepted} accepted  ·  "
            f"❌ {rejected} rejected"
        )

    def load_from_history(self, entries: list[dict]):
        """Load entries from history database."""
        self._entries = entries
        self._rebuild_grid()
