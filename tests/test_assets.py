from pathlib import Path

from wicketgate_publish.assets import copy_assets


def test_copy_assets_replaces_destination(tmp_path: Path) -> None:
    source = tmp_path / "assets"
    destination = tmp_path / "generated" / "site" / "assets"
    (source / "css").mkdir(parents=True)
    (destination / "old").mkdir(parents=True)
    (source / "css" / "styles.css").write_text("body {}", encoding="utf-8")
    (destination / "old" / "stale.txt").write_text("old", encoding="utf-8")

    copy_assets(source, destination)

    assert (destination / "css" / "styles.css").read_text(encoding="utf-8") == "body {}"
    assert not (destination / "old" / "stale.txt").exists()
