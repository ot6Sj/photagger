"""
Photagger — Smart auto-categorization into subfolders.
Maps AI tags to photography categories and routes files accordingly.
"""
import json
import shutil
from pathlib import Path
from .constants import RESOURCES_DIR
from .logger import get_logger

log = get_logger("sorter")

# Load category mappings at module level
_CATEGORY_MAP: dict[str, list[str]] = {}
_LABEL_TO_CATEGORY: dict[str, str] = {}


def _load_categories():
    """Load the photo_categories.json mapping file."""
    global _CATEGORY_MAP, _LABEL_TO_CATEGORY
    cat_file = RESOURCES_DIR / "photo_categories.json"
    try:
        with open(cat_file, "r", encoding="utf-8") as f:
            _CATEGORY_MAP = json.load(f)
        # Build reverse lookup: label -> category
        for category, labels in _CATEGORY_MAP.items():
            for label in labels:
                _LABEL_TO_CATEGORY[label.lower()] = category
        log.info(f"Loaded {len(_LABEL_TO_CATEGORY)} label→category mappings across {len(_CATEGORY_MAP)} categories")
    except Exception as e:
        log.warning(f"Could not load category mappings: {e}")


# Auto-load on import
_load_categories()


def classify_tags(tags: list[str]) -> tuple[str, list[str]]:
    """
    Given a list of AI-generated ImageNet tags, determine the best
    photography category and return enriched tags.

    Returns:
        (category_name, enriched_tags) where enriched_tags includes
        both the original labels and the category name.
    """
    category_votes: dict[str, int] = {}

    for tag in tags:
        tag_lower = tag.lower().strip()
        cat = _LABEL_TO_CATEGORY.get(tag_lower)
        if cat:
            category_votes[cat] = category_votes.get(cat, 0) + 1

    if category_votes:
        best_category = max(category_votes, key=category_votes.get)
    else:
        best_category = "uncategorized"

    # Enriched tags: category first, then original tags
    enriched = [best_category] + [t for t in tags if t.lower() != best_category]
    return best_category, enriched


def get_category_subfolder(output_dir: str | Path, category: str) -> Path:
    """
    Get or create the category subfolder within the output directory.
    Returns the subfolder path.
    """
    folder = Path(output_dir) / category.capitalize()
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def get_available_categories() -> list[str]:
    """Return list of all available photography categories."""
    return sorted(_CATEGORY_MAP.keys())
