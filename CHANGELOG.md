# Changelog

All notable changes to docsmith are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/), and this project uses [Semantic Versioning](https://semver.org/).

---

## [1.1.0] -- 2026-03-20

### Added

- **Image block support** -- embed PNG and JPEG images in generated documents
  - `path` (required): file path relative to the YAML file, or absolute
  - `width` (optional): width in inches, defaults to 5.0
  - `alignment` (optional): `left`, `center`, or `right`, defaults to `left`
  - `caption` (optional): italic caption text rendered below the image
- `normalize` module -- pure-function normalization layer for block validation
  - `normalize_heading_block()`: validates and canonicalizes heading blocks
  - `normalize_image_block()`: validates image path, format, dimensions, and alignment
  - `ImageBlock` dataclass for type-safe image block representation
- Domain-level test suite (`test_normalize.py`) covering heading and image normalization
- Integration test suite for image rendering (PNG, JPEG, caption, alignment, width, error cases)
- `pillow` added to dev dependencies (used for generating test fixture images)

### Fixed

- **Heading dict-form bug** -- `heading: {text: "Title", level: 2}` now renders correctly
  - Both flat (`heading: "Title"`) and nested dict forms produce identical output
  - Heading level clamped to valid range 1-4
  - Clear error messages for missing text, invalid types, or malformed input

### Changed

- Rendering pipeline now uses normalize-then-render pattern: input variance is resolved once at the normalization boundary, not in the renderer
- Test suite restructured: domain normalization tests separated from integration rendering tests

---

## [1.0.1] -- 2025-03-20

### Fixed

- Ruff linting issues resolved across source and test files
- GitHub Actions updated to Node.js 24 (`setup-uv@v5`)
- Pre-commit added to dev dependencies
- CI workflow aligned with PyPI publish patterns
- Smoke test added for CI pipeline

---

## [1.0.0] -- 2025-03-20

### Added

- Initial stable release
- YAML-to-Word document generation with block types:
  - `heading` (string form, levels 1-4)
  - `text` (paragraphs with `**bold**` and `*italic*` inline markup)
  - `bullets` (unordered lists)
  - `numbered` (ordered lists)
  - `table` (headers and rows with grid styling)
  - `decision` (red callout blocks for stakeholder decisions)
- Title page generation from `title`, `subtitle`, and `status` metadata
- Stdin support (`docsmith -` or piped input from LLMs)
- Output directory support (`-o`)
- SharePoint/OneDrive-compatible document properties
- Word 2016+ compatibility mode
- CLI via `docsmith` command and `python -m docsmith`
- Pre-commit hooks (ruff format and lint)
- CI/CD via GitHub Actions (lint, test, PyPI trusted publishing)
- GPL-3.0-or-later license