# wicketgate-publish

A simple, Python-based publisher for Wicketgate Systems.

`wicketgate-publish` reads a project config file, builds declared outputs from
Markdown and templates, and can publish those outputs to configured destinations.
Supported output kinds include static sites and Typst books.

## Install

```bash
uv sync --all-groups
```

Or install from a Git checkout into another project:

```bash
uv add git+https://github.com/chris-diakonos/wicketgate-publish.git
```

## Project Config

Consumer repositories provide a `wicketgate-publish.yaml` file:

```yaml
output_dir: generated

outputs:
  site:
    kind: static_site
    output_subdir: site
    content_dir: content/site
    templates_dir: templates
    assets_dir: assets
    config_dir: config/site
    destination: production

  field_guide:
    kind: typst_book
    output_subdir: field-guide
    source_dir: books/field-guide
    manuscript_dir: books/field-guide/chapters
    config_file: books/field-guide/book.yaml
    typst_entry: books/field-guide/typst/main.typ
    typst_assets_dir: books/field-guide/assets
    output_file: field-guide.pdf
    emit_typst: true

destinations:
  production:
    kind: cloudflare_pages
    project_name: wicketgate-systems
    branch: main
```

The main output directory defaults to repo-root `generated/`. Each output writes
into a subdirectory beneath it, defaulting to the output name.

## Commands

```bash
wicketgate-publish build
wicketgate-publish publish --build
wicketgate-publish build --config path/to/wicketgate-publish.yaml
wicketgate-publish build --output-dir generated-preview
wicketgate-publish build field_guide
```

## Output Kinds

### `static_site`

Builds HTML pages from Markdown content, Jinja2 templates, and site config under
`config_dir` (`site.yaml`, `navigation.yaml`).

### `typst_book`

Assembles ordered Markdown chapters into Typst source and compiles a PDF with the
`typst` CLI.

Minimal book layout:

```text
books/field-guide/
├── book.yaml
├── chapters/
│   ├── 00-preface.md
│   └── 01-introduction.md
├── assets/
│   └── cover.png
└── typst/
    └── main.typ
```

Example `book.yaml`:

```yaml
title: The Field Guide
author: Wicketgate Systems
subtitle: Notes on durable software practice
language: en

chapters:
  - file: 00-preface.md
    title: Preface
    kind: frontmatter
  - file: 01-introduction.md
    title: Introduction

outputs:
  pdf:
    format: pdf
    paper: us-letter
    margin: 0.85in
```

Chapter order comes from `book.yaml`, not from filename sorting. Numeric prefixes
are still useful for humans editing the manuscript.

The Typst entry file should export a `book-prelude` function:

```typ
#let book-prelude(title: "", author: "", subtitle: "") = {
  align(center)[
    #text(2em, weight: "bold")[#title]
    #if subtitle != "" [
      #v(1em)
      #text(1.2em)[#subtitle]
    ]
    #if author != "" [
      #v(2em)
      #text(1em)[#author]
    ]
  ]
  pagebreak()
}
```

Supported manuscript Markdown is intentionally conservative: headings, paragraphs,
emphasis, ordered and unordered lists, blockquotes, fenced code, links, images,
and YAML front matter.

The Typst CLI must be available on `PATH` when building `typst_book` outputs.

## Cloudflare Pages

Destination credentials are provided through environment variables:

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

The `wrangler` CLI must be available when publishing to Cloudflare Pages.

## Development

```bash
uv sync --all-groups
uv run pytest
```

## License

Copyright © Wicketgate Systems.

Licensed under the MIT License.
