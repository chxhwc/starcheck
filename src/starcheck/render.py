"""Renderers: terminal card, markdown report, SVG badge.

Every glyph goes through a `Glyphs` table so the same layout renders on a
GBK console, an ASCII-only pipe, and a font-in-a-GIF pipeline without drifting.
"""

from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
from dataclasses import dataclass

from starcheck.checks import DIMENSIONS
from starcheck.score import Result

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[36m"
GREY = "\033[90m"


@dataclass(frozen=True)
class Glyphs:
    tl: str
    tr: str
    bl: str
    br: str
    h: str
    v: str
    lt: str
    rt: str
    dot: str
    ellipsis: str
    bar_full: str
    bar_empty: str
    ok: str
    warn: str
    fail: str
    skip: str


RICH = Glyphs("┌", "┐", "└", "┘", "─", "│", "├", "┤", "·", "…", "█", "░", "✔", "!", "✘", "·")
ASCII = Glyphs("+", "+", "+", "+", "-", "|", "+", "+", "|", "...", "#", "-", "+", "!", "x", ".")


def _enc_ok(sample: str) -> bool:
    enc = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        sample.encode(enc)
        return True
    except (UnicodeEncodeError, LookupError):
        return False


GLYPHS = RICH if _enc_ok("░█✔✘─│┌┐·…") else ASCII

ICON_COLOR = {"pass": GREEN, "warn": YELLOW, "fail": RED, "skip": GREY}
GRADE_COLOR = {"A+": GREEN, "A": GREEN, "B+": BLUE, "B": BLUE, "C": YELLOW, "D": RED, "E": RED}

ANSI_RX = re.compile(r"\033\[[0-9;]*m")


class Painter:
    def __init__(self, enabled: bool):
        self.enabled = enabled

    def __call__(self, text: str, *codes: str) -> str:
        if not self.enabled or not codes:
            return text
        return "".join(codes) + text + RESET


def use_color(stream=None) -> bool:
    stream = stream or sys.stdout
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return bool(getattr(stream, "isatty", lambda: False)())


def _w(text: str) -> int:
    """Display width: CJK counts 2, ANSI escapes count 0.

    Only East-Asian *wide/fullwidth* characters count 2. Ambiguous ones
    (· — “ ” ─) count 1, which is what Cascadia Mono, Consolas, Menlo and
    every default terminal font actually draw. Check text therefore sticks to
    ASCII dashes so the same layout survives a CJK font too (see tools/).
    """
    plain = ANSI_RX.sub("", text)
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in plain)


def _clip(text: str, room: int, ellipsis: str = "…") -> str:
    if room <= 0:
        return ""
    if _w(text) <= room:
        return text
    budget = room - _w(ellipsis)
    out, used = "", 0
    for ch in text:
        cells = 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
        if used + cells > budget:
            break
        out += ch
        used += cells
    return out + ellipsis


def _pad(text: str, room: int) -> str:
    return text + " " * max(0, room - _w(text))


def _bar(value: int, g: Glyphs, width: int = 22) -> str:
    filled = round(width * max(0, min(100, value)) / 100)
    return g.bar_full * filled + g.bar_empty * (width - filled)


def _row(p: Painter, segments, width: int, g: Glyphs) -> str:
    """segments: list of (text, color codes tuple). Pads to `width` display cols."""
    body = ""
    used = 0
    for text, codes in segments:
        body += p(text, *codes)
        used += _w(text)
    return p(g.v, GREY) + body + " " * max(0, width - used) + p(g.v, GREY)


def render_card(result: Result, ctx, color: bool = True, width: int = 74, glyphs: Glyphs = None) -> str:
    g = glyphs or GLYPHS
    p = Painter(color)
    out = []
    accent = GRADE_COLOR.get(result.grade, BLUE)

    title = f" starcheck {g.dot} {ctx.name}"
    score_txt = f"{result.score:>3}/100  {result.grade} "
    gap = max(0, width - _w(title) - _w(score_txt))
    out.append(p(g.tl + g.h * width + g.tr, GREY))
    out.append(_row(p, [(title + " " * gap, (BOLD,)), (score_txt, (BOLD,))], width, g))
    out.append(p(g.lt + g.h * width + g.rt, GREY))

    out.append(
        _row(
            p,
            [
                (" ", ()),
                (_bar(result.score, g), (accent,)),
                ("  ", ()),
                (str(result.score), (BOLD, accent)),
                ("/100", ()),
            ],
            width,
            g,
        )
    )

    dim_segs = [(" ", ())]
    for i, d in enumerate(result.by_dim.values()):
        if i:
            dim_segs.append(("   ", ()))
        dim_segs.append((f"{d['label']} ", (DIM,)))
        dim_segs.append((f"{d['score'] if d['score'] is not None else '--'}", (DIM,)))
    out.append(_row(p, dim_segs, width, g))
    out.append(p(g.lt + g.h * width + g.rt, GREY))

    current = None
    for c in result.checks:
        if c.dimension != current:
            current = c.dimension
            label, tagline = DIMENSIONS[c.dimension]
            head = f" {label} {g.dot} {tagline} "
            out.append(
                p(g.v, GREY) + p(head + g.h * max(0, width - _w(head)), GREY, DIM) + p(g.v, GREY)
            )
        icon = {"pass": g.ok, "warn": g.warn, "fail": g.fail, "skip": g.skip}.get(c.status, "?")
        name_col = 27
        detail_room = width - 4 - name_col
        name = _pad(_clip(c.title, name_col - 1, g.ellipsis), name_col)
        detail = _pad(_clip(c.detail or "", detail_room, g.ellipsis), detail_room)
        out.append(
            p(g.v, GREY)
            + "  "
            + p(icon, ICON_COLOR.get(c.status, GREY))
            + " "
            + name
            + p(detail, GREY)
            + p(g.v, GREY)
        )

    out.append(p(g.lt + g.h * width + g.rt, GREY))
    fixes = result.failed[:3]
    if fixes:
        out.append(_row(p, [(" 下一步优先做这 3 件：", (BOLD,))], width, g))
        for i, c in enumerate(fixes, 1):
            fix = c.fix or c.detail
            prefix = f"  {i}. "
            label = f"{c.title}："
            room = width - 3 - _w(prefix) - _w(label)
            out.append(
                _row(p, [(prefix, ()), (label, (BOLD,)), (_clip(fix, room, g.ellipsis), (GREY,))], width, g)
            )
    else:
        out.append(_row(p, [(" 全部通过，可以发了。", (GREEN,))], width, g))

    if result.skipped:
        note = f" {result.skipped} 项因缺少 GitHub 元数据被跳过（--remote owner/repo 补齐）"
        out.append(_row(p, [(_clip(note, width - 1, g.ellipsis), (GREY,))], width, g))

    out.append(p(g.bl + g.h * width + g.br, GREY))
    return "\n".join(out)


def render_markdown(result: Result, ctx) -> str:
    lines = [
        f"# starcheck — {ctx.name}",
        "",
        f"**{result.score}/100 · {result.grade}**",
        "",
        "| 维度 | 得分 |",
        "| --- | --- |",
    ]
    for d in result.by_dim.values():
        lines.append(f"| {d['label']} | {d['score'] if d['score'] is not None else '—'} |")

    lines += ["", "| 状态 | 检查项 | 说明 |", "| --- | --- | --- |"]
    mark = {"pass": "✅", "warn": "⚠️", "fail": "❌", "skip": "➖"}
    for c in result.checks:
        lines.append(f"| {mark[c.status]} | {c.title} | {c.detail} |")

    if result.failed:
        lines += ["", "## 优先修复", ""]
        for i, c in enumerate(result.failed[:5], 1):
            lines.append(f"{i}. **{c.title}** — {c.fix or c.detail}")

    lines += ["", "---", "", "由 `starcheck` 生成 · https://github.com/chxhwc/starcheck", ""]
    return "\n".join(lines)


def badge_svg(result: Result) -> str:
    color = {
        "A+": "#3fb950",
        "A": "#3fb950",
        "B+": "#2f81f7",
        "B": "#2f81f7",
        "C": "#d29922",
        "D": "#db6d28",
        "E": "#f85149",
    }.get(result.grade, "#8b949e")
    label = "starcheck"
    value = f"{result.score} · {result.grade}"
    w_label = 11 + 7 * len(label)
    w_value = 11 + 7 * len(value)
    total = w_label + w_value
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total}" height="20" role="img" '
        f'aria-label="{label}: {value}">\n'
        f"  <title>{label}: {value}</title>\n"
        f'  <g shape-rendering="crispEdges">\n'
        f'    <rect width="{w_label}" height="20" fill="#555"/>\n'
        f'    <rect x="{w_label}" width="{w_value}" height="20" fill="{color}"/>\n'
        f"  </g>\n"
        f'  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">\n'
        f'    <text x="{w_label // 2}" y="14">{label}</text>\n'
        f'    <text x="{w_label + w_value // 2}" y="14">{value}</text>\n'
        f"  </g>\n"
        f"</svg>\n"
    )


def dumps(result: Result, ctx) -> str:
    payload = result.as_dict()
    payload["repo"] = ctx.name
    payload["path"] = str(ctx.root).replace("\\", "/")
    return json.dumps(payload, ensure_ascii=False, indent=2)
