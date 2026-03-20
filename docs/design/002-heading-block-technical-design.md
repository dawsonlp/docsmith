# TDS-002: Heading Block Normalization -- Technical Design

**Requirement:** [REQ-002](../requirements/002-heading-dict-form-bug.md)
**Design:** [DES-002](002-heading-block-normalization.md)
**Issue:** [#2](https://github.com/dawsonlp/docsmith/issues/2)
**Status:** Draft
**Author:** Senior Engineer

---

## Context

The architect's design document (DES-002) establishes that a normalization boundary must exist between raw YAML input and the rendering layer. For this change, normalization lives in `cli.py` as a standalone function with no python-docx dependency. This technical design describes how to realize that boundary in the current codebase.

---

## Technology Choices

| Concern | Choice | Rationale |
|---------|--------|-----------|
| Error type | `ValueError` | Standard Python for invalid input; no custom exception hierarchy justified for one block type |
| Return type | `tuple[str, int]` | Simple, typed, no dataclass overhead for two values; reconsider when more block types are normalized |
| Level clamping | `max(1, min(level, 4))` | Matches existing behavior in `render()` |
| Type checking | `isinstance` dispatch on the heading value | Clean, explicit, handles str/dict/other without ambiguity |

---

## Function Design

### `normalize_heading_block(block: dict) -> tuple[str, int]`

This function accepts a raw block dict from the YAML `content` list and returns `(text, level)`.

**Input dispatch logic:**

The `heading` value determines the code path:

- **String:** text comes from the value directly; level comes from `block.get("level", 1)` (the flat form, matching current behavior exactly).
- **Dict:** text comes from `heading["text"]`; level comes from `heading.get("level", 1)`. The top-level `block.get("level")` is ignored in this form because the dict is self-contained.
- **Anything else (list, int, float, None, bool):** raise `ValueError` with a message describing the valid forms.

**Validation rules (dict form only):**

- `text` key must be present
- `text` value must be a non-empty string (after stripping whitespace)
- `level`, if present, must be interpretable as an integer

**Level normalization (both forms):**

- Default to 1 when not specified
- Clamp to range 1-4 using `max(1, min(int(level), 4))`

**Error message format:**

Error messages should follow this pattern -- state what is wrong, then state what is expected:

- Missing text: `"Heading block nested form requires a 'text' key, e.g.: heading: {text: \"Section Title\", level: 2}"`
- Empty text: `"Heading block 'text' must be a non-empty string"`
- Invalid type: `"Heading block value must be a string or a dict with a 'text' key, got <type>"`

These messages are written for YAML authors, not Python developers.

---

## Integration into `render()`

The current heading handler in the render loop:

```python
if "heading" in block:
    level = block.get("level", 1)
    doc.add_heading(block["heading"], level=min(level, 4))
```

After this change, it becomes:

```python
if "heading" in block:
    text, level = normalize_heading_block(block)
    doc.add_heading(text, level=level)
```

The render loop no longer interprets the heading block structure. It delegates to `normalize_heading_block` and trusts the result (per DES-002 D4).

---

## Error Propagation

`normalize_heading_block` raises `ValueError`. The current `render()` function does not catch exceptions -- they propagate to `main()`, which also does not catch them. This means a `ValueError` will produce a Python traceback in the terminal.

For this change, that is acceptable. The error message itself is user-facing quality (per the format above), and the traceback provides debugging context. A future change could add a top-level exception handler in `main()` that catches `ValueError` and prints a clean message without traceback, but that is out of scope for this fix.

---

## Testing Strategy

### Unit Tests (normalization function)

These test `normalize_heading_block` directly. No python-docx, no file I/O.

| Test | Input | Expected |
|------|-------|----------|
| Flat form, text and level | `{"heading": "Title", "level": 2}` | `("Title", 2)` |
| Flat form, text only (default level) | `{"heading": "Title"}` | `("Title", 1)` |
| Nested form, text and level | `{"heading": {"text": "Title", "level": 3}}` | `("Title", 3)` |
| Nested form, text only (default level) | `{"heading": {"text": "Title"}}` | `("Title", 1)` |
| Level exceeds max, clamped to 4 | `{"heading": "Title", "level": 9}` | `("Title", 4)` |
| Level below min, clamped to 1 | `{"heading": "Title", "level": 0}` | `("Title", 1)` |
| Nested form, missing text key | `{"heading": {"level": 2}}` | `ValueError` |
| Nested form, empty text | `{"heading": {"text": "", "level": 2}}` | `ValueError` |
| Nested form, text is whitespace only | `{"heading": {"text": "   "}}` | `ValueError` |
| Heading value is a list | `{"heading": ["a", "b"]}` | `ValueError` |
| Heading value is an integer | `{"heading": 42}` | `ValueError` |
| Heading value is None | `{"heading": None}` | `ValueError` |

Use `pytest.raises(ValueError, match=...)` to verify error messages contain actionable guidance.

Use `@pytest.mark.parametrize` to group the happy-path cases and the error cases, rather than writing individual test functions for each row.

### Integration Tests (render path)

These call `render()` and inspect the generated .docx file using `python-docx` to read it back.

| Test | Input | Assertion |
|------|-------|-----------|
| Flat form renders heading | `{"heading": "Section", "level": 2}` | Document contains a heading paragraph with text "Section" |
| Nested form renders heading | `{"heading": {"text": "Section", "level": 2}}` | Document contains a heading paragraph with text "Section" |
| Invalid heading raises before producing file | `{"heading": {"level": 2}}` | `ValueError` raised, output file does not exist |

For reading back the document, use `Document(output_path)` and inspect `doc.paragraphs`. Heading paragraphs have a style name starting with "Heading".

### Existing Test

The existing `test_render_minimal` smoke test uses a text block only and must continue to pass unchanged.

---

## File Layout

All changes are in two files:

- `src/docsmith/cli.py` -- add `normalize_heading_block` function, update the heading handler in `render()`
- `tests/test_render.py` -- add unit tests for normalization and integration tests for the render path

Place `normalize_heading_block` above `render()` in `cli.py`, grouped with `add_formatted_text` in the "helper functions" region of the file. It has no dependency on python-docx and should be visually distinct from the rendering code.

Per DES-002, the architect expects REQ-001 will trigger extraction of normalization into a separate module. Writing a clean, isolated function now makes that future move a one-line import change.

---

## What This Change Does Not Do

- Does not normalize other block types (text, bullets, numbered, table, decision)
- Does not add a top-level exception handler in `main()`
- Does not extract normalization to a separate module
- Does not change heading styling or formatting
- Does not modify the CLI interface or YAML schema beyond supporting the nested heading form