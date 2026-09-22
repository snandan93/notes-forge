"""Critic: four independent checks run in parallel, then merged by `gate`."""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from notes_forge import prompts, style
from notes_forge.agents import visual as visual_agent
from notes_forge.llm import LLM
from notes_forge.schemas import (
    BrainOutput,
    ClarityIssue,
    ClarityOutput,
    FactCheckOutput,
    QuizAnswers,
    QuizGrades,
    QuizQuestions,
    ReaderOutput,
    ResearchOutput,
    VisualCheckOutput,
    VisualOutput,
)

NOT_IN_NOTES = "NOT IN NOTES"


@dataclass
class VisualVerdict:
    concept: str
    passed: bool
    problems: list[str] = field(default_factory=list)
    fix: str = ""


@dataclass
class Review:
    fact: FactCheckOutput
    quiz: QuizGrades
    clarity: ClarityOutput
    visuals: list[VisualVerdict]

    @property
    def quiz_correct(self) -> int:
        return sum(g.correct for g in self.quiz.grades)


def quiz_questions(llm: LLM, brain: BrainOutput) -> QuizQuestions:
    """Generated once per run from the distilled knowledge; the notes are never shown here."""
    return llm.call_json(
        "quiz", prompts.render("quiz_questions", brain_json=brain), QuizQuestions
    )


def _fact(llm, markdown, brain, research, reading) -> FactCheckOutput:
    prompt = prompts.render(
        "critic_fact",
        writer_markdown=markdown,
        brain_json=brain,
        research_json=research,
        original_concepts=[c.model_dump() for c in reading.concepts],
    )
    return llm.call_json("critic_fact", prompt, FactCheckOutput)


def _quiz(llm, markdown, questions: QuizQuestions) -> QuizGrades:
    answers = llm.call_json(
        "quiz",
        prompts.render("quiz_answer", writer_markdown=markdown, questions_json=[
            {"q": q.q} for q in questions.questions  # expected answers stay hidden
        ]),
        QuizAnswers,
    )
    grades = llm.call_json(
        "quiz_grader",
        prompts.render("quiz_grade", questions_json=questions, answers_json=answers),
        QuizGrades,
    )
    # Hard rule from the spec: NOT IN NOTES is always wrong, whatever the grader said.
    missing = {a.q for a in answers.answers if a.answer.strip().upper() == NOT_IN_NOTES}
    for g in grades.grades:
        if g.q in missing:
            g.correct = False
    return grades


def _clarity(llm, markdown, language_mix) -> ClarityOutput:
    prompt = prompts.render(
        "critic_clarity", style_guide=style.style_guide(language_mix), writer_markdown=markdown
    )
    result = llm.call_json("critic_clarity", prompt, ClarityOutput)
    # Cheap local checks catch what the editor model misses.
    quoted = " ".join(i.quote.lower() for i in result.issues)
    for phrase in style.find_banned(markdown):
        if phrase not in quoted:
            result.issues.append(
                ClarityIssue(type="banned_phrase", quote=phrase, rewrite="remove or reword")
            )
    return result


def concept_section(markdown: str, concept: str) -> str:
    pattern = re.compile(rf"^##\s+{re.escape(concept)}\s*$(.*?)(?=^##\s|\Z)", re.MULTILINE | re.DOTALL | re.IGNORECASE)
    match = pattern.search(markdown)
    return match.group(0) if match else markdown


def _visual(llm, markdown, visual: VisualOutput) -> VisualVerdict:
    if visual.type == "none":
        return VisualVerdict(visual.concept, True)
    local = visual_agent.local_problems(visual)
    if local:  # render/lint failure is an automatic fail; skip the model call
        return VisualVerdict(visual.concept, False, local, "fix the diagram syntax")
    prompt = prompts.render(
        "critic_visual",
        concept_section_markdown=concept_section(markdown, visual.concept),
        visual_json=visual,
    )
    check = llm.call_json("critic_visual", prompt, VisualCheckOutput)
    return VisualVerdict(visual.concept, check.passed, check.problems, check.fix)


def review(
    llm: LLM,
    markdown: str,
    *,
    reading: ReaderOutput,
    brain: BrainOutput,
    research: ResearchOutput,
    questions: QuizQuestions,
    visuals: list[VisualOutput],
) -> Review:
    with ThreadPoolExecutor(max_workers=4 + len(visuals)) as pool:
        fact = pool.submit(_fact, llm, markdown, brain, research, reading)
        quiz = pool.submit(_quiz, llm, markdown, questions)
        clarity = pool.submit(_clarity, llm, markdown, reading.style_profile.language_mix)
        vis = [pool.submit(_visual, llm, markdown, v) for v in visuals]
        return Review(
            fact=fact.result(),
            quiz=quiz.result(),
            clarity=clarity.result(),
            visuals=[f.result() for f in vis],
        )
