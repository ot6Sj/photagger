"""
Photagger — Application entry point.
Usage: python -m photagger
"""
import sys
import os


def main():
    # High DPI awareness for Windows
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

    # Pre-load ONNX runtime before PyQt6 to avoid DLL conflicts
    import onnxruntime  # noqa: F401

    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt

    from .logger import setup_logging
    from .app import MainWindow

    # Setup logging
    setup_logging()

    app = QApplication(sys.argv)
    app.setApplicationName("Photagger")
    app.setApplicationVersion("1.0.0")
    app.setStyle("Fusion")

    # Global exception hook
    def exception_hook(exc_type, exc_value, exc_tb):
        import traceback
        from .logger import get_logger
        log = get_logger("crash")
        log.critical("".join(traceback.format_exception(exc_type, exc_value, exc_tb)))
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = exception_hook

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
