from notes_forge.diagrams import count_nodes, lint_mermaid, lint_table

GOOD = """flowchart TD
    A[Client] --> B[SYN]
    B --> C[SYN-ACK]
    C --> D[ACK]"""


def test_good_flowchart_passes():
    assert lint_mermaid(GOOD) == []
    assert count_nodes(GOOD) == 4


def test_fenced_code_is_accepted():
    assert lint_mermaid(f"```mermaid\n{GOOD}\n```") == []


def test_unbalanced_brackets_fail():
    assert lint_mermaid("flowchart TD\n A[Client --> B[SYN]")


def test_too_many_nodes_fail():
    edges = "\n".join(f"    N{i}[n{i}] --> N{i+1}[n{i+1}]" for i in range(10))
    assert any("nodes" in p for p in lint_mermaid("flowchart TD\n" + edges))


def test_table_limits():
    table = "| a | b |\n|---|---|\n" + "| 1 | 2 |\n" * 6
    assert lint_table(table) == ["more than 5 rows"]
