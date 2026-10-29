"""Generate assets/demo.gif and assets/social.png from *real* starcheck output.

No screenshots, no mockups: the frame content is the tool's own ASCII-layout
render, so the asset cannot drift from the tool.

    python tools/make_assets.py            # writes assets/
    python tools/make_assets.py --target ..  # audit a different repo
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from starcheck.checks import build_context, run_checks  # noqa: E402
from starcheck.render import ASCII, render_card  # noqa: E402
from starcheck.score import score  # noqa: E402

BG = (13, 17, 23)
BAR = (22, 27, 34)
BORDER = (48, 54, 61)
FG = (201, 209, 217)
DIM = (110, 118, 129)
ACCENT = (63, 185, 80)

ANSI_TO_RGB = {
    "1": None,  # bold, handled by double-draw
    "2": DIM,
    "31": (248, 81, 73),
    "32": ACCENT,
    "33": (210, 153, 34),
    "36": (88, 166, 255),
    "90": (139, 148, 158),
}

FONT_CANDIDATES = [
    # SimSun first: ASCII 8px, CJK 16px -> exactly a 2:1 grid, and full GB2312
    # coverage. MS Gothic is metric-perfect but lacks simplified-only glyphs.
    r"C:\Windows\Fonts\simsun.ttc",
    r"C:\Windows\Fonts\msgothic.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
]


def load_font(size: int):
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def parse_runs(text: str):
    """'\\033[32mx\\033[0m' -> [('x', {color, bold})]"""
    runs = []
    style = {"color": FG, "bold": False, "dim": False}
    pos = 0
    for m in re.finditer(r"\033\[([0-9;]*)m", text):
        chunk = text[pos : m.start()]
        if chunk:
            runs.append((chunk, dict(style)))
        codes = [c for c in m.group(1).split(";") if c]
        if not codes or codes == ["0"]:
            style = {"color": FG, "bold": False, "dim": False}
        else:
            for code in codes:
                if code == "1":
                    style["bold"] = True
                elif code == "2":
                    style["dim"] = True
                elif code in ANSI_TO_RGB:
                    style["color"] = ANSI_TO_RGB[code]
        pos = m.end()
    if pos < len(text):
        runs.append((text[pos:], dict(style)))
    return runs


def draw_runs(draw: ImageDraw.ImageDraw, x: float, y: float, text: str, font) -> float:
    for chunk, style in parse_runs(text + "\033[0m"):
        color = style["color"] or FG
        if style["dim"]:
            color = tuple(int(a * 0.55 + b * 0.45) for a, b in zip(color, BG))
        for ch in chunk:
            draw.text((x, y), ch, font=font, fill=color)
            if style["bold"]:
                draw.text((x + 0.6, y), ch, font=font, fill=color)
            x += font.getlength(ch)
    return x


def reveal_steps(total: int):
    """Typing rhythm: one line at a time at first, then accelerate (GIF size)."""
    steps = list(range(1, min(total, 7)))
    steps += list(range(9, total + 1, 3))
    if steps[-1] != total:
        steps.append(total)
    return steps


def card_frames(lines, font, cell_w: float, line_h: int, size, pad=22, titlebar=34):
    """Terminal window with progressively revealed output."""
    frames = []
    max_cols = max(len(re.sub(r"\033\[[0-9;]*m", "", ln)) for ln in lines)
    width = int(max_cols * cell_w) + pad * 2
    height = len(lines) * line_h + pad * 2 + titlebar

    for upto in reveal_steps(len(lines)):
        img = Image.new("RGB", (width, height), BG)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([0, 0, width - 1, height - 1], radius=10, fill=BG, outline=BORDER)
        d.rectangle([1, 1, width - 2, titlebar], fill=BAR)
        for i, color in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
            cx = 18 + i * 18
            d.ellipse([cx, 12, cx + 10, 22], fill=color)
        d.text((82, 11), "starcheck", font=load_font(13), fill=(139, 148, 158))

        y = titlebar + pad - 6
        for line in lines[:upto]:
            draw_runs(d, pad, y, line, font)
            y += line_h

        if upto < len(lines):
            cursor_x = pad + font.getlength(re.sub(r"\033\[[0-9;]*m", "", lines[upto - 1]))
            d.rectangle([cursor_x + 2, y - line_h + 1, cursor_x + 9, y - 3], fill=FG)

        frames.append(img)
    return frames


def write_gif(frames, path: Path, hold_ms: int = 2800) -> None:
    pal = [f.convert("P", palette=Image.ADAPTIVE, colors=32) for f in frames]
    durations = [80] * (len(pal) - 1) + [hold_ms]
    pal[0].save(
        path,
        save_all=True,
        append_images=pal[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=2,
    )


def write_social(card_img: Image.Image, path: Path, meta: dict) -> None:
    W, H = 1280, 640
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    for x in range(W):
        t = x / W
        d.line([(x, 0), (x, H)], fill=(int(13 + 8 * t), int(17 + 10 * t), int(23 + 18 * t)))

    big = load_font(92)
    mid = load_font(30)
    small = load_font(20)
    tiny = load_font(22)

    d.text((64, 96), "starcheck", font=big, fill=(240, 246, 252))
    d.text((68, 206), "Audit any repo for star-readiness.", font=mid, fill=(139, 148, 158))
    d.text(
        (68, 252),
        f"{meta['score']}/100 · {meta['grade']} · 28 checks · no deps",
        font=tiny,
        fill=ACCENT,
    )
    d.rounded_rectangle([64, 320, 470, 376], radius=8, fill=(22, 27, 34), outline=BORDER)
    d.text((84, 334), "uvx starcheck owner/repo", font=small, fill=(201, 209, 217))
    d.text((64, 420), "发现 · 转化 · 可信 · 分发", font=small, fill=(88, 166, 255))
    d.text((64, 452), "one score, the top 3 fixes,", font=small, fill=DIM)
    d.text((64, 476), "paste-ready commands", font=small, fill=DIM)

    thumb = card_img.crop((0, 0, card_img.width, 490))
    scale = 600 / thumb.width
    thumb = thumb.resize((600, int(thumb.height * scale)), Image.LANCZOS)
    img.paste(thumb, (W - 640, (H - thumb.height) // 2))
    img.save(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default=".")
    ap.add_argument("--out", default="assets")
    args = ap.parse_args()

    root = Path(args.target).resolve()
    ctx = build_context(root)
    result = score(run_checks(ctx))
    card = render_card(result, ctx, color=True, glyphs=ASCII)
    lines = card.splitlines()

    font = load_font(16)
    cell_w = font.getlength("a")
    frames = card_frames(lines, font, cell_w, 20, None)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    write_gif(frames, out / "demo.gif")
    write_social(frames[-1], out / "social.png", {"score": result.score, "grade": result.grade})

    size = (out / "demo.gif").stat().st_size / 1024
    print(f"{ctx.name}: {result.score}/100 {result.grade}")
    print(f"wrote {out/'demo.gif'} ({size:.0f} KB, {len(frames)} frames)")
    print(f"wrote {out/'social.png'} ({frames[-1].width}x{frames[-1].height} card)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
