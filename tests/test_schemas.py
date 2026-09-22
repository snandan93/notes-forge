import pytest
from pydantic import ValidationError

from notes_forge.schemas import FactCheckOutput, Finding, ReaderOutput, VisualCheckOutput


def test_reader_defaults_fill_optional_fields():
    out = ReaderOutput.model_validate({"topic": "TCP", "concepts": [{"name": "handshake"}]})
    assert out.level == "beginner"
    assert out.style_profile.language_mix == "English"


def test_finding_requires_a_source():
    with pytest.raises(ValidationError):
        Finding.model_validate(
            {"task_id": "r1", "answer": "x", "confidence": "high", "sources": []}
        )


def test_fact_score_is_bounded():
    with pytest.raises(ValidationError):
        FactCheckOutput.model_validate({"score": 11})


def test_visual_check_reads_pass_alias():
    assert VisualCheckOutput.model_validate({"pass": True}).passed is True
