"""
Photagger — Adobe XMP sidecar file generator.
Generates Lightroom-compatible .xmp files with AI tags, ratings, and EXIF data.
"""
import os
from xml.sax.saxutils import escape
from .logger import get_logger

log = get_logger("xmp")


def generate_xmp(image_path: str, tags: list[str], rating: int = 0,
                 label: str = "", exif_description: str = "") -> bool:
    """
    Generate an Adobe Lightroom compatible .xmp sidecar file.

    Args:
        image_path: Path to the image file.
        tags: List of keyword strings to inject.
        rating: Star rating (0-5) to embed.
        label: Color label (e.g., 'Green', 'Red').
        exif_description: Optional description text.

    Returns:
        True if XMP file was written successfully.
    """
    file_name, _ = os.path.splitext(image_path)
    xmp_file = file_name + ".xmp"

    # Safely escape all tag values to prevent XML injection
    bag_items = "\n".join(
        [f"     <rdf:li>{escape(tag.strip())}</rdf:li>" for tag in tags if tag.strip()]
    )

    # Optional elements
    rating_attr = f'\n    xmp:Rating="{max(0, min(5, rating))}"' if rating > 0 else ""
    label_attr = f'\n    xmp:Label="{escape(label)}"' if label else ""

    desc_block = ""
    if exif_description:
        desc_block = f"""
   <dc:description>
    <rdf:Alt>
     <rdf:li xml:lang="x-default">{escape(exif_description)}</rdf:li>
    </rdf:Alt>
   </dc:description>"""

    xmp_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Photagger v1.0.0">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about=""
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:lr="http://ns.adobe.com/lightroom/1.0/"
    xmlns:xmp="http://ns.adobe.com/xap/1.0/"{rating_attr}{label_attr}>
   <dc:subject>
    <rdf:Bag>
{bag_items}
    </rdf:Bag>
   </dc:subject>
   <lr:hierarchicalSubject>
    <rdf:Bag>
{bag_items}
    </rdf:Bag>
   </lr:hierarchicalSubject>{desc_block}
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>"""

    try:
        with open(xmp_file, "w", encoding="utf-8") as f:
            f.write(xmp_content)
        log.info(f"XMP sidecar written: {os.path.basename(xmp_file)}")
        return True
    except Exception as e:
        log.error(f"Failed to write XMP for {image_path}: {e}")
        return False
