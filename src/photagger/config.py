"""
Photagger — Settings persistence via QSettings.
Stores user preferences in the Windows registry (or INI fallback).
"""
from PyQt6.QtCore import QSettings
from .constants import APP_NAME, APP_AUTHOR, DEFAULT_BLUR_THRESHOLD, DEFAULT_TOP_K_TAGS


class AppConfig:
    """Type-safe wrapper around QSettings for Photagger preferences."""

    def __init__(self):
        self._s = QSettings(APP_AUTHOR, APP_NAME)

    # ─── Paths ────────────────────────────────────────────────
    @property
    def drop_zone(self) -> str:
        return self._s.value("paths/drop_zone", "")

    @drop_zone.setter
    def drop_zone(self, val: str):
        self._s.setValue("paths/drop_zone", val)

    @property
    def output_zone(self) -> str:
        return self._s.value("paths/output_zone", "")

    @output_zone.setter
    def output_zone(self, val: str):
        self._s.setValue("paths/output_zone", val)

    @property
    def rejected_zone(self) -> str:
        return self._s.value("paths/rejected_zone", "")

    @rejected_zone.setter
    def rejected_zone(self, val: str):
        self._s.setValue("paths/rejected_zone", val)

    # ─── Processing ──────────────────────────────────────────
    @property
    def blur_threshold(self) -> float:
        return float(self._s.value("processing/blur_threshold", DEFAULT_BLUR_THRESHOLD))

    @blur_threshold.setter
    def blur_threshold(self, val: float):
        self._s.setValue("processing/blur_threshold", val)

    @property
    def top_k_tags(self) -> int:
        return int(self._s.value("processing/top_k_tags", DEFAULT_TOP_K_TAGS))

    @top_k_tags.setter
    def top_k_tags(self, val: int):
        self._s.setValue("processing/top_k_tags", val)

    @property
    def auto_categorize(self) -> bool:
        return self._s.value("processing/auto_categorize", True, type=bool)

    @auto_categorize.setter
    def auto_categorize(self, val: bool):
        self._s.setValue("processing/auto_categorize", val)

    @property
    def exposure_reject(self) -> bool:
        return self._s.value("processing/exposure_reject", False, type=bool)

    @exposure_reject.setter
    def exposure_reject(self, val: bool):
        self._s.setValue("processing/exposure_reject", val)

    # ─── Window ──────────────────────────────────────────────
    def save_geometry(self, geometry, state=None):
        self._s.setValue("window/geometry", geometry)
        if state:
            self._s.setValue("window/state", state)

    def restore_geometry(self):
        return self._s.value("window/geometry"), self._s.value("window/state")
