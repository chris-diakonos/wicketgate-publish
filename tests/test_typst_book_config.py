from pathlib import Path

import pytest

from wicketgate_publish.book_config import load_book_config, resolve_chapter_path


def write_book_config(path: Path) -> None:
    path.write_text(
        "title: The Field Guide\n"
        "author: Wicketgate Systems\n"
        "subtitle: Notes on durable software practice\n"
        "language: en\n"
        "\n"
        "chapters:\n"
        "  - file: 00-preface.md\n"
        "    title: Preface\n"
        "    kind: frontmatter\n"
        "  - file: 01-introduction.md\n"
        "    title: Introduction\n"
        "  - 02-foundations.md\n"
        "\n"
        "outputs:\n"
        "  pdf:\n"
        "    format: pdf\n"
        "    paper: us-letter\n"
        "    margin: 0.85in\n",
        encoding="utf-8",
    )


def test_load_book_config(tmp_path: Path) -> None:
    config_path = tmp_path / "book.yaml"
    write_book_config(config_path)

    book = load_book_config(config_path)

    assert book.title == "The Field Guide"
    assert book.author == "Wicketgate Systems"
    assert book.subtitle == "Notes on durable software practice"
    assert book.language == "en"
    assert len(book.chapters) == 3
    assert book.chapters[0].file == "00-preface.md"
    assert book.chapters[0].title == "Preface"
    assert book.chapters[0].kind == "frontmatter"
    assert book.chapters[2].file == "02-foundations.md"
    assert book.chapters[2].title is None
    assert book.outputs["pdf"]["paper"] == "us-letter"


def test_load_book_config_requires_title(tmp_path: Path) -> None:
    path = tmp_path / "book.yaml"
    path.write_text("chapters:\n  - file: 01.md\n", encoding="utf-8")

    with pytest.raises(ValueError, match="title"):
        load_book_config(path)


def test_load_book_config_requires_chapters(tmp_path: Path) -> None:
    path = tmp_path / "book.yaml"
    path.write_text("title: Empty Book\nchapters: []\n", encoding="utf-8")

    with pytest.raises(ValueError, match="at least one chapter"):
        load_book_config(path)


def test_load_book_config_rejects_chapter_without_file(tmp_path: Path) -> None:
    path = tmp_path / "book.yaml"
    path.write_text(
        "title: Broken\nchapters:\n  - title: Missing file\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing required field 'file'"):
        load_book_config(path)


def test_resolve_chapter_path(tmp_path: Path) -> None:
    manuscript = tmp_path / "chapters"
    manuscript.mkdir()
    chapter_file = manuscript / "01-introduction.md"
    chapter_file.write_text("# Intro\n", encoding="utf-8")
    write_book_config(tmp_path / "book.yaml")
    book = load_book_config(tmp_path / "book.yaml")

    resolved = resolve_chapter_path(manuscript, book.chapters[1])
    assert resolved == chapter_file


def test_resolve_chapter_path_missing(tmp_path: Path) -> None:
    write_book_config(tmp_path / "book.yaml")
    book = load_book_config(tmp_path / "book.yaml")

    with pytest.raises(FileNotFoundError, match="Chapter file not found"):
        resolve_chapter_path(tmp_path / "chapters", book.chapters[0])
