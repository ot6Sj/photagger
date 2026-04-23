import os
import time
import shutil
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from vision_engine import VisionEngine
from xmp_generator import generate_xmp

from PyQt6.QtCore import QThread, pyqtSignal

SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.raw', '.raf', '.dng', '.heic', '.arw', '.cr2', '.cr3'}

class NewPhotoHandler(FileSystemEventHandler):
    def __init__(self, processing_dir, rejected_dir, signals, vision_engine):
        super().__init__()
        self.processing_dir = Path(processing_dir)
        self.rejected_dir = Path(rejected_dir)
        self.signals = signals
        self.ai = vision_engine

    def on_created(self, event):
        if event.is_directory:
            return
        self.process_file(Path(event.src_path))

    def on_moved(self, event):
        if event.is_directory:
            return
        self.process_file(Path(event.dest_path))

    def process_file(self, file_path):
        
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return
            
        self._log(f"Detected: {file_path.name}")
        self._log(f"Waiting for copy to finish: {file_path.name}...")
        self.signals.progress_update.emit(10)
        
        if self.wait_for_file_transfer(file_path):
            self.signals.progress_update.emit(30)
            
            # --- PHASE 2 & 3: AI LOGIC ---
            self.signals.thumbnail_update.emit(str(file_path.absolute()))
            self._log(f"OpenCV: Variance check in progress...")
            
            # 1. Blur Check
            if isinstance(self.ai.is_blurry(file_path), tuple):
                is_blur, var_score = self.ai.is_blurry(file_path)
            else:
                 # fallback if something went wrong
                 is_blur, var_score = False, 999.0
                 
            self.signals.progress_update.emit(50)
            
            if is_blur:
                self._log(f"OpenCV: Variance {var_score:.1f} -> REJECTED (Blurry)")
                self.move_to_rejected(file_path)
                self.signals.progress_update.emit(0)
                return
            
            self._log(f"OpenCV: Variance {var_score:.1f} -> PASSED")
            self.signals.progress_update.emit(60)
            
            # 2. ResNet Tagging
            self._log(f"ResNet50: Extracting semantics...")
            tags = self.ai.get_tags(file_path, top_k=3)
            self._log(f"Tagged '{', '.join(tags)}'")
            self.signals.progress_update.emit(85)
            
            # --- PHASE 4: XMP GENERATION ---
            # Move the photo first, then generate XMP alongside it
            target_path = self.move_to_processing(file_path)
            if target_path:
                xmp_status = generate_xmp(target_path, tags)
                if xmp_status:
                    self._log(f"XMP Sidecar Generated Successfully.")
                else:
                    self._log(f"Failed to write XMP Sidecar.")

            self.signals.progress_update.emit(100)
            time.sleep(0.5)
            self.signals.progress_update.emit(0)

    def wait_for_file_transfer(self, file_path, timeout=60):
        previous_size = -1
        stable_count = 0
        required_stable_checks = 2
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if not file_path.exists():
                return False
                
            try:
                current_size = file_path.stat().st_size
                if current_size == previous_size:
                    stable_count += 1
                else:
                    stable_count = 0 
                
                previous_size = current_size
                
                if stable_count >= required_stable_checks:
                    return True
            except OSError:
                pass
                
            time.sleep(1)
            
        self._log(f"Timeout waiting for file transfer: {file_path}")
        return False

    def move_to_rejected(self, file_path):
        target_path = self.avoid_collision(self.rejected_dir, file_path)
        try:
            shutil.move(str(file_path), str(target_path))
            self._log(f"MOVED TO REJECTED: {target_path.name}")
        except Exception as e:
            self._log(f"Failed to move file {file_path.name}: {e}")

    def move_to_processing(self, file_path):
        target_path = self.avoid_collision(self.processing_dir, file_path)
        try:
            shutil.move(str(file_path), str(target_path))
            self._log(f"MOVED TO PROCESSING: {target_path.name}")
            return str(target_path)
        except Exception as e:
            self._log(f"Failed to move file {file_path.name}: {e}")
            return None

    def avoid_collision(self, dir_path, file_path):
        target_path = dir_path / file_path.name
        if target_path.exists():
            timestamp = int(time.time())
            new_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            target_path = dir_path / new_name
        return target_path
            
    def _log(self, text):
        now = time.strftime("%H:%M:%S")
        self.signals.log_msg.emit(f"[{now}] {text}")

class EngineWorker(QThread):
    log_msg = pyqtSignal(str)
    status_update = pyqtSignal(str)
    thumbnail_update = pyqtSignal(str)
    progress_update = pyqtSignal(int)
    
    def __init__(self, drop_zone, processing_zone):
        super().__init__()
        self.drop_zone = drop_zone
        self.processing_zone = processing_zone
        self.rejected_zone = "Rejected_Blurry"
        self.observer = None
        self.is_running = True

    def run(self):
        # Notify UI we are booting (PyTorch takes ~2s to load)
        self.status_update.emit("BOOTING AI...")
        self.log_msg.emit(f"[{time.strftime('%H:%M:%S')}] Booting ResNet50 Architecture in background...")
        try:
            ai_engine = VisionEngine(blur_threshold=100.0) # threshold of 100 is standard
        except Exception as e:
            self.log_msg.emit(f"[{time.strftime('%H:%M:%S')}] FATAL AI ERROR: {e}")
            self.status_update.emit("IDLE")
            return
            
        drop_path = Path(self.drop_zone)
        proc_path = Path(self.processing_zone)
        rej_path = Path(self.rejected_zone)
        
        drop_path.mkdir(parents=True, exist_ok=True)
        proc_path.mkdir(parents=True, exist_ok=True)
        rej_path.mkdir(parents=True, exist_ok=True)

        event_handler = NewPhotoHandler(proc_path, rej_path, self, ai_engine)
        self.observer = Observer()
        self.observer.schedule(event_handler, str(drop_path), recursive=False)
        
        self.observer.start()
        self.status_update.emit("PROCESSING EXISTING")
        self.log_msg.emit(f"[{time.strftime('%H:%M:%S')}] Core Started. Scanning for existing files in {self.drop_zone}...")
        
        # Retroactive Scan: Process files that were already in the folder
        existing_files_found = 0
        for item in drop_path.iterdir():
            if not self.is_running:
                break
            if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS:
                existing_files_found += 1
                event_handler.process_file(item)
                
        if existing_files_found > 0:
            self.log_msg.emit(f"[{time.strftime('%H:%M:%S')}] Finished processing {existing_files_found} existing file(s).")
            
        self.status_update.emit("WATCHING")
        self.log_msg.emit(f"[{time.strftime('%H:%M:%S')}] Live Watcher active. Waiting for new drops...")
        
        try:
            while self.is_running:
                time.sleep(1)
        except Exception:
            pass
            
        if self.observer:
            self.observer.stop()
            self.observer.join()
            
        self.status_update.emit("IDLE")
        self.log_msg.emit(f"[{time.strftime('%H:%M:%S')}] Engine Stopped.")

    def stop(self):
        self.is_running = False
