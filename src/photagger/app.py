"""
Photagger — Premium desktop UI.
Main application window with sidebar interface, stats dashboard, and settings.
"""
import sys
import os
import time
from pathlib import Path

import onnxruntime  # Pre-load DLLs before PyQt6

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QTextEdit,
    QProgressBar, QFrame, QSizePolicy, QStackedWidget, QDialog,
    QSlider, QCheckBox, QSpinBox, QFormLayout, QDialogButtonBox,
    QToolButton
)
from PyQt6.QtGui import QPixmap, QDragEnterEvent, QDropEvent
from PyQt6.QtCore import Qt, QTimer, pyqtSlot

from .watcher import EngineWorker
from .config import AppConfig
from .constants import APP_NAME, APP_VERSION
from .gallery_widget import GalleryWidget
from .image_viewer import ImageViewer
from .history_db import HistoryDB
from .session_report import generate_html_report
from .exif_reader import format_exif_summary
from .logger import setup_logging, get_logger
from .theme import apply_theme, get_palette, get_stylesheet, get_theme_preference, save_theme_preference
from .keyboard_shortcuts import ShortcutManager
from . import icons

log = get_logger("app")


# === Settings Dialog =======================================================

class SettingsDialog(QDialog):
    """Modal settings dialog for processing parameters."""
    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Settings")
        self.setFixedSize(460, 380)

        P = get_palette()
        self.setStyleSheet(f"""
            QDialog {{ background: {P.BG_PRIMARY}; color: {P.TEXT_PRIMARY}; }}
            QLabel {{ color: {P.TEXT_SECONDARY}; font-size: 13px; }}
            QSpinBox, QCheckBox {{ background: {P.BG_INPUT}; color: {P.TEXT_PRIMARY}; border: 1px solid {P.BORDER}; border-radius: 4px; padding: 4px 8px; }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Processing Settings")
        title.setStyleSheet(f"color: {P.TEXT_PRIMARY}; font-size: 18px; font-weight: 700;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)

        blur_layout = QHBoxLayout()
        self.blur_slider = QSlider(Qt.Orientation.Horizontal)
        self.blur_slider.setRange(20, 500)
        self.blur_slider.setValue(int(config.blur_threshold))
        self.blur_label = QLabel(f"{int(config.blur_threshold)}")
        self.blur_label.setFixedWidth(40)
        self.blur_label.setStyleSheet(f"color: {P.ACCENT}; font-weight: 600;")
        self.blur_slider.valueChanged.connect(lambda v: self.blur_label.setText(str(v)))
        blur_layout.addWidget(self.blur_slider)
        blur_layout.addWidget(self.blur_label)
        form.addRow("Blur Threshold:", blur_layout)

        self.topk_spin = QSpinBox()
        self.topk_spin.setRange(1, 10)
        self.topk_spin.setValue(config.top_k_tags)
        form.addRow("AI Tags Count:", self.topk_spin)

        self.cat_check = QCheckBox("Auto-sort into category subfolders")
        self.cat_check.setChecked(config.auto_categorize)
        form.addRow("", self.cat_check)

        self.exp_check = QCheckBox("Auto-reject badly exposed images")
        self.exp_check.setChecked(config.exposure_reject)
        form.addRow("", self.exp_check)

        layout.addLayout(form)
        layout.addStretch()

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self):
        self.config.blur_threshold = self.blur_slider.value()
        self.config.top_k_tags = self.topk_spin.value()
        self.config.auto_categorize = self.cat_check.isChecked()
        self.config.exposure_reject = self.exp_check.isChecked()
        self.accept()


# === Stat Card =============================================================

class StatCard(QFrame):
    """Compact dashboard stat card with animated counting."""
    def __init__(self, label: str, color: str):
        super().__init__()
        P = get_palette()
        self.setStyleSheet(f"""
            QFrame {{
                background: {P.BG_SURFACE};
                border: 1px solid {P.BORDER};
                border-radius: 10px;
                padding: 12px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(2)

        self.value_label = QLabel("0")
        self.value_label.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: 700;")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.value_label)

        desc = QLabel(label)
        desc.setStyleSheet(f"color: {P.TEXT_SECONDARY}; font-size: 11px; text-transform: uppercase; letter-spacing: 1px;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        self._current_val = 0
        self._target_val = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate_step)

    def set_value(self, val: int):
        self._target_val = val
        if self._target_val != self._current_val and not self._timer.isActive():
            self._timer.start(30)

    def _animate_step(self):
        if self._current_val < self._target_val:
            step = max(1, (self._target_val - self._current_val) // 5)
            self._current_val += step
            if self._current_val > self._target_val:
                self._current_val = self._target_val
            self.value_label.setText(str(self._current_val))
        else:
            self._timer.stop()


# === Main Window ===========================================================

class MainWindow(QMainWindow):
    """Photagger main application window with sidebar navigation."""

    def __init__(self):
        super().__init__()
        self.config = AppConfig()
        
        # Apply initial theme
        apply_theme(self.config.theme_mode)
        
        self.worker = None
        self._stats = {"processed": 0, "accepted": 0, "rejected": 0}

        self.setWindowTitle(f"{APP_NAME} — AI Photography Tagger")
        self.setMinimumSize(1024, 768)
        self.setAcceptDrops(True)

        self.setStyleSheet(get_stylesheet())

        # Setup Shortcuts
        self.shortcuts = ShortcutManager(self)
        self._register_shortcuts()

        self._build_ui()
        self._restore_state()

        log.info("Application started")

    def _register_shortcuts(self):
        self.shortcuts.register_all({
            "toggle_engine": lambda: self.engine_btn.setChecked(not self.engine_btn.isChecked()) or self._toggle_engine(self.engine_btn.isChecked()),
            "go_monitor": lambda: self._switch_view(0),
            "go_gallery": lambda: self._switch_view(1),
            "go_viewer": lambda: self._switch_view(2),
            "toggle_theme": self._toggle_theme_mode,
            "open_settings": self._open_settings,
            "generate_report": self._generate_report,
            "nav_prev": self._viewer_prev,
            "nav_next": self._viewer_next,
            "toggle_exif": self._viewer_toggle_exif,
            "zoom_fit": self._viewer_fit,
            "zoom_100": self._viewer_100,
        })

    # --- UI Build -------------------------------------------------------------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Sidebar
        self._build_sidebar(main_layout)

        # 2. Main Content Area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 16, 20, 16)
        content_layout.setSpacing(12)

        self._build_header(content_layout)
        self._build_stats_row(content_layout)
        self._build_control_bar(content_layout)

        # Stacked Views
        self.stack = QStackedWidget()
        
        # View 0: Monitor
        self._build_monitor_view()
        self.stack.addWidget(self.monitor_widget)
        
        # View 1: Gallery
        self.gallery = GalleryWidget()
        self.gallery.card_double_clicked.connect(self._open_in_viewer)
        self.stack.addWidget(self.gallery)
        
        # View 2: Viewer
        self.viewer = ImageViewer()
        self.stack.addWidget(self.viewer)
        
        content_layout.addWidget(self.stack, stretch=1)

        # Status footer
        self._build_footer(content_layout)

        main_layout.addWidget(content_widget, stretch=1)

    def _build_sidebar(self, parent_layout):
        P = get_palette()
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(64)
        self.sidebar.setStyleSheet(f"background: {P.BG_SIDEBAR}; border-right: 1px solid {P.BORDER};")
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(0, 20, 0, 20)
        side_layout.setSpacing(20)

        # Nav Buttons
        self.nav_monitor = self._create_nav_btn(icons.icon_monitor, "Monitor", 0)
        self.nav_monitor.setChecked(True)
        self.nav_gallery = self._create_nav_btn(icons.icon_grid, "Gallery", 1)
        self.nav_viewer = self._create_nav_btn(icons.icon_image, "Viewer", 2)

        side_layout.addWidget(self.nav_monitor)
        side_layout.addWidget(self.nav_gallery)
        side_layout.addWidget(self.nav_viewer)
        side_layout.addStretch()

        parent_layout.addWidget(self.sidebar)

    def _create_nav_btn(self, icon_fn, tooltip, index):
        btn = QToolButton()
        P = get_palette()
        btn.setIcon(icon_fn(24, P.TEXT_SECONDARY))
        btn.setToolTip(tooltip)
        btn.setFixedSize(48, 48)
        btn.setCheckable(True)
        btn.setAutoExclusive(True)
        btn.setStyleSheet(f"""
            QToolButton {{ border: none; border-radius: 8px; margin: 0 8px; }}
            QToolButton:hover {{ background: {P.BG_ELEVATED}; }}
            QToolButton:checked {{ background: {P.ACCENT_SUBTLE}; border-left: 3px solid {P.ACCENT}; border-radius: 4px; }}
        """)
        btn.clicked.connect(lambda: self._switch_view(index))
        return btn

    def _build_header(self, layout):
        P = get_palette()
        header = QHBoxLayout()
        brand = QLabel(f"{APP_NAME}")
        brand.setStyleSheet(f"color: {P.ACCENT}; font-size: 22px; font-weight: 800; letter-spacing: -0.5px;")
        header.addWidget(brand)

        version = QLabel(f"v{APP_VERSION}")
        version.setStyleSheet(f"color: {P.TEXT_DIM}; font-size: 12px; margin-top: 6px;")
        header.addWidget(version)
        header.addStretch()

        # Theme toggle
        self.theme_btn = QPushButton("")
        self._update_theme_icon()
        self.theme_btn.clicked.connect(self._toggle_theme_mode)
        header.addWidget(self.theme_btn)

        self.settings_btn = QPushButton(" Settings")
        self.settings_btn.setIcon(icons.icon_gear(18, P.TEXT_SECONDARY))
        self.settings_btn.clicked.connect(self._open_settings)
        header.addWidget(self.settings_btn)

        self.report_btn = QPushButton(" Report")
        self.report_btn.setIcon(icons.icon_chart(18, P.TEXT_SECONDARY))
        self.report_btn.clicked.connect(self._generate_report)
        self.report_btn.setEnabled(False)
        header.addWidget(self.report_btn)
        layout.addLayout(header)

    def _build_stats_row(self, layout):
        P = get_palette()
        stats_row = QHBoxLayout()
        stats_row.setSpacing(10)
        self.stat_processed = StatCard("Processed", P.ACCENT)
        self.stat_accepted = StatCard("Accepted", P.SUCCESS)
        self.stat_rejected = StatCard("Rejected", P.ERROR)
        stats_row.addWidget(self.stat_processed)
        stats_row.addWidget(self.stat_accepted)
        stats_row.addWidget(self.stat_rejected)
        layout.addLayout(stats_row)

    def _build_control_bar(self, layout):
        P = get_palette()
        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)

        drop_lbl = QLabel("Drop Zone:")
        drop_lbl.setStyleSheet(f"color: {P.TEXT_SECONDARY}; font-weight: 500;")
        ctrl.addWidget(drop_lbl)
        self.drop_input = QLineEdit()
        ctrl.addWidget(self.drop_input, stretch=1)
        drop_btn = QPushButton("Browse")
        drop_btn.clicked.connect(lambda: self._browse(self.drop_input))
        ctrl.addWidget(drop_btn)

        out_lbl = QLabel("Output:")
        out_lbl.setStyleSheet(f"color: {P.TEXT_SECONDARY}; font-weight: 500;")
        ctrl.addWidget(out_lbl)
        self.out_input = QLineEdit()
        ctrl.addWidget(self.out_input, stretch=1)
        out_btn = QPushButton("Browse")
        out_btn.clicked.connect(lambda: self._browse(self.out_input))
        ctrl.addWidget(out_btn)

        self.engine_btn = QPushButton(" Start Engine")
        self.engine_btn.setIcon(icons.icon_play(18, P.TEXT_INVERSE))
        self.engine_btn.setCheckable(True)
        self.engine_btn.setStyleSheet(f"""
            QPushButton {{
                background: {P.ACCENT}; color: {P.TEXT_INVERSE}; font-weight: 700; padding: 10px 24px; border: none;
            }}
            QPushButton:hover {{ background: {P.ACCENT_HOVER}; }}
            QPushButton:checked {{ background: {P.ERROR}; color: {P.TEXT_INVERSE}; }}
        """)
        self.engine_btn.clicked.connect(self._toggle_engine)
        ctrl.addWidget(self.engine_btn)
        layout.addLayout(ctrl)

    def _build_monitor_view(self):
        P = get_palette()
        self.monitor_widget = QWidget()
        mon_layout = QHBoxLayout(self.monitor_widget)
        mon_layout.setContentsMargins(0, 0, 0, 0)
        mon_layout.setSpacing(12)

        log_panel = QVBoxLayout()
        self.log_window = QTextEdit()
        self.log_window.setReadOnly(True)
        log_panel.addWidget(self.log_window, stretch=1)

        self.stage_label = QLabel("")
        self.stage_label.setStyleSheet(f"color: {P.TEXT_SECONDARY}; font-size: 11px;")
        log_panel.addWidget(self.stage_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        log_panel.addWidget(self.progress_bar)
        mon_layout.addLayout(log_panel, stretch=3)

        right_panel = QVBoxLayout()
        self.thumbnail_label = QLabel("No Image")
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setFixedSize(280, 220)
        self.thumbnail_label.setStyleSheet(f"background: {P.THUMBNAIL_BG}; border: 1px solid {P.BORDER}; border-radius: 8px; color: {P.TEXT_DIM};")
        right_panel.addWidget(self.thumbnail_label)

        self.exif_label = QLabel("No EXIF data")
        self.exif_label.setWordWrap(True)
        self.exif_label.setStyleSheet(f"background: {P.BG_SURFACE}; border: 1px solid {P.BORDER}; border-radius: 6px; padding: 10px; color: {P.TEXT_SECONDARY}; font-size: 11px;")
        self.exif_label.setFixedWidth(280)
        right_panel.addWidget(self.exif_label)

        self.tags_label = QLabel("No tags yet")
        self.tags_label.setWordWrap(True)
        self.tags_label.setStyleSheet(f"background: {P.BG_SURFACE}; border: 1px solid {P.BORDER}; border-radius: 6px; padding: 10px; color: {P.ACCENT}; font-weight: 600;")
        self.tags_label.setFixedWidth(280)
        right_panel.addWidget(self.tags_label)
        right_panel.addStretch()

        mon_layout.addLayout(right_panel)

    def _build_footer(self, layout):
        P = get_palette()
        footer = QHBoxLayout()
        self.status_label = QLabel("● IDLE")
        self.status_label.setStyleSheet(f"color: {P.STATUS_IDLE}; font-weight: bold;")
        footer.addWidget(self.status_label)
        
        self.queue_label = QLabel("Queue: 0")
        self.queue_label.setStyleSheet(f"color: {P.TEXT_SECONDARY};")
        footer.addWidget(self.queue_label)
        footer.addStretch()
        
        layout.addLayout(footer)

    # --- Theme & State --------------------------------------------------------
    def _restore_state(self):
        dp = self.config.drop_zone
        op = self.config.output_zone
        if dp: self.drop_input.setText(dp)
        if op: self.out_input.setText(op)

        geo, state = self.config.restore_geometry()
        if geo: self.restoreGeometry(geo)

    def closeEvent(self, event):
        self.config.drop_zone = self.drop_input.text()
        self.config.output_zone = self.out_input.text()
        self.config.save_geometry(self.saveGeometry(), self.saveState())
        if self.worker:
            self.worker.stop()
            # Give the worker a chance to exit cleanly, but don't hang the GUI
            self.worker.wait(1000)
            if self.worker.isRunning():
                self.worker.terminate()
                self.worker.wait(500)
        event.accept()

    def _update_theme_icon(self):
        P = get_palette()
        mode = get_theme_preference()
        if mode == "light":
            self.theme_btn.setIcon(icons.icon_moon(18, P.TEXT_SECONDARY))
        else:
            self.theme_btn.setIcon(icons.icon_sun(18, P.TEXT_SECONDARY))

    def _toggle_theme_mode(self):
        mode = get_theme_preference()
        new_mode = "light" if mode == "dark" else "dark"
        save_theme_preference(new_mode)
        apply_theme(new_mode)
        self.setStyleSheet(get_stylesheet())
        self._update_theme_icon()
        
        # Update nav icons colors
        P = get_palette()
        self.nav_monitor.setIcon(icons.icon_monitor(24, P.TEXT_SECONDARY))
        self.nav_gallery.setIcon(icons.icon_grid(24, P.TEXT_SECONDARY))
        self.nav_viewer.setIcon(icons.icon_image(24, P.TEXT_SECONDARY))
        self.settings_btn.setIcon(icons.icon_gear(18, P.TEXT_SECONDARY))
        self.report_btn.setIcon(icons.icon_chart(18, P.TEXT_SECONDARY))
        self.engine_btn.setIcon(icons.icon_play(18, P.TEXT_INVERSE) if not self.engine_btn.isChecked() else icons.icon_stop(18, P.TEXT_INVERSE))
        
        # Propagate to sub-widgets
        self.gallery.apply_theme()
        self.viewer.apply_theme()

    def _switch_view(self, index: int):
        self.stack.setCurrentIndex(index)
        self.nav_monitor.setChecked(index == 0)
        self.nav_gallery.setChecked(index == 1)
        self.nav_viewer.setChecked(index == 2)

    # --- Slots ----------------------------------------------------------------
    def _browse(self, line_edit: QLineEdit):
        folder = QFileDialog.getExistingDirectory(self, "Select Directory", line_edit.text() or os.getcwd())
        if folder: line_edit.setText(folder)

    def _open_settings(self):
        SettingsDialog(self.config, self).exec()

    def _toggle_engine(self, checked: bool):
        P = get_palette()
        if checked:
            drop = self.drop_input.text().strip()
            out = self.out_input.text().strip()
            if not drop or not out:
                self.engine_btn.setChecked(False)
                self._append_log(f"[{time.strftime('%H:%M:%S')}] [WARN] Set Drop Zone and Output paths first!")
                return

            self.engine_btn.setText(" Stop Engine")
            self.engine_btn.setIcon(icons.icon_stop(18, P.TEXT_INVERSE))
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
            self.worker.gallery_entry.connect(self.gallery.add_entry)
            self.worker.queue_update.connect(self.update_queue)
            
            self.worker.start()
            self.report_btn.setEnabled(True)
        else:
            self.engine_btn.setText(" Start Engine")
            self.engine_btn.setIcon(icons.icon_play(18, P.TEXT_INVERSE))
            if self.worker:
                self._append_log(f"[{time.strftime('%H:%M:%S')}] [STOP] Shutting down engine...")
                self.worker.stop()
                self.worker.wait(1000)
                if self.worker.isRunning():
                    self.worker.terminate()
                    self.worker.wait(500)
                self.worker = None

    def _append_log(self, text: str):
        self.log_window.append(text)

    @pyqtSlot(int, int, int)
    def update_queue(self, processed: int, total: int, eta_seconds: int):
        P = get_palette()
        if total == 0:
            self.queue_label.setText("Queue: 0")
            self.queue_label.setStyleSheet(f"color: {P.TEXT_SECONDARY};")
        elif processed >= total:
            self.queue_label.setText(f"Queue: {total}/{total} — Done")
            self.queue_label.setStyleSheet(f"color: {P.SUCCESS}; font-weight: bold;")
        else:
            mins, secs = divmod(eta_seconds, 60)
            eta_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
            self.queue_label.setText(f"Queue: {processed}/{total} | ETA: {eta_str}")
            self.queue_label.setStyleSheet(f"color: {P.ACCENT}; font-weight: bold;")

    def _update_status(self, status: str):
        P = get_palette()
        colors = {"WATCHING": P.STATUS_WATCHING, "BOOTING": P.STATUS_BOOTING, "SCANNING": P.STATUS_PROCESSING, "IDLE": P.STATUS_IDLE}
        color = colors.get(status, P.TEXT_SECONDARY)
        self.status_label.setText(f"● {status}")
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def _update_thumbnail(self, path: str):
        px = QPixmap(path)
        if not px.isNull():
            self.thumbnail_label.setPixmap(px.scaled(
                self.thumbnail_label.width(), self.thumbnail_label.height(),
                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))
        else:
            self.thumbnail_label.setText("Preview unavailable")

    def _update_stats(self, status: str):
        self._stats["processed"] += 1
        self._stats[status] += 1
        self.stat_processed.set_value(self._stats["processed"])
        self.stat_accepted.set_value(self._stats["accepted"])
        self.stat_rejected.set_value(self._stats["rejected"])

    def _update_tags(self, tags: list):
        self.tags_label.setText(" | ".join(tags) if tags else "No tags")

    def _update_exif(self, exif: dict):
        self.exif_label.setText(format_exif_summary(exif))

    def _open_in_viewer(self, entry: dict):
        self._switch_view(2)
        entries = self.gallery.get_filtered_entries()
        try:
            idx = entries.index(entry)
            self.viewer.set_entries(entries, idx)
        except ValueError:
            self.viewer.set_entries([entry], 0)

    def _viewer_next(self):
        if self.stack.currentIndex() == 2:
            self.viewer.navigate_next()

    def _viewer_prev(self):
        if self.stack.currentIndex() == 2:
            self.viewer.navigate_prev()

    def _viewer_toggle_exif(self):
        if self.stack.currentIndex() == 2:
            self.viewer.toggle_exif()

    def _viewer_fit(self):
        if self.stack.currentIndex() == 2:
            self.viewer.fit_view()

    def _viewer_100(self):
        if self.stack.currentIndex() == 2:
            self.viewer.zoom_100()

    def _generate_report(self):
        try:
            entries = HistoryDB().get_recent_entries(500)
            if not entries: return
            out_dir = self.out_input.text() or os.getcwd()
            stats = {
                "total_processed": self._stats["processed"],
                "total_accepted": self._stats["accepted"],
                "total_rejected": self._stats["rejected"],
                "categories": {}
            }
            for e in entries:
                if e.get("status") == "accepted":
                    cat = e.get("category", "uncategorized")
                    stats["categories"][cat] = stats["categories"].get(cat, 0) + 1
            report = generate_html_report(stats, entries, out_dir)
            from PyQt6.QtGui import QDesktopServices
            QDesktopServices.openUrl(QUrl.fromLocalFile(report))
        except Exception as e:
            self._append_log(f"[ERROR] Report failed: {e}")

    # --- Drag & Drop ----------------------------------------------------------
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        drop_dir = self.drop_input.text().strip()
        if not drop_dir: return
        import shutil
        Path(drop_dir).mkdir(parents=True, exist_ok=True)
        for url in event.mimeData().urls():
            src = url.toLocalFile()
            if os.path.isfile(src):
                try: shutil.copy2(src, os.path.join(drop_dir, os.path.basename(src)))
                except Exception as e: self._append_log(f"[ERROR] Drop failed: {e}")
