from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ChapterSpec:
    file: str
    title: str | None = None
    kind: str = "chapter"
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class BookConfig:
    title: str
    author: str = ""
    subtitle: str = ""
    language: str = "en"
    chapters: list[ChapterSpec] | None = None
    outputs: dict[str, Any] | None = None
    raw: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "chapters", self.chapters or [])
        object.__setattr__(self, "outputs", self.outputs or {})
        object.__setattr__(self, "raw", self.raw or {})


def load_book_config(path: Path) -> BookConfig:
    if not path.exists():
        raise FileNotFoundError(f"Book config not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        raw = yaml.safe_load(file) or {}

    if not isinstance(raw, dict):
        raise ValueError("Book config must be a YAML mapping.")

    title = raw.get("title")
    if not title:
        raise ValueError("Book config is missing required field 'title'.")

    chapters = [_parse_chapter(item, index) for index, item in enumerate(raw.get("chapters") or [])]
    if not chapters:
        raise ValueError("Book config must declare at least one chapter.")

    outputs = raw.get("outputs") or {}
    if not isinstance(outputs, dict):
        raise ValueError("'outputs' in book config must be a mapping.")

    return BookConfig(
        title=str(title),
        author=str(raw.get("author") or ""),
        subtitle=str(raw.get("subtitle") or ""),
        language=str(raw.get("language") or "en"),
        chapters=chapters,
        outputs=outputs,
        raw=raw,
    )


def _parse_chapter(item: Any, index: int) -> ChapterSpec:
    if isinstance(item, str):
        return ChapterSpec(file=item)

    if not isinstance(item, dict):
        raise ValueError(
            f"Chapter entry {index} must be a filename string or mapping, got {item!r}."
        )

    file_name = item.get("file")
    if not file_name:
        raise ValueError(f"Chapter entry {index} is missing required field 'file'.")

    known = {"file", "title", "kind"}
    metadata = {key: value for key, value in item.items() if key not in known}

    return ChapterSpec(
        file=str(file_name),
        title=str(item["title"]) if item.get("title") is not None else None,
        kind=str(item.get("kind") or "chapter"),
        metadata=metadata or None,
    )


def resolve_chapter_path(manuscript_dir: Path, chapter: ChapterSpec) -> Path:
    path = manuscript_dir / chapter.file
    if not path.exists():
        raise FileNotFoundError(f"Chapter file not found: {path}")
    return path
