"""Reader: understand the raw notes without fixing them."""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

from notes_forge import prompts
from notes_forge.llm import LLM
from notes_forge.schemas import ReaderOutput

IMAGE_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp"}


def run(llm: LLM, notes: str) -> ReaderOutput:
    prompt = prompts.render("reader", user_notes=notes)
    return llm.call_json("reader", prompt, ReaderOutput)


def run_image(llm: LLM, image_path: str | Path) -> ReaderOutput:
    """Handwritten or photographed notes: attach the image and let the Reader transcribe."""
    path = Path(image_path)
    media_type = mimetypes.guess_type(path.name)[0] or ""
    if media_type not in IMAGE_TYPES:
        raise ValueError(f"unsupported image type: {path.suffix}")
    data = base64.standard_b64encode(path.read_bytes()).decode()
    prompt = prompts.render("reader", user_notes="(see the attached image)")
    content = [
        {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": data}},
        {"type": "text", "text": prompt},
    ]
    return llm.call_json("reader", content, ReaderOutput)  # type: ignore[arg-type]
