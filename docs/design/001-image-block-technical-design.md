# TDS-001: Image Block Support -- Technical Design

**Requirement:** [REQ-001](../requirements/001-image-block-support.md)
**Design:** [DES-001](001-image-block-support.md)
**Issue:** [#1](https://github.com/dawsonlp/docsmith/issues/1)
**Status:** Draft
**Author:** Senior Engineer

---

## Context

The architect's design document (DES-001) establishes that image block support requires extracting block normalization into a dedicated module, adding path resolution and format validation in the normalization layer, and threading a base path from the CLI layer. This technical design describes how to realize those boundaries in the current codebase.

DES-001 builds on the normalization pattern established by DES-002 (heading block normalization). The heading normalizer already exists as a standalone function in `cli.py` with no python-docx dependency. This change extracts it into a normalization module alongside the new image normalizer.

---

## Technology Choices

| Concern | Choice | Rationale |
|---------|--------|-----------|
| Normalization module | `src/docsmith/normalize.py` | Single module, not a package. The codebase is small; one file for all normalizers keeps things simple. Matches the existing pattern of `cli.py` as a single module. |
| Canonical return type (image) | `dataclass` | Image normalization returns four fields (path, width, alignment, caption). A tuple is unwieldy at four elements. A frozen dataclass provides named fields, type clarity, and immutability. |
| Canonical return type (heading) | `tuple[str, int]` unchanged | Two fields; no reason to change the existing working interface. |
| Width unit in normalized output | `float` or `None` (inches) | Per DES-001 D4, normalization passes through the user's value in inches. The renderer converts to python-docx `Inches()`. |
| Default width | `None` in normalization; renderer applies `Inches(5.0)` | 5 inches is approximately 80% of a portrait page width (6.5 usable inches with default margins), suitable for most diagrams. The renderer owns this default because it is a presentation concern. |
| Alignment representation | Lowercase string: `"left"`, `"center"`, `"right"` | Normalization normalizes case and validates. The renderer maps to `WD_ALIGN_PARAGRAPH` enum values. |
| Error type | `ValueError` | Consistent with heading normalization. No custom exception hierarchy justified yet. |
| Path resolution | `pathlib.Path` | Already used throughout the codebase. `(base_path / relative_path).resolve()` handles both relative and absolute paths correctly. |
| Format validation | File extension check via `Path.suffix` | Per DES-001 D3. Case-insensitive comparison against `{".png", ".jpg", ".jpeg"}`. |

---

## Module Design

### `src/docsmith/normalize.py`

This new module contains all block normalization functions. It imports only from the standard library (`pathlib`, `dataclasses`). It does not import python-docx.

#### `normalize_heading_block` (moved from `cli.py`)

Exact function signature and behavior unchanged. Moved as-is, no modifications.

```python
def normalize_heading_block(block: dict) -> tuple[str, int]:
```

#### `ImageBlock` dataclass

```python
@dataclass(frozen=True)
class ImageBlock:
    path: Path
    width: float | None
    alignment: str
    caption: str | None
```

Frozen to enforce immutability. Fields match the canonical representation defined in DES-001 D4.

#### `normalize_image_block`

```python
SUPPORTED_IMAGE_EXTENSIONS: set[str] = {".png", ".jpg", ".jpeg"}
VALID_ALIGNMENTS: set[str] = {"left", "center", "right"}

def normalize_image_block(block: dict, base_path: Path) -> ImageBlock:
```

This function accepts a raw block dict from the YAML `content` list and a base path for resolving relative image paths. Returns an `ImageBlock`.

**Input validation and extraction:**

1. Extract the `image` value from the block dict.
2. Verify it is a dict. If not, raise `ValueError`.
3. Extract `path` (required). If missing, raise `ValueError`.
4. Resolve the path: `(base_path / raw_path).resolve()`. If the raw path is already absolute, `base_path` is effectively ignored by `pathlib`.
5. Check file existence: `resolved_path.exists()`. If not, raise `ValueError` including the resolved path.
6. Check file extension: `resolved_path.suffix.lower()` against `SUPPORTED_IMAGE_EXTENSIONS`. If not supported, raise `ValueError` listing the valid formats.
7. Extract `width` (optional). If present, validate it is a positive number (`int` or `float`, greater than zero). If not, raise `ValueError`. If absent, set to `None`.
8. Extract `alignment` (optional). If present, lowercase it and validate against `VALID_ALIGNMENTS`. If invalid, raise `ValueError` listing valid options. If absent, default to `"left"`.
9. Extract `caption` (optional). If present, pass through as a string. If absent, set to `None`.
10. Return `ImageBlock(path=resolved_path, width=width, alignment=alignment, caption=caption)`.

**Error message format:**

Consistent with heading normalization -- state what is wrong, then state what is expected:

- Not a dict: `"Image block must be a dict with at least a 'path' key, e.g.: image: {path: \"diagram.png\"}"`
- Missing path: `"Image block requires a 'path' key specifying the image file"`
- File not found: `"Image file not found: /resolved/path/to/diagram.png"`
- Unsupported format: `"Unsupported image format '.svg'. Supported formats: .png, .jpg, .jpeg"`
- Invalid width: `"Image block 'width' must be a positive number (inches), got: <value>"`
- Invalid alignment: `"Image block 'alignment' must be one of: left, center, right. Got: '<value>'"`

---

## Integration into `cli.py`

### Import changes

Remove `normalize_heading_block` definition from `cli.py`. Add import:

```python
from docsmith.normalize import normalize_heading_block, normalize_image_block, ImageBlock
```

### `render()` signature change

Add `base_path` parameter:

```python
def render(doc_data, output_path, base_path=None):
```

When `base_path` is `None`, image blocks cannot be normalized (no resolution context). This preserves backward compatibility for callers that do not use image blocks. If an image block is encountered and `base_path` is `None`, raise `ValueError` with a message explaining that image blocks require a base path (this should not happen in normal operation, but defends against programming errors).

### Image block handler in render loop

Add a new `elif` branch after the existing block handlers:

```python
elif "image" in block:
    img = normalize_image_block(block, base_path)
    width = Inches(img.width) if img.width is not None else Inches(5.0)
    pic_paragraph = doc.add_picture(str(img.path), width=width)
    # add_picture returns an InlineShape; get its parent paragraph for alignment
    last_paragraph = doc.paragraphs[-1]
    last_paragraph.alignment = _alignment_map[img.alignment]
    if img.caption:
        caption_para = doc.add_paragraph()
        caption_para.alignment = last_paragraph.alignment
        run = caption_para.add_run(img.caption)
        run.italic = True
        run.font.size = Pt(9)
```

### Alignment mapping

Add a module-level mapping in `cli.py`:

```python
_alignment_map = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
}
```

This keeps the string-to-enum translation in the rendering layer, as specified by DES-001 D6.

### `main()` changes

Thread the base path to `render()`:

- File input: `base_path = input_path.parent`
- Stdin input: `base_path = Path.cwd()`

The `base_path` is already computed in `main()` implicitly (it determines `default_output_dir`). Make it explicit and pass it to `render()`.

---

## Caption Styling

REQ-001 R5 delegates styling to the implementation team. The caption:

- Appears as a separate paragraph immediately below the image
- Uses italic text at 9pt font size
- Inherits the same alignment as the image
- Uses the default paragraph style (no heading or special style)

This is visually distinct from body text (which uses default font size, typically 11pt or 12pt, non-italic) while remaining understated. It follows the convention used in technical documents and academic papers.

---

## Error Propagation

Same pattern as TDS-002: `ValueError` propagates up through `render()` to `main()`, producing a traceback with a user-facing error message. No top-level exception handler is added in this change.

---

## Backward Compatibility

### Import compatibility

`normalize_heading_block` moves from `cli.py` to `normalize.py`. The existing tests import it from `cli.py`:

```python
from docsmith.cli import normalize_heading_block, render
```

After the move, `cli.py` imports `normalize_heading_block` from `normalize.py` and uses it internally. The tests should update their import to:

```python
from docsmith.normalize import normalize_heading_block
from docsmith.cli import render
```

Alternatively, `cli.py` could re-export `normalize_heading_block` for backward compatibility. Given that only the project's own test suite imports it, updating the test import is simpler and cleaner.

### `render()` signature

The new `base_path` parameter defaults to `None`, so existing callers that do not pass it continue to work. Image blocks will fail if encountered without a base path, but existing YAML documents have no image blocks.

---

## Testing Strategy

### Unit Tests: `normalize_image_block` (in `tests/test_normalize.py`)

New test file for normalization. Tests use `tmp_path` fixture to create temporary image files.

**Helper:** Tests need real files on disk (for existence checks). Create minimal valid PNG and JPEG files in fixtures. A 1x1 pixel PNG is 68 bytes and can be created inline as a bytes literal.

**Happy-path tests (parametrized):**

| Test | Input | Expected |
|------|-------|----------|
| All fields specified | `{"image": {"path": "img.png", "width": 3.5, "alignment": "center", "caption": "Fig 1"}}` | `ImageBlock(path=resolved, width=3.5, alignment="center", caption="Fig 1")` |
| Path only (defaults) | `{"image": {"path": "img.png"}}` | `ImageBlock(path=resolved, width=None, alignment="left", caption=None)` |
| JPEG extension (.jpg) | `{"image": {"path": "photo.jpg"}}` | `ImageBlock(path=resolved, ...)` |
| JPEG extension (.jpeg) | `{"image": {"path": "photo.jpeg"}}` | `ImageBlock(path=resolved, ...)` |
| Uppercase extension | `{"image": {"path": "DIAGRAM.PNG"}}` | `ImageBlock(path=resolved, ...)` |
| Alignment case-insensitive | `{"image": {"path": "img.png", "alignment": "CENTER"}}` | `alignment="center"` |
| Integer width | `{"image": {"path": "img.png", "width": 4}}` | `width=4` (int is acceptable) |
| Absolute path ignores base_path | `{"image": {"path": "/abs/path/img.png"}}` with base `/other` | `path=Path("/abs/path/img.png")` |

**Error tests (parametrized):**

| Test | Input | Expected error match |
|------|-------|---------------------|
| Image value is a string | `{"image": "img.png"}` | `"must be a dict"` |
| Image value is a list | `{"image": ["img.png"]}` | `"must be a dict"` |
| Missing path key | `{"image": {"width": 3}}` | `"requires a 'path' key"` |
| File does not exist | `{"image": {"path": "missing.png"}}` | `"not found"` |
| Unsupported extension (.svg) | `{"image": {"path": "diagram.svg"}}` | `"Unsupported image format"` |
| Unsupported extension (.txt) | `{"image": {"path": "notes.txt"}}` | `"Unsupported image format"` |
| Width is zero | `{"image": {"path": "img.png", "width": 0}}` | `"positive number"` |
| Width is negative | `{"image": {"path": "img.png", "width": -2}}` | `"positive number"` |
| Width is a string | `{"image": {"path": "img.png", "width": "big"}}` | `"positive number"` |
| Invalid alignment | `{"image": {"path": "img.png", "alignment": "top"}}` | `"must be one of"` |

For file-existence tests, create real files in `tmp_path`. For missing-file tests, reference a path that does not exist.

### Unit Tests: `normalize_heading_block` (moved to `tests/test_normalize.py`)

Move the existing heading normalization tests from `test_render.py` to `test_normalize.py`. Update the import to `from docsmith.normalize import normalize_heading_block`. The test logic does not change.

### Integration Tests: Image rendering (in `tests/test_render.py`)

These call `render()` with a base path and inspect the resulting .docx.

**Fixtures:** Create a minimal 1x1 pixel PNG and JPEG in `tmp_path` for each test that needs them.

| Test | Setup | Assertion |
|------|-------|-----------|
| PNG image renders | Create PNG file, render with image block | `.docx` contains an image (check via `doc.inline_shapes`) |
| JPEG image renders | Create JPEG file, render with image block | `.docx` contains an image |
| Image with caption | Render with caption | Document has a paragraph after the image with the caption text, italic |
| Image with center alignment | Render with `alignment: center` | Image paragraph alignment is center |
| Image with width | Render with `width: 3.0` | Image inline shape width is approximately `Inches(3.0)` |
| Default width applied | Render without width | Image inline shape width is approximately `Inches(5.0)` |
| Default alignment is left | Render without alignment | Image paragraph alignment is left (or None, which Word treats as left) |
| Missing image file errors before file creation | Render with non-existent path | `ValueError` raised, output `.docx` does not exist |

**Inspecting images in python-docx:** Use `doc.inline_shapes` to verify images are present. Each `InlineShape` has a `width` property (in EMU). Compare against expected value with a small tolerance.

**Inspecting captions:** After an image, the next paragraph in `doc.paragraphs` should contain the caption text. Check `paragraph.runs[0].italic` is `True` and `paragraph.runs[0].font.size` is `Pt(9)`.

### Existing Tests

- `test_render_minimal` must pass unchanged (uses text block only, no images, no base_path needed)
- All heading normalization tests must pass (moved to new file, import updated)
- All heading integration tests must pass (remain in `test_render.py`)

---

## File Layout After This Change

```
src/docsmith/
    __init__.py          # unchanged
    __main__.py          # unchanged
    cli.py               # render() gains base_path param; image handler added;
                         #   normalize_heading_block removed (imported from normalize)
    normalize.py         # NEW: normalize_heading_block (moved), normalize_image_block,
                         #   ImageBlock dataclass, constants
tests/
    __init__.py          # unchanged
    test_render.py       # heading integration tests remain; image integration tests added;
                         #   heading normalization unit tests removed (moved to test_normalize)
    test_normalize.py    # NEW: heading normalization unit tests (moved), image normalization
                         #   unit tests
```

---

## Minimal Image File Fixtures

Tests need real image files. These are the smallest valid files for each format:

**1x1 pixel PNG (68 bytes):**

```python
MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n"  # PNG signature
    b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde"
    b"\x00\x00\x00\x0cIDATx"
    b"\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)
```

**1x1 pixel JPEG:** Use a minimal JFIF. Alternatively, generate with `PIL` in a conftest fixture if `Pillow` is available (it is, as a dependency of `python-docx`). The engineer should choose whichever approach is simpler to maintain.

A shared `conftest.py` fixture that creates PNG and JPEG files in `tmp_path` avoids duplicating this setup across test functions:

```python
@pytest.fixture
def png_file(tmp_path):
    p = tmp_path / "test.png"
    p.write_bytes(MINIMAL_PNG)
    return p
```

---

## What This Change Does Not Do

- Does not normalize other block types (text, bullets, numbered, table, decision)
- Does not add a top-level exception handler in `main()`
- Does not support SVG images
- Does not support URL-based image sources
- Does not support inline images within text paragraphs
- Does not add image alt-text or accessibility metadata
- Does not add a string shorthand form for image blocks (deferred per DES-001)
- Does not change heading styling, formatting, or normalization behavior