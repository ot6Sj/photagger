<p align="center">
  <h1 align="center">Photagger</h1>
  <p align="center">
    <strong>Advanced AI Photography Culling & Semantic Tagging Pipeline</strong>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows">
    <img src="https://img.shields.io/badge/AI-CLIP_ViT--B/32-000000?style=for-the-badge&logo=openai&logoColor=white" alt="CLIP">
    <img src="https://img.shields.io/badge/engine-PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white" alt="PyTorch">
    <img src="https://img.shields.io/badge/GUI-PyQt6-41CD52?style=for-the-badge&logo=qt&logoColor=white" alt="PyQt6">
  </p>
</p>

---

Photagger is a professional-grade desktop application designed to automate the heavy lifting of photography culling. It evaluates focus, exposure, and composition while automatically tagging and sorting images using state-of-the-art computer vision. 

By integrating **CLIP (Contrastive Language-Image Pre-training)** and **Multiprocessing isolation**, Photagger provides an intelligent, open-vocabulary tagging experience without the stability issues common in Windows-based AI workflows.

---

## Performance & Intelligence

| Feature | Implementation |
|---------|----------------|
| **Semantic Tagging** | Full **OpenAI CLIP ViT-B/32** integration for zero-shot image classification and tagging. |
| **Face Detection** | UltraFace ONNX model for rapid face counting and automatic portrait identification. |
| **Duplicate Detection** | Perceptual hashing (pHash) to identify near-identical images in burst sequences. |
| **Quality Analysis** | Laplacian focus evaluation and histogram-based exposure analysis with noise estimation. |
| **Batch Transparency** | Intelligent Queue Manager with rolling-average ETA estimation and real-time progress. |

---

## Core Capabilities

### Semantic Intelligence
Unlike traditional classifiers with fixed labels, Photagger uses **CLIP** to understand photography in a human-like way. It classifies images into categories like `Landscape`, `Wildlife`, `Portrait`, `Architecture`, and `Street` by calculating semantic similarity between images and natural language prompts.

### Near-Duplicate Tracking
The pipeline computes perceptual hashes for every image. If you shoot a burst of 10 identical frames, Photagger identifies them as near-duplicates, allowing you to quickly cull the "redundant" shots and keep only the best one.

### Adobe Lightroom Integration
Photagger writes all AI-generated tags, face counts, and star ratings directly to industry-standard **.xmp** sidecar files. Lightroom and Adobe Bridge read these files automatically, populating your catalog with searchable keywords and ratings before you even open the Library module.

---

## Architecture

To ensure maximum stability on Windows, Photagger utilizes a **Decoupled Multiprocessing Architecture**. PyTorch and the heavy AI models are isolated in a completely separate Python process, preventing DLL initialization conflicts (`WinError 1114`) between deep learning libraries and the PyQt6 GUI thread.

```
┌─────────────────────────────────────────────────────┐
│                   PyQt6 GUI (Main Process)          │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │ Dashboard│  │ Gallery  │  │   Image Viewer    │  │
│  │ Monitor  │  │ Filter   │  │   Full-Screen     │  │
│  └──────────┘  └──────────┘  └───────────────────┘  │
└───────────────────────┬─────────────────────────────┘
                        │ IPC (multiprocessing.Queue)
┌───────────────────────▼─────────────────────────────┐
│               AI WORKER (Isolated Process)          │
│                                                     │
│  ┌──────────┐   ┌──────────┐   ┌─────────────────┐  │
│  │ CLIP     │   │ UltraFace│   │ Perceptual      │  │
│  │ PyTorch  │   │ ONNX     │   │ Hashing         │  │
│  └──────────┘   └──────────┘   └─────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## Installation

### Prerequisites
- **Python 3.10+**
- **Windows 10/11** (Optimized for Windows DLL handling)

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/photagger.git
   cd photagger
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

> **Note:** On the first launch, the application will download the CLIP ViT-B/32 model (~600 MB) from the HuggingFace Hub.

---

## Project Structure

```
photagger/
├── src/photagger/                # Core application package
│   ├── app.py                    # Main UI (Sidebar, Stats, Theme Engine)
│   ├── watcher.py                # Pipeline orchestrator & Multiprocessing proxy
│   ├── vision_engine.py          # Isolated AI Worker (CLIP & PyTorch)
│   ├── face_detector.py          # ONNX-based face detection
│   ├── duplicate_detector.py     # Perceptual hashing (imagehash)
│   ├── queue_manager.py          # ETA estimation & Batch tracking
│   ├── exposure_analyzer.py      # Histogram & Noise evaluation
│   ├── xmp_generator.py          # Adobe XMP generation
│   ├── smart_sorter.py           # Semantic routing logic
│   ├── gallery_widget.py         # Grid view with advanced filtering
│   ├── image_viewer.py           # Professional viewer with filmstrip
│   ├── theme.py                  # Light/Dark mode manager
│   ├── history_db.py             # SQLite persistence
│   └── icons.py                  # Programmatic SVG icon system
├── tests/                        # Automated test suite
├── run.py                        # Application entry point
└── requirements.txt              # Dependency manifest
```

---

## Configuration

| Setting | Description |
|---------|-------------|
| **Blur Threshold** | Laplacian variance cutoff for focus rejection. |
| **Top-K Tags** | Number of semantic tags to generate per image. |
| **Auto-Categorize** | Automatically sort images into category subfolders. |
| **Theme Mode** | Toggle between professional Light and Dark interfaces. |

---

## License
This project is licensed under the MIT License - see the LICENSE file for details.
