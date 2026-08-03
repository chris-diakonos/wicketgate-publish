from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from wicketgate_publish.project_config import DestinationConfig, OutputConfig, PublisherConfig


def publish_outputs(
    config: PublisherConfig,
    *,
    output_root: Path | None = None,
    output_names: list[str] | None = None,
) -> list[str]:
    resolved_root = config.resolve_output_root(output_root)
    selected = config.outputs if not output_names else {
        name: config.outputs[name] for name in output_names
    }

    missing = [name for name in (output_names or []) if name not in config.outputs]
    if missing:
        raise KeyError(f"Unknown output(s): {', '.join(missing)}")

    published: list[str] = []
    for name, output in selected.items():
        if not output.destination:
            raise ValueError(f"Output '{name}' does not declare a destination.")

        destination = config.get_destination(output.destination)
        target_dir = output.resolve_output_dir(config.project_root, resolved_root)
        if not target_dir.exists():
            raise FileNotFoundError(
                f"Output '{name}' has not been built yet: {target_dir}"
            )

        publish_destination(destination, target_dir)
        published.append(name)

    return published


def publish_destination(destination: DestinationConfig, output_dir: Path) -> None:
    if destination.kind == "cloudflare_pages":
        publish_cloudflare_pages(destination, output_dir)
        return

    raise ValueError(f"Unsupported destination kind: {destination.kind}")


def publish_cloudflare_pages(destination: DestinationConfig, output_dir: Path) -> None:
    project_name = destination.project_name
    if not project_name:
        raise ValueError(
            f"Destination '{destination.name}' requires 'project_name' for "
            "cloudflare_pages."
        )

    if not os.environ.get("CLOUDFLARE_API_TOKEN"):
        raise EnvironmentError(
            "CLOUDFLARE_API_TOKEN is required to publish to Cloudflare Pages."
        )
    if not os.environ.get("CLOUDFLARE_ACCOUNT_ID"):
        raise EnvironmentError(
            "CLOUDFLARE_ACCOUNT_ID is required to publish to Cloudflare Pages."
        )

    wrangler = shutil.which("wrangler")
    if wrangler is None:
        raise EnvironmentError(
            "wrangler is required to publish to Cloudflare Pages. "
            "Install it or run publish from an environment that provides it."
        )

    command = [
        wrangler,
        "pages",
        "deploy",
        str(output_dir),
        f"--project-name={project_name}",
    ]
    if destination.branch:
        command.append(f"--branch={destination.branch}")

    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            f"Cloudflare Pages deploy failed with exit code {completed.returncode}."
        )


def describe_destination(destination: DestinationConfig, output: OutputConfig) -> str:
    if destination.kind == "cloudflare_pages":
        project = destination.project_name or "(missing project_name)"
        branch = destination.branch or "(default)"
        return (
            f"{output.name} -> cloudflare_pages "
            f"project={project} branch={branch}"
        )
    return f"{output.name} -> {destination.kind}"
