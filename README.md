# 📸 Photagger — AI Photography Culling & Tagging Pipeline

A professional-grade desktop application that automatically evaluates, sorts, and tags RAW/JPG photography using computer vision and ONNX deep learning models. Built for photographers who want to automate their culling workflow with Adobe Lightroom integration.

## ✨ Features

### Core Pipeline
- **🔍 Blur Detection** — OpenCV Laplacian variance analysis instantly flags out-of-focus shots
- **📊 Exposure Analysis** — Histogram-based detection of blown highlights and crushed shadows
- **🧠 AI Semantic Tagging** — MobileNetV2 (ONNX) classifies images into meaningful categories
- **🏷️ Photography-Aware Categories** — Maps ImageNet labels to photographer-friendly terms (landscape, wildlife, portrait, etc.)
- **📝 XMP Sidecar Generation** — Adobe Lightroom-compatible `.xmp` files with keywords + star ratings

### Smart Organization
- **📁 Auto-Categorization** — Automatically sorts photos into category subfolders (Landscape/, Wildlife/, Portrait/, etc.)
- **📋 EXIF Extraction** — Reads camera model, lens, ISO, aperture, shutter speed, GPS
- **⭐ Quality Ratings** — Auto-assigns 1-5 star ratings based on blur + exposure quality

### Professional Tools
- **🖼️ Gallery View** — Thumbnail grid of all processed images with status indicators
- **📊 Session Reports** — Beautiful HTML reports with category breakdowns and statistics
- **💾 Processing History** — SQLite database logs every event for undo and analytics
- **🔄 Drag & Drop** — Drop images directly onto the app window from Explorer

### Architecture
- **Background Processing** — Watchdog + QThread keeps the UI responsive during heavy AI workloads
- **ONNX Runtime** — Bypasses PyTorch/CUDA DLL conflicts, runs natively on all hardware
- **Settings Persistence** — Remembers your preferences, paths, and window position
- **Proper Logging** — Rotating file logs in `%APPDATA%/Photagger/logs/`

## 🚀 Quick Start

### Requirements
- Python 3.10+
- Windows 10/11

### Installation

```bash
# Clone and setup
cd photagger
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Run

```bash
python run.py
```

Or as a module:
```bash
set PYTHONPATH=src
python -m photagger
```

### Usage

1. **Set Drop Zone** — Select the folder where photos will be imported from SD cards
2. **Set Output** — Select the destination for processed & categorized photos
3. **Click Start Engine** — The background watcher will scan existing files, then monitor for new drops
4. **Drop photos** — Copy/paste into the Drop Zone, or drag files directly onto the app window
5. **Review** — Check the Gallery tab for processed images, generate reports

## 📂 Project Structure

```
photagger/
├── src/photagger/          # Main package
│   ├── app.py              # Premium PyQt6 UI (tabbed, stats, gallery)
│   ├── watcher.py          # File system watcher + processing pipeline
│   ├── vision_engine.py    # ONNX blur detection + semantic tagging
│   ├── xmp_generator.py    # Adobe XMP sidecar generation
│   ├── exif_reader.py      # EXIF metadata extraction
│   ├── exposure_analyzer.py # Histogram-based exposure quality
│   ├── smart_sorter.py     # Auto-categorization engine
│   ├── gallery_widget.py   # Thumbnail grid widget
│   ├── history_db.py       # SQLite processing history
│   ├── session_report.py   # HTML/CSV report generation
│   ├── config.py           # QSettings persistence
│   ├── constants.py        # Centralized configuration
│   └── logger.py           # Rotating file logging
├── tests/                  # Test suite (18 tests)
├── pyproject.toml          # PEP 621 packaging
├── requirements.txt        # Pinned dependencies
└── run.py                  # Development launcher
```

## 🎯 Adobe Lightroom Sync

Processed images generate `.xmp` sidecar files with AI keywords and star ratings:

- **RAW Files** (`.CR2`, `.NEF`, etc.) — Lightroom reads `.xmp` sidecars automatically on import
- **JPEG Files** — In Lightroom Library, right-click → Metadata → "Read Metadata from File"

## 📜 License

MIT License — see [LICENSE](LICENSE)
