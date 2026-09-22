"""Local validation for diagrams before they reach the visual critic.

A Mermaid render error is an automatic fail. If the Mermaid CLI (`mmdc`) is on PATH
we use it; otherwise we fall back to structural checks that catch the common breakages.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

MAX_NODES = 9
MAX_TABLE_ROWS = 5
MAX_TABLE_COLS = 4

DIAGRAM_KEYWORDS = (
    "flowchart", "graph", "sequenceDiagram", "classDiagram", "stateDiagram",
    "stateDiagram-v2", "erDiagram", "timeline", "mindmap", "journey", "gantt",
)
_NODE_ID = re.compile(r"(?:^|[\s;>&|-])([A-Za-z_][\w]*)\s*(?:\[|\(|\{|>)")


def _strip_fence(code: str) -> str:
    code = code.strip()
    if code.startswith("```"):
        code = re.sub(r"^```\w*\n?", "", code)
        code = re.sub(r"\n?```$", "", code)
    return code.strip()


def count_nodes(code: str) -> int:
    body = "\n".join(line for line in code.splitlines()[1:] if not line.strip().startswith("%%"))
    return len(set(_NODE_ID.findall(body)))


def lint_mermaid(code: str) -> list[str]:
    code = _strip_fence(code)
    problems: list[str] = []
    if not code:
        return ["empty mermaid code"]
    first = code.splitlines()[0].strip()
    if not first.startswith(DIAGRAM_KEYWORDS):
        problems.append(f"unknown diagram type: '{first[:30]}'")
    for open_, close in ("[]", "()", "{}"):
        if code.count(open_) != code.count(close):
            problems.append(f"unbalanced '{open_}{close}' brackets")
    if code.count('"') % 2:
        problems.append("unbalanced double quotes")
    if first.startswith(("flowchart", "graph")) and count_nodes(code) > MAX_NODES:
        problems.append(f"more than {MAX_NODES} nodes")
    return problems


def render_mermaid(code: str) -> list[str]:
    """Render with mmdc when available. Returns a list of problems (empty = ok)."""
    problems = lint_mermaid(code)
    mmdc = shutil.which("mmdc")
    if problems or not mmdc:
        return problems
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "d.mmd"
        src.write_text(_strip_fence(code))
        proc = subprocess.run(
            [mmdc, "-i", str(src), "-o", str(Path(tmp) / "d.svg"), "--quiet"],
            capture_output=True, text=True, timeout=60, check=False,
        )
    if proc.returncode != 0:
        return [f"mermaid render error: {(proc.stderr or proc.stdout).strip()[:300]}"]
    return []


def lint_table(markdown: str) -> list[str]:
    rows = [r for r in markdown.strip().splitlines() if r.strip().startswith("|")]
    if len(rows) < 2:
        return ["not a markdown table"]
    body = [r for r in rows[2:]]
    cols = len([c for c in rows[0].strip().strip("|").split("|")])
    problems = []
    if len(body) > MAX_TABLE_ROWS:
        problems.append(f"more than {MAX_TABLE_ROWS} rows")
    if cols > MAX_TABLE_COLS:
        problems.append(f"more than {MAX_TABLE_COLS} columns")
    return problems
