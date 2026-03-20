# REQ-003: Page Orientation Support (Landscape/Portrait)

**Issue:** [#3](https://github.com/dawsonlp/docsmith/issues/3)
**Priority:** Medium
**Type:** Feature
**Status:** Approved

---

## Problem Statement

docsmith always produces portrait-oriented documents. Documents containing wide tables, timeline views, or landscape-oriented diagrams are unreadable or require users to manually change orientation in Word after generation. This breaks the "YAML is the complete document" promise.

## Business Context

Architecture diagrams and system context diagrams need landscape pages to be readable at print resolution. Wide comparison tables with many columns overflow or get compressed to illegibility in portrait. Users generating these documents in automated pipelines cannot manually fix orientation after the fact.

This feature becomes especially valuable in combination with image embedding (REQ-001), since diagrams are the primary driver for landscape orientation.

## Requirements

### R1: Orientation as a document-level setting

Users must be able to specify the page orientation of the document as either `portrait` or `landscape` using a top-level YAML key.

### R2: Default is portrait

When orientation is not specified, the document must be generated in portrait orientation. This preserves backward compatibility with all existing YAML files.

### R3: Landscape swaps page dimensions

When landscape is specified, the page width and height must be swapped so that the wider dimension becomes the width. The resulting document must open in Word with landscape orientation without requiring any manual adjustment.

### R4: Invalid orientation produces a clear error

If the orientation value is anything other than `portrait` or `landscape` (case-insensitive), the system must raise a clear error message listing the valid options.

### R5: Orientation applies to the entire document

This feature sets orientation for the whole document. Mixed orientation (some pages portrait, some landscape) is out of scope.

## Acceptance Criteria

- [ ] `orientation: landscape` produces a landscape document
- [ ] `orientation: portrait` produces a portrait document
- [ ] Omitting orientation produces a portrait document (backward compatible)
- [ ] Orientation value is case-insensitive
- [ ] Invalid orientation value produces a clear error with valid options listed
- [ ] Landscape documents open correctly in Microsoft Word, Google Docs, and LibreOffice
- [ ] Existing documents without orientation continue to work identically

## Out of Scope

- Mixed orientation within a single document (per-section orientation)
- Custom page sizes (may be a future enhancement)
- Margin adjustments specific to orientation