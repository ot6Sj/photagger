"""
Photagger — Thumbnail gallery widget with filtering, sorting, search, and dynamic columns.
"""
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QLabel, QFrame, QMenu, QSizePolicy, QComboBox, QLineEdit
)
from PyQt6.QtGui import QPixmap, QAction, QDesktopServices
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QSize

from .theme import get_palette
from . import icons


class ThumbnailCard(QFrame):
    """A single image thumbnail card with metadata."""
    clicked = pyqtSignal(dict)
    double_clicked = pyqtSignal(dict)

    def __init__(self, entry: dict, thumb_size: int = 180, parent=None):
        super().__init__(parent)
        self.entry = entry
        self._thumb_size = thumb_size
        card_h = thumb_size + 50
        self.setFixedSize(thumb_size + 12, card_h)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("thumbnail_card")

        P = get_palette()
        status = entry.get("status", "accepted")
        border_color = P.SUCCESS if status == "accepted" else P.ERROR
        self.setStyleSheet(f"""
            #thumbnail_card {{
                background: {P.BG_SURFACE};
                border: 2px solid {border_color};
                border-radius: 8px;
            }}
            #thumbnail_card:hover {{
                border-color: {P.ACCENT};
                background: {P.BG_ELEVATED};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # Thumbnail image
        img_w = thumb_size
        img_h = int(thumb_size * 0.72)
        self.img_label = QLabel()
        self.img_label.setFixedSize(img_w, img_h)
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_label.setStyleSheet(f"background: {P.THUMBNAIL_BG}; border-radius: 4px;")

        final_path = entry.get("final_path", "")
        if final_path and Path(final_path).exists():
            pixmap = QPixmap(final_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(img_w, img_h,
                                       Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
                self.img_label.setPixmap(pixmap)
            else:
                self.img_label.setText("!")
                self.img_label.setStyleSheet(f"background: {P.THUMBNAIL_BG}; border-radius: 4px; color: {P.WARNING}; font-size: 16px; font-weight: 700;")
        else:
            self.img_label.setText("No preview")
            self.img_label.setStyleSheet(f"background: {P.THUMBNAIL_BG}; border-radius: 4px; color: {P.TEXT_DIM}; font-size: 11px;")

        layout.addWidget(self.img_label)

        # Filename
        name_text = entry.get("filename", "Unknown")
        if len(name_text) > 28:
            name_text = name_text[:25] + "..."
        name_label = QLabel(name_text)
        name_label.setStyleSheet(f"color: {P.TEXT_PRIMARY}; font-size: 11px; font-weight: 500;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)

        # Category + rating
        cat = entry.get("category", "")
        rating = entry.get("star_rating", 0)
        stars = "\u2605" * rating + "\u2606" * (5 - rating)
        info_text = f"{cat.capitalize()}  {stars}" if cat else stars
        info_label = QLabel(info_text)
        info_label.setStyleSheet(f"color: {P.TEXT_SECONDARY}; font-size: 10px;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.entry)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.entry)
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        P = get_palette()
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {P.BG_ELEVATED};
                color: {P.TEXT_PRIMARY};
                border: 1px solid {P.BORDER};
                border-radius: 6px;
                padding: 4px;
            }}
            QMenu::item {{ padding: 8px 24px 8px 12px; border-radius: 4px; }}
            QMenu::item:selected {{ background: {P.ACCENT}; color: {P.TEXT_INVERSE}; }}
        """)

        open_action = QAction("Reveal in Explorer", self)
        open_action.triggered.connect(self._open_in_explorer)
        menu.addAction(open_action)

        view_action = QAction("Open in Viewer", self)
        view_action.triggered.connect(lambda: self.double_clicked.emit(self.entry))
        menu.addAction(view_action)

        menu.exec(event.globalPos())

    def _open_in_explorer(self):
        path = self.entry.get("final_path", "")
        if path and Path(path).exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(path).parent)))


class GalleryWidget(QWidget):
    """Scrollable thumbnail grid with filter bar, sort, search, and dynamic columns."""
    card_selected = pyqtSignal(dict)
    card_double_clicked = pyqtSignal(dict)  # opens viewer

    MIN_CARD_WIDTH = 192

    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries: list[dict] = []
        self._filtered: list[dict] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Filter bar
        filter_frame = QFrame()
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(12, 8, 12, 8)
        filter_layout.setSpacing(8)

        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search tags, filenames...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setFixedWidth(220)
        self.search_input.textChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.search_input)

        # Status filter
        self.status_combo = QComboBox()
        self.status_combo.addItems(["All", "Accepted", "Rejected"])
        self.status_combo.setFixedWidth(110)
        self.status_combo.currentTextChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.status_combo)

        # Category filter
        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories")
        self.category_combo.setFixedWidth(150)
        self.category_combo.currentTextChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.category_combo)

        # Rating filter
        self.rating_combo = QComboBox()
        self.rating_combo.addItems(["Any Rating", "\u2265 1\u2605", "\u2265 2\u2605", "\u2265 3\u2605", "\u2265 4\u2605", "5\u2605"])
        self.rating_combo.setFixedWidth(110)
        self.rating_combo.currentIndexChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.rating_combo)

        filter_layout.addStretch()

        # Sort
        sort_label = QLabel("Sort:")
        sort_label.setStyleSheet("font-size: 12px;")
        filter_layout.addWidget(sort_label)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Newest First", "Oldest First", "Rating High-Low", "Rating Low-High", "Filename A-Z"])
        self.sort_combo.setFixedWidth(140)
        self.sort_combo.currentTextChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.sort_combo)

        # Count label
        self.count_label = QLabel("No images processed yet")
        self.count_label.setStyleSheet("font-size: 12px; padding-left: 8px;")
        filter_layout.addWidget(self.count_label)

        layout.addWidget(filter_frame)

        # Scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(12)
        self.grid_layout.setContentsMargins(12, 12, 12, 12)
        self.scroll.setWidget(self.grid_widget)
        layout.addWidget(self.scroll)

        self._categories_seen: set[str] = set()

    def add_entry(self, entry: dict):
        """Add a new processed image entry to the gallery."""
        self._entries.insert(0, entry)
        cat = entry.get("category", "")
        if cat and cat not in self._categories_seen:
            self._categories_seen.add(cat)
            self.category_combo.addItem(cat.capitalize())
        self._apply_filters()

    def _apply_filters(self):
        """Filter and sort entries, then rebuild the grid."""
        query = self.search_input.text().strip().lower()
        status = self.status_combo.currentText().lower()
        category = self.category_combo.currentText()
        rating_idx = self.rating_combo.currentIndex()
        min_rating = rating_idx  # 0=any, 1=1+, 2=2+, etc.
        sort_key = self.sort_combo.currentText()

        filtered = []
        for e in self._entries:
            # Status filter
            if status != "all" and e.get("status", "") != status:
                continue
            # Category filter
            if category != "All Categories":
                if e.get("category", "").capitalize() != category:
                    continue
            # Rating filter
            if min_rating > 0 and e.get("star_rating", 0) < min_rating:
                continue
            # Search filter
            if query:
                searchable = f"{e.get('filename', '')} {e.get('tags', '')} {e.get('category', '')}".lower()
                if query not in searchable:
                    continue
            filtered.append(e)

        # Sort
        if sort_key == "Newest First":
            pass  # already newest-first from insert(0)
        elif sort_key == "Oldest First":
            filtered = list(reversed(filtered))
        elif sort_key == "Rating High-Low":
            filtered.sort(key=lambda x: x.get("star_rating", 0), reverse=True)
        elif sort_key == "Rating Low-High":
            filtered.sort(key=lambda x: x.get("star_rating", 0))
        elif sort_key == "Filename A-Z":
            filtered.sort(key=lambda x: x.get("filename", "").lower())

        self._filtered = filtered
        self._rebuild_grid()

    def _rebuild_grid(self):
        """Clear and rebuild the grid layout with dynamic column count."""
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Dynamic column count based on available width
        avail = self.scroll.viewport().width() - 24
        cols = max(1, avail // self.MIN_CARD_WIDTH) if avail > 0 else 4

        for i, entry in enumerate(self._filtered[:300]):
            card = ThumbnailCard(entry, parent=self.grid_widget)
            card.clicked.connect(self.card_selected.emit)
            card.double_clicked.connect(self.card_double_clicked.emit)
            row, col = divmod(i, cols)
            self.grid_layout.addWidget(card, row, col)

        # Stats
        accepted = sum(1 for e in self._entries if e.get("status") == "accepted")
        rejected = sum(1 for e in self._entries if e.get("status") == "rejected")
        showing = len(self._filtered)
        total = len(self._entries)
        self.count_label.setText(
            f"Showing {showing} of {total}  |  {accepted} accepted  |  {rejected} rejected"
        )

    def resizeEvent(self, event):
        """Rebuild grid on resize for dynamic columns."""
        super().resizeEvent(event)
        if self._filtered:
            self._rebuild_grid()

    def get_all_entries(self) -> list[dict]:
        """Return all entries (unfiltered)."""
        return list(self._entries)

    def get_filtered_entries(self) -> list[dict]:
        """Return currently filtered entries."""
        return list(self._filtered)

    def load_from_history(self, entries: list[dict]):
        """Load entries from history database."""
        self._entries = entries
        for e in entries:
            cat = e.get("category", "")
            if cat and cat not in self._categories_seen:
                self._categories_seen.add(cat)
                self.category_combo.addItem(cat.capitalize())
        self._apply_filters()

    def apply_theme(self):
        P = get_palette()
        self.setStyleSheet(f"background: {P.BG_PRIMARY};")
        self.count_label.setStyleSheet(f"color: {P.TEXT_SECONDARY}; font-size: 12px; padding-left: 8px;")
        self._apply_filters()  # rebuild with new palette
