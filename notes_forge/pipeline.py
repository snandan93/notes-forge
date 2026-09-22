"""Orchestrator: Reader -> Planner -> Research -> Brain -> (Writer + Visual -> Critic) x3."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from notes_forge.agents import brain as brain_agent
from notes_forge.agents import critic, planner, reader, research, writer
from notes_forge.agents import visual as visual_agent
from notes_forge.agents.writer import PLACEHOLDER
from notes_forge.config import settings
from notes_forge.gate import Verdict, evaluate
from notes_forge.llm import LLM, RunLogger
from notes_forge.schemas import BrainOutput, DistilledConcept, VisualOutput

Progress = Callable[[str], None]

NEEDS_REVIEW_BANNER = (
    "> ⚠️ **Needs review:** these notes did not pass every quality check. "
    "See the feedback file in the run folder.\n\n"
)


@dataclass
class Draft:
    markdown: str
    visuals: dict[str, VisualOutput]
    verdict: Verdict


@dataclass
class Result:
    markdown: str
    passed: bool
    score: float
    attempts: int
    run_dir: Path
    feedback: str


def match_concept(name: str, brain: BrainOutput) -> DistilledConcept | None:
    key = name.strip().lower()
    for c in brain.concepts:
        if c.name.lower() == key:
            return c
    for c in brain.concepts:
        if key in c.name.lower() or c.name.lower() in key:
            return c
    return None


def assemble(markdown: str, visuals: dict[str, VisualOutput]) -> str:
    def swap(match):
        visual = visuals.get(match.group(1))
        return visual_agent.to_markdown(visual) if visual else ""

    return PLACEHOLDER.sub(swap, markdown).replace("\n\n\n", "\n\n")


def _make_visuals(
    llm: LLM,
    names: list[str],
    brain: BrainOutput,
    previous: dict[str, VisualOutput],
    fixes: dict[str, str],
) -> dict[str, VisualOutput]:
    """Build visuals for new placeholders and rebuild failed ones. Passing ones are reused."""
    todo: dict[str, DistilledConcept] = {}
    out: dict[str, VisualOutput] = {}
    for name in names:
        if name in previous and name not in fixes:
            out[name] = previous[name]
            continue
        concept = match_concept(name, brain)
        if concept is not None:
            todo[name] = concept
    with ThreadPoolExecutor(max_workers=max(1, len(todo))) as pool:
        futures = {n: pool.submit(visual_agent.run, llm, c, fixes.get(n)) for n, c in todo.items()}
        for name, fut in futures.items():
            out[name] = fut.result().model_copy(update={"concept": name})
    return out


def run(
    notes: str | None = None,
    *,
    image: str | Path | None = None,
    llm: LLM | None = None,
    progress: Progress = lambda _msg: None,
) -> Result:
    if not notes and not image:
        raise ValueError("pass notes text or an image path")
    logger = RunLogger()
    llm = llm or LLM(logger=logger)
    if llm.logger is None:
        llm.logger = logger

    progress("Reading your notes")
    reading = reader.run_image(llm, image) if image else reader.run(llm, notes or "")

    progress(f"Planning '{reading.topic}'")
    plan = planner.run(llm, reading)

    progress(f"Researching {len(plan.research_tasks)} open questions")
    found = research.run(llm, plan.research_tasks)

    progress("Distilling the core ideas")
    brain = brain_agent.run(llm, reading, plan, found)
    questions = critic.quiz_questions(llm, brain)

    best: Draft | None = None
    feedback: str | None = None
    visuals: dict[str, VisualOutput] = {}
    fixes: dict[str, str] = {}
    attempt = 0
    for attempt in range(1, settings.max_attempts + 1):
        progress(f"Writing draft {attempt}")
        draft = writer.run(llm, reading, brain, notes or "", feedback=feedback, attempt=attempt)

        progress(f"Drawing {len(draft.visual_placeholders)} visuals")
        visuals = _make_visuals(llm, draft.visual_placeholders, brain, visuals, fixes)

        progress(f"Reviewing draft {attempt}")
        review = critic.review(
            llm,
            draft.markdown,
            reading=reading,
            brain=brain,
            research=found,
            questions=questions,
            visuals=list(visuals.values()),
        )
        verdict = evaluate(review)
        logger.write("gate", {"attempt": attempt, "passed": verdict.passed,
                              "score": verdict.score, "feedback": verdict.feedback})

        current = Draft(draft.markdown, dict(visuals), verdict)
        if best is None or verdict.score > best.verdict.score:
            best = current
        if verdict.passed:
            best = current
            break
        feedback = verdict.feedback
        fixes = {v.concept: f"{'; '.join(v.problems)} {v.fix}".strip()
                 for v in review.visuals if not v.passed}

    assert best is not None
    final = assemble(best.markdown, best.visuals)
    if not best.verdict.passed:
        final = NEEDS_REVIEW_BANNER + final
    (logger.dir / "notes.md").write_text(final, encoding="utf-8")
    if best.verdict.feedback:
        (logger.dir / "feedback.txt").write_text(best.verdict.feedback, encoding="utf-8")

    return Result(
        markdown=final,
        passed=best.verdict.passed,
        score=best.verdict.score,
        attempts=attempt,
        run_dir=logger.dir,
        feedback=best.verdict.feedback,
    )
