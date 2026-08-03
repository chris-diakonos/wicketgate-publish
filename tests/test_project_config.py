from pathlib import Path

import pytest

from wicketgate_publish.builder import build_outputs
from wicketgate_publish.project_config import load_publisher_config


def write_config(root: Path) -> Path:
    path = root / "wicketgate-publish.yaml"
    path.write_text(
        "output_dir: generated\n"
        "\n"
        "outputs:\n"
        "  site:\n"
        "    kind: static_site\n"
        "    output_subdir: site\n"
        "    content_dir: content\n"
        "    templates_dir: templates\n"
        "    assets_dir: assets\n"
        "    config_dir: config\n"
        "    destination: production\n"
        "\n"
        "destinations:\n"
        "  production:\n"
        "    kind: cloudflare_pages\n"
        "    project_name: wicketgate-systems\n"
        "    branch: main\n",
        encoding="utf-8",
    )
    return path


def create_project(root: Path) -> None:
    write_config(root)
    (root / "config").mkdir()
    (root / "content").mkdir()
    (root / "templates" / "partials").mkdir(parents=True)
    (root / "assets" / "css").mkdir(parents=True)

    (root / "config" / "site.yaml").write_text(
        "title: Test Site\ncopyright: 2026 Test Site\n",
        encoding="utf-8",
    )
    (root / "config" / "navigation.yaml").write_text(
        "- Home:\n    url: /\n",
        encoding="utf-8",
    )
    (root / "content" / "index.md").write_text(
        "---\ntitle: Home\ntemplate: home\n---\n# Home\n",
        encoding="utf-8",
    )
    (root / "templates" / "base.html").write_text(
        "<title>{{ page.title }} | {{ site.title }}</title>\n"
        "{% block content %}{% endblock %}\n",
        encoding="utf-8",
    )
    (root / "templates" / "home.html").write_text(
        '{% extends "base.html" %}{% block content %}{{ page.content_html | safe }}{% endblock %}',
        encoding="utf-8",
    )
    (root / "assets" / "css" / "styles.css").write_text("body {}", encoding="utf-8")


def test_load_publisher_config(tmp_path: Path) -> None:
    write_config(tmp_path)

    config = load_publisher_config(tmp_path)

    assert config.output_dir == "generated"
    assert set(config.outputs) == {"site"}
    assert config.outputs["site"].kind == "static_site"
    assert config.outputs["site"].output_subdir == "site"
    assert config.outputs["site"].destination == "production"
    assert config.destinations["production"].kind == "cloudflare_pages"
    assert config.destinations["production"].project_name == "wicketgate-systems"


def test_load_publisher_config_defaults_output_subdir_to_name(tmp_path: Path) -> None:
    (tmp_path / "wicketgate-publish.yaml").write_text(
        "outputs:\n"
        "  docs:\n"
        "    kind: static_site\n",
        encoding="utf-8",
    )

    config = load_publisher_config(tmp_path)

    assert config.output_dir == "generated"
    assert config.outputs["docs"].output_subdir == "docs"


def test_load_publisher_config_rejects_unknown_destination(tmp_path: Path) -> None:
    (tmp_path / "wicketgate-publish.yaml").write_text(
        "outputs:\n"
        "  site:\n"
        "    kind: static_site\n"
        "    destination: missing\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unknown destination"):
        load_publisher_config(tmp_path)


def test_build_outputs_writes_under_generated(tmp_path: Path) -> None:
    create_project(tmp_path)
    config = load_publisher_config(tmp_path)

    results = build_outputs(config)

    assert set(results) == {"site"}
    assert (tmp_path / "generated" / "site" / "index.html").exists()
    assert (tmp_path / "generated" / "site" / "assets" / "css" / "styles.css").exists()
