from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from wicketgate_publish.book_config import (
    BookConfig,
    ChapterSpec,
    load_book_config,
    resolve_chapter_path,
)
from wicketgate_publish.builder import BuildResult
from wicketgate_publish.content import parse_markdown_file, title_from_path
from wicketgate_publish.markdown_to_typst import markdown_to_typst, write_text
from wicketgate_publish.project_config import OutputConfig, PublisherConfig


@dataclass(frozen=True)
class ChapterDocument:
    spec: ChapterSpec
    source_path: Path
    title: str
    body_markdown: str
    body_typst: str
    metadata: dict[str, Any]
    output_path: Path


def build_typst_book(
    config: PublisherConfig,
    output: OutputConfig,
    output_root: Path,
) -> BuildResult:
    project_root = config.project_root
    source_dir = output.resolve_source_dir(project_root)
    manuscript_dir = output.resolve_manuscript_dir(project_root)
    config_file = output.resolve_config_file(project_root)
    typst_entry = output.resolve_typst_entry(project_root)
    assets_dir = output.resolve_typst_assets_dir(project_root)
    output_dir = output.resolve_output_dir(project_root, output_root)

    book = load_book_config(config_file)
    if not source_dir.exists():
        raise FileNotFoundError(f"Book source directory not found: {source_dir}")
    if not manuscript_dir.exists():
        raise FileNotFoundError(f"Manuscript directory not found: {manuscript_dir}")
    if not typst_entry.exists():
        raise FileNotFoundError(f"Typst entry file not found: {typst_entry}")

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    chapters = [
        _load_chapter(chapter, manuscript_dir, output_dir / "chapters")
        for chapter in book.chapters or []
    ]

    for chapter in chapters:
        write_text(chapter.output_path, _chapter_typst(chapter))

    if assets_dir.exists():
        shutil.copytree(assets_dir, output_dir / "assets")

    typst_dir = output_dir / "typst"
    typst_dir.mkdir(parents=True, exist_ok=True)
    for path in typst_entry.parent.rglob("*"):
        if path.is_file():
            relative = path.relative_to(typst_entry.parent)
            target = typst_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)

    assembled = _assemble_book_typst(book, chapters, typst_entry.name)
    book_typst_name = f"{_slugify(output.output_subdir)}.typ"
    book_typst_path = output_dir / book_typst_name
    write_text(book_typst_path, assembled)

    artifacts: list[Path] = []
    if output.emit_typst:
        artifacts.append(book_typst_path)

    pdf_path = output_dir / output.output_file
    _compile_typst(book_typst_path, pdf_path)
    artifacts.insert(0, pdf_path)

    return BuildResult(
        name=output.name,
        kind=output.kind,
        output_dir=output_dir,
        item_count=len(chapters),
        item_label="chapter",
        artifacts=artifacts,
        details={"book": book, "chapters": chapters, "pdf": pdf_path},
    )


def _load_chapter(
    spec: ChapterSpec,
    manuscript_dir: Path,
    chapters_output: Path,
) -> ChapterDocument:
    source_path = resolve_chapter_path(manuscript_dir, spec)
    metadata, body = parse_markdown_file(source_path)
    title = spec.title or metadata.get("title") or title_from_path(source_path)
    body = _strip_leading_title(body, title)
    body_typst = markdown_to_typst(body)
    stem = Path(spec.file).stem
    output_path = chapters_output / f"{stem}.typ"
    merged_metadata = dict(metadata)
    if spec.metadata:
        merged_metadata.update(spec.metadata)
    return ChapterDocument(
        spec=spec,
        source_path=source_path,
        title=title,
        body_markdown=body,
        body_typst=body_typst,
        metadata=merged_metadata,
        output_path=output_path,
    )


def _strip_leading_title(body: str, title: str) -> str:
    lines = body.splitlines()
    index = 0
    while index < len(lines) and not lines[index].strip():
        index += 1
    if index >= len(lines):
        return body
    heading = lines[index].strip()
    if heading.startswith("#") and heading.lstrip("#").strip() == title:
        remaining = lines[index + 1 :]
        while remaining and not remaining[0].strip():
            remaining = remaining[1:]
        return "\n".join(remaining)
    return body


def _chapter_typst(chapter: ChapterDocument) -> str:
    if chapter.spec.kind == "frontmatter":
        heading = f"#heading(outlined: false)[{_escape_typst_text(chapter.title)}]\n\n"
    else:
        heading = f"= {_escape_typst_text(chapter.title)}\n\n"
    # Weak breaks skip when already at the top of a page (e.g. after book-prelude).
    return f"#pagebreak(weak: true)\n\n{heading}{chapter.body_typst}"

def _assemble_book_typst(
    book: BookConfig,
    chapters: list[ChapterDocument],
    entry_name: str,
) -> str:
    includes = "\n".join(
        f'#include "chapters/{chapter.output_path.name}"'
        for chapter in chapters
    )
    pdf_options = (book.outputs or {}).get("pdf") or {}
    paper = pdf_options.get("paper", "us-letter")
    margin = pdf_options.get("margin", "0.85in")

    return (
        f'// Generated by wicketgate-publish\n'
        f'#import "typst/{entry_name}": *\n\n'
        f'#set document(title: "{_escape_string(book.title)}"'
        f'{_optional_author(book.author)})\n'
        f'#set page(paper: "{_escape_string(str(paper))}", margin: {_typst_length(margin)})\n'
        f'#set text(lang: "{_escape_string(book.language)}")\n\n'
        f'#book-prelude(\n'
        f'  title: "{_escape_string(book.title)}",\n'
        f'  author: "{_escape_string(book.author)}",\n'
        f'  subtitle: "{_escape_string(book.subtitle)}",\n'
        f')\n\n'
        f"{includes}\n"
    )


def _optional_author(author: str) -> str:
    if not author:
        return ""
    return f', author: "{_escape_string(author)}"'


def _typst_length(value: Any) -> str:
    text = str(value).strip()
    if text.endswith(("pt", "mm", "cm", "in", "em", "%")):
        return text
    return f'"{_escape_string(text)}"'


def _compile_typst(source: Path, pdf_path: Path) -> None:
    typst = shutil.which("typst")
    if typst is None:
        raise EnvironmentError(
            "typst is required to build typst_book outputs. "
            "Install the Typst CLI or make it available on PATH."
        )

    completed = subprocess.run(
        [typst, "compile", str(source), str(pdf_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        message = f"Typst compile failed with exit code {completed.returncode}."
        if detail:
            message = f"{message}\n{detail}"
        raise RuntimeError(message)


def _slugify(value: str) -> str:
    return value.strip().replace(" ", "-")


def _escape_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _escape_typst_text(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("#", "\\#")
        .replace("@", "\\@")
        .replace("$", "\\$")
        .replace("<", "\\<")
        .replace(">", "\\>")
    )
