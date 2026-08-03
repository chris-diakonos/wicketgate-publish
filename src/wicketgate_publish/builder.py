from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from wicketgate_publish.project_config import OutputConfig, PublisherConfig


@dataclass(frozen=True)
class BuildResult:
    name: str
    kind: str
    output_dir: Path
    item_count: int
    item_label: str = "item"
    artifacts: list[Path] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        label = self.item_label if self.item_count == 1 else f"{self.item_label}s"
        primary = self.artifacts[0] if self.artifacts else self.output_dir
        return f"Built {self.name}: {self.item_count} {label} -> {primary}"


Generator = Callable[[PublisherConfig, OutputConfig, Path], BuildResult]


def build_site_output(
    config: PublisherConfig,
    output: OutputConfig,
    output_root: Path,
) -> BuildResult:
    from wicketgate_publish.site import build_site

    output_dir = output.resolve_output_dir(config.project_root, output_root)
    pages = build_site(
        config.project_root,
        output_dir=output_dir,
        content_dir=output.resolve_content_dir(config.project_root),
        templates_dir=output.resolve_templates_dir(config.project_root),
        assets_dir=output.resolve_assets_dir(config.project_root),
        config_dir=output.resolve_config_dir(config.project_root),
    )
    return BuildResult(
        name=output.name,
        kind=output.kind,
        output_dir=output_dir,
        item_count=len(pages),
        item_label="page",
        artifacts=[output_dir],
        details={"pages": pages},
    )


def build_typst_book_output(
    config: PublisherConfig,
    output: OutputConfig,
    output_root: Path,
) -> BuildResult:
    from wicketgate_publish.typst_book import build_typst_book

    return build_typst_book(config, output, output_root)


GENERATORS: dict[str, Generator] = {
    "static_site": build_site_output,
    "typst_book": build_typst_book_output,
}


def build_outputs(
    config: PublisherConfig,
    *,
    output_root: Path | None = None,
    output_names: list[str] | None = None,
) -> dict[str, BuildResult]:
    resolved_root = config.resolve_output_root(output_root)
    selected = _select_outputs(config, output_names)
    results: dict[str, BuildResult] = {}

    for name, output in selected.items():
        results[name] = build_output(config, output, resolved_root)

    return results


def build_output(
    config: PublisherConfig,
    output: OutputConfig,
    output_root: Path,
) -> BuildResult:
    generator = GENERATORS.get(output.kind)
    if generator is None:
        raise ValueError(f"Unsupported output kind: {output.kind}")
    return generator(config, output, output_root)


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
