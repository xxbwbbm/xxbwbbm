"""Build assets/now-playing.svg from a public YouTube playlist.

Reads the playlist's RSS feed, picks one video (rotating every hour), uses its thumbnail as the
vinyl label and splits the video title into song / artist.

Usage: python3 scripts/now_playing.py [--feed-file feed.xml] [--thumb-file img.jpg]
Needs: Pillow (python3-pil). Everything else is the standard library.
"""
import base64
import hashlib
import html
import io
import pathlib
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET

from PIL import Image, ImageOps

PLAYLIST_ID = "PLeWdGep5MypQ"
FEED_URL = f"https://www.youtube.com/feeds/videos.xml?playlist_id={PLAYLIST_ID}"
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "now-playing.svg"
FONTS = ROOT / "assets" / "fonts"
W, H = 1416, 195
NS = {"a": "http://www.w3.org/2005/Atom", "media": "http://search.yahoo.com/mrss/",
      "yt": "http://www.youtube.com/xml/schemas/2015"}
NOISE = re.compile(r"\s*[\(\[\{][^\)\]\}]*(official|video|audio|lyric|lyrics|mv|m/v|visualizer|hd|4k|live|"
                   r"remaster|explicit|clean|prod\.?)[^\)\]\}]*[\)\]\}]", re.I)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (profile-readme bot)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def load_entries(feed_bytes):
    root = ET.fromstring(feed_bytes)
    out = []
    for e in root.findall("a:entry", NS):
        vid = e.findtext("yt:videoId", default="", namespaces=NS)
        title = e.findtext("a:title", default="", namespaces=NS)
        author = e.findtext("a:author/a:name", default="", namespaces=NS)
        thumb = e.find("media:group/media:thumbnail", NS)
        out.append({"id": vid, "title": title, "channel": author,
                    "thumb": thumb.get("url") if thumb is not None else f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"})
    return out


def split_title(raw, channel):
    t = NOISE.sub("", raw).strip()
    t = re.sub(r"\s*\|.*$", "", t)                      # drop "| something" tails
    for sep in (" - ", " – ", " — ", " ~ "):
        if sep in t:
            artist, song = t.split(sep, 1)
            return song.strip(" -–—"), artist.strip()
    artist = re.sub(r"\s*(- Topic|VEVO|Official)$", "", channel, flags=re.I).strip()
    return t, artist


def clip(text, limit):
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def label_data(img_bytes):
    im = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    # YouTube thumbnails are letter-boxed 4:3; keep the centre square of the 16:9 content
    w, h = im.size
    side = int(min(w, h * 0.75))
    im = im.crop(((w - side) // 2, (h - side) // 2, (w + side) // 2, (h + side) // 2))
    im = ImageOps.fit(im, (120, 120), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=82, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def font(weight, name):
    data = base64.b64encode((FONTS / name).read_bytes()).decode()
    return (f'@font-face {{ font-family: "PoppinsCard"; font-weight: {weight}; '
            f'src: url(data:font/woff;base64,{data}) format("woff"); }}')


def build_svg(song, artist, label_uri, index, total):
    """Wide player bar: same height as the GitHub Stats card, as wide as the stats row."""
    e = html.escape
    grooves = "".join(f'<circle r="{r}" fill="none" stroke="#1a2366" stroke-width=".8" opacity=".7"/>'
                      for r in range(36, 64, 4))
    viz = "".join(
        f'<rect class="eq" x="{26 + i * 10}" y="170" width="6" height="16" rx="3" fill="url(#eqg)" '
        f'style="animation-duration:{.7 + (i * 37 % 7) / 10:.1f}s;animation-delay:-{(i * 13 % 9) / 10:.1f}s"/>'
        for i in range(13))
    counter = f"{index + 1:02d} / {total:02d}" if total > 1 else ""
    big_eq = "".join(
        f'<rect class="eq" x="{1206 + i * 13}" y="62" width="8" height="84" rx="4" fill="url(#eqg)" '
        f'style="animation-duration:{.7 + (i * 29 % 8) / 10:.1f}s;animation-delay:-{(i * 17 % 9) / 10:.1f}s"/>'
        for i in range(14))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <linearGradient id="card" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#070b2e"/><stop offset="1" stop-color="#04082c"/></linearGradient>
  <linearGradient id="eqg" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#3f5bd9"/><stop offset="1" stop-color="#eaf1ff"/></linearGradient>
  <radialGradient id="shine" cx=".3" cy=".25" r=".9"><stop offset="0" stop-color="#fff" stop-opacity=".18"/><stop offset=".5" stop-color="#fff" stop-opacity="0"/></radialGradient>
  <clipPath id="lab"><circle r="30"/></clipPath>
  <clipPath id="track"><rect x="178" y="140" width="980" height="4" rx="2"/></clipPath>
</defs>
<style>
  {font(400, "Poppins-Regular-vi.woff")}
  {font(500, "Poppins-Medium-vi.woff")}
  text {{ font-family: "PoppinsCard", "Poppins", "Segoe UI", Helvetica, Arial, sans-serif; }}
  .spin {{ animation: spin 6s linear infinite; }}
  .eq {{ transform-box: fill-box; transform-origin: 50% 100%; animation: eq 1s ease-in-out infinite alternate; }}
  .prog {{ animation: prog 210s linear -70s infinite; }}
  @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
  @keyframes eq {{ from {{ transform: scaleY(.2); }} to {{ transform: scaleY(1); }} }}
  @keyframes prog {{ from {{ transform: translateX(-980px); }} to {{ transform: translateX(0); }} }}
  @media (prefers-reduced-motion: reduce) {{ .spin, .eq, .prog {{ animation: none; }} }}
</style>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="4.5" fill="url(#card)"/>
<g transform="translate(90,90)">
  <circle r="70" fill="#3f5bd9" opacity=".14"/>
  <g class="spin">
    <circle r="67" fill="#05070f" stroke="#111f69" stroke-width="1.5"/>
    {grooves}
    <g clip-path="url(#lab)"><image href="{label_uri}" x="-30" y="-30" width="60" height="60"/></g>
    <circle r="30" fill="none" stroke="#eaf1ff" stroke-opacity=".35"/>
    <circle r="3.5" fill="#04082c"/>
    <path d="M-45 -40 A60 60 0 0 1 38 -47" fill="none" stroke="#eaf1ff" stroke-opacity=".12" stroke-width="5"/>
  </g>
  <circle r="67" fill="url(#shine)"/>
</g>
{viz}
<text x="178" y="42" fill="#6a72a8" font-size="10.5" font-weight="500" letter-spacing="2.8">NOW PLAYING</text>
<text x="{W - 30}" y="42" fill="#6a72a8" font-size="10.5" text-anchor="end" letter-spacing="1">{counter}</text>
<text x="178" y="80" fill="#eaf1ff" font-size="21" font-weight="500">{e(clip(song, 60))}</text>
<text x="178" y="104" fill="#aab6f0" font-size="13">{e(clip(artist, 90))}</text>
<rect x="178" y="140" width="980" height="4" rx="2" fill="#1a2366"/>
<g clip-path="url(#track)"><rect class="prog" x="178" y="140" width="980" height="4" rx="2" fill="#eaf1ff"/></g>
<text x="178" y="166" fill="#6a72a8" font-size="11">YouTube playlist · 4github</text>
{big_eq}
</svg>
'''


def watch_url(vid):
    return f"https://www.youtube.com/watch?v={vid}&list={PLAYLIST_ID}"


def update_readme(entries, index, version):
    """Rewrite the block between the NOW-PLAYING markers so the buttons point at the right videos."""
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    start, end = "<!-- NOW-PLAYING:START -->", "<!-- NOW-PLAYING:END -->"
    if start not in text or end not in text:
        print("README markers not found; skipping README update")
        return
    cur = entries[index]
    block = f'''{start}
<p align="center">
  <a href="{watch_url(cur["id"])}"><img width="97%" src="./assets/now-playing.svg?v={version}" alt="Now playing" /></a>
</p>
{end}'''
    a, b = text.index(start), text.index(end) + len(end)
    readme.write_text(text[:a] + block + text[b:], encoding="utf-8")


def main(argv):
    args = dict(zip(argv[::2], argv[1::2]))
    feed = pathlib.Path(args["--feed-file"]).read_bytes() if "--feed-file" in args else fetch(FEED_URL)
    entries = [e for e in load_entries(feed) if e["id"]]
    if not entries:
        print("playlist feed is empty; keeping the current card")
        return
    index = (int(time.time()) // 3600) % len(entries)          # a different video every hour
    pick = entries[index]
    song, artist = split_title(pick["title"], pick["channel"])
    thumb = pathlib.Path(args["--thumb-file"]).read_bytes() if "--thumb-file" in args else fetch(pick["thumb"])
    svg = build_svg(song, artist, label_data(thumb), index, len(entries))
    OUT.write_text(svg, encoding="utf-8")
    # cache-busting: the image URL changes whenever the card changes, so GitHub can't keep an old copy
    update_readme(entries, index, hashlib.sha1(svg.encode()).hexdigest()[:10])
    print(f"now playing [{index + 1}/{len(entries)}]: {song} — {artist}")


if __name__ == "__main__":
    main(sys.argv[1:])
