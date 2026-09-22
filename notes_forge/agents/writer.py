"""Writer: turn the distilled structure into notes in the learner's voice."""

from __future__ import annotations

import re

from notes_forge import prompts
from notes_forge.llm import LLM
from notes_forge.schemas import BrainOutput, ReaderOutput, WriterOutput
from notes_forge.style import style_guide

PLACEHOLDER = re.compile(r"\[\[VISUAL:\s*(.+?)\s*\]\]")


def learner_samples(raw_notes: str, count: int = 3, max_chars: int = 400) -> str:
    """Pick a few of the learner's own paragraphs so the Writer can copy their voice."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", raw_notes) if len(p.strip()) > 40]
    if not paragraphs:
        paragraphs = [raw_notes.strip()]
    step = max(1, len(paragraphs) // count)
    picks = paragraphs[::step][:count]
    return "\n---\n".join(p[:max_chars] for p in picks)


def target_words(brain: BrainOutput) -> int:
    return min(1800, 250 + 220 * len(brain.concepts))


def run(
    llm: LLM,
    reading: ReaderOutput,
    brain: BrainOutput,
    raw_notes: str,
    *,
    feedback: str | None = None,
    attempt: int = 1,
) -> WriterOutput:
    revision_block = ""
    if feedback:
        revision_block = prompts.render(
            "writer_revision", attempt_number=attempt, critic_feedback=feedback
        )
    prompt = prompts.render(
        "writer",
        style_guide=style_guide(reading.style_profile.language_mix),
        learner_style=reading.style_profile,
        learner_samples=learner_samples(raw_notes) if raw_notes else "(no text samples)",
        brain_json=brain,
        revision_block=revision_block,
        topic=reading.topic,
        target_words=target_words(brain),
    )
    out = llm.call_json("writer", prompt, WriterOutput)
    # Trust the markdown over the model's own list of placeholders.
    found = list(dict.fromkeys(PLACEHOLDER.findall(out.markdown)))
    return out.model_copy(update={"visual_placeholders": found})
