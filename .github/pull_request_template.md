## What changed

<!-- one sentence -->

## Why

<!-- which repo / which check motivated this -->

## Checklist

- [ ] `python -m unittest discover -s tests` is green
- [ ] `PYTHONPATH=src python -m starcheck . --fail-under 70` still passes
- [ ] new checks return `skip` (not `fail`) when the data genuinely is not available
- [ ] no runtime dependency added
- [ ] output still renders on a GBK console (no Unicode-only glyph outside `Glyphs`)
