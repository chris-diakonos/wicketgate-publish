from pathlib import Path

from wicketgate_publish.cli import main
from wicketgate_publish.project_config import load_publisher_config


def create_project(root: Path) -> None:
    (root / "wicketgate-publish.yaml").write_text(
        "outputs:\n"
        "  site:\n"
        "    kind: static_site\n"
        "    destination: production\n"
        "\n"
        "destinations:\n"
        "  production:\n"
        "    kind: cloudflare_pages\n"
        "    project_name: example\n"
        "    branch: main\n",
        encoding="utf-8",
    )
    (root / "config").mkdir()
    (root / "content").mkdir()
    (root / "templates").mkdir()
    (root / "assets" / "css").mkdir(parents=True)

    (root / "config" / "site.yaml").write_text("title: CLI Site\n", encoding="utf-8")
    (root / "config" / "navigation.yaml").write_text(
        "- Home:\n    url: /\n",
        encoding="utf-8",
    )
    (root / "content" / "index.md").write_text(
        "---\ntitle: Home\ntemplate: page\n---\n# Home\n",
        encoding="utf-8",
    )
    (root / "templates" / "page.html").write_text(
        "<title>{{ page.title }}</title>{{ page.content_html | safe }}",
        encoding="utf-8",
    )
    (root / "assets" / "css" / "styles.css").write_text("body {}", encoding="utf-8")


def test_cli_build(tmp_path: Path, monkeypatch, capsys) -> None:
    create_project(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["build"])

    captured = capsys.readouterr()
    assert "Built site:" in captured.out
    assert (tmp_path / "generated" / "site" / "index.html").exists()

    config = load_publisher_config(tmp_path)
    assert config.outputs["site"].destination == "production"
