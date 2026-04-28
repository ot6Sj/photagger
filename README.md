<p align="center">
  <h1 align="center"> Photagger</h1>
  <p align="center">
    <strong>AI-Powered Photography Culling & Tagging Pipeline</strong>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows">
    <img src="https://img.shields.io/badge/AI-ONNX_Runtime-005CED?style=for-the-badge&logo=onnx&logoColor=white" alt="ONNX">
    <img src="https://img.shields.io/badge/GUI-PyQt6-41CD52?style=for-the-badge&logo=qt&logoColor=white" alt="PyQt6">
    <img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" alt="MIT License">
  </p>
</p>

---

A professional-grade desktop application that automatically **evaluates**, **sorts**, and **tags** RAW/JPG photography using computer vision and deep learning — with native Adobe Lightroom integration. Drop your photos in, get organized, tagged, and rated images out. Zero cloud dependency.

---

##  Why Photagger?

| Problem | Solution |
|---------|----------|
| Manually reviewing hundreds of shots after a shoot | **Auto-culls** blurry & poorly exposed images instantly |
| Spending hours tagging in Lightroom | **AI generates keywords** and writes them directly to `.xmp` sidecars |
| Dumping everything into one folder | **Auto-sorts** into `Landscape/`, `Wildlife/`, `Portrait/` subfolders |
| No idea which shots are your best | **Star ratings** (1-5★) auto-assigned based on focus + exposure quality |

---

##  Features

###  Core Pipeline

| Stage | What It Does | Technology |
|-------|-------------|------------|
| **Focus Detection** | Flags out-of-focus shots using Laplacian variance analysis | OpenCV |
| **Exposure Analysis** | Detects blown highlights & crushed shadows via histogram evaluation | OpenCV |
| **Semantic Tagging** | Classifies image content into 1000 ImageNet categories | MobileNetV2 (ONNX) |
| **Category Mapping** | Translates ImageNet labels → photographer-friendly terms | Custom JSON mapping |
| **XMP Generation** | Writes keywords + star ratings to Lightroom-compatible sidecar files | Adobe XMP |

###  Smart Organization

- **Auto-Categorization** — Photos are sorted into subfolders based on AI classification:
  ```
  Processing/
  ├── Landscape/        ← mountains, seashores, valleys
  ├── Wildlife/         ← animals, birds, marine life
  ├── Portrait/         ← people, fashion
  ├── Architecture/     ← buildings, churches, castles
  ├── Street/           ← vehicles, urban scenes
  ├── Macro/            ← insects, flowers, close-ups
  ├── Food/             ← culinary shots
  └── Uncategorized/    ← everything else
  ```
- **EXIF Extraction** — Reads camera model, lens, focal length, ISO, aperture, shutter speed, and GPS coordinates
- **Quality Ratings** — Auto-assigns 1-5★ based on combined focus sharpness + exposure quality

###  Professional Tools

| Tool | Description |
|------|-------------|
| **Gallery View** | Scrollable thumbnail grid with color-coded borders (green = accepted, red = rejected) |
| **Session Reports** | One-click HTML reports with stats cards, category breakdowns, and per-image details |
| **Processing History** | SQLite database logs every event — enables undo, re-processing, and analytics |
| **Drag & Drop** | Drag photos from Windows Explorer directly onto the app window |
| **Settings Dialog** | Adjustable blur threshold, tag count, auto-categorize toggle, exposure reject |

---

##  Architecture

```
┌─────────────────────────────────────────────────────┐
│                   PyQt6 GUI (Main Thread)           │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │  Monitor │  │ Gallery  │  │  Stats Dashboard  │  │
│  │   Tab    │  │   Tab    │  │  Processed/Accept │  │
│  └──────────┘  └──────────┘  └───────────────────┘  │
└───────────────────────┬─────────────────────────────┘
                        │ pyqtSignal (thread-safe IPC)
┌───────────────────────▼─────────────────────────────┐
│              EngineWorker (QThread)                 │
│                                                     │
│  ┌─────────┐   ┌──────────┐   ┌──────────────────┐  │
│  │Watchdog │──▶│ Bouncer  │──▶│   Brain (ONNX)  │  │
│  │Observer │   │OpenCV    │   │  MobileNetV2     │  │
│  │         │   │Blur+Exp  │   │  + SmartSorter   │  │
│  └─────────┘   └──────────┘   └──────────────────┘  │
│                                       │          v  │
│                             ┌─────────▼──────────┐  │
│                             │  XMP + Move + DB   │  │
│                             └────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

**Key design decisions:**
- **ONNX Runtime over PyTorch** — Eliminates CUDA/DLL conflicts (`WinError 1114`), runs on any hardware
- **QThread + Watchdog** — Heavy AI workload runs in background, GUI stays responsive
- **threading.Event** — Thread-safe shutdown (no race conditions)
- **File lock retry** — 3-attempt retry for `shutil.move()` when Windows antivirus holds file locks

---

##  Quick Start

### Prerequisites

- **Python 3.10+**
- **Windows 10/11**

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/photagger.git
cd photagger

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

> **Note:** On first launch, the ONNX model (`mobilenetv2-7.onnx`, ~14 MB) will be automatically downloaded from Microsoft's repository and cached in `%APPDATA%/Photagger/models/`.

### Launch

```bash
python run.py
```

Or run as a Python module:
```bash
set PYTHONPATH=src
python -m photagger
```

### Usage

1. ** Set Drop Zone** — Select the folder where photos will land (from SD cards, imports, etc.)
2. ** Set Output** — Select the destination for successfully processed & categorized photos
3. ** Start Engine** — Click to engage the background watcher
4. ** Drop photos** — Copy files into the Drop Zone, or drag & drop directly onto the app
5. ** Review** — Switch to the Gallery tab, inspect results, generate reports

---

##  Project Structure

```
photagger/
├── src/photagger/                # Main application package
│   ├── __init__.py               # Package init + version
│   ├── __main__.py               # Entry point (python -m photagger)
│   ├── app.py                    # Premium PyQt6 UI (tabbed, stats, gallery)
│   ├── watcher.py                # File system watcher + processing pipeline
│   ├── vision_engine.py          # ONNX blur detection + semantic tagging
│   ├── xmp_generator.py          # Adobe XMP sidecar generation
│   ├── exif_reader.py            # EXIF metadata extraction (Pillow)
│   ├── exposure_analyzer.py      # Histogram-based exposure quality scoring
│   ├── smart_sorter.py           # AI tag → photography category mapper
│   ├── gallery_widget.py         # Thumbnail grid widget with context menus
│   ├── history_db.py             # SQLite processing history + sessions
│   ├── session_report.py         # HTML/CSV report generator
│   ├── config.py                 # QSettings persistence layer
│   ├── constants.py              # Centralized config, colors, defaults
│   ├── logger.py                 # Rotating file logger (%APPDATA%)
│   └── resources/
│       ├── imagenet_classes.txt   # 1000 ImageNet class labels
│       └── photo_categories.json  # ImageNet → photography category mapping
├── tests/                        # Unit tests (18 tests)
│   ├── test_vision_engine.py     # Preprocessing, blur detection
│   ├── test_xmp_generator.py     # XMP generation, XML escaping, ratings
│   └── test_watcher.py           # Smart sorter, exposure analyzer
├── pyproject.toml                # PEP 621 packaging
├── requirements.txt              # Pinned dependencies
├── run.py                        # Development launcher
├── LICENSE                       # MIT License
└── README.md                     # This file
```

---

##  Adobe Lightroom Integration

Photagger generates `.xmp` sidecar files containing AI-generated keywords and quality star ratings. These files are natively compatible with Adobe Lightroom and Bridge.

### Importing into Lightroom

| File Type | How to Import |
|-----------|---------------|
| **RAW** (`.CR2`, `.NEF`, `.ARW`, `.DNG`, `.RAF`, etc.) | Lightroom reads `.xmp` sidecars **automatically** on import — just drag the output folder into the Library |
| **JPEG** (`.jpg`, `.jpeg`) | After import: select photos → right-click → **Metadata** → **Read Metadata from File** |

### What Gets Written to XMP

```xml
<!-- AI-generated keywords -->
<dc:subject>
  <rdf:Bag>
    <rdf:li>wildlife</rdf:li>      <!-- photography category -->
    <rdf:li>golden retriever</rdf:li> <!-- ImageNet classification -->
    <rdf:li>grass</rdf:li>
  </rdf:Bag>
</dc:subject>

<!-- Auto-assigned quality rating -->
xmp:Rating="4"

<!-- Optional color label for well-exposed shots -->
xmp:Label="Green"
```

---

##  Running Tests

```bash
# Activate venv
.venv\Scripts\activate

# Run full test suite
python -m pytest tests/ -v
```

All **18 tests** cover:
- Image preprocessing (shape, normalization range)
- Blur detection (sharp vs. blurry synthetic images)
- Exposure analysis (balanced vs. overexposed)
- XMP generation (basic, ratings, XML injection protection, edge cases)
- Smart categorization (wildlife, architecture, unknown tags)

---

##  Configuration

Settings are persisted automatically via `QSettings` (Windows Registry). Configurable options:

| Setting | Default | Description |
|---------|---------|-------------|
| Blur Threshold | `100.0` | Laplacian variance cutoff (lower = stricter) |
| AI Tags Count | `3` | Number of top-K tags per image |
| Auto-Categorize | `On` | Sort into category subfolders |
| Exposure Reject | `Off` | Auto-reject badly exposed images |

Access via the ** Settings** button in the app header.

---

##  Supported Formats

**Image formats:** `.jpg` `.jpeg` `.png` `.tif` `.tiff` `.bmp`

**RAW formats:** `.cr2` `.cr3` `.nef` `.arw` `.dng` `.raf` `.orf` `.rw2` `.raw` `.heic` `.heif`

---

##  Data Storage

| Data | Location |
|------|----------|
| ONNX Model | `%APPDATA%/Photagger/models/mobilenetv2-7.onnx` |
| Processing History | `%APPDATA%/Photagger/history.db` |
| Log Files | `%APPDATA%/Photagger/logs/photagger.log` |
| Settings | Windows Registry (`HKCU\Software\Photagger`) |

---

##  License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.
