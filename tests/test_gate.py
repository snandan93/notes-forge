from notes_forge.agents.critic import Review, VisualVerdict, concept_section
from notes_forge.gate import evaluate
from notes_forge.schemas import ClarityOutput, FactCheckOutput, QuizGrades


def make_review(fact=9, correct=5, clarity=8, visual_ok=True, unsupported=()):
    return Review(
        fact=FactCheckOutput.model_validate(
            {"score": fact, "unsupported_claims": [{"text": t, "fix": "cite"} for t in unsupported]}
        ),
        quiz=QuizGrades.model_validate(
            {"grades": [{"q": f"q{i}", "correct": i < correct, "missing_topic": f"t{i}"}
                        for i in range(5)]}
        ),
        clarity=ClarityOutput(score=clarity),
        visuals=[VisualVerdict("TCP", visual_ok, [] if visual_ok else ["bad label"])],
    )


def test_all_good_passes():
    assert evaluate(make_review()).passed


def test_quiz_threshold():
    assert evaluate(make_review(correct=4)).passed
    assert not evaluate(make_review(correct=3)).passed


def test_unsupported_claim_blocks_even_with_high_score():
    verdict = evaluate(make_review(fact=10, unsupported=["TCP was invented in 1999"]))
    assert not verdict.passed
    assert verdict.feedback.startswith("1. Unsupported claim")


def test_failed_visual_is_reported():
    verdict = evaluate(make_review(visual_ok=False))
    assert not verdict.passed and verdict.failed_visuals == ["TCP"]


def test_score_prefers_better_draft():
    assert evaluate(make_review(fact=9)).score > evaluate(make_review(fact=5)).score


def test_concept_section_extracts_heading_block():
    md = "# T\n## Handshake\nSYN then ACK\n## Ports\nnumbers"
    assert concept_section(md, "Handshake").strip() == "## Handshake\nSYN then ACK"
