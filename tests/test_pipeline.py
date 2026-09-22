from notes_forge.pipeline import assemble, match_concept
from notes_forge.schemas import BrainOutput, VisualOutput

BRAIN = BrainOutput.model_validate(
    {
        "core_idea": "x",
        "key_takeaways": ["y"],
        "concepts": [
            {
                "name": "Three-way handshake",
                "one_liner": "a",
                "why_it_exists": "b",
                "how_it_works": ["c"],
                "analogy": {"text": "d", "where_it_breaks": "e"},
                "example": "f",
            }
        ],
    }
)


def test_match_concept_exact_and_partial():
    assert match_concept("three-way handshake", BRAIN).name == "Three-way handshake"
    assert match_concept("handshake", BRAIN).name == "Three-way handshake"
    assert match_concept("congestion", BRAIN) is None


def test_assemble_swaps_and_drops_placeholders():
    md = "intro\n\n[[VISUAL: Handshake]]\n\n[[VISUAL: Unknown]]\n\nend"
    visuals = {
        "Handshake": VisualOutput(
            concept="Handshake", type="mermaid", code="flowchart LR\n A-->B", caption="Look"
        )
    }
    out = assemble(md, visuals)
    assert "```mermaid" in out and "*Look*" in out
    assert "[[VISUAL" not in out


def test_run_reuses_callers_logger(tmp_path, monkeypatch):
    from notes_forge import pipeline
    from notes_forge.llm import LLM, RunLogger

    logger = RunLogger(run_id="mine", root=str(tmp_path))
    llm = LLM(client=object(), logger=logger)

    def no_second_logger(*_args, **_kwargs):
        raise AssertionError("pipeline created a second run folder")

    def stop(*_args, **_kwargs):
        raise RuntimeError("stop after setup")

    monkeypatch.setattr(pipeline, "RunLogger", no_second_logger)
    monkeypatch.setattr(pipeline.reader, "run", stop)
    try:
        pipeline.run("notes", llm=llm)
    except RuntimeError:
        pass
    assert llm.logger is logger
