<div align="center">

# starcheck

**Your repo is good. That is why nobody stars it.**

28 checks → one score → the 3 fixes that actually move it.

[![CI](https://github.com/chxhwc/starcheck/actions/workflows/ci.yml/badge.svg)](https://github.com/chxhwc/starcheck/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/starcheck.svg)](https://pypi.org/project/starcheck/)
[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](#)
[![runtime deps](https://img.shields.io/badge/runtime%20deps-0-brightgreen.svg)](#)
[![license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![self-score](assets/score.svg)](docs/SCORECARD.md)

[Quick start](#quick-start) · [What it checks](#what-it-checks) · [Use in CI](#use-in-ci) · [中文说明](README.zh-CN.md)

</div>

![starcheck auditing a repo](assets/demo.gif)

## Quick start

```bash
uvx starcheck              # audit the repo you are standing in — no install
starcheck owner/repo       # audit someone else's (shallow clone + GitHub API)
```

<sub>Not on PyPI yet? `pip install git+https://github.com/chxhwc/starcheck` works today.</sub>

```console
$ starcheck .
┌──────────────────────────────────────────────────────────────────────────┐
│ starcheck · my-lib                                           62/100  C   │
├──────────────────────────────────────────────────────────────────────────┤
│ ██████████████░░░░░░░░  62/100                                            │
│ 发现 78   转化 44   可信 71   分发 37                                     │
├──────────────────────────────────────────────────────────────────────────┤
│   ✔ 安装命令在首屏            首屏就能看到 `pip install my-lib`            │
│   ✘ 演示图 / GIF              README 里没有任何演示图                      │
│   ! 多语言 README             只有一种语言                                │
└──────────────────────────────────────────────────────────────────────────┘
```

Then:

```bash
starcheck . --fix        # paste-ready commands for every failure
starcheck . --json       # machine readable (score, grade, all 28 checks)
starcheck . --badge score.svg --markdown REPORT.md
starcheck . --fail-under 80    # exit 1 below 80 — drop it in CI
```

## Why

Because the advice you get is always the same and always useless:

> "Write a good README, add a license, post it on Hacker News."

Three true statements, zero ordering, zero way to tell whether you are done.
`starcheck` exists to make that advice **falsifiable**:

- **Weighted, not a checklist.** A checklist says 20 things are wrong and you fix
  none. Weights say: fix the README hook and the GIF, ignore `SECURITY.md` this week.
- **Falsifiable, not vibes.** Every check reads a file or an API field. Nothing is
  a matter of taste, so you can argue with it and win.
- **Fix-first.** A failure without a paste-ready command is just criticism.

## The 30-second version

Stars are not a code-quality metric. They are:

```
stars  ≈  exposure  ×  first-screen conversion  ×  reuse frequency
```

Almost every "good repo nobody stars" fails the middle term for reasons that have
nothing to do with code: no description, 2 topics, no demo image, install command
240 lines down, README that opens with a table of contents instead of a reason to
care. `starcheck` turns that vague advice into 28 falsifiable checks, weighted so
that the things that actually kill conversion cost the most points.

## What it checks

| 维度 | 权重 | 看什么 |
| --- | --- | --- |
| **发现** discovery | 24 | description · topics · license · 仓库名 · 社交预览图 · homepage · README 首屏钩子 |
| **转化** conversion | 26 | 首屏安装命令 · 代码块 · GIF · 徽章 · Why 段落 · Quick start · 多语言 · README 长度 |
| **可信** credibility | 15 | CI · 测试 · tag/Release · CHANGELOG · CONTRIBUTING · issue 模板 · SECURITY · 提交新鲜度 · 依赖机器人 |
| **分发** distribution | 7 | Pages/文档站 · 包元数据与 keywords · action.yml · awesome-list 收录 |

Grades: `A+ ≥95`, `A ≥88`, `B ≥70`, `C ≥55`, `D ≥35`, `E < 35`.

Every check is one function in [`src/starcheck/checks.py`](src/starcheck/checks.py)
— readable, testable, and easy to argue with. Full table with evidence and weights:
[docs/SCORECARD.md](docs/SCORECARD.md).

## Design rules

1. **Stdlib only, always.** A dependency would defeat the point: you should be
   able to run this on a locked-down machine in a 3-second `uvx` call.
2. **A check must be decidable from the repo alone.** If it needs a human
   judgement call, it belongs in docs, not in code.
3. **`skip` is not `fail`.** Offline and local mode cannot see your description
   or topics, so those drop out of the denominator instead of pretending to fail.
4. **Every failure carries a fix you can paste.** No "consider improving your README".
5. **It never runs your code.** `starcheck` reads files as text. That is all.
6. **It renders on a GBK console.** See `Glyphs` in `render.py`; the whole layout
   degrades to ASCII rather than crashing on `█`.

## Use in CI

```yaml
- uses: actions/checkout@v4
- run: pipx run starcheck . --fail-under 85
```

Or as an action, with the report in your job summary:

```yaml
- uses: chxhwc/starcheck@v0.4.0
  with:
    fail-under: 85
```

## Exit codes

| code | meaning |
| --- | --- |
| 0 | ran fine (score whatever it is) |
| 1 | `--fail-under` not met |
| 2 | bad path or usage |

## Limits

`starcheck` scores **readiness**, not results. It cannot see your traffic, your
conversion, or whether your idea is interesting. A 100 here with a boring idea is
still a boring idea — it just gets read twice before being closed.

## Roadmap

- [x] 28 checks, weighted score, terminal card
- [x] `--json` / `--markdown` / `--badge` / `--fix` / `--fail-under`
- [x] remote mode: `owner/repo` via shallow clone + API
- [x] ASCII fallback for consoles without UTF-8
- [ ] `--fix --apply`: write the missing files instead of printing commands
- [ ] median comparison against sibling repos in the same topic
- [ ] web version that scores a repo from a URL, no install

## Contributing

Adding a check is ~15 lines. [`CONTRIBUTING.md`](CONTRIBUTING.md) has the rules
(weight ≤ 5, must carry a fix, must ship a test). Tests are stdlib-only:

```bash
python -m unittest discover -s tests -v
```

## License

MIT
