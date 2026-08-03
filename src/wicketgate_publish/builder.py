from __future__ import annotations

from pathlib import Path

from wicketgate_publish.content import Page
from wicketgate_publish.project_config import OutputConfig, PublisherConfig
from wicketgate_publish.site import build_site


def build_outputs(
    config: PublisherConfig,
    *,
    output_root: Path | None = None,
    output_names: list[str] | None = None,
) -> dict[str, list[Page]]:
    resolved_root = config.resolve_output_root(output_root)
    selected = _select_outputs(config, output_names)
    results: dict[str, list[Page]] = {}

    for name, output in selected.items():
        results[name] = build_output(config, output, resolved_root)

    return results


def build_output(
    config: PublisherConfig,
    output: OutputConfig,
    output_root: Path,
) -> list[Page]:
    if output.kind != "static_site":
        raise ValueError(f"Unsupported output kind: {output.kind}")

    return build_site(
        config.project_root,
        output_dir=output.resolve_output_dir(config.project_root, output_root),
        content_dir=output.resolve_content_dir(config.project_root),
        templates_dir=output.resolve_templates_dir(config.project_root),
        assets_dir=output.resolve_assets_dir(config.project_root),
        config_dir=output.resolve_config_dir(config.project_root),
    )


def _select_outputs(
    config: PublisherConfig,
    output_names: list[str] | None,
) -> dict[str, OutputConfig]:
    if not output_names:
        return config.outputs

    missing = [name for name in output_names if name not in config.outputs]
    if missing:
        raise KeyError(f"Unknown output(s): {', '.join(missing)}")

    return {name: config.outputs[name] for name in output_names}
