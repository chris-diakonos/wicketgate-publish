from pathlib import Path
import shutil

from jinja2 import Environment, FileSystemLoader, select_autoescape

from wicketgate_publish.assets import copy_assets
from wicketgate_publish.content import Page, discover_pages
from wicketgate_publish.site_config import load_navigation, load_site_config


def build_site(
    project_root: Path,
    *,
    output_dir: Path | None = None,
    content_dir: Path | None = None,
    templates_dir: Path | None = None,
    assets_dir: Path | None = None,
    config_dir: Path | None = None,
) -> list[Page]:
    resolved_content = content_dir or project_root / "content"
    resolved_templates = templates_dir or project_root / "templates"
    resolved_assets = assets_dir or project_root / "assets"
    resolved_config = config_dir or project_root / "config"
    resolved_output = output_dir or project_root / "generated" / "site"

    site_config = load_site_config(resolved_config)
    navigation = load_navigation(resolved_config)
    pages = discover_pages(resolved_content, resolved_output)

    if resolved_output.exists():
        shutil.rmtree(resolved_output)
    resolved_output.mkdir(parents=True)

    copy_assets(resolved_assets, resolved_output / "assets")
    render_pages(resolved_templates, site_config, navigation, pages)
    return pages


def render_pages(
    templates_dir: Path,
    site_config: dict,
    navigation: list[dict],
    pages: list[Page],
) -> None:
    environment = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(["html", "xml"]),
    )
    environment.globals["asset"] = asset_path

    page_index = {page.url: page for page in pages}

    for page in pages:
        template = environment.get_template(f"{page.template}.html")
        page.output_path.parent.mkdir(parents=True, exist_ok=True)
        html = template.render(
            site=site_config,
            navigation=navigation,
            page=page,
            pages=page_index,
        )
        page.output_path.write_text(html, encoding="utf-8")


def asset_path(path: str) -> str:
    return f"/assets/{path.lstrip('/')}"
