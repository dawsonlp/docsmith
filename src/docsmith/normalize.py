"""Block normalization for docsmith YAML schema.

Validates and normalizes raw YAML blocks into canonical representations
that the rendering layer can consume without guessing. This module has
no dependency on python-docx -- it imports only from the standard library.
"""

from dataclasses import dataclass
from pathlib import Path

SUPPORTED_IMAGE_EXTENSIONS: set[str] = {".png", ".jpg", ".jpeg"}
VALID_ALIGNMENTS: set[str] = {"left", "center", "right"}


def normalize_heading_block(block: dict) -> tuple[str, int]:
    """Extract and validate heading text and level from a raw YAML block.

    Accepts both flat form (heading: "text") and nested dict form
    (heading: {text: "text", level: 2}). Returns (text, level) with
    level clamped to 1-4.

    Raises ValueError for invalid input with user-facing messages.
    """
    value = block["heading"]

    if isinstance(value, str):
        text = value
        level = block.get("level", 1)
    elif isinstance(value, dict):
        if "text" not in value:
            raise ValueError(
                "Heading block nested form requires a 'text' key, "
                'e.g.: heading: {text: "Section Title", level: 2}'
            )
        text = value["text"]
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Heading block 'text' must be a non-empty string")
        level = value.get("level", 1)
    else:
        raise ValueError(
            f"Heading block value must be a string or a dict with a 'text' key, "
            f"got {type(value).__name__}"
        )

    level = max(1, min(int(level), 4))
    return text, level


@dataclass(frozen=True)
class ImageBlock:
    """Canonical representation of a normalized image block."""

    path: Path
    width: float | None
    alignment: str
    caption: str | None


def normalize_image_block(block: dict, base_path: Path) -> ImageBlock:
    """Validate and normalize a raw image block from YAML.

    Resolves the image path against base_path, validates file existence
    and format, extracts optional fields with defaults.

    Raises ValueError for invalid input with user-facing messages.
    """
    value = block["image"]

    if not isinstance(value, dict):
        raise ValueError(
            "Image block must be a dict with at least a 'path' key, "
            'e.g.: image: {path: "diagram.png"}'
        )

    if "path" not in value:
        raise ValueError("Image block requires a 'path' key specifying the image file")

    raw_path = Path(value["path"])
    if raw_path.is_absolute():
        resolved_path = raw_path.resolve()
    else:
        resolved_path = (base_path / raw_path).resolve()

    if not resolved_path.exists():
        raise ValueError(f"Image file not found: {resolved_path}")

    ext = resolved_path.suffix.lower()
    if ext not in SUPPORTED_IMAGE_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_IMAGE_EXTENSIONS))
        raise ValueError(
            f"Unsupported image format '{ext}'. Supported formats: {supported}"
        )

    # Width validation
    width = value.get("width")
    if width is not None:
        if not isinstance(width, int | float) or width <= 0:
            raise ValueError(
                f"Image block 'width' must be a positive number (inches), got: {width!r}"
            )
        width = float(width)

    # Alignment validation
    alignment = value.get("alignment", "left")
    if not isinstance(alignment, str):
        raise ValueError(
            f"Image block 'alignment' must be one of: left, center, right. "
            f"Got: {alignment!r}"
        )
    alignment = alignment.lower()
    if alignment not in VALID_ALIGNMENTS:
        raise ValueError(
            f"Image block 'alignment' must be one of: left, center, right. "
            f"Got: '{alignment}'"
        )

    # Caption extraction
    caption = value.get("caption")
    if caption is not None:
        caption = str(caption)

    return ImageBlock(
        path=resolved_path,
        width=width,
        alignment=alignment,
        caption=caption,
    )
