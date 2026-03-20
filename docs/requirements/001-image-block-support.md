# REQ-001: Image Block Type for Embedding Diagrams and Figures

**Issue:** [#1](https://github.com/dawsonlp/docsmith/issues/1)
**Priority:** High
**Type:** Feature
**Status:** Complete -- Implemented in v1.1.0

---

## Problem Statement

docsmith has no way to embed images into generated documents. Users who need to include architecture diagrams, charts, or figures must abandon the YAML workflow and write python-docx scripts directly. This breaks the single-source declarative model that is docsmith's core value proposition.

## Business Context

A primary use case for docsmith is generating client-shareable documents that include architecture diagrams rendered from tools like D2, Mermaid, or Graphviz. These diagrams are produced as image files (PNG, JPEG) and need to be embedded alongside text content in the final Word document. Without image support, users maintain parallel workflows -- YAML for text, custom scripts for diagrams -- which eliminates the productivity benefit of docsmith.

## Requirements

### R1: Image block type

Users must be able to embed an image into a document using a new `image` block type within the `content` list.

### R2: Required fields

An image block must specify a file path to the image. The path must be resolved relative to the YAML input file's location (or relative to the current working directory when reading from stdin).

### R3: Supported image formats

The following raster image formats must be supported:

- PNG
- JPEG / JPG

SVG is explicitly out of scope for this release (see Out of Scope).

### R4: Optional width control

Users may specify a width for the image in inches. When width is specified, height is calculated automatically to preserve the image's aspect ratio. When width is not specified, a sensible default should be used (the implementation team decides what "sensible" means for typical document layouts).

### R5: Optional caption

Users may specify a caption string that appears below the image. The caption must be visually distinct from body text (e.g., smaller, italic, or otherwise differentiated -- the implementation team decides the specific styling).

### R6: Optional alignment

Users may specify horizontal alignment for the image: left, center, or right. The default alignment when not specified is left.

### R7: Missing image file produces a clear error

If the specified image file does not exist at render time, the system must raise a clear, actionable error message that includes the resolved file path. The system must not silently skip the image or produce a broken document.

### R8: Non-image files produce a clear error

If the specified path points to a file that is not a supported image format, the system must raise a clear error.

## Acceptance Criteria

- [ ] PNG images render correctly in the generated document
- [ ] JPEG images render correctly in the generated document
- [ ] Width control works and preserves aspect ratio
- [ ] Caption appears below the image with distinct styling
- [ ] Alignment options (left, center, right) work correctly
- [ ] Default alignment is left when not specified
- [ ] Missing image file produces a clear error with the resolved path
- [ ] Unsupported file format produces a clear error
- [ ] Image path resolves relative to the YAML file location
- [ ] Image path resolves relative to cwd when reading from stdin
- [ ] Existing documents without images continue to work identically

## Out of Scope

- SVG support (requires conversion tooling; may be a future enhancement)
- Image resizing or cropping beyond width scaling
- Image borders, shadows, or decorative effects
- Inline images within text paragraphs (images are block-level only)
- Image alt-text or accessibility metadata in the Word document