"""Command line entry point."""

from __future__ import annotations

import logging
import mimetypes
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from notes_forge import __version__, diagrams, evals, pipeline
from notes_forge.agents.reader import IMAGE_TYPES

app = typer.Typer(add_completion=False, help="Turn rough study notes into clear, sourced notes.")
console = Console()


@app.command()
def run(
    notes: Annotated[
        Path, typer.Argument(exists=True, readable=True, help="Notes (.md/.txt) or image")
    ],
    out: Annotated[
        Path | None, typer.Option("--out", "-o", help="Where to write the final notes")
    ] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """Improve a notes file end to end."""
    logging.basicConfig(level=logging.INFO if verbose else logging.WARNING)
    is_image = (mimetypes.guess_type(notes.name)[0] or "") in IMAGE_TYPES
    with console.status("Starting…") as status:
        result = pipeline.run(
            None if is_image else notes.read_text(encoding="utf-8"),
            image=notes if is_image else None,
            progress=lambda msg: status.update(msg + "…"),
        )

    target = out or notes.with_name(f"{notes.stem}.improved.md")
    target.write_text(result.markdown, encoding="utf-8")
    colour = "green" if result.passed else "yellow"
    label = "passed" if result.passed else "needs review"
    console.print(f"[{colour}]{label}[/] · score {result.score} · {result.attempts} attempt(s)")
    console.print(f"Notes: {target}\nRun log: {result.run_dir}")


@app.command("lint-diagram")
def lint_diagram(path: Annotated[Path, typer.Argument(exists=True)]) -> None:
    """Check a Mermaid file against the diagram rules."""
    problems = diagrams.render_mermaid(path.read_text(encoding="utf-8"))
    if problems:
        for p in problems:
            console.print(f"[red]✗[/] {p}")
        raise typer.Exit(1)
    console.print("[green]✓[/] diagram looks good")


@app.command("eval")
def run_evals(
    cases: Annotated[Path, typer.Option("--cases", help="Folder of sample notes")] = Path(
        "evals/cases"
    ),
    keyword: Annotated[str | None, typer.Option("-k", help="Only cases matching this")] = None,
) -> None:
    """Run the pipeline on every sample note and record scores."""
    paths = evals.find_cases(cases, keyword)
    if not paths:
        console.print("[yellow]no cases found[/]")
        raise typer.Exit(1)
    root = cases.parent
    results = []
    with console.status("Starting…") as status:
        for path in paths:
            results.append(
                evals.run_case(path, root / "out", lambda msg: status.update(msg + "…"))
            )
    evals.write_results(results, root / "results.csv")
    for r in results:
        mark = "[green]✓[/]" if r.passed else "[yellow]![/]"
        console.print(f"{mark} {r.case}: score {r.score}, {r.attempts} attempt(s)")
    console.print(evals.summary(results))


@app.command()
def version() -> None:
    console.print(__version__)


if __name__ == "__main__":
    app()
