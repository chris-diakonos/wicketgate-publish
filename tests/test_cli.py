from pathlib import Path

from wicketgate_publish.cli import main
from wicketgate_publish.project_config import load_publisher_config
from wicketgate_publish import typst_book as typst_book_module


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


def create_book_project(root: Path) -> None:
    (root / "wicketgate-publish.yaml").write_text(
        "outputs:\n"
        "  field_guide:\n"
        "    kind: typst_book\n"
        "    source_dir: books/field-guide\n"
        "    output_file: field-guide.pdf\n",
        encoding="utf-8",
    )
    book_root = root / "books" / "field-guide"
    chapters = book_root / "chapters"
    typst = book_root / "typst"
    chapters.mkdir(parents=True)
    typst.mkdir(parents=True)
    (book_root / "book.yaml").write_text(
        "title: Field Guide\n"
        "chapters:\n"
        "  - file: 01-introduction.md\n"
        "    title: Introduction\n",
        encoding="utf-8",
    )
    (chapters / "01-introduction.md").write_text(
        "---\ntitle: Introduction\n---\n\nHello book.\n",
        encoding="utf-8",
    )
    (typst / "main.typ").write_text(
        '#let book-prelude(title: "", author: "", subtitle: "") = []\n',
        encoding="utf-8",
    )


def test_cli_build(tmp_path: Path, monkeypatch, capsys) -> None:
    create_project(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["build"])

    captured = capsys.readouterr()
    assert "Built site:" in captured.out
    assert (tmp_path / "generated" / "site" / "index.html").exists()

    config = load_publisher_config(tmp_path)
    assert config.outputs["site"].destination == "production"


def test_cli_build_typst_book(tmp_path: Path, monkeypatch, capsys) -> None:
    create_book_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        typst_book_module,
        "_compile_typst",
        lambda source, pdf_path: pdf_path.write_bytes(b"%PDF-fake"),
    )

    main(["build", "field_guide"])

    captured = capsys.readouterr()
    assert "Built field_guide: 1 chapter ->" in captured.out
    assert "field-guide.pdf" in captured.out
    assert (tmp_path / "generated" / "field_guide" / "field-guide.pdf").exists()
