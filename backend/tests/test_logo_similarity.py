from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from app.detection.engine import _score
from app.detection.signals import Signal, logo_signal
from app import logos


def _write_shape(path: Path, kind: str) -> None:
    image = Image.new("RGB", (128, 128), "#f8fafc")
    draw = ImageDraw.Draw(image)
    if kind == "official":
        draw.rounded_rectangle((22, 18, 106, 110), radius=20, fill="#2f6fed")
        draw.ellipse((42, 36, 86, 80), fill="#ffffff")
    elif kind == "near":
        draw.rounded_rectangle((23, 19, 107, 111), radius=20, fill="#2f6fed")
        draw.ellipse((43, 37, 87, 81), fill="#ffffff")
    else:
        for x in range(128):
            shade = round((127 - x) * 255 / 127)
            draw.line((x, 0, x, 127), fill=(shade, shade, shade))
    image.save(path, format="PNG")


def test_logo_signal_is_near_100_for_identical_local_files() -> None:
    directory = logos.ensure_logo_directory()
    _write_shape(directory / "test-logo-identical-official.png", "official")
    _write_shape(directory / "test-logo-identical-copy.png", "official")

    result = logo_signal("/static/logos/test-logo-identical-official.png", "/static/logos/test-logo-identical-copy.png")

    assert result.available is True
    assert result.score == 100.0
    assert result.details["hamming_distance"] == 0


def test_logo_signal_distinguishes_visibly_different_local_files() -> None:
    directory = logos.ensure_logo_directory()
    _write_shape(directory / "test-logo-difference-official.png", "official")
    _write_shape(directory / "test-logo-difference-candidate.png", "different")

    result = logo_signal("/static/logos/test-logo-difference-official.png", "/static/logos/test-logo-difference-candidate.png")

    assert result.available is True
    assert result.score is not None and result.score < 10


def test_logo_signal_is_unavailable_for_a_missing_file() -> None:
    directory = logos.ensure_logo_directory()
    _write_shape(directory / "test-logo-missing-official.png", "official")

    result = logo_signal("/static/logos/test-logo-missing-official.png", "/static/logos/test-logo-guaranteed-missing.png")

    assert result.available is False
    assert result.score is None
    assert "missing" in result.details["reason"].lower()


def test_high_logo_match_is_a_corroborating_signal_and_lifts_the_49_cap() -> None:
    directory = logos.ensure_logo_directory()
    _write_shape(directory / "test-logo-near-official.png", "official")
    _write_shape(directory / "test-logo-near-copy.png", "near")
    near_copy = logo_signal("/static/logos/test-logo-near-official.png", "/static/logos/test-logo-near-copy.png")
    assert near_copy.score is not None and near_copy.score >= 90
    signals = [
        Signal("OFFICIAL_ASSET_MATCH", False, None, 1, {}),
        Signal("NAME_SIMILARITY", True, 100.0, 2, {}),
        Signal("LOOKALIKE_NAME", True, 100.0, 3, {}),
        Signal("DESCRIPTION_SIMILARITY", True, 10.0, 4, {}),
        near_copy,
    ]

    score, _confidence = _score(signals, official_match=False)

    assert score > 49.0
    assert score >= 74.0


def test_dissimilar_logo_does_not_lower_the_no_logo_score() -> None:
    base = [
        Signal("OFFICIAL_ASSET_MATCH", True, None, 1, {}),
        Signal("NAME_SIMILARITY", True, 80.0, 2, {}),
        Signal("LOOKALIKE_NAME", True, 0.0, 3, {}),
        Signal("DESCRIPTION_SIMILARITY", True, 20.0, 4, {}),
    ]
    no_logo_score, _ = _score(base + [Signal("LOGO_SIMILARITY", False, None, 5, {})], official_match=False)
    low_logo = Signal("LOGO_SIMILARITY", True, 5.0, 5, {"hamming_distance": 31})
    different_logo_score, _ = _score(base + [low_logo], official_match=False)

    assert different_logo_score == no_logo_score
    assert low_logo.details["counted"] is False
    assert low_logo.details["reason"] == "below 70, not counted as evidence"
