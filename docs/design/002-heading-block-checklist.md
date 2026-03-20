# Implementation Checklist: Issue #2 -- Heading Block Normalization

**Requirement:** [REQ-002](../requirements/002-heading-dict-form-bug.md)
**Design:** [DES-002](002-heading-block-normalization.md)
**Technical Design:** [TDS-002](002-heading-block-technical-design.md)
**Issue:** [#2](https://github.com/dawsonlp/docsmith/issues/2)
**Branch:** `fix/heading-dict-form`

---

## Pre-flight

- [x] Read REQ-002, DES-002, and TDS-002 in full
- [x] Confirm existing tests pass: `pytest tests/ -v`
- [ ] Create branch from main: `git checkout -b fix/heading-dict-form`

## Domain: Normalization Function

- [x] Add `normalize_heading_block(block: dict) -> tuple[str, int]` to `cli.py`, placed above `render()`
- [x] Implement string path: extract text from `block["heading"]`, level from `block.get("level", 1)`
- [x] Implement dict path: extract text from `heading["text"]`, level from `heading.get("level", 1)`
- [x] Implement type guard: raise `ValueError` for non-string, non-dict heading values
- [x] Implement dict validation: raise `ValueError` when `text` key is missing
- [x] Implement dict validation: raise `ValueError` when `text` is empty or whitespace-only
- [x] Implement level normalization: `max(1, min(int(level), 4))` for both paths
- [x] Verify function has zero python-docx imports or references

## Domain Tests: Normalization

- [x] Add parametrized happy-path test covering: flat with level, flat default level, nested with level, nested default level, level clamped high, level clamped low
- [x] Add parametrized error test covering: nested missing text, nested empty text, nested whitespace text, heading is list, heading is int, heading is None
- [x] Verify error tests use `pytest.raises(ValueError, match=...)` to assert message content
- [x] Run domain tests in isolation: `pytest tests/test_render.py -v -k normalize`

## Infrastructure: Render Loop Update

- [x] Replace heading handler in `render()` with call to `normalize_heading_block`
- [x] Confirm the handler is now two lines: unpack tuple, call `doc.add_heading(text, level=level)`
- [x] No other block handlers modified

## Integration Tests: Render Path

- [x] Add test: flat form heading renders correct text in .docx (read back with `Document()`)
- [x] Add test: nested dict form heading renders correct text in .docx
- [x] Add test: invalid heading raises `ValueError` before producing output file

## Verification

- [x] All new tests pass: `pytest tests/ -v`
- [x] Existing `test_render_minimal` still passes
- [x] Lint clean: `ruff check src/ tests/`
- [x] Format clean: `ruff format --check src/ tests/`
- [x] Manual smoke test: render a YAML file with both heading forms, open in Word/LibreOffice, confirm headings display correctly

## Commit and PR

- [ ] Commit with message: `fix: normalize heading block to handle both flat and nested dict forms [#2]`
- [ ] Open PR referencing Issue #2
