from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from notes_forge.llm import LLM, AgentError, extract_json


class Out(BaseModel):
    value: int


def test_extract_json_plain():
    assert extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_with_fence_and_prose():
    reply = 'Here you go:\n```json\n{"a": {"b": 2}}\n```\nDone.'
    assert extract_json(reply) == {"a": {"b": 2}}


def test_extract_json_takes_last_object():
    assert extract_json('draft {"a": 1} final {"a": 2}') == {"a": 2}


def test_extract_json_raises_without_object():
    with pytest.raises(ValueError):
        extract_json("no json here")


class FakeMessages:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def create(self, **params):
        self.calls.append(params)
        text = self.replies.pop(0)
        return SimpleNamespace(
            stop_reason="end_turn", content=[SimpleNamespace(type="text", text=text)]
        )


def fake_client(*replies):
    return SimpleNamespace(messages=FakeMessages(replies))


def test_call_json_retries_once_on_bad_json():
    client = fake_client("oops", '{"value": 3}')
    result = LLM(client=client).call_json("reader", "hi", Out)
    assert result.value == 3
    assert len(client.messages.calls) == 2


def test_call_json_gives_up_after_retry():
    client = fake_client("oops", "still bad")
    with pytest.raises(AgentError):
        LLM(client=client).call_json("reader", "hi", Out)
