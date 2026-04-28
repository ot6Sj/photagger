"""Tests for the file watcher utilities."""
import os
import sys
import time
from pathlib import Path
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from photagger.smart_sorter import classify_tags, get_available_categories
from photagger.exposure_analyzer import analyze_exposure, ExposureResult


class TestSmartSorter:
    """Tests for photography category classification."""

    def test_wildlife_classification(self):
        """Wildlife tags should classify as wildlife."""
        category, tags = classify_tags(["lion", "savanna", "grass"])
        assert category == "wildlife"
        assert "wildlife" in tags

    def test_architecture_classification(self):
        """Architecture tags should classify correctly."""
        category, tags = classify_tags(["church", "bell cote", "stone"])
        assert category == "architecture"

    def test_unknown_tags_uncategorized(self):
        """Unknown tags should fall back to uncategorized."""
        category, tags = classify_tags(["xyznotreal", "fakeclass"])
        assert category == "uncategorized"

    def test_enriched_tags_include_category(self):
        """Enriched tags should include the category name."""
        _, tags = classify_tags(["golden retriever", "grass", "park"])
        assert tags[0] in get_available_categories() or tags[0] == "uncategorized"

    def test_available_categories(self):
        """Should have multiple categories loaded."""
        cats = get_available_categories()
        assert len(cats) >= 5
        assert "wildlife" in cats
        assert "landscape" in cats


class TestExposureAnalyzer:
    """Tests for exposure quality analysis."""

    def test_well_exposed_image(self, tmp_path):
        """A balanced gray image should score well."""
        import numpy as np
        import cv2

        img = np.full((200, 200, 3), 128, dtype=np.uint8)
        img += np.random.randint(-30, 30, img.shape, dtype=np.int8).astype(np.uint8)
        path = str(tmp_path / "balanced.png")
        cv2.imwrite(path, img)

        result = analyze_exposure(path)
        assert isinstance(result, ExposureResult)
        assert result.score >= 50
        assert result.rating >= 3

    def test_overexposed_image(self, tmp_path):
        """A nearly white image should be detected as overexposed."""
        import numpy as np
        import cv2

        img = np.full((200, 200, 3), 252, dtype=np.uint8)
        path = str(tmp_path / "blown.png")
        cv2.imwrite(path, img)

        result = analyze_exposure(path)
        assert result.highlights_clipped > 0
        assert result.score < 70

    def test_nonexistent_file(self):
        """Should handle missing files gracefully."""
        result = analyze_exposure("nonexistent.jpg")
        assert result.score == 50.0
        assert result.verdict == "unreadable"
