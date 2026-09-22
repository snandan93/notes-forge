# Evals

Real notes the pipeline should handle well. Rerun after every prompt change and compare
against the previous `results.csv`.

```bash
notes-forge eval            # all cases in evals/cases
notes-forge eval -k dns     # only cases whose name contains "dns"
```

Each case writes its improved notes to `evals/out/` and one row to `evals/results.csv`:
case, passed, score, attempts, run folder.

To add a case, drop a `.md` or image file in `evals/cases/`. Aim for 20 real notes with a
mix of topics and levels, including a few with deliberate mistakes.
