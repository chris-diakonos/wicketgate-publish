from pathlib import Path

import pytest

from wicketgate_publish.builder import build_outputs
from wicketgate_publish.project_config import load_publisher_config
from wicketgate_publish import typst_book as typst_book_module


def create_book_project(root: Path) -> None:
    (root / "wicketgate-publish.yaml").write_text(
        "output_dir: generated\n"
        "\n"
        "outputs:\n"
        "  field_guide:\n"
        "    kind: typst_book\n"
        "    output_subdir: field-guide\n"
        "    source_dir: books/field-guide\n"
        "    manuscript_dir: books/field-guide/chapters\n"
        "    config_file: books/field-guide/book.yaml\n"
        "    typst_entry: books/field-guide/typst/main.typ\n"
        "    typst_assets_dir: books/field-guide/assets\n"
        "    output_file: field-guide.pdf\n"
        "    emit_typst: true\n",
        encoding="utf-8",
    )

    book_root = root / "books" / "field-guide"
    chapters = book_root / "chapters"
    typst = book_root / "typst"
    assets = book_root / "assets"
    chapters.mkdir(parents=True)
    typst.mkdir(parents=True)
    assets.mkdir(parents=True)

    (book_root / "book.yaml").write_text(
        "title: The Field Guide\n"
        "author: Wicketgate Systems\n"
        "subtitle: Notes on durable software practice\n"
        "\n"
        "chapters:\n"
        "  - file: 00-preface.md\n"
        "    title: Preface\n"
        "    kind: frontmatter\n"
        "  - file: 01-introduction.md\n"
        "    title: Introduction\n"
        "\n"
        "outputs:\n"
        "  pdf:\n"
        "    paper: us-letter\n"
        "    margin: 0.85in\n",
        encoding="utf-8",
    )
    (chapters / "00-preface.md").write_text(
        "---\ntitle: Preface\n---\n\nWelcome to the guide.\n",
        encoding="utf-8",
    )
    (chapters / "01-introduction.md").write_text(
        "---\ntitle: Introduction\n---\n\n"
        "# Introduction\n\n"
        "This chapter explains the basics with **emphasis**.\n\n"
        "- point one\n"
        "- point two\n",
        encoding="utf-8",
    )
    (typst / "main.typ").write_text(
        '#let book-prelude(title: "", author: "", subtitle: "") = {\n'
        "  align(center)[\n"
        '    #text(2em, weight: "bold")[#title]\n'
        '    #if subtitle != "" [\n'
        "      #v(1em)\n"
        "      #text(1.2em)[#subtitle]\n"
        "    ]\n"
        '    #if author != "" [\n'
        "      #v(2em)\n"
        "      #text(1em)[#author]\n"
        "    ]\n"
        "  ]\n"
        "  pagebreak()\n"
        "}\n",
        encoding="utf-8",
    )
    (assets / "cover.png").write_text("fake-image", encoding="utf-8")


def test_build_typst_book_writes_generated_sources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create_book_project(tmp_path)

    def fake_compile(source: Path, pdf_path: Path) -> None:
        pdf_path.write_bytes(b"%PDF-fake")

    monkeypatch.setattr(typst_book_module, "_compile_typst", fake_compile)

    config = load_publisher_config(tmp_path)
    results = build_outputs(config)

    result = results["field_guide"]
    output_dir = tmp_path / "generated" / "field-guide"

    assert result.kind == "typst_book"
    assert result.item_count == 2
    assert result.item_label == "chapter"
    assert (output_dir / "field-guide.typ").exists()
    assert (output_dir / "chapters" / "00-preface.typ").exists()
    assert (output_dir / "chapters" / "01-introduction.typ").exists()
    assert (output_dir / "typst" / "main.typ").exists()
    assert (output_dir / "assets" / "cover.png").exists()
    assert (output_dir / "field-guide.pdf").exists()

    assembled = (output_dir / "field-guide.typ").read_text(encoding="utf-8")
    assert '#import "typst/main.typ": *' in assembled
    assert '#include "chapters/00-preface.typ"' in assembled
    assert '#include "chapters/01-introduction.typ"' in assembled
    assert 'title: "The Field Guide"' in assembled

    intro = (output_dir / "chapters" / "01-introduction.typ").read_text(encoding="utf-8")
    assert intro.startswith("= Introduction")
    assert "*emphasis*" in intro
    assert "- point one" in intro
    assert intro.count("= Introduction") == 1


def test_build_typst_book_requires_typst_binary(tmp_path: Path, monkeypatch) -> None:
    create_book_project(tmp_path)
    monkeypatch.setattr(typst_book_module.shutil, "which", lambda _: None)

    config = load_publisher_config(tmp_path)

    with pytest.raises(EnvironmentError, match="typst is required"):
        build_outputs(config)


def test_build_typst_book_summary(tmp_path: Path, monkeypatch) -> None:
    create_book_project(tmp_path)
    monkeypatch.setattr(
        typst_book_module,
        "_compile_typst",
        lambda source, pdf_path: pdf_path.write_bytes(b"%PDF-fake"),
    )

    config = load_publisher_config(tmp_path)
    result = build_outputs(config)["field_guide"]

    summary = result.summary()
    assert "Built field_guide: 2 chapters ->" in summary
    assert "field-guide.pdf" in summary
