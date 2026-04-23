# Smart Photography Culling Pipeline

A robust, multi-threaded desktop application designed to automatically evaluate, sort, and tag RAW/JPG photography captures natively using computer vision and lightweight ONNX deep learning models.

## Architecture Overview

The system architecture cleanly decouples the heavy mathematical workload of neural networks from the graphical interface via native Windows threading, guaranteeing a highly responsive user experience footprint.

1. **User Interface (PyQt6)**: Acts as the primary control dashboard operating strictly on standard system threads. 
2. **The Watcher (Watchdog & QThread)**: A background worker monitors a specified local `Drop Zone` directory for incoming assets. Upon booting, this daemon performs a retroactive scan of all pre-existing files before idling into a live event-watch state. Inter-Process Communication (IPC) is achieved safely via `pyqtSignal`.
3. **The Bouncer (OpenCV)**: Incoming files are passed through a Laplacian Variance focus-evaluation matrix. Any file identifying below the mathematical variance threshold is flagged as out-of-focus and immediately transferred to a `Rejected` directory to reserve compute time.
4. **The Brain (ONNX Runtime)**: In-focus photography is processed using a pre-trained `MobileNetV2` exported ONNX graph. By prioritizing the ONNX Runtime stack over massive framework distributions (i.e., PyTorch/CUDA), it bypasses complex Visual C++ DLL redistributable mismatches (`WinError 1114`) natively executing across all hardware.
5. **The Bridge (XMP Generation)**: Categorized targets are transitioned into the `Processing` directory simultaneously with a generated Adobe Extensible Metadata Platform (`.xmp`) sidecar file conveying its AI semantic keywords.

## Requirements

Ensure Python 3.10+ is actively installed and running from an isolated virtual environment (`.venv`).

```bash
pip install -r requirements.txt
```

### Core Dependencies
* `watchdog`: File system event monitoring
* `PyQt6`: Desktop GUI Framework
* `opencv-python`: Mathematical Laplace variance computations
* `onnxruntime`: Neural network inference engine
* `httpx`: Dynamic HTTP resource caching
* `Pillow` / `numpy`: Matrix and dimensional image preprocessing

## Usage

1. Launch the application dashboard:
```bash
python app.py
```
2. Designate a local **Drop Zone** path (where photographs will be aggregated from SD cards or external capture media).
3. Designate an **Output Zone** path (the destination for successfully categorized asset architecture).
4. Select **Start Engine** to engage the background `QThread`. *Note: Initializing the ONNX framework natively fetches required network binaries (`mobilenetv2-7.onnx` and string labels) from Microsoft repositories locally upon the very first run cycle.*
5. Drop un-sorted photographs into the Drop Zone. The GUI matrix-log will detail the processing step evaluating for variance tolerance vs semantic tagging logic in real-time. 

## Adobe Lightroom Synchronization

Processed images inherently generate a `.xmp` file for programmatic ingest. To ensure Adobe Lightroom parses this metadata accurately:

- **Raw Files (`.CR2`, `.NEF`, etc...)**: Simply drag the target output processing folder into Lightroom. The engine natively reads standard RAW `.xmp` formats automatically upon import.
- **JPEG Files (`.jpg`)**: Lightroom assumes Metadata natively embeds within `.jpg` headers, therefore ignoring sidecar files by default. To capture the AI-generated keywords, highlight the imported JPEG photos within the Lightroom Library, right-click, select **"Metadata"**, and click **"Read Metadata from File"**.
