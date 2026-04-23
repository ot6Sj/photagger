import sys
import os

# ABSOLUTE TOP IMPORT: Force AI Engine DLLs to load into memory
# before PyQt6 is even mentioned anywhere in the namespace!
import onnxruntime

from watcher import EngineWorker

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                                QFileDialog, QTextEdit, QProgressBar, QFrame, QSizePolicy)
from PyQt6.QtGui import QColor, QPalette, QPixmap, QFont
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Culling & Processing Pipeline")
        self.setMinimumSize(800, 600)
        
        # Set Dark Theme Palette
        self.setup_dark_theme()
        
        # Core UI Setup
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setSpacing(15)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        # 1. Control Header
        self.setup_header()
        
        # Divider
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setFrameShadow(QFrame.Shadow.Sunken)
        self.main_layout.addWidget(line1)

        # 2. Live Console
        self.setup_console()
        
        # 3. Progress Footer
        self.setup_footer()

        # Engine State
        self.worker = None

    def setup_dark_theme(self):
        # A simple, sleek dark theme
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 220))
        palette.setColor(QPalette.ColorRole.Base, QColor(18, 18, 18))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, QColor(220, 220, 220))
        palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 45))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(220, 220, 220))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        self.setPalette(palette)
        
        self.setStyleSheet("""
            QPushButton {
                background-color: #2D2D2D;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 6px;
                color: #DDD;
            }
            QPushButton:hover {
                background-color: #3D3D3D;
            }
            QPushButton#engine_btn {
                background-color: #2E8B57;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 10px;
            }
            QPushButton#engine_btn:checked {
                background-color: #B22222;
            }
            QLineEdit {
                background-color: #121212;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 5px;
                color: #A0A0A0;
            }
            QTextEdit {
                background-color: #0A0A0A;
                border: 1px solid #333;
                border-radius: 4px;
                color: #55FF55; /* Matrix green */
                font-family: Consolas, monospace;
                font-size: 13px;
            }
            QProgressBar {
                border: 1px solid #444;
                border-radius: 5px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #2A82DA;
                width: 20px;
            }
        """)

    def setup_header(self):
        header_layout = QVBoxLayout()
        
        # Status Label
        self.status_label = QLabel("Status: IDLE")
        self.status_label.setStyleSheet("color: #AAAAAA; font-weight: bold; font-size: 16px;")
        header_layout.addWidget(self.status_label)

        # Paths Layout
        paths_layout = QVBoxLayout()
        
        # Drop Zone Row
        drop_layout = QHBoxLayout()
        drop_layout.addWidget(QLabel("Drop Zone:"))
        self.drop_input = QLineEdit()
        self.drop_input.setText(os.path.abspath("Drop_Zone")) # Default to the existing one
        drop_layout.addWidget(self.drop_input)
        
        self.drop_browse = QPushButton("Browse")
        self.drop_browse.clicked.connect(lambda: self.browse_folder(self.drop_input))
        drop_layout.addWidget(self.drop_browse)
        paths_layout.addLayout(drop_layout)
        
        # Output Zone Row
        out_layout = QHBoxLayout()
        out_layout.addWidget(QLabel("Output Zone:"))
        self.out_input = QLineEdit()
        self.out_input.setText(os.path.abspath("Processing")) # Default
        out_layout.addWidget(self.out_input)
        
        self.out_browse = QPushButton("Browse")
        self.out_browse.clicked.connect(lambda: self.browse_folder(self.out_input))
        out_layout.addWidget(self.out_browse)
        paths_layout.addLayout(out_layout)
        
        header_layout.addLayout(paths_layout)
        
        # Start Engine Button
        self.engine_btn = QPushButton("Start Engine")
        self.engine_btn.setObjectName("engine_btn")
        self.engine_btn.setCheckable(True)
        self.engine_btn.clicked.connect(self.toggle_engine)
        header_layout.addWidget(self.engine_btn)

        self.main_layout.addLayout(header_layout)

    def setup_console(self):
        console_layout = QHBoxLayout()
        
        # Matrix Log Window
        self.log_window = QTextEdit()
        self.log_window.setReadOnly(True)
        console_layout.addWidget(self.log_window, stretch=3)
        
        # Live Thumbnail Box
        self.thumbnail_label = QLabel("No Image")
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setStyleSheet("background-color: #121212; border: 1px solid #444; border-radius: 4px; color: #555;")
        self.thumbnail_label.setMinimumSize(250, 250)
        self.thumbnail_label.setMaximumSize(300, 300)
        self.thumbnail_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        console_layout.addWidget(self.thumbnail_label, stretch=1)
        
        self.main_layout.addLayout(console_layout)

    def setup_footer(self):
        footer_layout = QHBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        footer_layout.addWidget(self.progress_bar)
        
        self.main_layout.addLayout(footer_layout)

    # --- SLOTS ---
    def browse_folder(self, line_edit):
        folder = QFileDialog.getExistingDirectory(self, "Select Directory", line_edit.text() or os.getcwd(), QFileDialog.Option.DontUseNativeDialog)
        if folder:
            line_edit.setText(folder)

    def toggle_engine(self, is_checked):
        if is_checked:
            # Start Watcher Background Thread
            self.engine_btn.setText("Stop Engine")
            
            drop_path = self.drop_input.text()
            out_path = self.out_input.text()
            
            self.worker = EngineWorker(drop_path, out_path)
            
            # Connect Worker signals to GUI slots
            self.worker.log_msg.connect(self.append_log)
            self.worker.status_update.connect(self.update_status)
            self.worker.thumbnail_update.connect(self.update_thumbnail)
            self.worker.progress_update.connect(self.update_progress)
            
            self.worker.start() # Start the QThread safely
        else:
            # Stop Watcher safely
            self.engine_btn.setText("Start Engine")
            if self.worker:
                self.worker.stop()
                self.append_log(f"[{None}] Shutting down engine...")
                # The thread will exit cleanly because we set is_running = False

    def append_log(self, text):
        self.log_window.append(text)
        
    def update_status(self, status):
        # Update text and coloring
        if status == "WATCHING":
            self.status_label.setText("Status: WATCHING")
            self.status_label.setStyleSheet("color: #55FF55; font-weight: bold; font-size: 16px;")
        else:
            self.status_label.setText("Status: IDLE")
            self.status_label.setStyleSheet("color: #AAAAAA; font-weight: bold; font-size: 16px;")

    def update_thumbnail(self, image_path):
        # Update Live Thumbnail flash
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            # scale keeping ratio
            pixmap = pixmap.scaled(self.thumbnail_label.width(), self.thumbnail_label.height(), 
                                   Qt.AspectRatioMode.KeepAspectRatio, 
                                   Qt.TransformationMode.SmoothTransformation)
            self.thumbnail_label.setPixmap(pixmap)
        else:
            self.thumbnail_label.setText("Unable to load image")

    def update_progress(self, val):
        self.progress_bar.setValue(val)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
