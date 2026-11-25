"""Radar ("spider") chart of soft skills -> assets/soft-skills.svg. Edit SKILLS and rerun."""
import base64, math, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILLS = [("Creative thinking", 80), ("Problem-solving", 90), ("Adaptability", 85),
          ("Communication", 80), ("Attention to detail", 75), ("Teamwork", 50)]
W, H, CX, CY, R = 720, 510, 360, 282, 150

def b64(name):
    return base64.b64encode((ROOT / "assets/fonts" / name).read_bytes()).decode()

def pt(i, r):
    a = -math.pi / 2 + i * 2 * math.pi / len(SKILLS)
    return CX + r * math.cos(a), CY + r * math.sin(a)

def poly(r):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in (pt(i, r) for i in range(len(SKILLS))))

avg = round(sum(v for _, v in SKILLS) / len(SKILLS))
out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">', f"""<defs>
<radialGradient id="fill" cx="50%" cy="50%" r="60%"><stop offset="0" stop-color="#eaf1ff" stop-opacity=".35"/><stop offset=".55" stop-color="#5b7bf0" stop-opacity=".22"/><stop offset="1" stop-color="#3f5bd9" stop-opacity=".14"/></radialGradient>
<filter id="glow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="7"/></filter>
</defs>
<style>
@font-face {{ font-family: "PoppinsR"; font-weight: 400; src: url(data:font/woff;base64,{b64("Poppins-Regular-subset.woff")}) format("woff"); }}
@font-face {{ font-family: "PoppinsR"; font-weight: 500; src: url(data:font/woff;base64,{b64("Poppins-Medium-subset.woff")}) format("woff"); }}
text {{ font-family: "PoppinsR", "Poppins", "Segoe UI", Helvetica, Arial, sans-serif; }}
.title {{ font-size: 22px; font-weight: 500; fill: #eaf1ff; }}
.sub {{ font-size: 15px; fill: #6a72a8; }}
.lab {{ font-size: 16px; fill: #cbcddb; }}
.val {{ font-size: 16px; font-weight: 500; fill: #eaf1ff; }}
</style>
<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="14" fill="#04082c" stroke="#111f69"/>
<text class="title" x="28" y="44">Soft skills</text>
<text class="sub" x="28" y="68">Self-assessed, average {avg}%</text>"""]
# spider-web grid: 18 threads (every 3rd one is a skill axis) + sagging spiral rings
import random
rnd = random.Random(7)
N_SP, N_RING = 18, 9
ang = [-math.pi / 2 + i * 2 * math.pi / N_SP + (0 if i % 3 == 0 else rnd.uniform(-.06, .06)) for i in range(N_SP)]
def wp(a, r):
    return CX + r * math.cos(a), CY + r * math.sin(a)
for i, a in enumerate(ang):
    x, y = wp(a, R * rnd.uniform(1.08, 1.2))
    axis = i % 3 == 0
    out.append(f'<line x1="{CX}" y1="{CY}" x2="{x:.1f}" y2="{y:.1f}" stroke="#8fa6f5" stroke-opacity="{.7 if axis else .4}" stroke-width="{1.1 if axis else .8}"/>')
for k in range(1, N_RING + 1):
    r0 = R * k / N_RING
    rs = [r0 * rnd.uniform(.96, 1.03) for _ in range(N_SP)]
    d = []
    for i in range(N_SP):
        a1, a2 = ang[i], ang[(i + 1) % N_SP]
        x1, y1 = wp(a1, rs[i]); x2, y2 = wp(a2, rs[(i + 1) % N_SP])
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        cx, cy = CX + (mx - CX) * .9, CY + (my - CY) * .9
        d.append(("M" if i == 0 else "") + (f"{x1:.1f},{y1:.1f} " if i == 0 else "") + f"Q{cx:.1f},{cy:.1f} {x2:.1f},{y2:.1f}")
    out.append(f'<path d="{" ".join(d)}" fill="none" stroke="#8fa6f5" stroke-opacity="{.45 if k < N_RING else .7}" stroke-width=".9"/>')
vals = " ".join(f"{x:.1f},{y:.1f}" for x, y in (pt(i, R * v / 100) for i, (_, v) in enumerate(SKILLS)))
out.append(f'<polygon points="{vals}" fill="#5b7bf0" opacity=".3" filter="url(#glow)"/>')
out.append(f'<polygon points="{vals}" fill="url(#fill)" stroke="#eaf1ff" stroke-width="2" stroke-linejoin="round"/>')
for i, (name, v) in enumerate(SKILLS):
    x, y = pt(i, R * v / 100)
    out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8" fill="#eaf1ff" opacity=".18"/><circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#eaf1ff"/>')
    lx, ly = pt(i, R + 26)
    top_or_bottom = abs(lx - CX) < 5
    anchor = "middle" if top_or_bottom else ("start" if lx > CX else "end")
    if top_or_bottom:
        ly += -10 if ly < CY else 14
    else:
        ly += 5
    out.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}"><tspan class="lab">{name}</tspan><tspan class="val" dx="8">{v}%</tspan></text>')
out.append("</svg>")
(ROOT / "assets/soft-skills.svg").write_text("\n".join(out), encoding="utf-8")
