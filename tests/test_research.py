from notes_forge.agents.research import reconcile, source_urls
from notes_forge.schemas import ResearchOutput, ResearchTask


def _tasks():
    return [ResearchTask(id="r1", question="a"), ResearchTask(id="r2", question="b")]


def test_reconcile_marks_missing_tasks_unresolved():
    result = ResearchOutput.model_validate(
        {
            "findings": [
                {"task_id": "r1", "answer": "x", "confidence": "high",
                 "sources": [{"url": "https://a.dev"}]},
                {"task_id": "r9", "answer": "stray", "confidence": "low",
                 "sources": [{"url": "https://b.dev"}]},
            ]
        }
    )
    fixed = reconcile(result, _tasks())
    assert [f.task_id for f in fixed.findings] == ["r1"]
    assert [u.task_id for u in fixed.unresolved] == ["r2"]


def test_source_urls_are_unique_and_ordered():
    result = ResearchOutput.model_validate(
        {
            "findings": [
                {"task_id": "r1", "answer": "x", "confidence": "high",
                 "sources": [{"url": "https://a.dev"}, {"url": "https://b.dev"}]},
                {"task_id": "r2", "answer": "y", "confidence": "high",
                 "sources": [{"url": "https://a.dev"}]},
            ]
        }
    )
    assert source_urls(result) == ["https://a.dev", "https://b.dev"]
