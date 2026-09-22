"""Shared style guide plus a cheap local check for banned phrases."""

from __future__ import annotations

import re

from notes_forge import prompts

BANNED_PHRASES = [
    "delve",
    "crucial",
    "landscape",
    "realm",
    "robust",
    "seamless",
    "it's important to note",
    "in today's world",
    "in conclusion",
    "let's dive in",
    "unlock",
    "game-changer",
    "navigate the complexities",
]
_LEVERAGE_VERB = re.compile(r"\bleverag(e|es|ed|ing)\b(?!\s+(ratio|point))", re.IGNORECASE)


def style_guide(language_mix: str = "English") -> str:
    return prompts.render("style_guide", language_mix=language_mix or "English")


def find_banned(text: str) -> list[str]:
    """Return banned phrases present in text. Runs before the LLM editor to save a call."""
    lowered = text.lower()
    hits = [p for p in BANNED_PHRASES if re.search(rf"\b{re.escape(p)}\b", lowered)]
    if _LEVERAGE_VERB.search(text):
        hits.append("leverage")
    return hits


def long_sentences(text: str, limit: int = 25) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", re.sub(r"```.*?```", "", text, flags=re.DOTALL))
    return [s.strip() for s in sentences if len(s.split()) > limit]
