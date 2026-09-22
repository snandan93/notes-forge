"""Run the pipeline over a folder of sample notes and record scores for regression checks."""

from __future__ import annotations

import csv
import mimetypes
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from notes_forge import pipeline
from notes_forge.agents.reader import IMAGE_TYPES

CASE_SUFFIXES = {".md", ".txt", ".png", ".jpg", ".jpeg", ".webp", ".gif"}
FIELDS = ["case", "passed", "score", "attempts", "run_dir"]


@dataclass
class CaseResult:
    case: str
    passed: bool
    score: float
    attempts: int
    run_dir: str


def find_cases(folder: Path, keyword: str | None = None) -> list[Path]:
    cases = sorted(p for p in folder.iterdir() if p.suffix.lower() in CASE_SUFFIXES)
    if keyword:
        cases = [p for p in cases if keyword.lower() in p.stem.lower()]
    return cases


def run_case(path: Path, out_dir: Path, progress: Callable[[str], None]) -> CaseResult:
    is_image = (mimetypes.guess_type(path.name)[0] or "") in IMAGE_TYPES
    result = pipeline.run(
        None if is_image else path.read_text(encoding="utf-8"),
        image=path if is_image else None,
        progress=lambda msg: progress(f"{path.stem}: {msg}"),
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{path.stem}.md").write_text(result.markdown, encoding="utf-8")
    return CaseResult(path.stem, result.passed, result.score, result.attempts, str(result.run_dir))


def write_results(results: list[CaseResult], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        for r in results:
            writer.writerow({f: getattr(r, f) for f in FIELDS})


def summary(results: list[CaseResult]) -> str:
    if not results:
        return "no cases run"
    passed = sum(r.passed for r in results)
    avg = sum(r.score for r in results) / len(results)
    return f"{passed}/{len(results)} passed · avg score {avg:.2f}"
