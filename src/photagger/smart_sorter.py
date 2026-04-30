"""
Photagger — Smart auto-categorization into subfolders.
Maps AI tags to photography categories and routes files accordingly.
"""
from pathlib import Path
from .logger import get_logger

log = get_logger("sorter")


def classify_tags(tags: list[str]) -> tuple[str, list[str]]:
    """
    Given a list of CLIP-generated categories, determine the best
    photography category and return enriched tags.

    Returns:
        (category_name, enriched_tags)
    """
    if not tags:
        return "uncategorized", []
        
    best_category = tags[0]
    
    # Enriched tags are simply the unique CLIP tags
    enriched = tags.copy()
    
    return best_category, enriched


def get_category_subfolder(output_dir: str | Path, category: str) -> Path:
    """
    Get or create the category subfolder within the output directory.
    Returns the subfolder path.
    """
    folder = Path(output_dir) / category.capitalize()
    folder.mkdir(parents=True, exist_ok=True)
    return folder
