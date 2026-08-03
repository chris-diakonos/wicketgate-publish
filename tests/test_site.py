from pathlib import Path

from wicketgate_publish.site import build_site


def test_build_site_generates_pages_and_assets(tmp_path: Path) -> None:
    create_project(tmp_path)

    pages = build_site(tmp_path)

    assert {page.url for page in pages} == {"/", "/about/"}
    assert (tmp_path / "generated" / "site" / "index.html").exists()
    assert (tmp_path / "generated" / "site" / "about" / "index.html").exists()
    assert (tmp_path / "generated" / "site" / "assets" / "css" / "styles.css").exists()
    assert (tmp_path / "generated" / "site" / "assets" / "logos" / "gate-hero.svg").exists()

    home_html = (tmp_path / "generated" / "site" / "index.html").read_text(encoding="utf-8")
    about_html = (tmp_path / "generated" / "site" / "about" / "index.html").read_text(
        encoding="utf-8"
    )

    assert "<title>Home | Test Site</title>" in home_html
    assert '<link rel="stylesheet" href="/assets/css/styles.css">' in home_html
    assert '<a href="/about/">About</a>' in home_html
    assert "<h1>About</h1>" in about_html


def create_project(root: Path) -> None:
    (root / "config").mkdir()
    (root / "content").mkdir()
    (root / "templates" / "partials").mkdir(parents=True)
    (root / "assets" / "css").mkdir(parents=True)
    (root / "assets" / "logos").mkdir(parents=True)

    (root / "config" / "site.yaml").write_text(
        "title: Test Site\n"
        "tagline: Test tagline\n"
        "copyright: 2026 Test Site\n",
        encoding="utf-8",
    )
    (root / "config" / "navigation.yaml").write_text(
        "- Home:\n"
        "    url: /\n"
        "- About:\n"
        "    url: /about/\n",
        encoding="utf-8",
    )
    (root / "content" / "index.md").write_text(
        "---\n"
        "title: Home\n"
        "template: home\n"
        "---\n"
        "# Home\n",
        encoding="utf-8",
    )
    (root / "content" / "about.md").write_text(
        "---\n"
        "title: About\n"
        "template: page\n"
        "---\n"
        "# About\n",
        encoding="utf-8",
    )
    (root / "templates" / "base.html").write_text(
        "<title>{{ page.title }} | {{ site.title }}</title>\n"
        '<link rel="stylesheet" href="{{ asset("css/styles.css") }}">\n'
        '{% include "partials/navigation.html" %}\n'
        "{% block content %}{% endblock %}\n",
        encoding="utf-8",
    )
    (root / "templates" / "home.html").write_text(
        '{% extends "base.html" %}{% block content %}{{ page.content_html | safe }}{% endblock %}',
        encoding="utf-8",
    )
    (root / "templates" / "page.html").write_text(
        '{% extends "base.html" %}{% block content %}{{ page.content_html | safe }}{% endblock %}',
        encoding="utf-8",
    )
    (root / "templates" / "partials" / "navigation.html").write_text(
        '{% for item in navigation %}<a href="{{ item.url }}"{% if item.url == page.url %} aria-current="page"{% endif %}>{{ item.title }}</a>{% endfor %}',
        encoding="utf-8",
    )
    (root / "assets" / "css" / "styles.css").write_text("body {}", encoding="utf-8")
    (root / "assets" / "logos" / "gate-hero.svg").write_text("<svg></svg>", encoding="utf-8")
