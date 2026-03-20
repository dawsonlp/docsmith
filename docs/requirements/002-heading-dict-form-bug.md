# REQ-002: Heading Block Must Handle All Valid Input Forms

**Issue:** [#2](https://github.com/dawsonlp/docsmith/issues/2)
**Priority:** Critical
**Type:** Bug fix
**Status:** Approved

---

## Problem Statement

When a heading block uses a nested dictionary form in YAML, the document renders garbled text instead of the intended heading. No error is raised. The user discovers the problem only after opening the generated document -- or worse, after sharing it with a client.

This is a silent data corruption issue.

## Business Context

docsmith is used to generate client-shareable documents. A heading that renders as concatenated dictionary keys (e.g., "textlevel") instead of the intended text destroys the credibility of the output. Users cannot trust the tool if it silently produces wrong content.

## Requirements

### R1: Both heading forms must produce correct output

The following two YAML forms must produce identical documents with the heading "Section Title" at level 2:

**Flat form (currently works):**

```yaml
- heading: "Section Title"
  level: 2
```

**Nested dict form (currently broken):**

```yaml
- heading:
    text: "Section Title"
    level: 2
```

### R2: Missing heading text must produce a clear error

If the nested dict form is used but `text` is missing or empty, the system must raise a clear, actionable error message rather than rendering an empty or garbled heading.

### R3: Invalid heading structure must produce a clear error

If `heading` contains a value that is neither a string nor a dict with a `text` key (e.g., a list, a number, or a dict without `text`), the system must raise a clear error.

### R4: Heading level constraints remain unchanged

- Level defaults to 1 when not specified
- Level is clamped to the range 1-4
- This behavior must hold for both the flat and nested forms

### R5: Existing flat-form behavior is preserved

All existing documents using the flat heading form must continue to work identically. This fix must not be a breaking change.

## Acceptance Criteria

- [ ] Flat heading form continues to work as before
- [ ] Nested dict heading form renders correct text at correct level
- [ ] Missing `text` in nested form produces a clear error message
- [ ] Invalid heading types (list, number, dict without `text`) produce clear errors
- [ ] Existing tests continue to pass
- [ ] New tests cover both forms and error cases

## Out of Scope

- Changes to any other block types
- Changes to heading styling or formatting
- New heading features (e.g., anchors, numbering)