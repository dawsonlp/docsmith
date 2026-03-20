# Implementation Checklist: Issue #1 -- Image Block Support

**Requirement:** [REQ-001](../requirements/001-image-block-support.md)
**Design:** [DES-001](001-image-block-support.md)
**Technical Design:** [TDS-001](001-image-block-technical-design.md)
**Issue:** [#1](https://github.com/dawsonlp/docsmith/issues/1)
**Branch:** `feat/image-block-support`

---

## Senior Engineer Review Notes

TDS-001 reviewed for boundary compliance and completeness. Three items noted during review; all addressed inline below rather than requiring a TDS revision:

1. **`Inches` import missing from current `cli.py`.** The TDS code snippets use `Inches()` but the current import is `from docx.shared import Pt, RGBColor`. The checklist includes adding `Inches` to the import.

2. **`add_picture` accepts `str`, not `Path`.** python-docx's `add_picture` does an `isinstance(image_file, str)` check internally. Passing a `Path` object would be treated as a file-like object and fail. The TDS correctly uses `str(img.path)` in the code snippet. The engineer must use `str()` conversion.

3. **Default width trade-off.** The TDS specifies `Inches(5.0)` as default width. This will upscale small images (e.g., a 200px icon). An alternative is `None` (native size), but that risks oversized images blowing out the page. `Inches(5.0)` is the safer default for the diagram use case described in the requirements. If this proves problematic for small images, a future enhancement could use `min(native_width, Inches(5.0))`, but that requires reading image dimensions -- out of scope for this change.

**Verdict: TDS-001 is approved. Proceed with implementation.**

---

## Pre-flight

- [x] Read REQ-001, DES-001, and TDS-001 in full
- [x] Confirm existing tests pass: `pytest tests/ -v`
- [ ] Create branch from main: `git checkout -b feat/image-block-support`

## Domain: Normalization Module

- [x] Create `src/docsmith/normalize.py`
- [x] Move `normalize_heading_block` from `cli.py` to `normalize.py` (exact function, no changes)
- [x] Add `ImageBlock` frozen dataclass with fields: `path: Path`, `width: float | None`, `alignment: str`, `caption: str | None`
- [x] Add `SUPPORTED_IMAGE_EXTENSIONS` constant: `{".png", ".jpg", ".jpeg"}`
- [x] Add `VALID_ALIGNMENTS` constant: `{"left", "center", "right"}`
- [x] Implement `normalize_image_block(block: dict, base_path: Path) -> ImageBlock`:
  - [x] Validate `image` value is a dict
  - [x] Extract and validate `path` (required, must be present)
  - [x] Resolve path: `(base_path / raw_path).resolve()`
  - [x] Validate resolved path exists on disk
  - [x] Validate file extension against `SUPPORTED_IMAGE_EXTENSIONS` (case-insensitive)
  - [x] Extract and validate `width` (optional, must be positive number if present)
  - [x] Extract and validate `alignment` (optional, case-insensitive, default `"left"`)
  - [x] Extract `caption` (optional, default `None`)
  - [x] Return `ImageBlock` instance
- [x] Verify module imports only from standard library (`pathlib`, `dataclasses`)
- [x] Verify module does not import python-docx

## Domain Tests: Normalization (`tests/test_normalize.py`)

- [x] Create `tests/test_normalize.py`
- [x] Move heading normalization unit tests from `test_render.py` to `test_normalize.py`
  - [x] Update import: `from docsmith.normalize import normalize_heading_block`
  - [x] Verify moved tests still pass
- [x] Add parametrized happy-path test for `normalize_image_block` covering:
  - [x] All fields specified (path, width, alignment, caption)
  - [x] Path only (defaults: width=None, alignment="left", caption=None)
  - [x] JPEG extension (.jpg)
  - [x] JPEG extension (.jpeg)
  - [x] Uppercase extension (.PNG)
  - [x] Alignment case-insensitive ("CENTER" -> "center")
  - [x] Integer width accepted
  - [x] Absolute path ignores base_path
- [x] Add parametrized error test for `normalize_image_block` covering:
  - [x] Image value is a string -> `ValueError` matching "must be a dict"
  - [x] Image value is a list -> `ValueError` matching "must be a dict"
  - [x] Missing path key -> `ValueError` matching "requires a 'path' key"
  - [x] File does not exist -> `ValueError` matching "not found"
  - [x] Unsupported extension (.svg) -> `ValueError` matching "Unsupported image format"
  - [x] Unsupported extension (.txt) -> `ValueError` matching "Unsupported image format"
  - [x] Width is zero -> `ValueError` matching "positive number"
  - [x] Width is negative -> `ValueError` matching "positive number"
  - [x] Width is a string -> `ValueError` matching "positive number"
  - [x] Invalid alignment -> `ValueError` matching "must be one of"
- [x] Add shared fixtures for minimal PNG and JPEG files (conftest or inline)
- [x] Run normalization tests in isolation: `pytest tests/test_normalize.py -v`

## Infrastructure: CLI and Render Updates (`src/docsmith/cli.py`)

- [x] Remove `normalize_heading_block` function definition from `cli.py`
- [x] Add import: `from docsmith.normalize import normalize_heading_block, normalize_image_block`
- [x] Add `Inches` to the `from docx.shared import` line
- [x] Add `_alignment_map` dict mapping `"left"`, `"center"`, `"right"` to `WD_ALIGN_PARAGRAPH` enum values
- [x] Add `base_path` parameter to `render()` with default `None`
- [x] Add image block handler in the render loop (`elif "image" in block:`):
  - [x] Call `normalize_image_block(block, base_path)`
  - [x] Apply width: `Inches(img.width) if img.width is not None else Inches(5.0)`
  - [x] Call `doc.add_picture(str(img.path), width=width)` (note: must use `str()`)
  - [x] Set alignment on the image paragraph via `doc.paragraphs[-1].alignment`
  - [x] If caption: add paragraph with caption text, italic, 9pt, same alignment
- [x] Add guard: if `"image" in block` and `base_path is None`, raise `ValueError`
- [x] Update `main()` to pass `base_path` to `render()`:
  - [x] File input: `base_path=input_path.parent`
  - [x] Stdin input: `base_path=Path.cwd()`
- [x] Update `HELP_EPILOG` to document the image block type

## Integration Tests: Image Rendering (`tests/test_render.py`)

- [x] Remove heading normalization unit tests (now in `test_normalize.py`)
- [x] Update imports if needed (heading normalization no longer imported from `cli`)
- [x] Add shared fixtures for minimal PNG and JPEG files
- [x] Add test: PNG image renders in generated document (check `doc.inline_shapes`)
- [x] Add test: JPEG image renders in generated document
- [x] Add test: image with caption produces caption paragraph (italic, 9pt)
- [x] Add test: image with center alignment sets paragraph alignment
- [x] Add test: image with explicit width sets inline shape width (~`Inches(3.0)`)
- [x] Add test: image without width gets default width (~`Inches(5.0)`)
- [x] Add test: image without alignment defaults to left
- [x] Add test: missing image file raises `ValueError` before producing output file

## Verification

- [x] All new tests pass: `pytest tests/ -v` (42 passed)
- [x] All existing tests pass (including `test_render_minimal`, heading integration tests)
- [x] Lint clean: `ruff check src/ tests/`
- [x] Format clean: `ruff format --check src/ tests/`
- [ ] Manual smoke test: create a YAML file with an image block, render to .docx, open in Word/LibreOffice, confirm image displays correctly with caption and alignment

## Post-Implementation

- [ ] Update README.md to document the image block type and its fields
- [ ] Commit with message: `feat: add image block type for embedding PNG and JPEG images [#1]`
- [ ] Open PR referencing Issue #1