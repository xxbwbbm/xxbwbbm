"""About me facts card -> assets/about-me.svg. Edit ROWS and rerun."""
import base64, pathlib
from xml.sax.saxutils import escape
ROOT = pathlib.Path(__file__).resolve().parent.parent
ROWS = [
    ("Studying", ["Information Systems at UIT – VNU-HCM"]),
    ("Aiming for", ["Data Analyst / Data Engineer / AI Engineer"]),
    ("Also into", ["Scientific research, getting started"]),
    ("MBTI", ["ENTP"]),
    ("Deadly sin", ["Ego"]),
    ("Off the clock", ["Music, movies, gaming, the gym,", "video editing and photography"]),
]
W, PAD, LX, VX, ROW, LINE = 700, 18, 10, 190, 58, 28

def b64(n):
    return base64.b64encode((ROOT / "assets/fonts" / n).read_bytes()).decode()

h = PAD + sum(ROW + LINE * (len(v) - 1) for _, v in ROWS) + 4
out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}">', f"""<style>
@font-face {{ font-family: "PoppinsA"; font-weight: 400; src: url(data:font/woff;base64,{b64("Poppins-Regular-subset.woff")}) format("woff"); }}
@font-face {{ font-family: "PoppinsA"; font-weight: 500; src: url(data:font/woff;base64,{b64("Poppins-Medium-subset.woff")}) format("woff"); }}
text {{ font-family: "PoppinsA", "Poppins", "Segoe UI", Helvetica, Arial, sans-serif; }}
.k {{ font-size: 17px; fill: #8a92c4; }}
.v {{ font-size: 21px; font-weight: 500; fill: #eaf1ff; }}
</style>"""]
y = PAD
for i, (k, vals) in enumerate(ROWS):
    base = y + 30
    out.append(f'<circle cx="{LX + 3}" cy="{base - 6}" r="3" fill="#5b7bf0"/>')
    out.append(f'<text class="k" x="{LX + 18}" y="{base}">{escape(k)}</text>')
    for j, v in enumerate(vals):
        out.append(f'<text class="v" x="{VX}" y="{base + j * LINE}">{escape(v)}</text>')
    y += ROW + LINE * (len(vals) - 1)
    if i < len(ROWS) - 1:
        out.append(f'<line x1="{LX}" y1="{y - 6}" x2="{W - 10}" y2="{y - 6}" stroke="#111f69" stroke-width="1"/>')
out.append("</svg>")
(ROOT / "assets/about-me.svg").write_text("\n".join(out), encoding="utf-8")
