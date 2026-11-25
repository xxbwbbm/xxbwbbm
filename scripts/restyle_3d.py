"""Post-process the SVG made by yoshi389111/github-profile-3d-contrib:
  * drop the language pie chart and the radar ("web") chart
  * re-frame the 3D calendar as 16:9 (1280x720)
  * swap the font for an embedded Poppins subset (geometric sans)
  * replace the star/fork icons with plain text stats placed in the empty corner

Usage: python3 scripts/restyle_3d.py profile-3d-contrib/profile-night.svg
Only uses the Python standard library so it runs on a stock GitHub Actions runner.
"""
import base64
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
NS = "{%s}" % SVG_NS
ET.register_namespace("", SVG_NS)

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "assets" / "fonts"
W, H = 1280, 720  # 16:9


def font_face(weight, file):
    data = base64.b64encode((FONT_DIR / file).read_bytes()).decode()
    return (f'@font-face {{ font-family: "Poppins3D"; font-weight: {weight}; '
            f'src: url(data:font/woff;base64,{data}) format("woff"); }}')


def texts(el):
    return [t.text or "" for t in el.iter(NS + "text")]


def main(path):
    tree = ET.parse(path)
    svg = tree.getroot()
    if svg.get("data-restyled") == "1":
        print("already restyled, skipping")
        return

    calendar = radar = pie = stats = None
    for child in list(svg):
        if child.tag != NS + "g":
            continue
        classes = {e.get("class", "") for e in child.iter()}
        if "radar" in classes or "axis" in classes:
            radar = child
        elif "contributions" in texts(child):
            stats = child
        elif any(t.get("font-size") for t in child.iter(NS + "text")) and child.find(".//" + NS + "path") is not None:
            pie = child
        elif len(child) > 50:
            calendar = child

    for el in (radar, pie):
        if el is not None:
            svg.remove(el)

    # ---- calendar bounds -> vertical framing ----
    ys_top, ys_bottom = [], []
    for cell in calendar:
        m = re.match(r"translate\(([-\d.]+)[ ,]+([-\d.]+)\)", cell.get("transform", ""))
        if not m:
            continue
        y = float(m.group(2))
        heights = [float(r.get("height", 0)) for r in cell.findall(NS + "rect")[1:]]
        ys_top.append(y - 12)
        ys_bottom.append(y + max(heights or [0]) * 1.15 + 22)
    top, bottom = min(ys_top), max(ys_bottom)
    vb_y = (top + bottom) / 2 - H / 2
    vb_y = min(vb_y, top - 8)  # never clip the tallest bars

    svg.set("width", str(W))
    svg.set("height", str(H))
    svg.set("viewBox", f"0 {vb_y:.2f} {W} {H}")
    svg.set("data-restyled", "1")
    for rect in svg.findall(NS + "rect"):
        if rect.get("class") == "fill-bg":
            rect.set("y", f"{vb_y:.2f}")
            rect.set("height", str(H))

    # ---- stats: read numbers, rebuild as text in the empty lower-left corner ----
    contrib, stars, forks, period = "0", "0", "0", ""
    if stats is not None:
        tx = [t for t in stats.iter(NS + "text")]
        values = [t.text for t in tx if t.text and re.fullmatch(r"[\d.,]+[kKM]?", t.text.strip())]
        if values:
            contrib = values[0]
        if len(values) > 1:
            stars = values[1]
        if len(values) > 2:
            forks = values[2]
        period = next((t.text for t in tx if t.text and "/" in t.text), "")
        svg.remove(stats)

    g = ET.SubElement(svg, NS + "g")
    x0, base = 60, vb_y + H - 110
    big = ET.SubElement(g, NS + "text", {"x": str(x0), "y": f"{base:.1f}", "class": "fill-strong",
                                         "style": "font-size: 64px; font-weight: 500; letter-spacing: -1px;"})
    big.text = contrib
    lab = ET.SubElement(g, NS + "text", {"x": str(x0 + 4), "y": f"{base + 40:.1f}", "class": "fill-fg",
                                         "style": "font-size: 24px; font-weight: 400; letter-spacing: .5px;"})
    lab.text = "contributions"
    sub = ET.SubElement(g, NS + "text", {"x": str(x0 + 4), "y": f"{base + 74:.1f}", "class": "fill-weak",
                                         "style": "font-size: 18px; font-weight: 400; letter-spacing: .5px;"})
    sub.text = f"{stars} stars  ·  {forks} forks"
    if period:
        per = ET.SubElement(g, NS + "text", {"x": str(W - 40), "y": f"{vb_y + 44:.1f}", "class": "fill-weak",
                                             "text-anchor": "end",
                                             "style": "font-size: 16px; font-weight: 400; letter-spacing: .5px;"})
        per.text = period

    # ---- font ----
    style = svg.find(NS + "style")
    css = style.text or ""
    css = re.sub(r"\*\s*\{\s*font-family:[^}]*\}",
                 '* { font-family: "Poppins3D", "Poppins", "Helvetica", "Arial", sans-serif; }', css, count=1)
    style.text = font_face(400, "Poppins-Regular-subset.woff") + "\n" + font_face(500, "Poppins-Medium-subset.woff") + "\n" + css

    tree.write(path, encoding="unicode", xml_declaration=False)
    print(f"restyled {path}: viewBox y={vb_y:.1f}, contributions={contrib}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "profile-3d-contrib/profile-night.svg")
