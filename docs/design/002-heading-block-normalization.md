# DES-002: Heading Block Normalization

**Requirement:** [REQ-002](../requirements/002-heading-dict-form-bug.md)
**Issue:** [#2](https://github.com/dawsonlp/docsmith/issues/2)
**Status:** Draft
**Author:** Architect

---

## Architectural Analysis

### Root Cause

The heading bug is not a typo or off-by-one error. It is a consequence of missing domain logic. The `render()` function currently passes raw YAML values directly to python-docx without any validation or normalization. When the YAML parser produces a dict for the heading value, that dict flows unchecked into `doc.add_heading()`, which calls `str()` on it and renders the dict's keys.

The same architectural gap -- no validation layer between YAML input and docx output -- would produce similar silent corruption bugs in any block type that accepts multiple input forms.

### Current State

All logic lives in `render()` inside `cli.py`. The function interleaves three distinct responsibilities in a single loop:

1. **Block identification** -- determining what type of block this is (heading, text, bullets, etc.)
2. **Input interpretation** -- extracting the actual values from the raw YAML structure
3. **Document rendering** -- calling python-docx to produce Word elements

Responsibilities 1 and 2 are domain concerns: they embody the rules of docsmith's YAML schema. Responsibility 3 is infrastructure: it translates validated data into a specific output format.

The bug exists because responsibility 2 is absent for heading blocks. The code jumps from identification (1) directly to rendering (3).

### Architectural Impact of Upcoming Work

This is not the last block type that will need input normalization:

- **REQ-001 (Image blocks)** introduces a block with required fields, optional fields, path resolution, and format validation -- all of which are input interpretation concerns that must happen before rendering.
- **REQ-003 (Page orientation)** introduces document-level validation (not block-level), but follows the same pattern: raw YAML value must be validated and normalized before it reaches python-docx.

Fixing the heading bug with an inline conditional would solve the immediate problem but would not establish the pattern needed for the next two features.

---

## Design Decisions

### D1: Introduce a block normalization boundary

There must be a clear boundary between raw YAML input and the data that reaches the rendering layer. On one side: untrusted, polymorphic YAML values. On the other side: validated, uniform data that the renderer can consume without guessing.

This boundary is a domain concern. It encodes docsmith's schema rules -- what shapes of input are valid for each block type, what defaults apply, and what the canonical representation looks like.

### D2: Normalization produces a uniform representation per block type

After normalization, each block type must have exactly one representation. The renderer should not need to inspect whether a heading was originally a string or a dict. It receives a heading with a text value and a level value, always, regardless of which YAML form the user chose.

This eliminates the class of bugs where a new input form is added to the YAML schema but the renderer only handles one form.

### D3: Normalization is where validation errors originate

Invalid input (missing text, wrong types, out-of-range values) must be detected and reported during normalization, not during rendering. Error messages must reference the user's input, not python-docx internals.

### D4: The renderer trusts normalized data

After normalization, the rendering layer must not re-validate or re-interpret block contents. It receives well-typed, well-formed data and translates it to python-docx calls. If the renderer encounters unexpected data, it is a bug in the normalization layer.

### D5: Scope of structural change for this fix

The bug fix must establish the normalization boundary for heading blocks. It does not need to normalize all existing block types in this change.

However, the pattern established here should be reusable. When REQ-001 (image blocks) is implemented, the engineer should be able to follow the same pattern without refactoring the heading work.

The engineer decides whether to keep all code in `cli.py` or split into separate modules. The conceptual boundary matters; the file boundary is an engineering judgment call based on the current size of the codebase.

---

## Component Boundaries

### Block Normalization (Domain)

**Responsibility:** Accept a raw block dict from YAML, determine its type, validate its structure, and return a normalized representation.

**Interface contract (heading block):**

- Input: a raw dict from the YAML `content` list that contains a `heading` key
- The `heading` value may be a string (flat form) or a dict (nested form)
- Output: the heading text as a string, and the heading level as an integer (1-4)
- Level defaults to 1 when not specified in either form
- Level is clamped to the range 1-4
- Errors raised when:
  - `heading` value is a dict but has no `text` key
  - `heading` value is a dict but `text` is empty or not a string
  - `heading` value is neither a string nor a dict (e.g., list, number, None)

**Constraints:**

- No dependency on python-docx
- No I/O
- Directly testable with plain dicts as input
- Error messages must be clear to a user who only knows YAML, not Python

### Document Rendering (Infrastructure)

**Responsibility:** Accept normalized block data and produce Word document elements via python-docx.

**For headings after this change:** receives a text string and an integer level. Calls `doc.add_heading(text, level=level)`. No conditional logic about input forms.

---

## Constraints

1. **Backward compatibility is non-negotiable.** All existing YAML documents using the flat heading form must produce identical output.

2. **No new dependencies.** The fix uses only the standard library and existing project dependencies.

3. **Error messages must be user-facing quality.** They must say what was wrong and what was expected, in terms of the YAML structure -- not in terms of Python types or python-docx exceptions.

4. **The existing smoke test must continue to pass.** New tests are required for the new behavior.

---

## Testing Guidance

Tests for this change should follow the construction order: domain tests first, then integration tests that verify the full render path.

**Domain (normalization) tests should cover:**

- Flat form heading produces correct text and level
- Nested dict form heading produces correct text and level
- Level defaults to 1 when omitted in both forms
- Level is clamped to 4 when exceeding range
- Missing `text` in nested form raises a clear error
- Empty `text` in nested form raises a clear error
- Non-string, non-dict heading value raises a clear error (e.g., list, integer, None)

These tests operate on plain dicts and assert returned values or raised exceptions. No file I/O, no python-docx.

**Integration tests should cover:**

- Flat form heading appears in generated document with correct text and level
- Nested dict form heading appears in generated document with correct text and level

These tests call `render()` and inspect the resulting .docx file.

---

## Design Advice for the Implementing Engineer

### On the bug fix itself

The core fix is small: before the heading text reaches `doc.add_heading()`, it must pass through logic that handles both input forms and produces a single (text, level) pair. The key insight is that this logic is a domain function -- it encodes docsmith schema rules -- and should be testable independently of python-docx.

### On error handling

The requirements specify three error cases (missing text, empty text, invalid type). These should produce exceptions with messages that a YAML author can act on. Consider what the user sees: they have a YAML file and a terminal error. The error should tell them which block is wrong and what it should look like.

### On structural decisions

Keep normalization in `cli.py` for this change. The codebase is approximately 200 lines; a separate module for a single normalization function would be premature structure.

However, write the normalization as a standalone function with a clean signature: plain dict in, normalized values (or exception) out. Specifically:

- No python-docx imports or objects in the function signature or body
- No dependency on the `doc` variable or any rendering state
- No module-level mutable state that would complicate extraction later

The architect expects that REQ-001 (image blocks) will add enough normalization logic -- path resolution, format validation, optional field defaults, alignment normalization -- to justify extracting a dedicated normalization module. Writing the heading normalization cleanly now makes that future extraction trivial: move the function, update one import, done.

The design document for REQ-001 will formally decide the extraction. For this change, the goal is a function that is easy to test in place and easy to move later.

### On scope discipline

This change fixes heading blocks only. Do not normalize other block types in this change. The pattern should be obvious enough that future block types can adopt it, but the actual work of normalizing text, bullets, tables, etc. is not part of this issue.