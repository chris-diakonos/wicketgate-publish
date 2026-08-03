from dataclasses import dataclass
from pathlib import Path
from typing import Any

import markdown
import yaml


@dataclass(frozen=True)
class Page:
    source_path: Path
    output_path: Path
    url: str
    title: str
    description: str
    template: str
    nav_title: str
    content_html: str
    metadata: dict[str, Any]


def discover_pages(content_dir: Path, output_dir: Path) -> list[Page]:
    pages = [
        load_page(path, content_dir, output_dir)
        for path in sorted(content_dir.rglob("*.md"))
    ]
    return pages


def load_page(path: Path, content_dir: Path, output_dir: Path) -> Page:
    metadata, body = parse_markdown_file(path)
    relative = path.relative_to(content_dir)
    url = page_url(relative, metadata.get("slug"))
    html = render_markdown(body)
    title = metadata.get("title") or title_from_path(path)

    return Page(
        source_path=path,
        output_path=output_path_for_url(output_dir, url),
        url=url,
        title=title,
        description=metadata.get("description", ""),
        template=metadata.get("template", "page"),
        nav_title=metadata.get("nav_title", title),
        content_html=html,
        metadata=metadata,
    )


def parse_markdown_file(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    return split_front_matter(text)


def split_front_matter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text

    _, front_matter, body = text.split("---", 2)
    metadata = yaml.safe_load(front_matter) or {}
    if not isinstance(metadata, dict):
        raise ValueError("Front matter must be a YAML mapping.")
    return metadata, body.lstrip()


def render_markdown(text: str) -> str:
    renderer = markdown.Markdown(extensions=["extra", "fenced_code", "tables"])
    return renderer.convert(text)


def page_url(relative_path: Path, slug: str | None = None) -> str:
    if slug:
        normalized = slug.strip("/")
        return "/" if not normalized else f"/{normalized}/"

    if relative_path.name == "index.md":
        parent = relative_path.parent.as_posix()
        return "/" if parent == "." else f"/{parent}/"

    without_suffix = relative_path.with_suffix("").as_posix()
    return f"/{without_suffix}/"


def output_path_for_url(output_dir: Path, url: str) -> Path:
    if url == "/":
        return output_dir / "index.html"
    return output_dir / url.strip("/") / "index.html"


def title_from_path(path: Path) -> str:
    return path.stem.replace("-", " ").replace("_", " ").title()
