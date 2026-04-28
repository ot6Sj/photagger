"""
Photagger — Premium desktop UI.
Main application window with tabbed interface, stats dashboard, and settings.
"""
import sys
import os
import time

import onnxruntime  # Pre-load DLLs before PyQt6

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QTextEdit,
    QProgressBar, QFrame, QSizePolicy, QTabWidget, QDialog,
    QSlider, QCheckBox, QSpinBox, QFormLayout, QDialogButtonBox,
    QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QColor, QPixmap, QFont, QIcon, QDragEnterEvent, QDropEvent
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve

from .watcher import EngineWorker
from .config import AppConfig
from .constants import Colors, APP_NAME, APP_VERSION, DEFAULT_BLUR_THRESHOLD
from .gallery_widget import GalleryWidget
from .history_db import HistoryDB
from .session_report import generate_html_report, generate_csv_report
from .exif_reader import format_exif_summary
from .logger import setup_logging, get_logger

log = get_logger("app")


# ═══════════════════════════════════════════════════════════════
#  SETTINGS DIALOG
# ═══════════════════════════════════════════════════════════════

class SettingsDialog(QDialog):
    """Modal settings dialog for processing parameters."""

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Settings")
        self.setFixedSize(460, 380)
        self.setStyleSheet(f"""
            QDialog {{
                background: {Colors.BG_PRIMARY};
                color: {Colors.TEXT_PRIMARY};
            }}
            QLabel {{
                color: {Colors.TEXT_SECONDARY};
                font-size: 13px;
            }}
            QSlider::groove:horizontal {{
                height: 6px;
                background: {Colors.BORDER};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {Colors.ACCENT};
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
            QSlider::sub-page:horizontal {{
                background: {Colors.ACCENT};
                border-radius: 3px;
            }}
            QSpinBox, QCheckBox {{
                background: {Colors.BG_INPUT};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                padding: 4px 8px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("⚙️ Processing Settings")
        title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 18px; font-weight: 700;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)

        # Blur threshold
        blur_layout = QHBoxLayout()
        self.blur_slider = QSlider(Qt.Orientation.Horizontal)
        self.blur_slider.setRange(20, 500)
        self.blur_slider.setValue(int(config.blur_threshold))
        self.blur_label = QLabel(f"{int(config.blur_threshold)}")
        self.blur_label.setFixedWidth(40)
        self.blur_label.setStyleSheet(f"color: {Colors.ACCENT}; font-weight: 600;")
        self.blur_slider.valueChanged.connect(lambda v: self.blur_label.setText(str(v)))
        blur_layout.addWidget(self.blur_slider)
        blur_layout.addWidget(self.blur_label)
        form.addRow("Blur Threshold:", blur_layout)

        # Top K tags
        self.topk_spin = QSpinBox()
        self.topk_spin.setRange(1, 10)
        self.topk_spin.setValue(config.top_k_tags)
        form.addRow("AI Tags Count:", self.topk_spin)

        # Auto categorize
        self.cat_check = QCheckBox("Auto-sort into category subfolders")
        self.cat_check.setChecked(config.auto_categorize)
        self.cat_check.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        form.addRow("", self.cat_check)

        # Exposure reject
        self.exp_check = QCheckBox("Auto-reject badly exposed images")
        self.exp_check.setChecked(config.exposure_reject)
        self.exp_check.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        form.addRow("", self.exp_check)

        layout.addLayout(form)
        layout.addStretch()

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.BG_ELEVATED};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: {Colors.ACCENT}; }}
        """)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self):
        self.config.blur_threshold = self.blur_slider.value()
        self.config.top_k_tags = self.topk_spin.value()
        self.config.auto_categorize = self.cat_check.isChecked()
        self.config.exposure_reject = self.exp_check.isChecked()
        self.accept()


# ═══════════════════════════════════════════════════════════════
#  STAT CARD WIDGET
# ═══════════════════════════════════════════════════════════════

class StatCard(QFrame):
    """Compact dashboard stat card."""

    def __init__(self, label: str, initial: str = "0", color: str = Colors.ACCENT):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG_SURFACE};
                border: 1px solid {Colors.BORDER};
                border-radius: 10px;
                padding: 12px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(2)

        self.value_label = QLabel(initial)
        self.value_label.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: 700;")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.value_label)

        desc = QLabel(label)
        desc.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 11px; text-transform: uppercase; letter-spacing: 1px;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

    def set_value(self, val):
        self.value_label.setText(str(val))


# ═══════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ═══════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    """Photagger main application window."""

    def __init__(self):
        super().__init__()
        self.config = AppConfig()
        self.worker = None
        self._stats = {"processed": 0, "accepted": 0, "rejected": 0}

        self.setWindowTitle(f"{APP_NAME} — AI Photography Tagger")
        self.setMinimumSize(960, 680)
        self.setAcceptDrops(True)

        self._apply_theme()
        self._build_ui()
        self._restore_state()

        log.info("Application started")

    # ─── Theme ────────────────────────────────────────────────
    def _apply_theme(self):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background: {Colors.BG_PRIMARY};
                color: {Colors.TEXT_PRIMARY};
                font-family: 'Segoe UI', system-ui, sans-serif;
            }}
            QTabWidget::pane {{
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                background: {Colors.BG_PRIMARY};
                top: -1px;
            }}
            QTabBar::tab {{
                background: {Colors.BG_SURFACE};
                color: {Colors.TEXT_SECONDARY};
                padding: 10px 24px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 600;
                font-size: 13px;
            }}
            QTabBar::tab:selected {{
                background: {Colors.BG_PRIMARY};
                color: {Colors.ACCENT};
                border: 1px solid {Colors.BORDER};
                border-bottom: none;
            }}
            QTabBar::tab:hover {{
                color: {Colors.TEXT_PRIMARY};
            }}
            QPushButton {{
                background: {Colors.BG_ELEVATED};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                padding: 8px 16px;
                color: {Colors.TEXT_PRIMARY};
                font-weight: 500;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: {Colors.BORDER_HOVER};
                border-color: {Colors.BORDER_HOVER};
            }}
            QLineEdit {{
                background: {Colors.BG_INPUT};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                padding: 8px 12px;
                color: {Colors.TEXT_PRIMARY};
                font-size: 13px;
                selection-background-color: {Colors.ACCENT};
            }}
            QLineEdit:focus {{
                border-color: {Colors.ACCENT};
            }}
            QTextEdit {{
                background: {Colors.BG_INPUT};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                color: {Colors.SUCCESS};
                font-family: 'Cascadia Code', 'Consolas', monospace;
                font-size: 12px;
                padding: 8px;
                selection-background-color: {Colors.ACCENT};
            }}
            QProgressBar {{
                border: none;
                border-radius: 4px;
                background: {Colors.PROGRESS_BG};
                text-align: center;
                color: {Colors.TEXT_PRIMARY};
                font-size: 11px;
                height: 8px;
            }}
            QProgressBar::chunk {{
                border-radius: 4px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.ACCENT}, stop:1 {Colors.SUCCESS});
            }}
        """)

    # ─── UI Build ─────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(12)
        root.setContentsMargins(20, 16, 20, 16)

        # ── Header ──
        header = QHBoxLayout()
        brand = QLabel(f"📸 {APP_NAME}")
        brand.setStyleSheet(f"color: {Colors.ACCENT}; font-size: 22px; font-weight: 800; letter-spacing: -0.5px;")
        header.addWidget(brand)

        version = QLabel(f"v{APP_VERSION}")
        version.setStyleSheet(f"color: {Colors.TEXT_DIM}; font-size: 12px; margin-top: 6px;")
        header.addWidget(version)
        header.addStretch()

        self.settings_btn = QPushButton("⚙️ Settings")
        self.settings_btn.clicked.connect(self._open_settings)
        header.addWidget(self.settings_btn)

        self.report_btn = QPushButton("📊 Report")
        self.report_btn.clicked.connect(self._generate_report)
        self.report_btn.setEnabled(False)
        header.addWidget(self.report_btn)
        root.addLayout(header)

        # ── Stats Cards ──
        stats_row = QHBoxLayout()
        stats_row.setSpacing(10)
        self.stat_processed = StatCard("Processed", "0", Colors.ACCENT)
        self.stat_accepted = StatCard("Accepted", "0", Colors.SUCCESS)
        self.stat_rejected = StatCard("Rejected", "0", Colors.ERROR)
        stats_row.addWidget(self.stat_processed)
        stats_row.addWidget(self.stat_accepted)
        stats_row.addWidget(self.stat_rejected)
        root.addLayout(stats_row)

        # ── Control Bar ──
        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)

        ctrl.addWidget(QLabel("📂 Drop Zone:"))
        self.drop_input = QLineEdit()
        self.drop_input.setPlaceholderText("Select folder to watch for new photos...")
        ctrl.addWidget(self.drop_input, stretch=1)
        drop_btn = QPushButton("Browse")
        drop_btn.clicked.connect(lambda: self._browse(self.drop_input))
        ctrl.addWidget(drop_btn)

        ctrl.addWidget(QLabel("📁 Output:"))
        self.out_input = QLineEdit()
        self.out_input.setPlaceholderText("Select output folder for processed photos...")
        ctrl.addWidget(self.out_input, stretch=1)
        out_btn = QPushButton("Browse")
        out_btn.clicked.connect(lambda: self._browse(self.out_input))
        ctrl.addWidget(out_btn)

        self.engine_btn = QPushButton("▶  Start Engine")
        self.engine_btn.setCheckable(True)
        self.engine_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.ACCENT};
                color: white;
                font-weight: 700;
                font-size: 14px;
                padding: 10px 28px;
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{ background: {Colors.ACCENT_HOVER}; }}
            QPushButton:checked {{
                background: {Colors.ERROR};
            }}
        """)
        self.engine_btn.clicked.connect(self._toggle_engine)
        ctrl.addWidget(self.engine_btn)
        root.addLayout(ctrl)

        # ── Tabs ──
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, stretch=1)

        # Tab 1: Monitor
        monitor_tab = QWidget()
        mon_layout = QHBoxLayout(monitor_tab)
        mon_layout.setSpacing(12)

        # Log console
        log_panel = QVBoxLayout()
        self.log_window = QTextEdit()
        self.log_window.setReadOnly(True)
        self.log_window.setPlaceholderText("Processing log will appear here...")
        log_panel.addWidget(self.log_window, stretch=1)

        # Stage label
        self.stage_label = QLabel("")
        self.stage_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 11px; padding: 2px 0;")
        log_panel.addWidget(self.stage_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        log_panel.addWidget(self.progress_bar)
        mon_layout.addLayout(log_panel, stretch=3)

        # Right panel: thumbnail + EXIF + tags
        right_panel = QVBoxLayout()
        right_panel.setSpacing(8)

        self.thumbnail_label = QLabel("📷")
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setFixedSize(280, 220)
        self.thumbnail_label.setStyleSheet(f"""
            background: {Colors.THUMBNAIL_BG};
            border: 1px solid {Colors.BORDER};
            border-radius: 8px;
            color: {Colors.TEXT_DIM};
            font-size: 48px;
        """)
        right_panel.addWidget(self.thumbnail_label)

        # EXIF info
        self.exif_label = QLabel("No EXIF data")
        self.exif_label.setWordWrap(True)
        self.exif_label.setStyleSheet(f"""
            background: {Colors.BG_SURFACE};
            border: 1px solid {Colors.BORDER};
            border-radius: 6px;
            padding: 10px;
            color: {Colors.TEXT_SECONDARY};
            font-size: 11px;
        """)
        self.exif_label.setFixedWidth(280)
        right_panel.addWidget(self.exif_label)

        # Tags display
        self.tags_label = QLabel("No tags yet")
        self.tags_label.setWordWrap(True)
        self.tags_label.setStyleSheet(f"""
            background: {Colors.BG_SURFACE};
            border: 1px solid {Colors.BORDER};
            border-radius: 6px;
            padding: 10px;
            color: {Colors.ACCENT};
            font-size: 12px;
            font-weight: 600;
        """)
        self.tags_label.setFixedWidth(280)
        right_panel.addWidget(self.tags_label)
        right_panel.addStretch()

        mon_layout.addLayout(right_panel)
        self.tabs.addTab(monitor_tab, "🖥️ Monitor")

        # Tab 2: Gallery
        self.gallery = GalleryWidget()
        self.gallery.card_selected.connect(self._on_gallery_select)
        self.tabs.addTab(self.gallery, "🖼️ Gallery")

        # ── Status bar ──
        self.status_label = QLabel("Status: IDLE")
        self.status_label.setStyleSheet(f"color: {Colors.TEXT_DIM}; font-size: 12px; padding: 4px;")
        root.addWidget(self.status_label)

    # ─── State Persistence ───────────────────────────────────
    def _restore_state(self):
        dp = self.config.drop_zone
        op = self.config.output_zone
        if dp:
            self.drop_input.setText(dp)
        if op:
            self.out_input.setText(op)

        geo, state = self.config.restore_geometry()
        if geo:
            self.restoreGeometry(geo)

    def closeEvent(self, event):
        self.config.drop_zone = self.drop_input.text()
        self.config.output_zone = self.out_input.text()
        self.config.save_geometry(self.saveGeometry(), self.saveState())
        if self.worker:
            self.worker.stop()
            self.worker.wait(3000)
        event.accept()

    # ─── Slots ────────────────────────────────────────────────
    def _browse(self, line_edit: QLineEdit):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Directory", line_edit.text() or os.getcwd()
        )
        if folder:
            line_edit.setText(folder)

    def _open_settings(self):
        dlg = SettingsDialog(self.config, self)
        dlg.exec()

    def _toggle_engine(self, checked: bool):
        if checked:
            drop = self.drop_input.text().strip()
            out = self.out_input.text().strip()
            if not drop or not out:
                self.engine_btn.setChecked(False)
                self._append_log(f"[{time.strftime('%H:%M:%S')}] ⚠️ Please set Drop Zone and Output paths first!")
                return

            self.engine_btn.setText("⏹  Stop Engine")
            self._stats = {"processed": 0, "accepted": 0, "rejected": 0}

            rej = self.config.rejected_zone or os.path.join(out, "_Rejected")

            self.worker = EngineWorker(
                drop, out, rej,
                blur_threshold=self.config.blur_threshold,
                auto_categorize=self.config.auto_categorize,
                top_k=self.config.top_k_tags,
            )
            self.worker.log_msg.connect(self._append_log)
            self.worker.status_update.connect(self._update_status)
            self.worker.thumbnail_update.connect(self._update_thumbnail)
            self.worker.progress_update.connect(self.progress_bar.setValue)
            self.worker.stage_update.connect(self.stage_label.setText)
            self.worker.stats_update.connect(self._update_stats)
            self.worker.tags_update.connect(self._update_tags)
            self.worker.exif_update.connect(self._update_exif)
            self.worker.start()
            self.report_btn.setEnabled(True)
        else:
            self.engine_btn.setText("▶  Start Engine")
            if self.worker:
                self._append_log(f"[{time.strftime('%H:%M:%S')}] 🛑 Shutting down engine...")
                self.worker.stop()
                self.worker.wait(5000)
                self.worker = None

    def _append_log(self, text: str):
        self.log_window.append(text)

    def _update_status(self, status: str):
        color_map = {
            "WATCHING": Colors.SUCCESS,
            "BOOTING": Colors.WARNING,
            "SCANNING": Colors.ACCENT,
            "IDLE": Colors.TEXT_DIM,
        }
        color = color_map.get(status, Colors.TEXT_SECONDARY)
        self.status_label.setText(f"Status: {status}")
        self.status_label.setStyleSheet(f"color: {color}; font-size: 12px; padding: 4px; font-weight: 600;")

    def _update_thumbnail(self, path: str):
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(
                self.thumbnail_label.width(), self.thumbnail_label.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.thumbnail_label.setPixmap(pixmap)
        else:
            self.thumbnail_label.setText("⚠️")

    def _update_stats(self, status: str):
        self._stats["processed"] += 1
        self._stats[status] += 1
        self.stat_processed.set_value(self._stats["processed"])
        self.stat_accepted.set_value(self._stats["accepted"])
        self.stat_rejected.set_value(self._stats["rejected"])

        # Add to gallery
        # We'll reconstruct a minimal entry for the gallery from available info
        self.gallery.add_entry({
            "filename": self._last_filename if hasattr(self, '_last_filename') else "unknown",
            "status": status,
            "final_path": self._last_final_path if hasattr(self, '_last_final_path') else "",
            "category": self._last_category if hasattr(self, '_last_category') else "",
            "star_rating": self._last_rating if hasattr(self, '_last_rating') else 0,
        })

    def _update_tags(self, tags: list):
        if tags:
            self._last_category = tags[0] if tags else ""
            tag_badges = "  ".join([f"🏷️ {t}" for t in tags])
            self.tags_label.setText(tag_badges)
        else:
            self.tags_label.setText("No tags")

    def _update_exif(self, exif: dict):
        parts = []
        if exif.get("camera"):
            parts.append(f"📷 {exif['camera']}")
        if exif.get("focal_length"):
            parts.append(f"🔭 {exif['focal_length']}")
        if exif.get("aperture"):
            parts.append(f"⬡ {exif['aperture']}")
        if exif.get("shutter_speed"):
            parts.append(f"⏱️ {exif['shutter_speed']}")
        if exif.get("iso"):
            parts.append(f"ISO {exif['iso']}")
        if exif.get("width") and exif.get("height"):
            parts.append(f"📐 {exif['width']}×{exif['height']}")
        self.exif_label.setText("\n".join(parts) if parts else "No EXIF data")

    def _on_gallery_select(self, entry: dict):
        """Handle gallery thumbnail click — show in monitor tab."""
        self.tabs.setCurrentIndex(0)
        path = entry.get("final_path", "")
        if path:
            self._update_thumbnail(path)

    def _generate_report(self):
        try:
            history = HistoryDB()
            entries = history.get_recent_entries(500)
            if not entries:
                self._append_log(f"[{time.strftime('%H:%M:%S')}] ⚠️ No processing history to report on.")
                return

            out_dir = self.out_input.text() or os.getcwd()
            stats = {
                "total_processed": self._stats["processed"],
                "total_accepted": self._stats["accepted"],
                "total_rejected": self._stats["rejected"],
                "categories": {},
                "duration": 0,
            }
            # Build category counts
            for e in entries:
                cat = e.get("category", "uncategorized")
                if e.get("status") == "accepted":
                    stats["categories"][cat] = stats["categories"].get(cat, 0) + 1

            report_path = generate_html_report(stats, entries, out_dir)
            self._append_log(f"[{time.strftime('%H:%M:%S')}] 📊 Report saved: {report_path}")

            from PyQt6.QtGui import QDesktopServices
            from PyQt6.QtCore import QUrl
            QDesktopServices.openUrl(QUrl.fromLocalFile(report_path))
        except Exception as e:
            self._append_log(f"[{time.strftime('%H:%M:%S')}] ❌ Report generation failed: {e}")

    # ─── Drag & Drop ─────────────────────────────────────────
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        drop_dir = self.drop_input.text().strip()
        if not drop_dir:
            self._append_log(f"[{time.strftime('%H:%M:%S')}] ⚠️ Set a Drop Zone first!")
            return
        import shutil
        from pathlib import Path
        Path(drop_dir).mkdir(parents=True, exist_ok=True)
        for url in event.mimeData().urls():
            src = url.toLocalFile()
            if os.path.isfile(src):
                dst = os.path.join(drop_dir, os.path.basename(src))
                try:
                    shutil.copy2(src, dst)
                    self._append_log(f"[{time.strftime('%H:%M:%S')}] 📥 Dropped: {os.path.basename(src)}")
                except Exception as e:
                    self._append_log(f"[{time.strftime('%H:%M:%S')}] ❌ Drop failed: {e}")
