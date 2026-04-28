"""
Photagger — EXIF metadata extraction from image files.
Uses Pillow's EXIF parser for camera info, exposure settings, and GPS data.
"""
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from .logger import get_logger

log = get_logger("exif")


def _convert_to_degrees(value):
    """Convert GPS coordinates from EXIF rational format to decimal degrees."""
    try:
        d, m, s = value
        return float(d) + float(m) / 60.0 + float(s) / 3600.0
    except (ValueError, TypeError, ZeroDivisionError):
        return None


def extract_exif(image_path: str | Path) -> dict:
    """
    Extract EXIF metadata from an image file.
    Returns a dict with human-readable camera/exposure/GPS info.
    """
    result = {
        "camera": None,
        "lens": None,
        "focal_length": None,
        "iso": None,
        "aperture": None,
        "shutter_speed": None,
        "date_taken": None,
        "gps_lat": None,
        "gps_lon": None,
        "width": None,
        "height": None,
    }

    try:
        img = Image.open(str(image_path))
        result["width"] = img.width
        result["height"] = img.height

        exif_data = img._getexif()
        if not exif_data:
            return result

        decoded = {}
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, tag_id)
            decoded[tag_name] = value

        # Camera model
        result["camera"] = decoded.get("Model", decoded.get("Make"))

        # Lens
        result["lens"] = decoded.get("LensModel")

        # Focal length
        fl = decoded.get("FocalLength")
        if fl:
            result["focal_length"] = f"{float(fl):.0f}mm"

        # ISO
        result["iso"] = decoded.get("ISOSpeedRatings")

        # Aperture (FNumber)
        fn = decoded.get("FNumber")
        if fn:
            result["aperture"] = f"f/{float(fn):.1f}"

        # Shutter speed
        et = decoded.get("ExposureTime")
        if et:
            et_val = float(et)
            if et_val >= 1:
                result["shutter_speed"] = f"{et_val:.1f}s"
            else:
                result["shutter_speed"] = f"1/{int(1 / et_val)}s"

        # Date taken
        result["date_taken"] = decoded.get("DateTimeOriginal",
                                            decoded.get("DateTime"))

        # GPS
        gps_info = decoded.get("GPSInfo")
        if gps_info:
            gps_decoded = {}
            for key, val in gps_info.items():
                gps_tag = GPSTAGS.get(key, key)
                gps_decoded[gps_tag] = val

            lat = gps_decoded.get("GPSLatitude")
            lat_ref = gps_decoded.get("GPSLatitudeRef")
            lon = gps_decoded.get("GPSLongitude")
            lon_ref = gps_decoded.get("GPSLongitudeRef")

            if lat and lon:
                lat_deg = _convert_to_degrees(lat)
                lon_deg = _convert_to_degrees(lon)
                if lat_deg and lon_deg:
                    if lat_ref == "S":
                        lat_deg = -lat_deg
                    if lon_ref == "W":
                        lon_deg = -lon_deg
                    result["gps_lat"] = round(lat_deg, 6)
                    result["gps_lon"] = round(lon_deg, 6)

    except Exception as e:
        log.debug(f"EXIF extraction failed for {image_path}: {e}")

    return result


def format_exif_summary(exif: dict) -> str:
    """Format EXIF data into a human-readable one-liner."""
    parts = []
    if exif.get("camera"):
        parts.append(exif["camera"])
    if exif.get("focal_length"):
        parts.append(exif["focal_length"])
    if exif.get("aperture"):
        parts.append(exif["aperture"])
    if exif.get("shutter_speed"):
        parts.append(exif["shutter_speed"])
    if exif.get("iso"):
        parts.append(f"ISO {exif['iso']}")
    return " · ".join(parts) if parts else "No EXIF data"
