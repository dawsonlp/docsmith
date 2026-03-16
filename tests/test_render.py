"""Smoke test for docsmith rendering."""

from docsmith.cli import render


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
