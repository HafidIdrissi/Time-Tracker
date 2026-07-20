"""Configurable keyword-based activity categorization."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class Category:
    name: str
    color: str
    keywords: tuple[str, ...]


class CategoryConfigError(ValueError):
    """Raised when the category JSON does not match the expected shape."""


class Categorizer:
    """Assign the first matching category, case-insensitively."""

    def __init__(
        self,
        categories: list[Category],
        default_name: str = "Other",
        default_color: str = "#64748b",
    ) -> None:
        self.categories = categories
        self.default_name = default_name
        self.default_color = default_color

    def categorize(
        self, application: str, window_title: str, is_idle: bool = False
    ) -> tuple[str, str]:
        if is_idle:
            return "Idle", "#94a3b8"

        haystack = f"{application} {window_title}".casefold()
        for category in self.categories:
            if any(keyword.casefold() in haystack for keyword in category.keywords):
                return category.name, category.color
        return self.default_name, self.default_color


def _required_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CategoryConfigError(f"'{field}' must be a non-empty string")
    return value.strip()


def _color(value: Any, field: str) -> str:
    color = _required_string(value, field)
    if re.fullmatch(r"#[0-9a-fA-F]{6}", color) is None:
        raise CategoryConfigError(f"'{field}' must be a hexadecimal #RRGGBB color")
    return color


def load_categorizer(path: str | Path) -> Categorizer:
    """Load and validate a JSON category configuration."""

    config_path = Path(path)
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CategoryConfigError(f"Configuration not found: {config_path}") from exc
    except json.JSONDecodeError as exc:
        raise CategoryConfigError(
            f"Invalid JSON in {config_path} (line {exc.lineno})"
        ) from exc

    if not isinstance(raw, dict):
        raise CategoryConfigError("The configuration root must be a JSON object")

    default_name = _required_string(raw.get("default_category", "Other"), "default_category")
    default_color = _color(raw.get("default_color", "#64748b"), "default_color")
    raw_categories = raw.get("categories")
    if not isinstance(raw_categories, list):
        raise CategoryConfigError("'categories' must be a list")

    categories: list[Category] = []
    seen_names: set[str] = set()
    for index, item in enumerate(raw_categories):
        if not isinstance(item, dict):
            raise CategoryConfigError(f"categories[{index}] must be an object")
        name = _required_string(item.get("name"), f"categories[{index}].name")
        color = _color(
            item.get("color", "#64748b"), f"categories[{index}].color"
        )
        keywords = item.get("keywords")
        if not isinstance(keywords, list) or not keywords:
            raise CategoryConfigError(
                f"categories[{index}].keywords must be a non-empty list"
            )
        clean_keywords = tuple(
            _required_string(keyword, f"categories[{index}].keywords")
            for keyword in keywords
        )
        if name.casefold() in seen_names:
            raise CategoryConfigError(f"Duplicate category: {name}")
        seen_names.add(name.casefold())
        categories.append(Category(name=name, color=color, keywords=clean_keywords))

    return Categorizer(categories, default_name, default_color)
