from __future__ import annotations

import argparse
import sys
from pathlib import Path

from wicketgate_publish.builder import build_outputs
from wicketgate_publish.project_config import DEFAULT_CONFIG_NAME, load_publisher_config
from wicketgate_publish.publish import describe_destination, publish_outputs


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="wicketgate-publish",
        description="Build and publish configured outputs for Wicketgate projects.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help=f"Path to publisher config (default: ./{DEFAULT_CONFIG_NAME})",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Project root directory (default: current working directory)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build configured outputs")
    build_parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Override the main output directory (default: generated/)",
    )
    build_parser.add_argument(
        "outputs",
        nargs="*",
        help="Optional output names to build (default: all)",
    )

    publish_parser = subparsers.add_parser(
        "publish",
        help="Publish previously built outputs to configured destinations",
    )
    publish_parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Override the main output directory (default: generated/)",
    )
    publish_parser.add_argument(
        "outputs",
        nargs="*",
        help="Optional output names to publish (default: all with destinations)",
    )
    publish_parser.add_argument(
        "--build",
        action="store_true",
        help="Build outputs before publishing",
    )

    args = parser.parse_args(argv)
    project_root = (args.project_root or Path.cwd()).resolve()

    try:
        config = load_publisher_config(project_root, args.config)
    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(str(error)) from error

    if args.command == "build":
        _run_build(config, args.output_dir, args.outputs or None)
        return

    if args.command == "publish":
        if args.build:
            _run_build(config, args.output_dir, args.outputs or None)
        _run_publish(config, args.output_dir, args.outputs or None)
        return

    raise SystemExit(f"Unknown command: {args.command}")


def _run_build(config, output_dir: Path | None, outputs: list[str] | None) -> None:
    try:
        results = build_outputs(config, output_root=output_dir, output_names=outputs)
    except (KeyError, ValueError, FileNotFoundError, EnvironmentError, RuntimeError) as error:
        raise SystemExit(str(error)) from error

    for result in results.values():
        print(result.summary())


def _run_publish(config, output_dir: Path | None, outputs: list[str] | None) -> None:
    try:
        published = publish_outputs(
            config,
            output_root=output_dir,
            output_names=outputs,
        )
    except (KeyError, ValueError, FileNotFoundError, EnvironmentError, RuntimeError) as error:
        raise SystemExit(str(error)) from error

    for name in published:
        output = config.outputs[name]
        destination = config.get_destination(output.destination)  # type: ignore[arg-type]
        print(f"Published {describe_destination(destination, output)}")


if __name__ == "__main__":
    main(sys.argv[1:])
