from pathlib import Path

from wicketgate_publish.site_config import load_navigation, load_site_config


def test_load_site_config(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "site.yaml").write_text(
        "title: Wicketgate Systems\n"
        "tagline: Systems that endure\n",
        encoding="utf-8",
    )

    config = load_site_config(config_dir)

    assert config["title"] == "Wicketgate Systems"
    assert config["tagline"] == "Systems that endure"


def test_load_navigation_normalizes_yaml_shape(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "navigation.yaml").write_text(
        "- Home:\n"
        "    url: /\n"
        "- Services:\n"
        "    url: /services/\n"
        "- Contact\n",
        encoding="utf-8",
    )

    navigation = load_navigation(config_dir)

    assert navigation == [
        {"title": "Home", "url": "/", "children": []},
        {"title": "Services", "url": "/services/", "children": []},
        {"title": "Contact", "url": "/contact/", "children": []},
    ]
