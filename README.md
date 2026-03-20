# docsmith

YAML-in, Word-out. Define document content in a simple YAML schema and docsmith forges it into a professionally formatted Word (.docx) file.

## Why docsmith?

docsmith is built for **automated pipelines and LLM-driven content generation**. The YAML input format is deliberately simple -- flat, predictable, and easy for any language model or script to produce. No template engine, no programming required. Hand it a YAML file (or pipe it via stdin), get a Word document back.

Use cases:

- **LLM document generation** -- have an AI produce structured YAML, then render to Word
- **CI/CD pipelines** -- generate reports, proposals, or compliance documents as build artifacts
- **Batch processing** -- convert a directory of YAML files to Word in one pass
- **Content-first authoring** -- focus on content in YAML, let docsmith handle formatting

## Installation

```bash
pipx install docsmith
```

Or with pip:

```bash
pip install docsmith
```

## Usage

```bash
# Generate a Word document from a YAML file
docsmith input.yaml

# Specify output directory
docsmith input.yaml -o output/

# Pipe YAML from stdin
cat input.yaml | docsmith -

# Pipe directly from an LLM
llm "write a project status report in docsmith YAML format" | docsmith -
```

When reading from stdin (`-`), the output file is `docsmith_output.docx` in the current directory. Use `-o` to override the output directory.

Also works as a Python module:

```bash
python -m docsmith input.yaml
```

## YAML Document Format

```yaml
title: "Document Title"
subtitle: "Subtitle text"
status: "Draft"

content:
  - heading: "Section Heading"
    level: 1

  - text: "Paragraph with **bold** and *italic* support."

  - bullets:
      - "First bullet point"
      - "Second bullet with **bold**"

  - numbered:
      - "Step one"
      - "Step two"

  - table:
      headers: ["Column A", "Column B"]
      rows:
        - ["Cell 1", "Cell 2"]
        - ["Cell 3", "Cell 4"]

  - image:
      path: "diagram.png"
      width: 4.0
      alignment: center
      caption: "Figure 1: System architecture"

  - decision: "A decision callout that needs stakeholder input"
```

## Supported Block Types

| Block | Purpose |
|-------|---------|
| `heading` | Section heading (level 1-4) |
| `text` | Paragraph with inline bold/italic |
| `bullets` | Unordered list |
| `numbered` | Ordered list |
| `table` | Table with headers and rows |
| `image` | Embedded PNG/JPEG image |
| `decision` | Red decision callout |

### Image Block Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `path` | Yes | -- | File path relative to the YAML file, or absolute |
| `width` | No | 5.0 | Width in inches (aspect ratio preserved) |
| `alignment` | No | `left` | `left`, `center`, or `right` |
| `caption` | No | -- | Caption text displayed below the image in italic |

## Document Metadata

docsmith sets SharePoint/OneDrive-compatible document properties:

- `dc:creator` and `cp:lastModifiedBy` set to "docsmith"
- `dcterms:created` and `dcterms:modified` set to generation timestamp
- `dc:title` and `dc:subject` populated from YAML metadata

## Development

```bash
git clone https://github.com/dawsonlp/docsmith.git
cd docsmith
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Install pre-commit hooks (ruff format + lint)
pre-commit install
```

CI runs ruff lint/format checks and pytest on every push and PR. Releases to PyPI are automated via GitHub Actions trusted publishing on tagged releases.

## Future Output Formats

Word is the first format. The YAML source schema is designed to be renderable to multiple output formats (PDF, HTML, Markdown) in future versions.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE) for details.