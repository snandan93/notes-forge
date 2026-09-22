"""Merge rule: decide pass/fail and build revision feedback. Pure code, no model calls."""

from __future__ import annotations

from dataclasses import dataclass

from notes_forge.agents.critic import Review

FACT_MIN = 8
QUIZ_MIN = 4
CLARITY_MIN = 7


@dataclass
class Verdict:
    passed: bool
    score: float
    feedback: str
    failed_visuals: list[str]


def score(review: Review) -> float:
    """Single number used to pick the best draft when no attempt passes."""
    quiz_total = max(1, len(review.quiz.grades))
    visuals_ok = sum(v.passed for v in review.visuals) / max(1, len(review.visuals))
    return round(
        0.4 * review.fact.score
        + 0.3 * 10 * review.quiz_correct / quiz_total
        + 0.2 * review.clarity.score
        + 0.1 * 10 * visuals_ok
        - 1.0 * len(review.fact.unsupported_claims),
        2,
    )


def feedback(review: Review) -> list[str]:
    """All problems as a list, most severe first."""
    items: list[str] = []
    f = review.fact
    items += [f"Contradicts a source: \"{c.text}\". Source says: {c.source_says}" for c in f.contradictions]
    items += [f"Unsupported claim: \"{u.text}\". Fix: {u.fix}" for u in f.unsupported_claims]
    items += [f"Missing correction: {m}" for m in f.missing_corrections]
    items += [f"Missing concept: {m}" for m in f.missing_concepts]
    items += [
        f"Notes do not explain: {g.missing_topic or g.q}" for g in review.quiz.grades if not g.correct
    ]
    for v in review.visuals:
        if not v.passed:
            items.append(f"Visual for '{v.concept}' failed: {'; '.join(v.problems)} {v.fix}".strip())
    items += [
        f"Clarity ({i.type}): \"{i.quote}\" -> \"{i.rewrite}\"" for i in review.clarity.issues
    ]
    return items


def evaluate(review: Review) -> Verdict:
    passed = (
        review.fact.score >= FACT_MIN
        and review.quiz_correct >= QUIZ_MIN
        and review.clarity.score >= CLARITY_MIN
        and all(v.passed for v in review.visuals)
        and not review.fact.unsupported_claims
    )
    items = feedback(review)
    return Verdict(
        passed=passed,
        score=score(review),
        feedback="\n".join(f"{n}. {text}" for n, text in enumerate(items, 1)),
        failed_visuals=[v.concept for v in review.visuals if not v.passed],
    )
