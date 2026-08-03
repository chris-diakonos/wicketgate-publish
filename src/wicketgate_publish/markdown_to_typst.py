from __future__ import annotations

import re
from pathlib import Path


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
UNORDERED_RE = re.compile(r"^(\s*)([-*+])\s+(.*)$")
ORDERED_RE = re.compile(r"^(\s*)(\d+)[.)]\s+(.*)$")
FENCE_RE = re.compile(r"^```(\w+)?\s*$")
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*|__(.+?)__")
ITALIC_RE = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)|(?<!_)_(?!_)(.+?)(?<!_)_(?!_)")
CODE_RE = re.compile(r"`([^`]+)`")


def markdown_to_typst(text: str) -> str:
    """Convert a conservative Markdown subset to Typst markup."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks: list[str] = []
    paragraph: list[str] = []
    list_items: list[tuple[str, str]] = []
    in_code = False
    code_lang = ""
    code_lines: list[str] = []
    in_quote = False
    quote_lines: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if not paragraph:
            return
        body = " ".join(line.strip() for line in paragraph if line.strip())
        if body:
            blocks.append(inline_to_typst(body))
        paragraph = []

    def flush_list() -> None:
        nonlocal list_items
        if not list_items:
            return
        ordered = list_items[0][0] == "ordered"
        rendered = []
        for kind, item in list_items:
            marker = "+" if kind == "ordered" or ordered else "-"
            rendered.append(f"{marker} {inline_to_typst(item)}")
        blocks.append("\n".join(rendered))
        list_items = []

    def flush_quote() -> None:
        nonlocal quote_lines, in_quote
        if not quote_lines:
            in_quote = False
            return
        body = " ".join(line.strip() for line in quote_lines if line.strip())
        blocks.append(f"#quote[{inline_to_typst(body)}]")
        quote_lines = []
        in_quote = False

    for raw_line in lines:
        if in_code:
            if FENCE_RE.match(raw_line):
                lang = f'lang: "{code_lang}"' if code_lang else ""
                code_body = "\n".join(code_lines)
                if lang:
                    blocks.append(f"```{code_lang}\n{code_body}\n```")
                else:
                    blocks.append(f"```\n{code_body}\n```")
                in_code = False
                code_lang = ""
                code_lines = []
            else:
                code_lines.append(raw_line)
            continue

        fence = FENCE_RE.match(raw_line)
        if fence:
            flush_paragraph()
            flush_list()
            flush_quote()
            in_code = True
            code_lang = fence.group(1) or ""
            code_lines = []
            continue

        if not raw_line.strip():
            flush_paragraph()
            flush_list()
            flush_quote()
            continue

        if raw_line.startswith(">"):
            flush_paragraph()
            flush_list()
            in_quote = True
            quote_lines.append(raw_line.lstrip("> ").rstrip())
            continue
        if in_quote:
            flush_quote()

        heading = HEADING_RE.match(raw_line)
        if heading:
            flush_paragraph()
            flush_list()
            level = len(heading.group(1))
            title = inline_to_typst(heading.group(2).strip())
            if level == 1:
                blocks.append(f"= {title}")
            elif level == 2:
                blocks.append(f"== {title}")
            elif level == 3:
                blocks.append(f"=== {title}")
            else:
                blocks.append(f"{'=' * min(level, 4)} {title}")
            continue

        unordered = UNORDERED_RE.match(raw_line)
        if unordered:
            flush_paragraph()
            flush_quote()
            list_items.append(("unordered", unordered.group(3).strip()))
            continue

        ordered = ORDERED_RE.match(raw_line)
        if ordered:
            flush_paragraph()
            flush_quote()
            list_items.append(("ordered", ordered.group(3).strip()))
            continue

        if list_items:
            flush_list()
        paragraph.append(raw_line.strip())

    flush_paragraph()
    flush_list()
    flush_quote()
    if in_code:
        code_body = "\n".join(code_lines)
        blocks.append(f"```\n{code_body}\n```")

    return "\n\n".join(blocks).strip() + ("\n" if blocks else "")


def inline_to_typst(text: str) -> str:
    placeholders: list[str] = []

    def stash(value: str) -> str:
        placeholders.append(value)
        return f"\x00{len(placeholders) - 1}\x00"

    text = IMAGE_RE.sub(
        lambda match: stash(_image(match.group(1), match.group(2))),
        text,
    )
    text = LINK_RE.sub(
        lambda match: stash(
            f'#link("{_escape_string(match.group(2))}")[{_escape_text(match.group(1))}]'
        ),
        text,
    )
    text = BOLD_RE.sub(
        lambda match: stash(f"*{_escape_text(match.group(1) or match.group(2))}*"),
        text,
    )
    text = CODE_RE.sub(
        lambda match: stash(f"`{_escape_text(match.group(1))}`"),
        text,
    )
    text = ITALIC_RE.sub(
        lambda match: stash(f"_{_escape_text(match.group(1) or match.group(2))}_"),
        text,
    )
    text = _escape_text(text)
    for index, placeholder in enumerate(placeholders):
        text = text.replace(f"\x00{index}\x00", placeholder)
    return text


def _image(alt: str, src: str) -> str:
    alt_text = _escape_string(alt) if alt else ""
    src_text = _escape_string(src)
    if alt_text:
        return f'#figure(image("{src_text}"), caption: [{alt_text}])'
    return f'#image("{src_text}")'


def _escape_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _escape_text(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("#", "\\#")
        .replace("@", "\\@")
        .replace("$", "\\$")
        .replace("<", "\\<")
        .replace(">", "\\>")
    )


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
