"""
Photagger — Duplicate Detector.
Generates perceptual hashes (pHash) for images to identify exact and near-duplicates.
"""
from pathlib import Path
from PIL import Image
import imagehash
from .logger import get_logger

log = get_logger("duplicate_detector")

# Threshold for considering images as "near-duplicates".
# 0 = exact match. 1-8 = similar (burst shots, slight crops, slight exposure changes).
DUPLICATE_THRESHOLD = 8


class DuplicateDetector:
    """Manages perceptual hashing and duplicate grouping."""

    def __init__(self):
        pass

    def compute_hash(self, file_path: Path | str) -> str | None:
        """
        Compute the perceptual hash of an image.
        Returns a string representation of the hash.
        """
        try:
            with Image.open(file_path) as img:
                # Use phash (perceptual hash) as it is robust to minor modifications
                phash = imagehash.phash(img)
                return str(phash)
        except Exception as e:
            log.error(f"Failed to compute hash for {file_path}: {e}")
            return None

    def calculate_distance(self, hash1_str: str, hash2_str: str) -> int:
        """
        Calculate the Hamming distance between two hash strings.
        Returns the integer distance, or -1 if invalid.
        """
        try:
            h1 = imagehash.hex_to_hash(hash1_str)
            h2 = imagehash.hex_to_hash(hash2_str)
            return h1 - h2
        except Exception:
            return -1

    def is_duplicate(self, hash1_str: str, hash2_str: str, threshold: int = DUPLICATE_THRESHOLD) -> bool:
        """
        Check if two hashes represent near-duplicate images based on the threshold.
        """
        distance = self.calculate_distance(hash1_str, hash2_str)
        if distance < 0:
            return False
        return distance <= threshold

    def find_duplicates(self, target_hash: str, hash_pool: list[tuple[str, str]], threshold: int = DUPLICATE_THRESHOLD) -> list[str]:
        """
        Find duplicates for a target hash within a pool of hashes.
        
        Args:
            target_hash: The hash string to match against.
            hash_pool: A list of tuples (identifier, hash_string).
            threshold: The maximum Hamming distance.
            
        Returns:
            List of identifiers from the pool that are duplicates.
        """
        duplicates = []
        for identifier, pool_hash in hash_pool:
            if self.is_duplicate(target_hash, pool_hash, threshold):
                duplicates.append(identifier)
        return duplicates
