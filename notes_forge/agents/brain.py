"""Brain: distil reading + plan + research into the smallest correct core."""

from __future__ import annotations

from notes_forge import prompts
from notes_forge.llm import LLM
from notes_forge.schemas import BrainOutput, PlannerOutput, ReaderOutput, ResearchOutput


def run(
    llm: LLM, reading: ReaderOutput, plan: PlannerOutput, research: ResearchOutput
) -> BrainOutput:
    prompt = prompts.render(
        "brain", reader_json=reading, planner_json=plan, research_json=research
    )
    return llm.call_json("brain", prompt, BrainOutput)
