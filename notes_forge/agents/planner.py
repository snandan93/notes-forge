"""Planner: map prerequisites, review claims, and queue research."""

from __future__ import annotations

from notes_forge import prompts
from notes_forge.llm import LLM
from notes_forge.schemas import PlannerOutput, ReaderOutput


def run(llm: LLM, reading: ReaderOutput) -> PlannerOutput:
    prompt = prompts.render("planner", reader_json=reading, level=reading.level)
    plan = llm.call_json("planner", prompt, PlannerOutput)
    return _ensure_order_covers_concepts(plan, reading)


def _ensure_order_covers_concepts(plan: PlannerOutput, reading: ReaderOutput) -> PlannerOutput:
    """Concepts the planner forgot to schedule go at the end, so nothing is silently dropped."""
    ordered = {c.lower() for c in plan.teaching_order}
    extra = [c.name for c in reading.concepts if c.name.lower() not in ordered]
    if extra:
        plan = plan.model_copy(update={"teaching_order": [*plan.teaching_order, *extra]})
    return plan
