"""Turn the SVG made by yoshi389111/github-profile-3d-contrib into a lightweight animated WebP.

  * drops the language pie chart and the radar chart, re-frames the calendar to 16:9
  * draws the stats text with Poppins (converted to paths, so no font install is needed)
  * every 10 s a wave sweeps along the weeks: each column grows taller and turns whiter
    the higher it rises, then settles back

The wave is pre-rendered frame by frame (librsvg) and packed into one animated WebP, so the
browser only plays an image instead of re-drawing ~1,100 shapes every frame (which lagged).

Usage: python3 scripts/make_3d_anim.py <in.svg> <out.webp>
Needs: rsvg-convert (librsvg2-bin), Pillow, fontTools.
"""
import io
import math
import pathlib
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

from PIL import Image
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

SVG_NS = "http://www.w3.org/2000/svg"
NS = "{%s}" % SVG_NS
ET.register_namespace("", SVG_NS)
ROOT = pathlib.Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "assets" / "fonts"

W, H = 1280, 720            # 16:9 canvas (svg units)
OUT_W = 1280                # output pixel width
FPS = 20
LIFT = 40.0                 # extra height at the crest
CYCLE, SWEEP = 10.0, 3.2    # seconds per cycle, time for the crest to cross the calendar
RISE, FALL = 0.5, 0.7       # seconds for a column to rise / settle
PEAK = {"top": (246, 249, 255), "left": (217, 225, 244), "right": (185, 197, 227)}
CELL_RE = re.compile(r"translate\(([-\d.]+)[ ,]+([-\d.]+)\)")


# ---------------------------------------------------------------- text -> path
_fonts = {}


def font(weight):
    name = "Poppins-Medium-subset.woff" if weight >= 500 else "Poppins-Regular-subset.woff"
    if name not in _fonts:
        _fonts[name] = TTFont(str(FONT_DIR / name))
    return _fonts[name]


def text_path(text, size, weight=400, x=0.0, y=0.0, anchor="start", tracking=0.0, fill="#fff"):
    f = font(weight)
    cmap, gs = f.getBestCmap(), f.getGlyphSet()
    s = size / f["head"].unitsPerEm
    glyphs, adv = [], 0.0
    for ch in text:
        g = cmap.get(ord(ch))
        if g is None:
            continue
        glyphs.append((g, adv))
        adv += gs[g].width + tracking / s
    width = adv * s - tracking
    x0 = x - width if anchor == "end" else x - width / 2 if anchor == "middle" else x
    parts = []
    for g, a in glyphs:
        pen = SVGPathPen(gs)
        gs[g].draw(TransformPen(pen, (s, 0, 0, -s, x0 + a * s, y)))
        if pen.getCommands():
            parts.append(pen.getCommands())
    return f'<path fill="{fill}" d="{" ".join(parts)}"/>'


# ---------------------------------------------------------------- parsing
def parse(path):
    svg = ET.parse(path).getroot()
    css = svg.find(NS + "style").text or ""
    colors = {k: tuple(int(v) for v in re.findall(r"\d+", c)) if c.startswith("rgb") else c
              for k, c in re.findall(r"\.([\w-]+)\s*\{\s*fill:\s*([^;]+);", css)}
    calendar, stats = None, None
    for child in svg:
        if child.tag != NS + "g":
            continue
        tx = [t.text or "" for t in child.iter(NS + "text")]
        if "contributions" in tx:
            stats = child
        elif len(child) > 50:
            calendar = child
    cells = []
    for g in calendar:
        m = CELL_RE.match(g.get("transform", ""))
        if not m:
            continue
        x, y = float(m.group(1)), float(m.group(2))
        rects = []
        for r in g.findall(NS + "rect"):
            rects.append({k: r.get(k) for k in ("x", "y", "width", "height", "transform", "class")})
        cells.append({"x": x, "y": y, "rects": rects})
    nums = [t.text.strip() for t in stats.iter(NS + "text")
            if t.text and re.fullmatch(r"[\d.,]+[kKM]?", t.text.strip())] if stats is not None else []
    period = next((t.text for t in stats.iter(NS + "text") if t.text and "/" in t.text), "") if stats is not None else ""
    nums += ["0"] * (3 - len(nums))
    return colors, cells, nums[:3], period


def hexify(c):
    return c if isinstance(c, str) else "#%02x%02x%02x" % c


def mix(a, b, k):
    if isinstance(a, str):
        return a
    return "#%02x%02x%02x" % tuple(round(a[i] + (b[i] - a[i]) * k) for i in range(3))


# ---------------------------------------------------------------- wave
def ease_out(u):
    return 1 - (1 - u) ** 3


def ease_in_out(u):
    return u * u * (3 - 2 * u)


def lift_at(t):
    """0..1 lift for a column whose wave started t seconds ago."""
    if t < 0 or t > RISE + FALL:
        return 0.0
    if t <= RISE:
        return ease_out(t / RISE)
    return 1 - ease_in_out((t - RISE) / FALL)


# ---------------------------------------------------------------- frame
def build_frame(colors, cells, layout, static_parts, t):
    bg = hexify(colors.get("fill-bg", (4, 8, 44)))
    vb_y, scale, cy = layout
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 {vb_y:.2f} {W} {H}">',
           f'<rect x="0" y="{vb_y:.2f}" width="{W}" height="{H}" fill="{bg}"/>',
           f'<g transform="translate({W / 2} {cy:.2f}) scale({scale:.4f}) translate({-W / 2} {-cy:.2f})">']
    for c in cells:
        k = lift_at(t - c["begin"])
        dy = -LIFT * k
        out.append(f'<g transform="translate({c["x"]} {c["y"] + dy:.2f})">')
        for r in c["rects"]:
            cls = r["class"] or ""
            face = cls.split("-")[1] if cls.startswith("cont-") else None
            h = float(r["height"])
            if face in ("left", "right"):
                h += LIFT * k / 1.15
            base = colors.get(cls, (40, 60, 140))
            fill = mix(base, PEAK.get(face, (255, 255, 255)), k) if face else hexify(base)
            tr = f' transform="{r["transform"]}"' if r["transform"] else ""
            out.append(f'<rect x="{r["x"]}" y="{r["y"]}" width="{r["width"]}" height="{h:.2f}"{tr} fill="{fill}"/>')
        out.append("</g>")
    out.append("</g>")
    out.append(static_parts)
    out.append("</svg>")
    return "".join(out)


def render(svg_text):
    png = subprocess.run(["rsvg-convert", "-w", str(OUT_W), "-f", "png"], input=svg_text.encode(),
                         capture_output=True, check=True).stdout
    return Image.open(io.BytesIO(png)).convert("RGB")


def main(src, dst):
    colors, cells, (contrib, stars, forks), period = parse(src)

    # framing (16:9) with head-room for the crest; shrink slightly if needed
    tops = [c["y"] - 12 for c in cells]
    bottoms = [c["y"] + max(float(r["height"]) for r in c["rects"][1:]) * 1.15 + 22 for c in cells]
    span_top = min(tops) - LIFT - 6
    bottom = max(bottoms)
    scale = min(1.0, (H - 10) / (bottom - span_top))
    cy = (span_top + bottom) / 2
    vb_y = cy - H / 2

    # wave start time per column: projection on the "week" direction (30 deg)
    proj = [c["x"] * 0.866 + c["y"] * 0.5 for c in cells]
    pmin, pmax = min(proj), max(proj)
    for c, p in zip(cells, proj):
        c["begin"] = (p - pmin) / ((pmax - pmin) or 1) * SWEEP

    fg = hexify(colors.get("fill-fg", (203, 205, 219)))
    weak = hexify(colors.get("fill-weak", (106, 114, 168)))
    strong = hexify(colors.get("fill-strong", (234, 241, 255)))
    base_y = vb_y + H - 110
    static = "".join([
        text_path(contrib, 64, 500, 60, base_y, tracking=-1, fill=strong),
        text_path("contributions", 24, 400, 64, base_y + 40, tracking=0.5, fill=fg),
        text_path(f"{stars} stars  ·  {forks} forks", 18, 400, 64, base_y + 74, tracking=0.5, fill=weak),
        text_path(period, 16, 400, W - 40, vb_y + 44, anchor="end", tracking=0.5, fill=weak) if period else "",
    ])

    active = SWEEP + RISE + FALL
    n = math.ceil(active * FPS)
    frames, durations = [], []
    for i in range(n + 1):
        t = i / FPS
        frames.append(render(build_frame(colors, cells, (vb_y, scale, cy), static, t)))
        durations.append(round(1000 / FPS))
    durations[-1] = round((CYCLE - n / FPS) * 1000)   # the calm part is one long frame
    frames[0].save(dst, save_all=True, append_images=frames[1:], duration=durations, loop=0,
                   quality=82, method=6)
    print(f"wrote {dst}: {len(frames)} frames, {pathlib.Path(dst).stat().st_size // 1024} KB")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
