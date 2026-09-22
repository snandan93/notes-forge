"""Runtime settings, read from the environment."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class AgentSettings:
    model: str
    max_tokens: int = 16000
    # Only sent to models that still accept sampling params.
    temperature: float | None = None


@dataclass(frozen=True)
class Settings:
    smart_model: str = field(
        default_factory=lambda: os.getenv("NOTES_FORGE_SMART_MODEL", "claude-sonnet-5")
    )
    fast_model: str = field(
        default_factory=lambda: os.getenv("NOTES_FORGE_FAST_MODEL", "claude-haiku-4-5")
    )
    max_attempts: int = 3
    runs_dir: str = field(default_factory=lambda: os.getenv("NOTES_FORGE_RUNS_DIR", "runs"))

    def agent(self, name: str) -> AgentSettings:
        """Model + sampling choice per agent. Smart model for reasoning, fast one for checks."""
        smart = {"planner", "brain", "writer", "visual", "research"}
        if name in smart:
            return AgentSettings(model=self.smart_model)
        low_temp = {"reader", "critic_fact", "critic_clarity", "critic_visual", "quiz_grader"}
        return AgentSettings(
            model=self.fast_model,
            max_tokens=8000,
            temperature=0.2 if name in low_temp else 0.5,
        )


settings = Settings()
