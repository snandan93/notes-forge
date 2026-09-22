from notes_forge.evals import CaseResult, find_cases, summary, write_results


def test_find_cases_filters_by_suffix_and_keyword(tmp_path):
    for name in ["dns.md", "tcp.md", "notes.pdf", "photo.jpg"]:
        (tmp_path / name).write_text("x")
    assert [p.name for p in find_cases(tmp_path)] == ["dns.md", "photo.jpg", "tcp.md"]
    assert [p.name for p in find_cases(tmp_path, "DNS")] == ["dns.md"]


def test_results_csv_and_summary(tmp_path):
    results = [CaseResult("a", True, 9.0, 1, "runs/a"), CaseResult("b", False, 6.0, 3, "runs/b")]
    out = tmp_path / "results.csv"
    write_results(results, out)
    assert out.read_text().splitlines()[0] == "case,passed,score,attempts,run_dir"
    assert summary(results) == "1/2 passed · avg score 7.50"
