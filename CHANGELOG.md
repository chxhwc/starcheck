# Changelog

All notable changes to this project. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
versioning: [SemVer](https://semver.org/).

## [Unreleased]

### Planned
- `--fix --apply` writes the missing files instead of printing commands
- star median comparison against sibling repos in the same topic
- official GitHub Action wrapper

## [0.4.0] — 2026-10-29

### Added
- 28 checks across 4 weighted dimensions (discovery / conversion / credibility / distribution)
- terminal card with per-dimension subscores and the top 3 fixes
- `--json`, `--markdown FILE`, `--badge FILE`, `--fix`, `--fail-under N`
- remote mode: `owner/repo` or a GitHub URL → shallow clone + API metadata
- ASCII glyph fallback for consoles that cannot encode box drawing
- `assets/demo.gif` generated from real output by `tools/make_assets.py`

## [0.1.0] — 2026-10-20

### Added
- first sketch: 9 README-only checks, no dimensions, no score

[Unreleased]: https://github.com/chxhwc/starcheck/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/chxhwc/starcheck/releases/tag/v0.4.0
[0.1.0]: https://github.com/chxhwc/starcheck/releases/tag/v0.1.0
