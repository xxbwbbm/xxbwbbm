"""Radar ("spider") chart of soft skills -> assets/soft-skills.svg. Edit SKILLS and rerun."""
import base64, math, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILLS = [("Creative thinking", 80), ("Problem-solving", 90), ("Adaptability", 85),
          ("Communication", 80), ("Attention to detail", 75), ("Teamwork", 50)]
W, H, CX, CY, R = 700, 470, 350, 240, 160

def b64(name):
    return base64.b64encode((ROOT / "assets/fonts" / name).read_bytes()).decode()

def pt(i, r):
    a = -math.pi / 2 + i * 2 * math.pi / len(SKILLS)
    return CX + r * math.cos(a), CY + r * math.sin(a)

def poly(r):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in (pt(i, r) for i in range(len(SKILLS))))

out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">', f"""<style>
@font-face {{ font-family: "PoppinsR"; font-weight: 400; src: url(data:font/woff;base64,{b64("Poppins-Regular-subset.woff")}) format("woff"); }}
@font-face {{ font-family: "PoppinsR"; font-weight: 500; src: url(data:font/woff;base64,{b64("Poppins-Medium-subset.woff")}) format("woff"); }}
text {{ font-family: "PoppinsR", "Poppins", "Segoe UI", Helvetica, Arial, sans-serif; }}
.lab {{ font-size: 17px; font-weight: 500; fill: #eaf1ff; }}
.val {{ font-size: 15px; fill: #8a92c4; }}
.ring {{ fill: none; stroke: #172e80; stroke-width: 1; }}
.ax {{ stroke: #111f69; stroke-width: 1; }}
</style>"""]
for k in range(1, 6):
    out.append(f'<polygon class="ring" points="{poly(R * k / 5)}"' + (' stroke-dasharray="3 4"' if k < 5 else '') + '/>')
for i in range(len(SKILLS)):
    x, y = pt(i, R)
    out.append(f'<line class="ax" x1="{CX}" y1="{CY}" x2="{x:.1f}" y2="{y:.1f}"/>')
vals = " ".join(f"{x:.1f},{y:.1f}" for x, y in (pt(i, R * v / 100) for i, (_, v) in enumerate(SKILLS)))
out.append(f'<polygon points="{vals}" fill="#3f5bd9" fill-opacity=".28" stroke="#eaf1ff" stroke-width="1.8" stroke-linejoin="round"/>')
for i, (name, v) in enumerate(SKILLS):
    x, y = pt(i, R * v / 100)
    out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#eaf1ff"/>')
    lx, ly = pt(i, R + 30)
    anchor = "middle" if abs(lx - CX) < 5 else ("start" if lx > CX else "end")
    if abs(lx - CX) < 5:
        ly += -14 if ly < CY else 8
    out.append(f'<text class="lab" x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}">{name}</text>')
    out.append(f'<text class="val" x="{lx:.1f}" y="{ly + 20:.1f}" text-anchor="{anchor}">{v}%</text>')
out.append("</svg>")
(ROOT / "assets/soft-skills.svg").write_text("\n".join(out), encoding="utf-8")
