"""Tests for block normalization (domain layer).

These tests validate normalization logic using plain dicts and temporary
files. They do not import python-docx.
"""

import pytest

from docsmith.normalize import (
    normalize_heading_block,
    normalize_image_block,
)

# ---------------------------------------------------------------------------
# Test image fixtures (generated via Pillow for format correctness)
# ---------------------------------------------------------------------------


def _make_image_bytes(fmt):
    """Generate minimal valid image bytes using Pillow."""
    import io

    from PIL import Image as PILImage

    img = PILImage.new("RGB", (1, 1), color="red")
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


@pytest.fixture()
def png_file(tmp_path):
    """Create a minimal PNG file in tmp_path."""
    p = tmp_path / "test.png"
    p.write_bytes(_make_image_bytes("PNG"))
    return p


@pytest.fixture()
def jpeg_file(tmp_path):
    """Create a minimal JPEG file in tmp_path."""
    p = tmp_path / "test.jpg"
    p.write_bytes(_make_image_bytes("JPEG"))
    return p


# ---------------------------------------------------------------------------
# Domain tests: normalize_heading_block (moved from test_render.py)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "block, expected",
    [
        pytest.param(
            {"heading": "Title", "level": 2},
            ("Title", 2),
            id="flat-with-level",
        ),
        pytest.param(
            {"heading": "Title"},
            ("Title", 1),
            id="flat-default-level",
        ),
        pytest.param(
            {"heading": {"text": "Title", "level": 3}},
            ("Title", 3),
            id="nested-with-level",
        ),
        pytest.param(
            {"heading": {"text": "Title"}},
            ("Title", 1),
            id="nested-default-level",
        ),
        pytest.param(
            {"heading": "Title", "level": 9},
            ("Title", 4),
            id="level-clamped-high",
        ),
        pytest.param(
            {"heading": "Title", "level": 0},
            ("Title", 1),
            id="level-clamped-low",
        ),
        pytest.param(
            {"heading": {"text": "Title", "level": 99}},
            ("Title", 4),
            id="nested-level-clamped-high",
        ),
        pytest.param(
            {"heading": {"text": "Title", "level": -5}},
            ("Title", 1),
            id="nested-level-clamped-low",
        ),
    ],
)
def test_normalize_heading_block_valid(block, expected):
    """Valid heading blocks produce correct (text, level) tuples."""
    assert normalize_heading_block(block) == expected


@pytest.mark.parametrize(
    "block, match",
    [
        pytest.param(
            {"heading": {"level": 2}},
            "requires a 'text' key",
            id="nested-missing-text",
        ),
        pytest.param(
            {"heading": {"text": "", "level": 2}},
            "non-empty string",
            id="nested-empty-text",
        ),
        pytest.param(
            {"heading": {"text": "   "}},
            "non-empty string",
            id="nested-whitespace-text",
        ),
        pytest.param(
            {"heading": ["a", "b"]},
            "got list",
            id="heading-is-list",
        ),
        pytest.param(
            {"heading": 42},
            "got int",
            id="heading-is-int",
        ),
        pytest.param(
            {"heading": None},
            "got NoneType",
            id="heading-is-none",
        ),
    ],
)
def test_normalize_heading_block_invalid(block, match):
    """Invalid heading blocks raise ValueError with actionable messages."""
    with pytest.raises(ValueError, match=match):
        normalize_heading_block(block)


# ---------------------------------------------------------------------------
# Domain tests: normalize_image_block -- happy path
# ---------------------------------------------------------------------------


def test_normalize_image_all_fields(tmp_path, png_file):
    """Image block with all fields produces correct ImageBlock."""
    block = {
        "image": {
            "path": "test.png",
            "width": 3.5,
            "alignment": "center",
            "caption": "Figure 1",
        }
    }
    result = normalize_image_block(block, tmp_path)
    assert result.path == png_file.resolve()
    assert result.width == 3.5
    assert result.alignment == "center"
    assert result.caption == "Figure 1"


def test_normalize_image_path_only(tmp_path, png_file):
    """Image block with path only uses correct defaults."""
    block = {"image": {"path": "test.png"}}
    result = normalize_image_block(block, tmp_path)
    assert result.path == png_file.resolve()
    assert result.width is None
    assert result.alignment == "left"
    assert result.caption is None


def test_normalize_image_jpeg_jpg(tmp_path, jpeg_file):
    """JPEG file with .jpg extension is accepted."""
    block = {"image": {"path": "test.jpg"}}
    result = normalize_image_block(block, tmp_path)
    assert result.path == jpeg_file.resolve()


def test_normalize_image_jpeg_extension(tmp_path):
    """JPEG file with .jpeg extension is accepted."""
    p = tmp_path / "photo.jpeg"
    p.write_bytes(_make_image_bytes("JPEG"))
    block = {"image": {"path": "photo.jpeg"}}
    result = normalize_image_block(block, tmp_path)
    assert result.path == p.resolve()


def test_normalize_image_uppercase_extension(tmp_path):
    """Uppercase file extension is accepted (case-insensitive)."""
    p = tmp_path / "DIAGRAM.PNG"
    p.write_bytes(_make_image_bytes("PNG"))
    block = {"image": {"path": "DIAGRAM.PNG"}}
    result = normalize_image_block(block, tmp_path)
    assert result.path == p.resolve()


def test_normalize_image_alignment_case_insensitive(tmp_path, png_file):
    """Alignment value is normalized to lowercase."""
    block = {"image": {"path": "test.png", "alignment": "CENTER"}}
    result = normalize_image_block(block, tmp_path)
    assert result.alignment == "center"


def test_normalize_image_integer_width(tmp_path, png_file):
    """Integer width is accepted and stored as float."""
    block = {"image": {"path": "test.png", "width": 4}}
    result = normalize_image_block(block, tmp_path)
    assert result.width == 4.0


def test_normalize_image_absolute_path(tmp_path, png_file):
    """Absolute path is used as-is, ignoring base_path."""
    abs_path = str(png_file.resolve())
    block = {"image": {"path": abs_path}}
    other_base = tmp_path / "other"
    other_base.mkdir()
    result = normalize_image_block(block, other_base)
    assert result.path == png_file.resolve()


# ---------------------------------------------------------------------------
# Domain tests: normalize_image_block -- error cases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "block, match",
    [
        pytest.param(
            {"image": "img.png"},
            "must be a dict",
            id="image-is-string",
        ),
        pytest.param(
            {"image": ["img.png"]},
            "must be a dict",
            id="image-is-list",
        ),
        pytest.param(
            {"image": {"width": 3}},
            "requires a 'path' key",
            id="missing-path",
        ),
    ],
)
def test_normalize_image_block_structure_errors(block, match, tmp_path):
    """Structural errors in image block raise ValueError."""
    with pytest.raises(ValueError, match=match):
        normalize_image_block(block, tmp_path)


def test_normalize_image_file_not_found(tmp_path):
    """Non-existent image file raises ValueError with resolved path."""
    block = {"image": {"path": "missing.png"}}
    with pytest.raises(ValueError, match="not found"):
        normalize_image_block(block, tmp_path)


@pytest.mark.parametrize(
    "filename, match",
    [
        pytest.param("diagram.svg", "Unsupported image format", id="svg"),
        pytest.param("notes.txt", "Unsupported image format", id="txt"),
        pytest.param("data.bmp", "Unsupported image format", id="bmp"),
    ],
)
def test_normalize_image_unsupported_format(filename, match, tmp_path):
    """Unsupported file extension raises ValueError."""
    p = tmp_path / filename
    p.write_bytes(b"fake content")
    block = {"image": {"path": filename}}
    with pytest.raises(ValueError, match=match):
        normalize_image_block(block, tmp_path)


@pytest.mark.parametrize(
    "width, match",
    [
        pytest.param(0, "positive number", id="zero"),
        pytest.param(-2, "positive number", id="negative"),
        pytest.param("big", "positive number", id="string"),
    ],
)
def test_normalize_image_invalid_width(width, match, tmp_path, png_file):
    """Invalid width values raise ValueError."""
    block = {"image": {"path": "test.png", "width": width}}
    with pytest.raises(ValueError, match=match):
        normalize_image_block(block, tmp_path)


def test_normalize_image_invalid_alignment(tmp_path, png_file):
    """Invalid alignment raises ValueError listing valid options."""
    block = {"image": {"path": "test.png", "alignment": "top"}}
    with pytest.raises(ValueError, match="must be one of"):
        normalize_image_block(block, tmp_path)
