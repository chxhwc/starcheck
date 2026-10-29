# Contributing

Thanks for looking. Two ways to help, both small:

## Add or fix a check

Every check is one function in `src/starcheck/checks.py`:

```python
@check("install", "安装命令在首屏", "conversion", 5)
def _install(ctx: Context) -> Check:
    ...
    return c
```

Rules:

1. **A check must be falsifiable from the repo alone.** If you cannot decide it by
   reading files (or the GitHub API), it does not belong here.
2. **Status is `pass` / `warn` / `fail` / `skip`.** Use `skip` when the data is
   genuinely unavailable (offline, no remote) — never to avoid a decision.
3. **Every non-pass check must carry a `fix`**: something a human can paste.
4. **Weight ≤ 5.** Weights are a budget, not a vote. A single check should never
   move the score by more than ~7 points.
5. **Add a test.** `tests/test_starcheck.py` has a fixture builder; extend it.

## Run it

```bash
python -m unittest discover -s tests -v   # no deps, no venv, stdlib only
python -m starcheck . --no-color          # audit this repo
PYTHONPATH=src python -m starcheck .
```

Windows: `$env:PYTHONPATH="src"` first.

## Style

- stdlib only. A dependency is a bug unless there is no other way.
- No network calls outside `remote.py`.
- Every output path must work on a GBK console (see `Glyphs` in `render.py`).

## Pull requests

Small PRs land fast. If you are adding a dimension or changing the scoring model,
open an issue first — that is a 30-second conversation that saves a rewrite.
