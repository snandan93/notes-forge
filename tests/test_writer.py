from notes_forge import prompts
from notes_forge.agents.writer import PLACEHOLDER, learner_samples


def test_learner_samples_skips_tiny_lines():
    notes = "TCP\n\nTCP is reliable because it resends lost packets, I think??\n\nok"
    assert "resends lost packets" in learner_samples(notes)
    assert "ok" not in learner_samples(notes).split("\n")


def test_placeholder_pattern():
    md = "text\n[[VISUAL: Three-way handshake]]\nmore"
    assert PLACEHOLDER.findall(md) == ["Three-way handshake"]


def test_revision_block_renders():
    block = prompts.render("writer_revision", attempt_number=2, critic_feedback="1. fix x")
    assert "revision 2" in block and "1. fix x" in block
