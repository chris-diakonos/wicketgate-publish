from pathlib import Path

from wicketgate_publish.markdown_to_typst import markdown_to_typst


def test_markdown_to_typst_headings_and_paragraphs() -> None:
    result = markdown_to_typst("# Title\n\nA paragraph with **bold** and *italic*.\n")
    assert "= Title" in result
    assert "*bold*" in result
    assert "_italic_" in result


def test_markdown_to_typst_lists_code_and_quote() -> None:
    result = markdown_to_typst(
        "- one\n"
        "- two\n"
        "\n"
        "1. first\n"
        "2. second\n"
        "\n"
        "> quoted wisdom\n"
        "\n"
        "```python\n"
        "print('hi')\n"
        "```\n"
    )
    assert "- one" in result
    assert "+ first" in result
    assert "#quote[quoted wisdom]" in result
    assert "```python" in result
    assert "print('hi')" in result


def test_markdown_to_typst_links_and_images() -> None:
    result = markdown_to_typst(
        "See [docs](https://example.com) and ![Logo](assets/logo.png).\n"
    )
    assert '#link("https://example.com")[docs]' in result
    assert '#figure(image("assets/logo.png"), caption: [Logo])' in result
