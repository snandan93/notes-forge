"""Visual: one simple diagram per [[VISUAL: ...]] placeholder."""

from __future__ import annotations

from notes_forge import diagrams, prompts
from notes_forge.llm import LLM
from notes_forge.schemas import DistilledConcept, VisualOutput


def run(llm: LLM, concept: DistilledConcept, fix: str | None = None) -> VisualOutput:
    fix_block = f"\n<previous_attempt_problems>\n{fix}\n</previous_attempt_problems>\n" if fix else ""
    prompt = prompts.render(
        "visual",
        concept_json=concept,
        visual_hint=concept.visual_hint,
        fix_block=fix_block,
    )
    return llm.call_json("visual", prompt, VisualOutput)


def local_problems(visual: VisualOutput) -> list[str]:
    if visual.type == "mermaid":
        return diagrams.render_mermaid(visual.code)
    if visual.type == "table":
        return diagrams.lint_table(visual.code)
    return []


def to_markdown(visual: VisualOutput) -> str:
    """What replaces the placeholder in the final notes."""
    if visual.type == "none":
        return ""
    if visual.type == "mermaid":
        body = f"```mermaid\n{diagrams._strip_fence(visual.code)}\n```"
    elif visual.type == "table":
        body = visual.code.strip()
    else:
        body = f"> 🖼️ *Image idea:* {visual.code.strip()}"
    caption = f"\n\n*{visual.caption}*" if visual.caption else ""
    return body + caption
