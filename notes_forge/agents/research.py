"""Research: answer the planner's questions with sourced facts only."""

from __future__ import annotations

from notes_forge import prompts
from notes_forge.llm import LLM
from notes_forge.schemas import ResearchOutput, ResearchTask, Unresolved

# Server-side tools: search runs on the API side, no local execution loop needed.
WEB_TOOLS = [
    {"type": "web_search_20260209", "name": "web_search", "max_uses": 16},
    {"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": 12},
]


def run(llm: LLM, tasks: list[ResearchTask]) -> ResearchOutput:
    if not tasks:
        return ResearchOutput()
    prompt = prompts.render("research", research_tasks_json=[t.model_dump() for t in tasks])
    result = llm.call_json("research", prompt, ResearchOutput, tools=WEB_TOOLS)
    return reconcile(result, tasks)


def reconcile(result: ResearchOutput, tasks: list[ResearchTask]) -> ResearchOutput:
    """Drop findings for unknown tasks and mark any task left unanswered as unresolved."""
    known = {t.id for t in tasks}
    findings = [f for f in result.findings if f.task_id in known]
    covered = {f.task_id for f in findings} | {u.task_id for u in result.unresolved}
    unresolved = [u for u in result.unresolved if u.task_id in known]
    unresolved += [
        Unresolved(task_id=t.id, reason="no answer returned") for t in tasks if t.id not in covered
    ]
    return ResearchOutput(findings=findings, unresolved=unresolved)


def source_urls(result: ResearchOutput) -> list[str]:
    seen: dict[str, None] = {}
    for finding in result.findings:
        for src in finding.sources:
            seen.setdefault(src.url, None)
    return list(seen)
