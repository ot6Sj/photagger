"""
Photagger — Full-screen image viewer with zoom, pan, filmstrip, and EXIF overlay.
"""
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QSizePolicy
)
from PyQt6.QtGui import QPixmap, QWheelEvent, QMouseEvent, QPainter, QColor, QBrush
from PyQt6.QtCore import Qt, QPointF, pyqtSignal, QRectF

from .constants import FONT_MONO
from .theme import get_palette
from . import icons


class ZoomableImageView(QGraphicsView):
    """A graphics view with smooth zoom and pan for high-res images."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._pixmap_item: QGraphicsPixmapItem | None = None
        self._zoom = 1.0

        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.Shape.NoFrame)

    def set_image(self, path: str):
        """Load and display an image from path."""
        self._scene.clear()
        pixmap = QPixmap(path)
        if pixmap.isNull():
            return
        self._pixmap_item = self._scene.addPixmap(pixmap)
        self._scene.setSceneRect(QRectF(pixmap.rect()))
        self.fit_in_view()

    def fit_in_view(self):
        """Fit image to the viewport."""
        if self._pixmap_item:
            self.fitInView(self._pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
            self._zoom = 1.0

    def zoom_100(self):
        """Set zoom to 100% (1:1 pixel mapping)."""
        self.resetTransform()
        self._zoom = 1.0

    def wheelEvent(self, event: QWheelEvent):
        """Zoom with scroll wheel."""
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self._zoom *= factor
        self._zoom = max(0.1, min(self._zoom, 20.0))
        self.scale(factor, factor)

    def resizeEvent(self, event):
        """Re-fit on resize."""
        super().resizeEvent(event)
        if self._pixmap_item:
            self.fit_in_view()

    def apply_theme(self):
        P = get_palette()
        self.setStyleSheet(f"background: {P.BG_PRIMARY}; border: none;")
        self._scene.setBackgroundBrush(QBrush(QColor(P.BG_PRIMARY)))


class FilmstripWidget(QScrollArea):
    """Horizontal filmstrip of small thumbnails for navigation."""
    thumbnail_clicked = pyqtSignal(int)  # index

    THUMB_SIZE = 64

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFixedHeight(self.THUMB_SIZE + 16)
        self.setFrameShape(QFrame.Shape.NoFrame)

        self._container = QWidget()
        self._layout = QHBoxLayout(self._container)
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._layout.setSpacing(4)
        self._layout.addStretch()
        self.setWidget(self._container)

        self._entries: list[dict] = []
        self._selected_idx = -1
        self._thumb_labels: list[QLabel] = []

    def set_entries(self, entries: list[dict]):
        """Set the list of entries to display."""
        self._entries = entries
        self._rebuild()

    def _rebuild(self):
        # Clear
        for lbl in self._thumb_labels:
            lbl.deleteLater()
        self._thumb_labels.clear()

        # Remove stretch
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        P = get_palette()
        for i, entry in enumerate(self._entries[:100]):
            lbl = QLabel()
            lbl.setFixedSize(self.THUMB_SIZE, self.THUMB_SIZE)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setCursor(Qt.CursorShape.PointingHandCursor)

            path = entry.get("final_path", "")
            if path and Path(path).exists():
                px = QPixmap(path)
                if not px.isNull():
                    px = px.scaled(self.THUMB_SIZE, self.THUMB_SIZE,
                                   Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
                    lbl.setPixmap(px)

            border = P.BORDER
            if i == self._selected_idx:
                border = P.ACCENT

            lbl.setStyleSheet(f"""
                background: {P.BG_SURFACE};
                border: 2px solid {border};
                border-radius: 4px;
            """)

            # Capture index
            idx = i
            lbl.mousePressEvent = lambda e, ii=idx: self._on_click(ii)
            self._layout.addWidget(lbl)
            self._thumb_labels.append(lbl)

        self._layout.addStretch()

    def _on_click(self, idx: int):
        self._selected_idx = idx
        self.thumbnail_clicked.emit(idx)
        self._update_selection()

    def set_selected(self, idx: int):
        self._selected_idx = idx
        self._update_selection()
        # Scroll to visible
        if 0 <= idx < len(self._thumb_labels):
            self.ensureWidgetVisible(self._thumb_labels[idx])

    def _update_selection(self):
        P = get_palette()
        for i, lbl in enumerate(self._thumb_labels):
            border = P.ACCENT if i == self._selected_idx else P.BORDER
            lbl.setStyleSheet(f"""
                background: {P.BG_SURFACE};
                border: 2px solid {border};
                border-radius: 4px;
            """)

    def apply_theme(self):
        P = get_palette()
        self.setStyleSheet(f"background: {P.BG_SURFACE}; border: none;")
        self._update_selection()


class ImageViewer(QWidget):
    """Full image viewer with zoom, filmstrip, EXIF overlay, and navigation."""
    back_requested = pyqtSignal()
    entry_changed = pyqtSignal(dict)  # emitted when active entry changes

    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries: list[dict] = []
        self._current_idx = -1
        self._show_exif = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top toolbar
        self._toolbar = QHBoxLayout()
        self._toolbar.setContentsMargins(12, 8, 12, 8)
        self._toolbar.setSpacing(8)

        toolbar_frame = QFrame()
        toolbar_frame.setLayout(self._toolbar)
        layout.addWidget(toolbar_frame)

        # Filename label
        self._filename_label = QLabel("No image selected")
        self._filename_label.setStyleSheet("font-size: 14px; font-weight: 600;")
        self._toolbar.addWidget(self._filename_label)
        self._toolbar.addStretch()

        # Info label (rating, category)
        self._info_label = QLabel("")
        self._info_label.setStyleSheet("font-size: 12px;")
        self._toolbar.addWidget(self._info_label)

        # Main image view
        self._image_view = ZoomableImageView()
        layout.addWidget(self._image_view, stretch=1)

        # EXIF overlay
        self._exif_overlay = QLabel("")
        self._exif_overlay.setWordWrap(True)
        self._exif_overlay.setVisible(self._show_exif)
        self._exif_overlay.setFixedWidth(260)
        self._exif_overlay.setAlignment(Qt.AlignmentFlag.AlignTop)
        # Position as overlay (will be placed by parent or manually)

        # Filmstrip
        self._filmstrip = FilmstripWidget()
        self._filmstrip.thumbnail_clicked.connect(self._on_filmstrip_click)
        layout.addWidget(self._filmstrip)

        self.apply_theme()

    def set_entries(self, entries: list[dict], start_index: int = 0):
        """Set the entry list and navigate to start_index."""
        self._entries = entries
        self._filmstrip.set_entries(entries)
        if entries:
            self.navigate_to(start_index)

    def navigate_to(self, idx: int):
        """Navigate to a specific entry index."""
        if not self._entries or idx < 0 or idx >= len(self._entries):
            return
        self._current_idx = idx
        entry = self._entries[idx]

        path = entry.get("final_path", "")
        if path and Path(path).exists():
            self._image_view.set_image(path)

        self._filename_label.setText(entry.get("filename", "Unknown"))

        # Build info string
        rating = entry.get("star_rating", 0)
        cat = entry.get("category", "")
        stars = "\u2605" * rating + "\u2606" * (5 - rating)
        status = entry.get("status", "")
        info_parts = []
        if cat:
            info_parts.append(cat.capitalize())
        info_parts.append(stars)
        if status:
            info_parts.append(f"[{status.upper()}]")
        self._info_label.setText("  |  ".join(info_parts))

        # Update filmstrip selection
        self._filmstrip.set_selected(idx)
        self.entry_changed.emit(entry)

    def navigate_prev(self):
        if self._current_idx > 0:
            self.navigate_to(self._current_idx - 1)

    def navigate_next(self):
        if self._current_idx < len(self._entries) - 1:
            self.navigate_to(self._current_idx + 1)

    def toggle_exif(self):
        self._show_exif = not self._show_exif
        self._exif_overlay.setVisible(self._show_exif)

    def fit_view(self):
        self._image_view.fit_in_view()

    def zoom_100(self):
        self._image_view.zoom_100()

    def _on_filmstrip_click(self, idx: int):
        self.navigate_to(idx)

    def get_current_entry(self) -> dict | None:
        if 0 <= self._current_idx < len(self._entries):
            return self._entries[self._current_idx]
        return None

    def apply_theme(self):
        P = get_palette()
        self.setStyleSheet(f"background: {P.BG_PRIMARY};")
        self._image_view.apply_theme()
        self._filmstrip.apply_theme()
        self._filename_label.setStyleSheet(
            f"color: {P.TEXT_PRIMARY}; font-size: 14px; font-weight: 600;"
        )
        self._info_label.setStyleSheet(
            f"color: {P.TEXT_SECONDARY}; font-size: 12px;"
        )
        self._exif_overlay.setStyleSheet(f"""
            background: {P.BG_OVERLAY};
            color: {P.TEXT_PRIMARY};
            border-radius: 8px;
            padding: 12px;
            font-family: {FONT_MONO};
            font-size: 11px;
        """)
        # Toolbar frame
        for child in self.findChildren(QFrame):
            if child.layout() == self._toolbar:
                child.setStyleSheet(f"background: {P.BG_SURFACE}; border-bottom: 1px solid {P.BORDER};")
                break
