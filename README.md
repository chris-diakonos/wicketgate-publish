# wicketgate-publish

A simple, Python-based static site publisher for Wicketgate Systems.

`wicketgate-publish` reads a project config file, builds declared outputs from
Markdown and templates, and can publish those outputs to configured destinations.

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
    content_dir: content
    templates_dir: templates
    assets_dir: assets
    config_dir: config
    destination: production

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
```

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
