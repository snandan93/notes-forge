"""Pydantic models for every agent's JSON output.

Every agent reply is validated against one of these before it enters pipeline state.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Level = Literal["beginner", "intermediate", "advanced"]
VisualHint = Literal[
    "flowchart", "concept_map", "comparison_table", "timeline", "architecture",
    "analogy_image", "none",
]


# ---------- Reader ----------
class Concept(BaseModel):
    name: str
    learner_explanation: str = ""


class Claim(BaseModel):
    id: str
    text: str


class StyleProfile(BaseModel):
    avg_sentence_length: Literal["short", "medium", "long"] = "medium"
    tone: str = ""
    language_mix: str = "English"
    uses_examples: bool = False
    sample_phrases: list[str] = Field(default_factory=list)


class ReaderOutput(BaseModel):
    topic: str
    concepts: list[Concept]
    claims: list[Claim] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    style_profile: StyleProfile = Field(default_factory=StyleProfile)
    level: Level = "beginner"
    unclear_parts: list[str] = Field(default_factory=list)


# ---------- Planner ----------
class ConceptLink(BaseModel):
    concept: str
    requires: list[str] = Field(default_factory=list)


class MissingPrereq(BaseModel):
    concept: str
    why_needed: str


class ClaimReview(BaseModel):
    claim_id: str
    status: Literal["likely_correct", "likely_wrong", "incomplete", "needs_verification"]
    reason: str = ""


class Misconception(BaseModel):
    misconception: str
    correct_view: str
    evidence_in_notes: bool = False


class ResearchTask(BaseModel):
    id: str
    question: str
    resolves: list[str] = Field(default_factory=list)


class PlannerOutput(BaseModel):
    core_idea_draft: str
    concept_map: list[ConceptLink] = Field(default_factory=list)
    missing_prerequisites: list[MissingPrereq] = Field(default_factory=list)
    claim_review: list[ClaimReview] = Field(default_factory=list)
    misconceptions: list[Misconception] = Field(default_factory=list)
    research_tasks: list[ResearchTask] = Field(default_factory=list, max_length=8)
    teaching_order: list[str]


# ---------- Research ----------
class Source(BaseModel):
    title: str = ""
    url: str
    date: str = ""


class Finding(BaseModel):
    task_id: str
    answer: str
    confidence: Literal["high", "medium", "low"]
    sources: list[Source] = Field(min_length=1)
    conflicts: str = ""


class Unresolved(BaseModel):
    task_id: str
    reason: str


class ResearchOutput(BaseModel):
    findings: list[Finding] = Field(default_factory=list)
    unresolved: list[Unresolved] = Field(default_factory=list)


# ---------- Brain ----------
class Analogy(BaseModel):
    text: str
    where_it_breaks: str


class DistilledConcept(BaseModel):
    name: str
    one_liner: str
    why_it_exists: str
    how_it_works: list[str]
    analogy: Analogy
    example: str
    common_mistake: str = ""
    visual_hint: VisualHint = "none"
    source_urls: list[str] = Field(default_factory=list)


class Correction(BaseModel):
    learner_said: str
    actually: str
    source_url: str = ""


class BrainOutput(BaseModel):
    core_idea: str
    concepts: list[DistilledConcept]
    corrections: list[Correction] = Field(default_factory=list)
    key_takeaways: list[str] = Field(min_length=1, max_length=5)


# ---------- Writer ----------
class WriterOutput(BaseModel):
    markdown: str
    visual_placeholders: list[str] = Field(default_factory=list)


# ---------- Visual ----------
class VisualOutput(BaseModel):
    concept: str
    type: Literal["mermaid", "table", "image_prompt", "none"]
    code: str = ""
    caption: str = ""
    alt_text: str = ""


# ---------- Critics ----------
class UnsupportedClaim(BaseModel):
    text: str
    fix: str


class Contradiction(BaseModel):
    text: str
    source_says: str


class FactCheckOutput(BaseModel):
    unsupported_claims: list[UnsupportedClaim] = Field(default_factory=list)
    missing_concepts: list[str] = Field(default_factory=list)
    missing_corrections: list[str] = Field(default_factory=list)
    contradictions: list[Contradiction] = Field(default_factory=list)
    score: int = Field(ge=0, le=10)


class QuizQuestion(BaseModel):
    q: str
    expected_answer: str


class QuizQuestions(BaseModel):
    questions: list[QuizQuestion] = Field(min_length=1)


class QuizAnswer(BaseModel):
    q: str
    answer: str


class QuizAnswers(BaseModel):
    answers: list[QuizAnswer]


class QuizGrade(BaseModel):
    q: str
    correct: bool
    missing_topic: str = ""


class QuizGrades(BaseModel):
    grades: list[QuizGrade]


class ClarityIssue(BaseModel):
    type: str
    quote: str
    rewrite: str


class ClarityOutput(BaseModel):
    issues: list[ClarityIssue] = Field(default_factory=list)
    score: int = Field(ge=0, le=10)


class VisualCheckOutput(BaseModel):
    # "pass" is a keyword, so alias it.
    passed: bool = Field(alias="pass")
    problems: list[str] = Field(default_factory=list)
    fix: str = ""

    model_config = {"populate_by_name": True}
