"""
Photagger — File system watcher and processing pipeline.
Monitors drop zones, orchestrates blur/exposure/tagging/categorization.
"""
import os
import time
import shutil
import threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .queue_manager import QueueManager
import multiprocessing as mp
from .face_detector import FaceDetector
from .duplicate_detector import DuplicateDetector
from .xmp_generator import generate_xmp
from .exif_reader import extract_exif, format_exif_summary
from .exposure_analyzer import analyze_exposure
from .smart_sorter import classify_tags, get_category_subfolder
from .history_db import HistoryDB
from .constants import SUPPORTED_EXTENSIONS, DEFAULT_BLUR_THRESHOLD, FILE_TRANSFER_TIMEOUT, FILE_STABLE_CHECKS
from .logger import get_logger

from PyQt6.QtCore import QThread, pyqtSignal

log = get_logger("watcher")

class AIProxy:
    """Proxy class that runs the real VisionEngine in an isolated process."""
    def __init__(self, blur_threshold, signals):
        from .vision_engine import _run_ai_process
        self.cmd_q = mp.Queue()
        self.res_q = mp.Queue()
        self.signals = signals
        self.p = mp.Process(target=_run_ai_process, args=(self.cmd_q, self.res_q, blur_threshold), daemon=True)
        self.p.start()
        
        # Wait for init
        while True:
            msg_type, payload = self.res_q.get()
            if msg_type == "progress":
                self.signals.log_msg.emit(f"[{time.strftime('%H:%M:%S')}] {payload}")
            elif msg_type == "init_done":
                if isinstance(payload, Exception):
                    raise payload
                self.is_ready = payload
                break

    def is_blurry(self, file_path):
        self.cmd_q.put(("blur", file_path))
        while True:
            msg_type, payload = self.res_q.get()
            if msg_type == "blur":
                return payload
            elif msg_type == "progress":
                self.signals.log_msg.emit(f"[{time.strftime('%H:%M:%S')}] {payload}")
                
    def get_tags(self, file_path, top_k=3):
        self.cmd_q.put(("tag", file_path, top_k))
        while True:
            msg_type, payload = self.res_q.get()
            if msg_type == "tag":
                return payload
            elif msg_type == "progress":
                self.signals.log_msg.emit(f"[{time.strftime('%H:%M:%S')}] {payload}")
                
    def stop(self):
        self.cmd_q.put(None)
        self.p.join(timeout=5)


class NewPhotoHandler(FileSystemEventHandler):
    """Handles new file events from the watchdog observer."""

    def __init__(self, processing_dir: Path, rejected_dir: Path,
                 signals, ai_proxy: AIProxy, queue_manager: QueueManager,
                 history_db: HistoryDB, session_id: str,
                 face_detector: FaceDetector,
                 auto_categorize: bool = True, top_k: int = 3):
        super().__init__()
        self.processing_dir = Path(processing_dir)
        self.rejected_dir = Path(rejected_dir)
        self.signals = signals
        self.ai = ai_proxy
        self.queue = queue_manager
        self.face_detector = face_detector
        self.dup_detector = DuplicateDetector()
        self.history = history_db
        self.session_id = session_id
        self.auto_categorize = auto_categorize
        self.top_k = top_k
        self.session_hashes: list[tuple[str, str]] = []  # (filename, hash_str)

    def on_created(self, event):
        if event.is_directory:
            return
        self.process_file(Path(event.src_path))

    def on_moved(self, event):
        if event.is_directory:
            return
        self.process_file(Path(event.dest_path))

    def process_file(self, file_path: Path):
        """Full processing pipeline for a single image file."""
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return

        self.queue.mark_start()
        processed, total, eta = self.queue.get_status()
        self.signals.queue_update.emit(processed, total, eta)

        self._log(f"[DETECT] {file_path.name}")
        self._log(f"[WAIT] File transfer in progress...")
        self.signals.progress_update.emit(5)
        self.signals.stage_update.emit("Waiting for file transfer...")

        if not self.wait_for_file_transfer(file_path):
            self._log(f"[WARN] File transfer timed out: {file_path.name}")
            return

        self.signals.progress_update.emit(15)
        self.signals.thumbnail_update.emit(str(file_path.absolute()))

        # ─── EXIF Extraction ─────────────────────────────────
        self.signals.stage_update.emit("Reading EXIF metadata...")
        exif = extract_exif(file_path)
        exif_summary = format_exif_summary(exif)
        if exif_summary != "No EXIF data":
            self._log(f"[EXIF] {exif_summary}")
        self.signals.exif_update.emit(exif)
        self.signals.progress_update.emit(25)

        # ─── Blur Detection ──────────────────────────────────
        self.signals.stage_update.emit("Analyzing focus quality...")
        self._log(f"[FOCUS] Analyzing Laplacian variance...")
        is_blur, var_score = self.ai.is_blurry(file_path)
        self.signals.progress_update.emit(40)

        if is_blur:
            self._log(f"[REJECT] Variance {var_score:.1f} — Blurry")
            target = self._move_to_rejected(file_path)
            self.history.log_processed(
                filename=file_path.name, original_path=str(file_path),
                final_path=str(target) if target else "",
                blur_score=var_score, exposure_score=0, exposure_verdict="skipped",
                star_rating=0, tags=[], category="rejected",
                status="rejected", exif_summary=exif_summary,
                session_id=self.session_id
            )
            self.signals.stats_update.emit("rejected")
            self.signals.gallery_entry.emit({
                "filename": file_path.name,
                "final_path": str(target) if target else "",
                "status": "rejected",
                "category": "rejected",
                "star_rating": 0,
                "tags": "",
                "blur_score": var_score,
                "exposure_score": 0,
            })
            self.signals.progress_update.emit(0)
            self.signals.stage_update.emit("")
            self.queue.mark_processed()
            processed, total, eta = self.queue.get_status()
            self.signals.queue_update.emit(processed, total, eta)
            return

        self._log(f"[PASS] Variance {var_score:.1f} — Sharp")

        # ─── Exposure Analysis ───────────────────────────────
        self.signals.stage_update.emit("Evaluating exposure quality...")
        self._log(f"[EXPOSURE] Analyzing histogram...")
        exposure = analyze_exposure(file_path)
        self._log(f"[EXPOSURE] Score: {exposure.score:.0f}/100 ({exposure.verdict}) "
                  f"| Highlights: {exposure.highlights_clipped}% | Shadows: {exposure.shadows_clipped}%")
        self.signals.progress_update.emit(55)

        # ─── Duplicate Detection ─────────────────────────────
        self.signals.stage_update.emit("Checking for duplicates...")
        img_hash = self.dup_detector.compute_hash(file_path)
        duplicate_group = ""
        if img_hash:
            dups = self.dup_detector.find_duplicates(img_hash, self.session_hashes)
            if dups:
                duplicate_group = f"dup_of_{dups[0]}"
                self._log(f"[DUPE] Found duplicate of {dups[0]}")
            self.session_hashes.append((file_path.name, img_hash))
        
        # ─── Face Detection ──────────────────────────────────
        self.signals.stage_update.emit("Detecting faces...")
        face_count = self.face_detector.detect_faces(file_path)
        if face_count > 0:
            self._log(f"[FACES] Detected {face_count} face(s)")

        # ─── AI Semantic Tagging ─────────────────────────────
        self.signals.stage_update.emit("Extracting semantic tags...")
        self._log(f"[AI] CLIP inference...")
        raw_tags = self.ai.get_tags(file_path, top_k=self.top_k)
        self._log(f"[TAGS] {', '.join(raw_tags)}")
        self.signals.progress_update.emit(75)

        # ─── Category Classification ────────────────────────
        self.signals.stage_update.emit("Classifying category...")
        category, enriched_tags = classify_tags(raw_tags)
        
        if face_count > 0 and "portrait" not in enriched_tags:
            enriched_tags.append("portrait")
            if category == "uncategorized":
                category = "portrait"
                
        if duplicate_group:
            enriched_tags.append("duplicate")
            
        self._log(f"[SORT] Category: {category.capitalize()} | Tags: {', '.join(enriched_tags)}")
        self.signals.tags_update.emit(enriched_tags)
        self.signals.progress_update.emit(85)

        # ─── Move & Generate XMP ─────────────────────────────
        self.signals.stage_update.emit("Writing XMP sidecar...")
        if self.auto_categorize:
            dest_dir = get_category_subfolder(self.processing_dir, category)
        else:
            dest_dir = self.processing_dir

        target_path = self._move_file(file_path, dest_dir)
        if target_path:
            generate_xmp(
                target_path, enriched_tags,
                rating=exposure.rating,
                label="Green" if exposure.score >= 70 else "",
                exif_description=exif_summary,
            )
            self._log(f"[XMP] Sidecar generated — {exposure.rating} star rating")

        self.signals.progress_update.emit(95)

        # ─── Log to History ──────────────────────────────────
        self.history.log_processed(
            filename=file_path.name, original_path=str(file_path),
            final_path=target_path or "",
            blur_score=var_score, exposure_score=exposure.score,
            exposure_verdict=exposure.verdict, star_rating=exposure.rating,
            tags=enriched_tags, category=category,
            status="accepted", exif_summary=exif_summary,
            session_id=self.session_id
        )
        self.signals.stats_update.emit("accepted")
        self.signals.gallery_entry.emit({
            "filename": file_path.name,
            "final_path": target_path or "",
            "status": "accepted",
            "category": category,
            "star_rating": exposure.rating,
            "tags": ",".join(enriched_tags),
            "blur_score": var_score,
            "exposure_score": exposure.score,
        })

        self._log(f"Processing complete: {file_path.name}")
        self.signals.progress_update.emit(100)
        
        self.queue.mark_processed()
        processed, total, eta = self.queue.get_status()
        self.signals.queue_update.emit(processed, total, eta)
        
        time.sleep(0.3)
        self.signals.progress_update.emit(0)
        self.signals.stage_update.emit("")

    def wait_for_file_transfer(self, file_path: Path) -> bool:
        """Wait until a file has finished being written (stable size check)."""
        previous_size = -1
        stable_count = 0
        start_time = time.time()

        while time.time() - start_time < FILE_TRANSFER_TIMEOUT:
            if not file_path.exists():
                return False
            try:
                current_size = file_path.stat().st_size
                if current_size == previous_size and current_size > 0:
                    stable_count += 1
                else:
                    stable_count = 0
                previous_size = current_size
                if stable_count >= FILE_STABLE_CHECKS:
                    return True
            except OSError:
                pass
            time.sleep(1)

        self._log(f"[WARN] Timeout waiting for: {file_path.name}")
        return False

    def _move_to_rejected(self, file_path: Path) -> str | None:
        """Move file to rejected directory with collision avoidance."""
        return self._move_file(file_path, self.rejected_dir)

    def _move_file(self, file_path: Path, dest_dir: Path) -> str | None:
        """Move a file to a destination with collision avoidance and retry logic."""
        target_path = self._avoid_collision(dest_dir, file_path)
        for attempt in range(3):
            try:
                shutil.move(str(file_path), str(target_path))
                self._log(f"[MOVE] {target_path.parent.name}/{target_path.name}")
                return str(target_path)
            except PermissionError:
                if attempt < 2:
                    log.warning(f"File locked, retry {attempt + 1}/3: {file_path.name}")
                    time.sleep(1)
                else:
                    self._log(f"[ERROR] Failed to move (file locked): {file_path.name}")
                    return None
            except Exception as e:
                self._log(f"[ERROR] Failed to move {file_path.name}: {e}")
                return None

    def _avoid_collision(self, dir_path: Path, file_path: Path) -> Path:
        """Generate a unique filename if target already exists."""
        target = dir_path / file_path.name
        if target.exists():
            timestamp = int(time.time())
            new_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            target = dir_path / new_name
        return target

    def _log(self, text: str):
        now = time.strftime("%H:%M:%S")
        self.signals.log_msg.emit(f"[{now}] {text}")
        log.info(text)


class EngineWorker(QThread):
    """Background worker thread that runs the full processing pipeline."""

    log_msg = pyqtSignal(str)
    status_update = pyqtSignal(str)
    thumbnail_update = pyqtSignal(str)
    progress_update = pyqtSignal(int)
    stage_update = pyqtSignal(str)
    stats_update = pyqtSignal(str)     # "accepted" or "rejected"
    tags_update = pyqtSignal(list)     # enriched tag list
    exif_update = pyqtSignal(dict)     # EXIF data dict
    gallery_entry = pyqtSignal(dict)   # full entry for gallery display
    queue_update = pyqtSignal(int, int, int) # processed, total, eta_seconds

    def __init__(self, drop_zone: str, processing_zone: str, rejected_zone: str,
                 blur_threshold: float = DEFAULT_BLUR_THRESHOLD,
                 auto_categorize: bool = True, top_k: int = 3):
        super().__init__()
        self.drop_zone = drop_zone
        self.processing_zone = processing_zone
        self.rejected_zone = rejected_zone
        self.blur_threshold = blur_threshold
        self.auto_categorize = auto_categorize
        self.top_k = top_k
        self.observer = None
        self._stop_event = threading.Event()

    def run(self):
        self.status_update.emit("BOOTING")
        self.log_msg.emit(f"[{time.strftime('%H:%M:%S')}] [BOOT] Initializing AI engine...")

        # Progress callback for model downloads
        def on_progress(msg):
            self.log_msg.emit(f"[{time.strftime('%H:%M:%S')}] {msg}")

        try:
            self.ai_proxy = AIProxy(
                blur_threshold=self.blur_threshold,
                signals=self
            )
            face_detector = FaceDetector(
                progress_callback=on_progress
            )
        except Exception as e:
            self.log_msg.emit(f"[{time.strftime('%H:%M:%S')}] [FATAL] Engine initialization error: {e}")
            self.status_update.emit("IDLE")
            return

        if not getattr(self.ai_proxy, 'is_ready', False):
            self.log_msg.emit(f"[{time.strftime('%H:%M:%S')}] [WARN] AI engine in degraded mode (tagging disabled)")

        # Initialize history database
        history = HistoryDB()
        session_id = history.start_session()

        # Setup directories
        drop_path = Path(self.drop_zone)
        proc_path = Path(self.processing_zone)
        rej_path = Path(self.rejected_zone)
        for p in (drop_path, proc_path, rej_path):
            p.mkdir(parents=True, exist_ok=True)

        # Create queue manager
        queue_manager = QueueManager(str(drop_path))

        # Create event handler and observer
        handler = NewPhotoHandler(
            proc_path, rej_path, self, self.ai_proxy, queue_manager, history, session_id,
            face_detector=face_detector,
            auto_categorize=self.auto_categorize, top_k=self.top_k
        )
        self.observer = Observer()
        self.observer.schedule(handler, str(drop_path), recursive=False)
        self.observer.start()

        self.status_update.emit("SCANNING")
        self.log_msg.emit(f"[{time.strftime('%H:%M:%S')}] [SCAN] Scanning existing files in {self.drop_zone}...")

        # Retroactive scan
        existing = 0
        for item in sorted(drop_path.iterdir()):
            if self._stop_event.is_set():
                break
            if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS:
                existing += 1
                handler.process_file(item)

        if existing > 0:
            self.log_msg.emit(f"[{time.strftime('%H:%M:%S')}] [DONE] Processed {existing} existing file(s)")

        self.status_update.emit("WATCHING")
        self.log_msg.emit(f"[{time.strftime('%H:%M:%S')}] [WATCH] Live watcher active. Waiting for new drops...")

        # Wait loop — using threading.Event for thread-safe shutdown
        while not self._stop_event.wait(timeout=1.0):
            pass

        # Clean shutdown
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5)
            
        try:
            if hasattr(self, 'ai_proxy'):
                self.ai_proxy.stop()
        except:
            pass

        # Finalize session
        try:
            history.end_session(session_id)
        except Exception:
            pass

        self.status_update.emit("IDLE")
        self.log_msg.emit(f"[{time.strftime('%H:%M:%S')}] [STOP] Engine stopped.")

    def stop(self):
        """Thread-safe stop signal."""
        self._stop_event.set()

    @property
    def session_id(self) -> str:
        """Get the current session ID (available after run starts)."""
        return getattr(self, '_session_id', '')
