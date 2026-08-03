from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_NAME = "wicketgate-publish.yaml"
DEFAULT_OUTPUT_DIR = "generated"


@dataclass(frozen=True)
class DestinationConfig:
    name: str
    kind: str
    options: dict[str, Any]

    @property
    def project_name(self) -> str | None:
        value = self.options.get("project_name")
        return str(value) if value is not None else None

    @property
    def branch(self) -> str | None:
        value = self.options.get("branch")
        return str(value) if value is not None else None


@dataclass(frozen=True)
class OutputConfig:
    name: str
    kind: str
    output_subdir: str
    content_dir: str
    templates_dir: str
    assets_dir: str
    config_dir: str
    destination: str | None = None

    def resolve_output_dir(self, project_root: Path, output_root: Path) -> Path:
        return output_root / self.output_subdir

    def resolve_content_dir(self, project_root: Path) -> Path:
        return project_root / self.content_dir

    def resolve_templates_dir(self, project_root: Path) -> Path:
        return project_root / self.templates_dir

    def resolve_assets_dir(self, project_root: Path) -> Path:
        return project_root / self.assets_dir

    def resolve_config_dir(self, project_root: Path) -> Path:
        return project_root / self.config_dir


@dataclass(frozen=True)
class PublisherConfig:
    project_root: Path
    config_path: Path
    output_dir: str
    outputs: dict[str, OutputConfig]
    destinations: dict[str, DestinationConfig]

    def resolve_output_root(self, override: Path | None = None) -> Path:
        if override is not None:
            return override if override.is_absolute() else self.project_root / override
        return self.project_root / self.output_dir

    def get_destination(self, name: str) -> DestinationConfig:
        try:
            return self.destinations[name]
        except KeyError as error:
            raise KeyError(f"Unknown destination: {name}") from error


def load_publisher_config(
    project_root: Path | None = None,
    config_path: Path | None = None,
) -> PublisherConfig:
    root = (project_root or Path.cwd()).resolve()
    path = config_path or root / DEFAULT_CONFIG_NAME
    if not path.is_absolute():
        path = (root / path).resolve()

    if not path.exists():
        raise FileNotFoundError(f"Publisher config not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        raw = yaml.safe_load(file) or {}

    if not isinstance(raw, dict):
        raise ValueError("Publisher config must be a YAML mapping.")

    output_dir = str(raw.get("output_dir") or DEFAULT_OUTPUT_DIR)
    outputs = _parse_outputs(raw.get("outputs") or {})
    destinations = _parse_destinations(raw.get("destinations") or {})

    for output in outputs.values():
        if output.destination and output.destination not in destinations:
            raise ValueError(
                f"Output '{output.name}' references unknown destination "
                f"'{output.destination}'."
            )

    return PublisherConfig(
        project_root=root,
        config_path=path,
        output_dir=output_dir,
        outputs=outputs,
        destinations=destinations,
    )


def _parse_outputs(raw_outputs: Any) -> dict[str, OutputConfig]:
    if not isinstance(raw_outputs, dict):
        raise ValueError("'outputs' must be a mapping of named outputs.")

    outputs: dict[str, OutputConfig] = {}
    for name, value in raw_outputs.items():
        if not isinstance(value, dict):
            raise ValueError(f"Output '{name}' must be a mapping.")

        kind = value.get("kind")
        if not kind:
            raise ValueError(f"Output '{name}' is missing required field 'kind'.")

        outputs[str(name)] = OutputConfig(
            name=str(name),
            kind=str(kind),
            output_subdir=str(value.get("output_subdir") or name),
            content_dir=str(value.get("content_dir") or "content"),
            templates_dir=str(value.get("templates_dir") or "templates"),
            assets_dir=str(value.get("assets_dir") or "assets"),
            config_dir=str(value.get("config_dir") or "config"),
            destination=(
                str(value["destination"]) if value.get("destination") is not None else None
            ),
        )
    return outputs


def _parse_destinations(raw_destinations: Any) -> dict[str, DestinationConfig]:
    if not isinstance(raw_destinations, dict):
        raise ValueError("'destinations' must be a mapping of named destinations.")

    destinations: dict[str, DestinationConfig] = {}
    for name, value in raw_destinations.items():
        if not isinstance(value, dict):
            raise ValueError(f"Destination '{name}' must be a mapping.")

        kind = value.get("kind")
        if not kind:
            raise ValueError(f"Destination '{name}' is missing required field 'kind'.")

        options = {key: option for key, option in value.items() if key != "kind"}
        destinations[str(name)] = DestinationConfig(
            name=str(name),
            kind=str(kind),
            options=options,
        )
    return destinations
