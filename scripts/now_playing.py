"""Build assets/now-playing.svg from a public YouTube playlist.

Reads the playlist's RSS feed, picks one video (rotating every hour), uses its thumbnail as the
vinyl label and splits the video title into song / artist.

Usage: python3 scripts/now_playing.py [--feed-file feed.xml] [--thumb-file img.jpg]
Needs: Pillow (python3-pil). Everything else is the standard library.
"""
import base64
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
W, H = 430, 120
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
    e = html.escape
    grooves = "".join(f'<circle r="{r}" fill="none" stroke="#1a2366" stroke-width=".7" opacity=".7"/>'
                      for r in range(26, 44, 3))
    bars = "".join(
        f'<rect class="eq" x="{352 + i * 9}" y="44" width="5" height="44" rx="2.5" fill="url(#eqg)" '
        f'style="animation-duration:{d}s;animation-delay:-{dl}s"/>'
        for i, (d, dl) in enumerate([(.9, 0), (1.3, .3), (.7, .15), (1.1, .45), (.8, .2), (1.4, .05), (1.0, .35)]))
    counter = f"{index + 1:02d} / {total:02d}" if total > 1 else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <linearGradient id="card" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#070b2e"/><stop offset="1" stop-color="#04082c"/></linearGradient>
  <linearGradient id="eqg" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#3f5bd9"/><stop offset="1" stop-color="#eaf1ff"/></linearGradient>
  <radialGradient id="shine" cx=".3" cy=".25" r=".9"><stop offset="0" stop-color="#fff" stop-opacity=".18"/><stop offset=".5" stop-color="#fff" stop-opacity="0"/></radialGradient>
  <clipPath id="lab"><circle r="21"/></clipPath>
  <clipPath id="track"><rect x="118" y="92" width="210" height="3" rx="1.5"/></clipPath>
</defs>
<style>
  {font(400, "Poppins-Regular-vi.woff")}
  {font(500, "Poppins-Medium-vi.woff")}
  text {{ font-family: "PoppinsCard", "Poppins", "Segoe UI", Helvetica, Arial, sans-serif; }}
  .spin {{ animation: spin 6s linear infinite; }}
  .eq {{ transform-box: fill-box; transform-origin: 50% 100%; animation: eq 1s ease-in-out infinite alternate; }}
  .prog {{ animation: prog 210s linear -70s infinite; }}
  @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
  @keyframes eq {{ from {{ transform: scaleY(.18); }} to {{ transform: scaleY(1); }} }}
  @keyframes prog {{ from {{ transform: translateX(-210px); }} to {{ transform: translateX(0); }} }}
  @media (prefers-reduced-motion: reduce) {{ .spin, .eq, .prog {{ animation: none; }} }}
</style>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="url(#card)" stroke="#172e80" stroke-opacity=".6"/>
<g transform="translate(58,60)">
  <circle r="47" fill="#3f5bd9" opacity=".15"/>
  <g class="spin">
    <circle r="45" fill="#05070f" stroke="#111f69" stroke-width="1.2"/>
    {grooves}
    <g clip-path="url(#lab)"><image href="{label_uri}" x="-21" y="-21" width="42" height="42"/></g>
    <circle r="21" fill="none" stroke="#eaf1ff" stroke-opacity=".35"/>
    <circle r="2.8" fill="#04082c"/>
    <path d="M-30 -27 A41 41 0 0 1 26 -32" fill="none" stroke="#eaf1ff" stroke-opacity=".12" stroke-width="4"/>
  </g>
  <circle r="45" fill="url(#shine)"/>
</g>
<text x="118" y="30" fill="#6a72a8" font-size="9" font-weight="500" letter-spacing="2.4">NOW PLAYING</text>
<text x="{W - 16}" y="30" fill="#6a72a8" font-size="9" text-anchor="end" letter-spacing=".8">{counter}</text>
<text x="118" y="56" fill="#eaf1ff" font-size="18" font-weight="500">{e(clip(song, 22))}</text>
<text x="118" y="75" fill="#aab6f0" font-size="11.5">{e(clip(artist, 34))}</text>
<rect x="118" y="92" width="210" height="3" rx="1.5" fill="#1a2366"/>
<g clip-path="url(#track)"><rect class="prog" x="118" y="92" width="210" height="3" rx="1.5" fill="#eaf1ff"/></g>
{bars}
</svg>
'''


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
    OUT.write_text(build_svg(song, artist, label_data(thumb), index, len(entries)), encoding="utf-8")
    print(f"now playing [{index + 1}/{len(entries)}]: {song} — {artist}")


if __name__ == "__main__":
    main(sys.argv[1:])
