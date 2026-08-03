from pathlib import Path
import shutil


def copy_assets(source: Path, destination: Path) -> None:
    """Copy static assets into the generated site."""
    if not source.exists():
        return

    if destination.exists():
        shutil.rmtree(destination)

    shutil.copytree(source, destination)
