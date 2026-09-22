from notes_forge.agents.planner import _ensure_order_covers_concepts
from notes_forge.schemas import PlannerOutput, ReaderOutput


def test_unscheduled_concepts_are_appended():
    reading = ReaderOutput.model_validate(
        {"topic": "DNS", "concepts": [{"name": "resolver"}, {"name": "TTL"}]}
    )
    plan = PlannerOutput.model_validate({"core_idea_draft": "x", "teaching_order": ["Resolver"]})
    fixed = _ensure_order_covers_concepts(plan, reading)
    assert fixed.teaching_order == ["Resolver", "TTL"]
