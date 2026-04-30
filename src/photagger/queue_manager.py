"""
Photagger — Queue Management and ETA calculation.
Tracks the drop zone queue, processed files, and estimates remaining time.
"""
import time
from pathlib import Path
from collections import deque
from .constants import SUPPORTED_EXTENSIONS

class QueueManager:
    """Manages processing queue status and ETA."""
    def __init__(self, drop_zone: str):
        self.drop_zone = Path(drop_zone)
        self.processed_count = 0
        self.total_discovered = 0
        self.file_times = deque(maxlen=20)  # Rolling window for speed calculation
        self._last_start = None

    def refresh_total(self) -> int:
        """Scan the drop zone for supported files and update total."""
        if not self.drop_zone.exists():
            return 0
            
        count = sum(1 for p in self.drop_zone.iterdir() 
                   if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS)
        
        # Total is whatever is left in the directory PLUS what we've already processed
        self.total_discovered = self.processed_count + count
        return self.total_discovered

    def mark_start(self):
        """Mark the start of processing a file."""
        self._last_start = time.time()

    def mark_processed(self):
        """Mark a file as processed and record its time."""
        self.processed_count += 1
        if self._last_start is not None:
            duration = time.time() - self._last_start
            self.file_times.append(duration)
            self._last_start = None

    def get_eta_seconds(self) -> int:
        """Calculate ETA in seconds based on rolling average speed."""
        remaining = self.total_discovered - self.processed_count
        if remaining <= 0 or not self.file_times:
            return 0
            
        avg_time = sum(self.file_times) / len(self.file_times)
        return int(avg_time * remaining)

    def get_status(self) -> tuple[int, int, int]:
        """Return (processed, total, eta_seconds)."""
        self.refresh_total()
        return (self.processed_count, self.total_discovered, self.get_eta_seconds())
