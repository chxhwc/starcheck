"""starcheck CLI."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from starcheck import __version__
from starcheck import remote as gh
from starcheck.checks import build_context, run_checks
from starcheck.score import score

EPILOG = """examples:
  starcheck                          # audit the repo you are standing in
  starcheck ../my-lib                # audit any local path
  starcheck chxhwc/starcheck     # audit a GitHub repo (shallow clone + API)
  starcheck --json | jq .score       # machine readable
  starcheck --badge score.svg        # SVG badge for the README
"""


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="starcheck",
        description="Audit any repo for star-readiness. 28 checks, one score, copy-paste fixes.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("target", nargs="?", default=".", help="local path, owner/repo, or GitHub URL")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--markdown", metavar="FILE", help="write a markdown report")
    ap.add_argument("--badge", metavar="FILE", help="write an SVG score badge")
    ap.add_argument("--fix", action="store_true", help="print the exact commands to fix failures")
    ap.add_argument("--no-color", action="store_true", help="disable ANSI color")
    ap.add_argument("--ascii", action="store_true", help="force ASCII box drawing (no UTF-8 glyphs)")
    ap.add_argument("--fail-under", type=int, default=None, metavar="N", help="exit 1 if score < N")
    ap.add_argument("--version", action="version", version=f"starcheck {__version__}")
    return ap


def resolve(target: str):
    """-> (root Path, remote meta dict, cleanup Path or None)"""
    as_remote = gh.parse_target(target) if not Path(target).exists() or target.startswith("http") else None
    if as_remote:
        owner, repo = as_remote
        meta = gh.fetch(owner, repo)
        tmp = Path(tempfile.mkdtemp(prefix="starcheck-"))
        dest = tmp / repo
        if gh.shallow_clone(owner, repo, dest):
            return dest, meta, tmp
        return Path.cwd(), meta, tmp

    if target.startswith("http") or "/" in target and not Path(target).exists():
        parsed = gh.parse_target(target)
        if parsed:
            return Path.cwd(), gh.fetch(*parsed), None

    root = Path(target)
    if not root.exists():
        raise SystemExit(f"starcheck: no such path: {target}")
    from starcheck.checks import git_info, parse_origin

    info = git_info(root)
    parsed = parse_origin(info.get("origin", ""))
    meta = gh.fetch(*parsed) if parsed else {}
    return root, meta, None


def _configure_stdio() -> None:
    """Windows consoles default to GBK; CJK output and piped JSON need UTF-8."""
    for stream in (sys.stdout, sys.stderr):
        try:
            if hasattr(stream, "reconfigure"):
                enc = (getattr(stream, "encoding", "") or "").lower()
                if enc.replace("-", "") not in ("utf8", "utf8mb4"):
                    stream.reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError, AttributeError):
            pass


def main(argv=None) -> int:
    _configure_stdio()
    from starcheck.render import ASCII, badge_svg, dumps, render_card, render_markdown, use_color

    args = build_parser().parse_args(argv)

    try:
        root, meta, cleanup = resolve(args.target)
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        return 2

    try:
        ctx = build_context(root, meta)
        result = score(run_checks(ctx))

        color = use_color() and not args.no_color
        if args.json:
            print(dumps(result, ctx))
        else:
            print(render_card(result, ctx, color, glyphs=ASCII if args.ascii else None))

        if args.markdown:
            Path(args.markdown).write_text(render_markdown(result, ctx), encoding="utf-8")
            print(f"\nmarkdown 已写入 {args.markdown}", file=sys.stderr)
        if args.badge:
            Path(args.badge).write_text(badge_svg(result), encoding="utf-8")
            print(f"badge 已写入 {args.badge}", file=sys.stderr)

        if args.fix:
            todo = [c for c in result.checks if c.status in ("fail", "warn") and c.fix]
            unverified = [c for c in result.checks if c.status == "skip" and c.fix]
            if todo:
                print("\n# 按优先级排好的修复命令\n", file=sys.stderr)
                for c in todo:
                    print(f"# [{c.status}] {c.title} — {c.detail}", file=sys.stderr)
                    print(c.fix, file=sys.stderr)
                    print(file=sys.stderr)
            if unverified:
                print("# 本地模式无法验证，联网后手动确认：\n", file=sys.stderr)
                for c in unverified:
                    print(f"# {c.title} — {c.detail}", file=sys.stderr)
                    print(c.fix, file=sys.stderr)
                    print(file=sys.stderr)

        if args.fail_under is not None and result.score < args.fail_under:
            return 1
        return 0
    finally:
        if cleanup:
            import shutil

            shutil.rmtree(cleanup, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
