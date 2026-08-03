from pathlib import Path

from wicketgate_publish.content import output_path_for_url, page_url, split_front_matter


def test_split_front_matter_reads_yaml_metadata() -> None:
    metadata, body = split_front_matter(
        "---\n"
        "title: About\n"
        "template: page\n"
        "---\n"
        "\n"
        "# Hello\n"
    )

    assert metadata == {"title": "About", "template": "page"}
    assert body == "# Hello\n"


def test_page_url_uses_clean_urls() -> None:
    assert page_url(Path("index.md")) == "/"
    assert page_url(Path("about.md")) == "/about/"
    assert page_url(Path("software/philosophy.md")) == "/software/philosophy/"
    assert page_url(Path("anything.md"), "custom/path") == "/custom/path/"


def test_output_path_for_clean_url() -> None:
    output = Path("generated/site")

    assert output_path_for_url(output, "/") == output / "index.html"
    assert output_path_for_url(output, "/about/") == output / "about" / "index.html"
