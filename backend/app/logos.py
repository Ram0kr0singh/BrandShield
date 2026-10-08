"""Local logo storage, safe resolution, and deterministic 64-bit dHash helpers."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
LOGO_DIRECTORY = REPOSITORY_ROOT / "data" / "logos"
UPLOAD_LOGO_DIRECTORY = LOGO_DIRECTORY / "uploads"
STATIC_LOGO_PREFIX = "/static/logos/"


def ensure_logo_directory() -> Path:
    LOGO_DIRECTORY.mkdir(parents=True, exist_ok=True)
    return LOGO_DIRECTORY


def ensure_upload_logo_directory() -> Path:
    directory = ensure_logo_directory() / "uploads"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def logo_url(filename: str) -> str:
    return f"{STATIC_LOGO_PREFIX}{filename}"


def local_logo_path(reference: str | None) -> Path | None:
    """Resolve only our static-logo URLs; never permit filesystem traversal or HTTP."""
    if not reference or not reference.startswith(STATIC_LOGO_PREFIX):
        return None
    filename = reference.removeprefix(STATIC_LOGO_PREFIX)
    relative_path = Path(filename)
    if not filename or relative_path.is_absolute() or any(part in {".", ".."} for part in relative_path.parts):
        return None
    path = ensure_logo_directory() / relative_path
    try:
        path.resolve().relative_to(LOGO_DIRECTORY.resolve())
    except ValueError:
        return None
    return path


def dhash(path: Path) -> int:
    """Return a 64-bit difference hash for a local image using Pillow only."""
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source).convert("L")
        pixels = image.resize((9, 8), Image.Resampling.LANCZOS)
        value = 0
        for y in range(8):
            for x in range(8):
                value = (value << 1) | int(pixels.getpixel((x, y)) > pixels.getpixel((x + 1, y)))
        return value


def compare_logo_references(official_reference: str | None, candidate_reference: str | None) -> tuple[float | None, dict]:
    """Compare two local logo references and explain why comparison was unavailable."""
    official_path = local_logo_path(official_reference)
    candidate_path = local_logo_path(candidate_reference)
    if official_path is None:
        return None, {"reason": "No supported local official logo is registered. Only /static/logos/ files are compared."}
    if candidate_path is None:
        return None, {"reason": "No supported local candidate logo is available. Only /static/logos/ files are compared."}
    if not official_path.is_file():
        return None, {"reason": "The registered official local logo file is missing.", "official_logo": official_reference}
    if not candidate_path.is_file():
        return None, {"reason": "The registered candidate local logo file is missing.", "candidate_logo": candidate_reference}
    try:
        distance = (dhash(official_path) ^ dhash(candidate_path)).bit_count()
    except (OSError, UnidentifiedImageError, ValueError) as error:
        return None, {"reason": "A local logo file could not be decoded safely.", "exception_type": type(error).__name__}
    score = round(max(0, 1 - distance / 32) * 100, 2)
    return score, {
        "official_logo": official_reference,
        "candidate_logo": candidate_reference,
        "hash_algorithm": "dHash-64",
        "hamming_distance": distance,
        "visually_matches": score >= 90,
    }
