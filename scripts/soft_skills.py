"""Radar ("spider") chart of soft skills -> assets/soft-skills.svg. Edit SKILLS and rerun."""
import base64, math, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILLS = [("Analytical thinking", 85), ("Problem-solving", 85), ("Critical thinking", 80),
          ("Self-learning", 75), ("Communication", 75), ("Teamwork", 65),
          ("Time management", 65), ("Adaptability", 85)]
W, H, CX, CY, R = 820, 540, 410, 298, 172

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
<text class="title" x="28" y="44">Soft skills</text>
<text class="sub" x="28" y="68">Self-assessed, average {avg}%</text>"""]
# ---- orb web: anchor lines, radials, 10 rings (10% each), dew, torn strands ----
import random
rnd = random.Random(23)
N = len(SKILLS)
MAIN = [-math.pi / 2 + i * 2 * math.pi / N for i in range(N)]
SUB = 1                                   # radials per sector (main threads only)
RAD = [MAIN[i // SUB] + (i % SUB) * 2 * math.pi / N / SUB + (0 if i % SUB == 0 else rnd.uniform(-.05, .05))
       for i in range(N * SUB)]
SILK = "#aebcf5"
def wp(a, r):
    return CX + r * math.cos(a), CY + r * math.sin(a)
def qpt(p0, c, p1, t):
    return ((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * p1[0],
            (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * p1[1])
def sway(inner, ax, ay, amp, dur):
    return (f'<g>{inner}<animateTransform attributeName="transform" type="rotate" '
            f'values="{-amp:.1f} {ax:.1f} {ay:.1f};{amp:.1f} {ax:.1f} {ay:.1f};{-amp:.1f} {ax:.1f} {ay:.1f}" dur="{dur:.1f}s" '
            f'begin="-{rnd.uniform(0, dur):.1f}s" repeatCount="indefinite" calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1"/></g>')
# bridge / anchor threads running off toward the edges of the frame
for a in MAIN:
    x1, y1 = wp(a, R)
    x2, y2 = wp(a + rnd.uniform(-.08, .08), R * rnd.uniform(1.45, 1.8))
    out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{SILK}" stroke-opacity=".22" stroke-width=".8"/>')
# faint secondary radials (start partway out, like real orb webs)
for i, a in enumerate(RAD):
    if i % SUB:
        x1, y1 = wp(a, R * rnd.uniform(.2, .45)); x2, y2 = wp(a, R)
        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{SILK}" stroke-opacity=".2" stroke-width=".7"/>')
# 10 rings, one per 10%: every crossing with a radial sits exactly on that percentage
dews = []
SNAP = set(rnd.sample([(k, j) for k in (6, 7, 8, 9) for j in range(len(RAD))], 6))
for k in range(1, 11):
    r = R * k / 10
    for j in range(len(RAD)):
        p0, p1 = wp(RAD[j], r), wp(RAD[(j + 1) % len(RAD)], r)
        L = math.dist(p0, p1)
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        c = (CX + (mx - CX) * .9, CY + (my - CY) * .9 + L * .06)
        roll = rnd.random()
        if (k, j) in SNAP:
            # snapped thread: breaks at a random point, both halves fall and hang from their anchors
            t = rnd.uniform(.3, .7)
            for (ax, ay), (bx, by), l in ((p0, p1, L * t), (p1, p0, L * (1 - t))):
                ux, uy = (bx - ax) / L, (by - ay) / L
                e = (ax + ux * l * .3, ay + uy * l * .3 + l * .9)
                q = (ax + ux * l * .55, ay + uy * l * .55 + l * .15)
                out.append(sway(f'<path d="M{ax:.1f},{ay:.1f} Q{q[0]:.1f},{q[1]:.1f} {e[0]:.1f},{e[1]:.1f}" fill="none" stroke="{SILK}" stroke-opacity=".75" stroke-width="1" stroke-linecap="round"/>',
                                ax, ay, rnd.uniform(4, 8), rnd.uniform(3.5, 6.5)))
            continue
        op = .7 if k == 10 else (.42 if k % 5 == 0 else .3)
        out.append(f'<path d="M{p0[0]:.1f},{p0[1]:.1f} Q{c[0]:.1f},{c[1]:.1f} {p1[0]:.1f},{p1[1]:.1f}" fill="none" stroke="{SILK}" stroke-opacity="{op}" stroke-width="{1.1 if k == 10 else .8}"/>')
        if rnd.random() < .04:
            dews.append(qpt(p0, c, p1, rnd.uniform(.3, .7)))
# main radials on top, crisp
for a in MAIN:
    x, y = wp(a, R)
    out.append(f'<line x1="{CX}" y1="{CY}" x2="{x:.1f}" y2="{y:.1f}" stroke="#dfe6ff" stroke-opacity=".9" stroke-width="1.5" stroke-linecap="round"/>')
# dew beads, a few of them glint
for i, (x, y) in enumerate(dews):
    rr = rnd.uniform(1.2, 2.2)
    glint = '' if i % 4 else f'<animate attributeName="opacity" values=".35;.95;.35" dur="{rnd.uniform(3, 6):.1f}s" begin="-{rnd.uniform(0, 4):.1f}s" repeatCount="indefinite"/>'
    out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rr:.1f}" fill="#eaf1ff" opacity=".6">{glint}</circle>')
# outer bridge threads: tie the rim to a radial's anchor line, sagging in the middle
def rim_pt(j, t):
    p0, p1 = wp(RAD[j % N], R), wp(RAD[(j + 1) % N], R)
    L = math.dist(p0, p1); mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    return qpt(p0, (CX + (mx - CX) * .9, CY + (my - CY) * .9 + L * .06), p1, t)
for spoke, seg, t in ((7, 6, .55), (5, 5, .45), (3, 2, .55)):
    A = wp(MAIN[spoke], R * 1.2)
    B = rim_pt(seg, t)
    mx, my = (A[0] + B[0]) / 2, (A[1] + B[1]) / 2
    ox, oy = (mx - CX), (my - CY); n = math.hypot(ox, oy)
    c = (mx + ox / n * 9, my + oy / n * 9 + 10)
    out.append(f'<path d="M{A[0]:.1f},{A[1]:.1f} Q{c[0]:.1f},{c[1]:.1f} {B[0]:.1f},{B[1]:.1f}" fill="none" stroke="{SILK}" stroke-opacity=".8" stroke-width="1.1"/>')
# ---- data shape: edges bow inward like silk pulled taut between points ----
P = [pt(i, R * v / 100) for i, (_, v) in enumerate(SKILLS)]
d = f"M{P[0][0]:.1f},{P[0][1]:.1f}"
for i in range(N):
    p0, p1 = P[i], P[(i + 1) % N]
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    d += f" Q{CX + (mx - CX) * .82:.1f},{CY + (my - CY) * .82:.1f} {p1[0]:.1f},{p1[1]:.1f}"
d += "Z"
out.append(f'<path d="{d}" fill="#5b7bf0" opacity=".3" filter="url(#glow)"/>')
out.append(f'<path d="{d}" fill="url(#fill)" stroke="#eaf1ff" stroke-width="2" stroke-linejoin="round"/>')
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
