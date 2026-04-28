"""Tests for the XMP sidecar generator."""
import os
import tempfile
import pytest

# Add src to path for testing
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from photagger.xmp_generator import generate_xmp


class TestXMPGenerator:
    """Tests for XMP sidecar file generation."""

    def test_basic_xmp_generation(self, tmp_path):
        """Test that a valid XMP file is created with basic tags."""
        img_path = str(tmp_path / "test_photo.jpg")
        open(img_path, 'w').close()  # Create dummy file

        result = generate_xmp(img_path, ["landscape", "mountain", "sunset"])
        assert result is True

        xmp_path = str(tmp_path / "test_photo.xmp")
        assert os.path.exists(xmp_path)

        with open(xmp_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "landscape" in content
        assert "mountain" in content
        assert "sunset" in content
        assert 'xmlns:dc' in content
        assert 'Photagger' in content

    def test_xmp_with_rating(self, tmp_path):
        """Test that star rating is embedded correctly."""
        img_path = str(tmp_path / "rated.jpg")
        open(img_path, 'w').close()

        generate_xmp(img_path, ["wildlife"], rating=4)

        xmp_path = str(tmp_path / "rated.xmp")
        with open(xmp_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert 'xmp:Rating="4"' in content

    def test_xml_injection_protection(self, tmp_path):
        """Test that special XML characters are escaped."""
        img_path = str(tmp_path / "evil.jpg")
        open(img_path, 'w').close()

        malicious_tags = ['<script>alert("xss")</script>', 'tag&value', 'normal']
        result = generate_xmp(img_path, malicious_tags)
        assert result is True

        xmp_path = str(tmp_path / "evil.xmp")
        with open(xmp_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Should be escaped, not raw
        assert '<script>' not in content
        assert '&lt;script&gt;' in content
        assert '&amp;' in content

    def test_empty_tags(self, tmp_path):
        """Test XMP generation with empty tag list."""
        img_path = str(tmp_path / "notags.jpg")
        open(img_path, 'w').close()

        result = generate_xmp(img_path, [])
        assert result is True

    def test_rating_clamping(self, tmp_path):
        """Test that ratings are clamped to 0-5 range."""
        img_path = str(tmp_path / "clamped.jpg")
        open(img_path, 'w').close()

        generate_xmp(img_path, ["test"], rating=99)
        xmp_path = str(tmp_path / "clamped.xmp")
        with open(xmp_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'xmp:Rating="5"' in content
