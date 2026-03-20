# DES-001: Image Block Support

**Requirement:** [REQ-001](../requirements/001-image-block-support.md)
**Issue:** [#1](https://github.com/dawsonlp/docsmith/issues/1)
**Status:** Draft
**Author:** Architect

---

## Architectural Analysis

### Current State

docsmith renders six block types (heading, text, bullets, numbered, table, decision), all of which are text-based. The `render()` function in `cli.py` processes blocks in a loop, dispatching by key name. Block normalization exists for headings (introduced in DES-002) but not for other block types.

The current architecture has no concept of external file references. Every block's content is self-contained within the YAML. The image block is the first block type that references an external resource, which introduces two new concerns the architecture must address: path resolution and file validation.

### Why This Is Architecturally Significant

Text blocks are pure data transforms: YAML string in, python-docx call out. Image blocks break this pattern in three ways:

1. **External file dependency.** The block references a file that must exist on disk at render time. This is a new failure mode -- the document cannot be rendered if the file is missing or unreadable.

2. **Path resolution context.** Where the image file is located depends on how docsmith was invoked: from a file path (resolve relative to the YAML file) or from stdin (resolve relative to cwd). The block normalization layer must receive this context from the CLI layer.

3. **Format validation requires file inspection.** Unlike text fields that can be validated purely from YAML content, image format validation requires examining the referenced file (at minimum its extension, ideally its actual content).

These concerns must be handled before the rendering layer sees the block. The renderer should receive a validated, resolved file path and rendering parameters -- not a raw YAML dict with an unresolved relative path.

### Relationship to DES-002

DES-002 established the "normalize early, process once" pattern and predicted that REQ-001 would add enough normalization logic to justify extracting a dedicated normalization module. This design formalizes that extraction.

---

## Design Decisions

### D1: Extract block normalization into a dedicated module

DES-002 D5 noted that heading normalization was deliberately written as a standalone function with no python-docx dependency, anticipating extraction. The image block adds path resolution, format validation, optional field defaulting, and alignment normalization -- enough distinct logic to justify a separate module.

After this change, the architecture has three distinct layers:

| Layer | Responsibility | Depends On |
|-------|---------------|------------|
| **CLI** | Parse arguments, read YAML, determine base path, invoke render | Normalization, Rendering |
| **Normalization (Domain)** | Validate and normalize raw YAML blocks into canonical representations | Standard library only |
| **Rendering (Infrastructure)** | Translate normalized block data into python-docx calls | python-docx |

The normalization module contains all block normalization functions (heading and image, with the pattern available for future block types). Normalization functions have no dependency on python-docx. Filesystem path checks are permitted where required for precondition validation (see D2).

The engineer decides the module name and whether to use a single module or a package. The constraint is that normalization code must be importable and testable without importing python-docx.

### D2: Path resolution is a normalization responsibility

Path resolution -- converting a relative path from YAML into an absolute, validated path -- is a domain concern. It encodes docsmith's schema rules about how image paths are interpreted.

The normalization function must receive a **base path** parameter that determines where relative paths are resolved from. This base path is:

- The parent directory of the YAML input file (when invoked with a file path)
- The current working directory (when invoked with stdin)

The CLI layer determines the base path and passes it to normalization. Normalization resolves the path and validates that the file exists. The renderer receives only a resolved absolute path.

This means the image normalization function performs I/O (checking file existence). This is a deliberate deviation from the pure-function pattern used for heading normalization. The justification:

- File existence is a precondition, not a side effect. The normalization is answering the question "is this a valid image block?" and that question cannot be answered without checking the filesystem.
- The alternative -- deferring existence checks to the renderer -- would violate DES-002 D3 (normalization is where validation errors originate) and D4 (the renderer trusts normalized data).
- The I/O is a single `Path.exists()` call, not a complex operation. It does not write, mutate, or connect to external services.

### D3: Format validation uses file extension

The supported formats are PNG and JPEG (REQ-001 R3). Format validation checks the file extension against an allowed set (`.png`, `.jpg`, `.jpeg`), case-insensitive.

Magic byte validation is not required for this release. Rationale:

- docsmith users are document authors, not adversaries. The primary failure mode is a typo or wrong path, not a deliberately mislabeled file.
- python-docx will raise its own error if the file content does not match what it expects, providing a second line of defense.
- Magic byte validation adds complexity (reading file headers, maintaining a format table) for a threat model that does not apply.

If future requirements introduce untrusted input sources, format validation can be strengthened at the normalization boundary without changing the renderer.

### D4: Image normalization produces a canonical representation with all fields resolved

After normalization, the image block has exactly one representation:

- **path**: Resolved absolute `Path` to an existing image file
- **width**: Width in inches as specified by the user (per REQ-001 R4), passed through as a numeric value. The renderer converts inches to the rendering library's internal unit system. No unit conversion happens in normalization. `None` when not specified, meaning the renderer applies a sensible default.
- **alignment**: One of a fixed set of alignment values, defaulting to left
- **caption**: Caption string, or `None` if not provided

The renderer receives this canonical form and does not inspect the original YAML structure. All defaulting, validation, and path resolution has already happened.

### D5: Caption is part of the image block, not a separate block

The caption is logically part of the image block. It appears below the image and is specified within the image block's YAML structure. The normalization function includes the caption in its output. The renderer produces both the image and the caption paragraph as part of handling the image block.

The alternative -- treating caption as a separate block -- would split a single user intent across two blocks, complicating the YAML authoring experience and creating ordering fragility.

### D6: Alignment is a rendering concern carried through normalization

Alignment (left, center, right) affects how python-docx positions the image paragraph. Normalization validates and normalizes the alignment value (e.g., case-insensitive matching, defaulting to left). The renderer translates the normalized alignment value into the appropriate python-docx alignment constant.

Normalization does not import python-docx alignment enums. It works with plain strings. The mapping from string to enum is the renderer's job.

---

## Component Boundaries

### Block Normalization -- Image (Domain)

**Responsibility:** Accept a raw image block dict from YAML plus a base path for resolution. Validate all fields, resolve the image path, and return a canonical representation.

**Interface contract:**

- Input: raw dict from the YAML `content` list containing an `image` key, plus a base path
- The `image` value must be a dict (no string shorthand form for this block type). Rationale: image blocks have multiple fields (path, width, caption, alignment) making a dict the natural YAML representation. A string shorthand (e.g., `image: "diagram.png"`) could be added later at the normalization boundary without changing the renderer, following the same pattern used for heading blocks. It is omitted now to avoid designing two input forms before the first one is proven in use.
- Output: canonical representation containing resolved path, optional width, optional caption, and alignment
- Errors raised when:
  - `image` value is not a dict
  - Required `path` field is missing
  - Resolved path does not exist on disk
  - File extension is not in the supported set (`.png`, `.jpg`, `.jpeg`)
  - `width` is present but not a positive number
  - `alignment` is present but not one of `left`, `center`, `right`

**Constraints:**

- No dependency on python-docx
- I/O limited to path existence check and nothing else
- Error messages reference the YAML structure and the resolved file path
- Directly testable with dicts and temporary files

### Block Normalization -- Heading (Domain, existing)

Moves from `cli.py` into the normalization module. Interface contract unchanged from DES-002.

### Document Rendering -- Image (Infrastructure)

**Responsibility:** Accept normalized image data and produce the image (and optional caption) in the Word document via python-docx.

**Interface contract:**

- Receives: resolved absolute path, optional width, alignment, optional caption
- Produces: an image in the document at the specified width and alignment, followed by a caption paragraph if provided
- Does not validate the path, check file existence, or interpret YAML structure
- Caption styling decisions belong to the renderer (the requirements delegate styling to the implementation team)

### CLI Layer (Orchestration)

**Change required:** The CLI must determine the base path for image resolution and pass it to the render function (or to a normalization step). Currently, `render()` receives `doc_data` and `output_path`. It must now also receive the base path for resolving relative image references.

The engineer decides how to thread this context -- an additional parameter to `render()`, a pre-processing normalization pass over all blocks before rendering, or another mechanism. The constraint is that the base path must be available when image blocks are normalized.

---

## Data Flow

```
CLI: parse args, read YAML, determine base_path
  |
  v
For each block in content:
  |
  +--> Normalize (domain)
  |      Heading: extract text + level, validate, return canonical form
  |      Image: resolve path against base_path, validate existence + format,
  |             extract width/caption/alignment, apply defaults, return canonical form
  |      Other blocks: pass through (or normalize as needed in future)
  |
  +--> Render (infrastructure)
         Heading: doc.add_heading(text, level)
         Image: doc.add_picture(path, width) + optional caption paragraph + alignment
         Other blocks: existing rendering logic
```

---

## Constraints

1. **Backward compatibility is non-negotiable.** All existing YAML documents without image blocks must produce identical output.

2. **No new runtime dependencies.** python-docx already supports `add_picture()` for PNG and JPEG. Path handling uses `pathlib` from the standard library.

3. **Error messages must be user-facing quality.** They must say what was wrong (e.g., "Image file not found") and include the resolved path so the user can diagnose the problem. Errors about unsupported formats must list the supported formats.

4. **All existing tests must continue to pass.** The normalization module extraction must not break existing imports in the test suite.

5. **The normalization module must be testable without python-docx.** This is the key structural constraint that keeps the domain layer clean.

---

## Testing Guidance

Tests follow the construction order: domain tests first, then integration tests.

**Domain (normalization) tests for image blocks should cover:**

- Valid image block with all fields produces correct canonical output
- Valid image block with only required field (path) uses correct defaults
- Missing path field raises a clear error
- Non-existent image file raises a clear error that includes the resolved path
- Unsupported file extension raises a clear error listing valid formats
- Width validation: positive number accepted, zero/negative rejected, non-numeric rejected
- Alignment validation: left/center/right accepted (case-insensitive), invalid value rejected
- Caption: present string passes through, absent field defaults to None
- Path resolution: relative path resolved against provided base path
- Path resolution: absolute path used as-is regardless of base path

These tests use temporary directories and files. They do not import python-docx.

**Domain tests for heading normalization should be moved to the normalization test file** (or remain where they are if the engineer keeps them alongside the normalization code). The tests themselves do not change.

**Integration tests for image rendering should cover:**

- PNG image renders in the generated document
- JPEG image renders in the generated document
- Image with caption produces image followed by caption text
- Image with alignment is correctly positioned
- Image with width constraint is correctly sized
- Missing image produces error before generating the output file

These tests call `render()` with temporary image files and inspect the resulting .docx.

---

## Trade-offs

| Decision | Trade-off | Rationale |
|----------|-----------|-----------|
| Extract normalization module now | Adds a module to a small codebase | Image normalization is complex enough to justify it; DES-002 predicted this |
| File extension only, no magic bytes | A renamed .txt file would pass validation until python-docx rejects it | Acceptable for the trust model; python-docx provides second-line defense |
| Path resolution in normalization (I/O in domain) | Impure function in the domain layer | File existence is a precondition, not a side effect; alternative violates DES-002 D3/D4 |
| Caption as part of image block | Renderer must produce two document elements for one block | Matches user intent; splitting would complicate YAML authoring |
| Base path threaded from CLI to normalization | Adds a parameter to the render interface | Required by the path resolution semantics in REQ-001 R2; no way to avoid it |
| Dict-only input, no string shorthand | Slightly more verbose YAML for simple cases | Natural for multi-field blocks; shorthand can be added at normalization boundary later |

---

## Open Questions

None. The requirements are specific enough to proceed with technical design.