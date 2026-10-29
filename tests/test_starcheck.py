import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from starcheck.checks import build_context, run_checks  # noqa: E402
from starcheck.remote import parse_target  # noqa: E402
from starcheck.render import _w, badge_svg, render_card, render_markdown  # noqa: E402
from starcheck.score import grade_for, score  # noqa: E402


def write(root: Path, rel: str, content: str = "x") -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


GOOD_README = """# mytool: replace the thing you hate in one command

A zero-dependency CLI that does the boring part so you stop doing it by hand every morning.

![demo](assets/demo.gif)

[![license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![ci](https://img.shields.io/badge/ci-passing-green.svg)](.github)

## Why

- 3x faster than the tool you are using now
- one binary, no runtime
- works offline

## Quick start

```bash
uvx mytool .
```

```console
$ mytool .
done in 0.4s
```
"""


def make_repo(root: Path, full: bool = True) -> None:
    write(root, "README.md", GOOD_README)
    write(root, "pyproject.toml", 'description = "x"\nkeywords = ["a", "b", "c", "d", "e"]\n')
    if not full:
        return
    write(root, "LICENSE", "MIT")
    write(root, "CHANGELOG.md", "# 0.1.0")
    write(root, "CONTRIBUTING.md", "prs welcome")
    write(root, "SECURITY.md", "report privately")
    write(root, "action.yml", "runs: {}")
    write(root, ".github/workflows/ci.yml", "on: push")
    write(root, ".github/ISSUE_TEMPLATE/bug.yml", "name: bug")
    write(root, ".github/dependabot.yml", "version: 2")
    write(root, "tests/test_thing.py", "def test_x(): assert True")
    write(root, "assets/social.png", "png")
    write(root, "docs/index.md", "# docs")
    write(root, "README.zh-CN.md", "# 中文")


class CheckTests(unittest.TestCase):
    def setUp(self):
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def by_id(self, checks):
        return {c.id: c for c in checks}

    def test_full_repo_passes_core_checks(self):
        make_repo(self.root, full=True)
        ctx = build_context(self.root)
        checks = self.by_id(run_checks(ctx))
        for cid in ("license", "ci", "tests", "changelog", "install", "visual", "hook", "features"):
            self.assertEqual(checks[cid].status, "pass", f"{cid}: {checks[cid].detail}")

    def test_bare_repo_fails_discovery(self):
        make_repo(self.root, full=False)
        (self.root / "README.md").write_text("# empty\n", encoding="utf-8")
        checks = self.by_id(run_checks(build_context(self.root)))
        self.assertEqual(checks["license"].status, "fail")
        self.assertEqual(checks["ci"].status, "fail")
        self.assertEqual(checks["quickstart"].status, "fail")

    def test_remote_only_checks_are_skipped_offline(self):
        make_repo(self.root)
        checks = self.by_id(run_checks(build_context(self.root, remote={})))
        for cid in ("desc", "topics", "homepage"):
            self.assertEqual(checks[cid].status, "skip")

    def test_remote_metadata_is_used_when_present(self):
        make_repo(self.root)
        remote = {
            "name": "mytool",
            "description": "A zero-dependency CLI that eats boring work.",
            "topics": [f"t{i}" for i in range(12)],
            "homepage": "https://mytool.dev",
            "has_pages": True,
        }
        checks = self.by_id(run_checks(build_context(self.root, remote=remote)))
        self.assertEqual(checks["desc"].status, "pass")
        self.assertEqual(checks["topics"].status, "pass")
        self.assertEqual(checks["homepage"].status, "pass")
        self.assertEqual(checks["docs-site"].status, "pass")

    def test_check_crash_never_breaks_run(self):
        make_repo(self.root)
        checks = run_checks(build_context(self.root))
        self.assertEqual(len(checks), 28)
        self.assertTrue(all(c.status in ("pass", "warn", "fail", "skip") for c in checks))


class ScoreTests(unittest.TestCase):
    def test_grade_boundaries(self):
        self.assertEqual(grade_for(100), "A+")
        self.assertEqual(grade_for(88), "A")
        self.assertEqual(grade_for(70), "B")
        self.assertEqual(grade_for(0), "E")

    def test_weighted_score_math(self):
        from starcheck.checks import Check

        checks = [
            Check("a", "A", "discovery", 10, "pass"),
            Check("b", "B", "discovery", 10, "fail"),
            Check("c", "C", "conversion", 20, "warn"),
        ]
        result = score(checks)
        self.assertEqual(result.total, 40)
        self.assertEqual(result.score, 50)  # 10 + 0 + 10
        self.assertEqual(result.earned, 20)

    def test_skips_are_excluded_from_denominator(self):
        from starcheck.checks import Check

        checks = [
            Check("a", "A", "discovery", 10, "pass"),
            Check("b", "B", "discovery", 10, "skip"),
        ]
        self.assertEqual(score(checks).score, 100)

    def test_failed_is_sorted_by_weight_then_severity(self):
        from starcheck.checks import Check

        checks = [
            Check("a", "A", "discovery", 1, "fail"),
            Check("b", "B", "discovery", 5, "warn"),
            Check("c", "C", "discovery", 5, "fail"),
        ]
        self.assertEqual([c.id for c in score(checks).failed][:2], ["c", "b"])


class RenderTests(unittest.TestCase):
    def setUp(self):
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        make_repo(self.root, full=True)
        self.ctx = build_context(self.root)
        self.result = score(run_checks(self.ctx))

    def tearDown(self):
        self._tmp.cleanup()

    def test_every_card_line_has_equal_display_width(self):
        card = render_card(self.result, self.ctx, color=False)
        widths = {_w(line) for line in card.splitlines()}
        self.assertEqual(len(widths), 1, f"ragged card: {widths}")

    def test_card_contains_score_and_grade(self):
        card = render_card(self.result, self.ctx, color=False)
        self.assertIn(f"{self.result.score}/100", card)
        self.assertIn(self.result.grade, card)

    def test_markdown_report_has_tables(self):
        md = render_markdown(self.result, self.ctx)
        self.assertIn("| 维度 | 得分 |", md)
        self.assertIn(str(self.result.score), md)

    def test_badge_svg_is_valid_looking(self):
        svg = badge_svg(self.result)
        self.assertTrue(svg.startswith("<svg"))
        self.assertIn(str(self.result.score), svg)
        self.assertIn("</svg>", svg)


class TargetTests(unittest.TestCase):
    def test_parse_target_forms(self):
        self.assertEqual(parse_target("psf/requests"), ("psf", "requests"))
        self.assertEqual(parse_target("https://github.com/psf/requests"), ("psf", "requests"))
        self.assertEqual(parse_target("git@github.com:psf/requests.git"), ("psf", "requests"))
        self.assertIsNone(parse_target("./local/path"))


class CliTests(unittest.TestCase):
    def setUp(self):
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def run_cli(self, argv):
        """Call main() in-process: robust where pipe capture is restricted."""
        import contextlib
        import io

        from starcheck.cli import main

        buf_out, buf_err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
            code = main(argv)
        return code, buf_out.getvalue(), buf_err.getvalue()

    def test_json_mode_parses(self):
        import json

        make_repo(self.root)
        code, out, err = self.run_cli([str(self.root), "--json"])
        self.assertEqual(code, 0, err)
        data = json.loads(out)
        self.assertEqual(len(data["checks"]), 28)
        self.assertGreater(data["score"], 70)

    def test_fail_under_exits_one(self):
        (self.root / "README.md").write_text("# nothing", encoding="utf-8")
        code, out, _ = self.run_cli([str(self.root), "--fail-under", "90", "--no-color"])
        self.assertEqual(code, 1)
        self.assertIn("/100", out)

    def test_badge_and_markdown_are_written(self):
        make_repo(self.root)
        md = self.root / "REPORT.md"
        svg = self.root / "score.svg"
        code, _, _ = self.run_cli(
            [str(self.root), "--no-color", "--markdown", str(md), "--badge", str(svg)]
        )
        self.assertEqual(code, 0)
        self.assertTrue(md.read_text(encoding="utf-8").startswith("# starcheck"))
        self.assertIn("<svg", svg.read_text(encoding="utf-8"))

    def test_fix_mode_prints_commands(self):
        (self.root / "README.md").write_text("# nothing", encoding="utf-8")
        _, _, err = self.run_cli([str(self.root), "--fix", "--no-color"])
        self.assertIn("gh repo edit", err)


if __name__ == "__main__":
    unittest.main()
