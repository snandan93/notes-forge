"""Prompt templates. Placeholders look like {{name}}."""

from __future__ import annotations

import json
import re
from functools import cache
from importlib import resources
from typing import Any

_PLACEHOLDER = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")


@cache
def load(name: str) -> str:
    return resources.files(__package__).joinpath(f"{name}.md").read_text(encoding="utf-8")


def _stringify(value: Any) -> str:
    if isinstance(value, str):
        return value
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    return json.dumps(value, indent=2, ensure_ascii=False)


def render(name: str, **values: Any) -> str:
    """Fill a template. Missing values raise, so a typo never ships a blank prompt."""
    template = load(name)

    def sub(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            raise KeyError(f"prompt '{name}' needs value for '{key}'")
        return _stringify(values[key])

    return _PLACEHOLDER.sub(sub, template)
