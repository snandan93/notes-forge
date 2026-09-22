"""Thin wrapper around the Anthropic Messages API.

Every agent goes through `call_json`: send a prompt, pull JSON out of the reply,
validate it against a pydantic model, and retry once with the validation error
if the model returned something malformed.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any, TypeVar

import anthropic
from pydantic import BaseModel, ValidationError

from notes_forge.config import settings

log = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

MAX_PAUSE_CONTINUATIONS = 5


class AgentError(RuntimeError):
    pass


class RunLogger:
    """Writes each agent's input and output to runs/<run_id>/ so bad outputs can be traced."""

    def __init__(self, run_id: str | None = None, root: str | None = None):
        self.run_id = run_id or time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
        self.dir = Path(root or settings.runs_dir) / self.run_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self._step = 0

    def write(self, agent: str, payload: dict[str, Any]) -> None:
        self._step += 1
        path = self.dir / f"{self._step:02d}-{agent}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def extract_json(text: str) -> Any:
    """Find the JSON object in a reply, tolerating code fences and stray prose."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    found: Any = None
    idx = text.find("{")
    while idx != -1:
        try:
            obj, end = decoder.raw_decode(text, idx)
        except json.JSONDecodeError:
            idx = text.find("{", idx + 1)
            continue
        found = obj  # keep the last complete object; final answers come last
        idx = text.find("{", end)
    if found is None:
        raise ValueError("no JSON object found in model reply")
    return found


def _text_of(content: list[Any]) -> str:
    return "\n".join(block.text for block in content if getattr(block, "type", "") == "text")


class LLM:
    def __init__(self, client: anthropic.Anthropic | None = None, logger: RunLogger | None = None):
        self.client = client or anthropic.Anthropic()
        self.logger = logger

    def _send(
        self,
        agent: str,
        messages: list[dict[str, Any]],
        system: str | None,
        tools: list[dict[str, Any]] | None,
    ) -> str:
        cfg = settings.agent(agent)
        params: dict[str, Any] = {
            "model": cfg.model,
            "max_tokens": cfg.max_tokens,
            "messages": messages,
        }
        if system:
            params["system"] = system
        if tools:
            params["tools"] = tools
        if cfg.temperature is not None:
            params["temperature"] = cfg.temperature

        text_parts: list[str] = []
        for _ in range(MAX_PAUSE_CONTINUATIONS + 1):
            response = self.client.messages.create(**params)
            if response.stop_reason == "refusal":
                raise AgentError(f"{agent}: model declined the request")
            text_parts.append(_text_of(response.content))
            if response.stop_reason != "pause_turn":
                break
            # Long server-tool turns (web search) pause; send the partial turn back to resume.
            params["messages"] = [
                *params["messages"],
                {"role": "assistant", "content": response.content},
            ]
        if response.stop_reason == "max_tokens":
            log.warning("%s hit max_tokens; output may be truncated", agent)
        return "\n".join(text_parts)

    def call_json(
        self,
        agent: str,
        prompt: str | list[dict[str, Any]],
        schema: type[T],
        *,
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        retries: int = 1,
    ) -> T:
        messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
        last_error = ""
        raw = ""
        for attempt in range(retries + 1):
            started = time.perf_counter()
            raw = self._send(agent, messages, system, tools)
            try:
                result = schema.model_validate(extract_json(raw))
            except (ValueError, ValidationError) as exc:
                last_error = str(exc)
                log.info("%s returned invalid JSON (attempt %d): %s", agent, attempt + 1, exc)
                messages = [
                    *messages,
                    {"role": "assistant", "content": raw or "(empty)"},
                    {
                        "role": "user",
                        "content": "Your reply was not valid for the required JSON schema:\n"
                        f"{last_error}\nReturn only the corrected JSON object.",
                    },
                ]
                continue
            if self.logger:
                self.logger.write(
                    agent,
                    {
                        "prompt": prompt,
                        "raw": raw,
                        "parsed": result.model_dump(by_alias=True),
                        "attempts": attempt + 1,
                        "seconds": round(time.perf_counter() - started, 2),
                    },
                )
            return result

        if self.logger:
            self.logger.write(agent, {"prompt": prompt, "raw": raw, "error": last_error})
        raise AgentError(f"{agent}: invalid JSON after {retries + 1} attempts: {last_error}")
