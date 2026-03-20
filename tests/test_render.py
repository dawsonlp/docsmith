"""Tests for docsmith rendering and block normalization."""

import pytest
from docx import Document

from docsmith.cli import normalize_heading_block, render

# ---------------------------------------------------------------------------
# Domain tests: normalize_heading_block
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
# Integration tests: render path for headings
# ---------------------------------------------------------------------------


def test_render_flat_heading(tmp_path):
    """Flat form heading renders correct text in generated document."""
    doc_data = {
        "content": [
            {"heading": "Flat Section", "level": 2},
        ],
    }
    output_path = tmp_path / "output.docx"
    render(doc_data, output_path)

    doc = Document(output_path)
    heading_paragraphs = [
        p for p in doc.paragraphs if p.style.name.startswith("Heading")
    ]
    assert len(heading_paragraphs) == 1
    assert heading_paragraphs[0].text == "Flat Section"


def test_render_nested_heading(tmp_path):
    """Nested dict form heading renders correct text in generated document."""
    doc_data = {
        "content": [
            {"heading": {"text": "Nested Section", "level": 3}},
        ],
    }
    output_path = tmp_path / "output.docx"
    render(doc_data, output_path)

    doc = Document(output_path)
    heading_paragraphs = [
        p for p in doc.paragraphs if p.style.name.startswith("Heading")
    ]
    assert len(heading_paragraphs) == 1
    assert heading_paragraphs[0].text == "Nested Section"


def test_render_invalid_heading_does_not_produce_file(tmp_path):
    """Invalid heading raises ValueError before producing output file."""
    doc_data = {
        "content": [
            {"heading": {"level": 2}},
        ],
    }
    output_path = tmp_path / "output.docx"
    with pytest.raises(ValueError, match="requires a 'text' key"):
        render(doc_data, output_path)
    assert not output_path.exists()


# ---------------------------------------------------------------------------
# Existing smoke test (must remain unchanged)
# ---------------------------------------------------------------------------


def test_render_minimal(tmp_path):
    """Rendering a minimal document produces a .docx file."""
    doc_data = {
        "title": "Test Document",
        "content": [
            {"text": "Hello, world."},
        ],
    }
    output_path = tmp_path / "output.docx"
    render(doc_data, output_path)
    assert output_path.exists()
    assert output_path.stat().st_size > 0
