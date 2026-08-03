from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def load_site_config(config_dir: Path) -> dict[str, Any]:
    return load_yaml(config_dir / "site.yaml")


def load_navigation(config_dir: Path) -> list[dict[str, Any]]:
    raw_items = load_yaml(config_dir / "navigation.yaml")
    return [normalize_nav_item(item) for item in raw_items]


def normalize_nav_item(item: Any) -> dict[str, Any]:
    if isinstance(item, str):
        return {"title": item, "url": url_for_title(item), "children": []}

    if not isinstance(item, dict) or len(item) != 1:
        raise ValueError(f"Navigation item must be a string or single-key mapping: {item!r}")

    title, value = next(iter(item.items()))
    if value is None:
        value = {}

    if isinstance(value, str):
        return {"title": title, "url": value, "children": []}

    if not isinstance(value, dict):
        raise ValueError(f"Navigation item value must be a string or mapping: {item!r}")

    children = value.get("children") or []
    return {
        "title": title,
        "url": value.get("url") or url_for_title(title),
        "children": [normalize_nav_item(child) for child in children],
    }


def url_for_title(title: str) -> str:
    slug = title.strip().lower().replace("&", "and")
    slug = "-".join(part for part in slug.split() if part)
    if slug == "home":
        return "/"
    return f"/{slug}/"
