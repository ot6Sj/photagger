# Smart Photography Culling Pipeline

A robust, multi-threaded desktop application designed to evaluate, sort, and tag RAW/JPG photography captures autonomously using computer vision and deep learning models. 

## Architecture Overview

The system is designed to entirely decouple the heavy computational overhead of neural networks from the graphical interface, maintaining a highly responsive user experience. 

1. **User Interface (PyQt6)**: Acts as the primary control dashboard spanning standard system threads. 
2. **The Watcher (Watchdog & QThread)**: A background worker monitors a specified local `Drop Zone` directory for incoming assets. Threading and Inter-Process Communication (IPC) is achieved via `pyqtSignal`, safely piping computational output strings into the main UI log interface.
3. **The Bouncer (OpenCV)**: Incoming files are evaluated for focus integrity via a Laplacian Variance check. Any file scoring below the mathematical variance threshold is flagged as blurry and moved to a `Rejected` directory to save classification time.
4. **The Brain (PyTorch & ResNet50)**: In-focus photography is cast through a pre-trained ResNet50 Convolutional Neural Network forward pass (running on CUDA where available). Semantic probabilistic strings correspond to dominant image features.
5. **The Bridge (XMP Generation)**: Successfully categorized images are transitioned to the standard `Processing` directory simultaneously with an Adobe Extensible Metadata Platform (`.xmp`) sidecar file. 

## Requirements

Ensure Python 3.10+ is installed prior to setup. 

```bash
pip install -r requirements.txt
```

### Core Dependencies
* `watchdog`: File system event monitoring
* `PyQt6`: Desktop GUI Framework
* `opencv-python`: Mathematical Laplace variance computations
* `torch` / `torchvision`: ResNet classification
* `Pillow`: Image pre-processing for tensors

## Usage

1. Launch the application dashboard:
```bash
python app.py
```
2. Designate a local **Drop Zone** path (where photographs will be aggregated from SD cards or external capture).
3. Designate an **Output Zone** path (where categorized architecture will be migrated).
4. Select **Start Engine** to initiate the background `QThread`. *Note: Initializing the ResNet50 framework natively caches required `.pth` weights to the local system on the first run cycle.*
5. Drop un-sorted photographs into the assigned Drop Zone. The GUI matrix-log will detail the processing step evaluation for variance passing vs tagging logic in real-time. 
6. Processed `.xmp` enabled directories can be natively dragged into photo editing frameworks (like Adobe Lightroom Classic) for immediate categorical synchronization.
