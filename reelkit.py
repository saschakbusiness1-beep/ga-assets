# -*- coding: utf-8 -*-
"""Wiederverwendbarer Reel-Baukasten @gesundheitsakte.

Hintergruende, Textkarten und Montage fuer jeden Reel. Aus Akte 003 verallgemeinert.
"""
import base64, os, asyncio, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter
import random

W, H, FPS = 1080, 1920, 30
NAVY = (13, 20, 41)

# ── Hintergruende ─────────────────────────────────────────────────────
LICHT = [(0.26, 0.18, 0.40), (0.74, 0.26, 0.34), (0.20, 0.40, 0.37),
         (0.80, 0.20, 0.32), (0.50, 0.14, 0.43), (0.34, 0.30, 0.36)]
TON = [(123, 53, 232), (90, 60, 210), (123, 53, 232),
       (72, 66, 200), (140, 60, 235), (105, 58, 224)]

def hintergrund(seed, cx, cy, kraft, ton):
    base = Image.new("RGB", (W, H), NAVY)
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(glow)
    px, py = cx * W, cy * H
    r, schritte = int(W * 1.05), 90
    for s in range(schritte, 0, -1):
        f = s / schritte
        rad = int(r * f)
        a = (1 - f) ** 2.4 * kraft
        d.ellipse([px - rad, py - rad * 1.25, px + rad, py + rad * 1.25],
                  fill=tuple(int(c * a) for c in ton))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    pb, pg = base.load(), glow.load()
    out = Image.new("RGB", (W, H)); po = out.load()
    for y in range(H):
        for x in range(W):
            br, bg, bb = pb[x, y]; gr, gg, gb = pg[x, y]
            po[x, y] = (min(255, br + gr), min(255, bg + gg), min(255, bb + gb))
    grad = Image.new("L", (1, H)); gd = grad.load()
    for y in range(H):
        t = max(0.0, (y / H - 0.24) / 0.76)
        gd[0, y] = int(238 * (t ** 1.25))
    out = Image.composite(Image.new("RGB", (W, H), NAVY), out, grad.resize((W, H)))
    rnd = random.Random(4000 + seed)
    k = Image.new("L", (W // 2, H // 2))
    k.putdata([rnd.randint(112, 143) for _ in range(W // 2 * H // 2)])
    k = k.resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(0.4))
    return Image.blend(out, Image.merge("RGB", (k, k, k)), 0.012)

def baue_hintergruende(outdir, n):
    os.makedirs(f"{outdir}/echt", exist_ok=True)
    for i in range(1, n + 1):
        cx, cy, kr = LICHT[(i - 1) % len(LICHT)]
        hintergrund(i, cx, cy, kr, TON[(i - 1) % len(TON)]).save(
            f"{outdir}/echt/{i:02d}.jpg", "JPEG", quality=94)

# ── Textkarten ────────────────────────────────────────────────────────
def font_uri(p):
    return "data:font/woff2;base64," + base64.b64encode(open(p, "rb").read()).decode()
ANTON = font_uri("node_modules/@fontsource/anton/files/anton-latin-400-normal.woff2")
PJS = {w: font_uri(f"node_modules/@fontsource/plus-jakarta-sans/files/plus-jakarta-sans-latin-{w}-normal.woff2")
       for w in (400, 600)}

MARK = '''<svg viewBox="3 12.5 58 39" class="mk"><g>
<mask id="m"><rect x="0" y="0" width="64" height="64" fill="#fff"/><rect x="2.3" y="18.8" width="48.4" height="33.4" rx="9" fill="#000"/></mask>
<rect x="16" y="14.5" width="43" height="28" rx="7" fill="none" stroke="#E8335A" stroke-width="4" mask="url(#m)"/>
<rect x="5" y="21.5" width="43" height="28" rx="7" fill="none" stroke="#A78BFA" stroke-width="4"/>
<path d="M10 35.5 h6 l3 -7 4 14 3.5 -7 H43" fill="none" stroke="#fff" stroke-width="3.12" stroke-linecap="round" stroke-linejoin="round"/>
</g></svg>'''

CSS = f'''
@font-face{{font-family:Anton;src:url({ANTON}) format("woff2")}}
@font-face{{font-family:PJS;src:url({PJS[400]}) format("woff2");font-weight:400}}
@font-face{{font-family:PJS;src:url({PJS[600]}) format("woff2");font-weight:600}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{background:transparent}}
.card{{position:relative;width:{W}px;height:{H}px;font-family:PJS,sans-serif;color:#fff;
  background:transparent;overflow:hidden}}
.card::before{{content:"";position:absolute;left:0;right:0;bottom:0;height:56%;
  background:linear-gradient(to top,rgba(13,20,41,.97) 12%,rgba(13,20,41,.88) 40%,rgba(13,20,41,0) 100%)}}
.lock{{position:absolute;top:96px;left:64px;display:flex;align-items:center;gap:14px}}
.mk{{height:40px;width:{40*58/39:.1f}px;display:block}}
.wm{{font-family:Anton;font-size:24px;letter-spacing:.12em;text-transform:uppercase;
  color:rgba(255,255,255,.94);line-height:1}}
.txt{{position:absolute;left:64px;right:64px;bottom:470px}}
h1{{font-family:Anton;text-transform:uppercase;font-size:96px;line-height:.96}}
h2{{font-family:Anton;text-transform:uppercase;font-size:74px;line-height:1.0}}
h3{{font-family:Anton;text-transform:uppercase;font-size:82px;line-height:1.04}}
.ul{{height:6px;width:120px;background:#E8335A;margin:34px 0 30px}}
.sub{{font-size:40px;line-height:1.36;color:#D6DBE6;max-width:900px}}
.handle{{font-family:Anton;font-size:46px;letter-spacing:.06em;color:#A78BFA;margin-top:40px}}
'''

def card(s):
    k = s.get("kind", "line")
    if k == "hook":
        inner = f'<h1>{s["h"]}</h1><div class="ul"></div><p class="sub">{s["sub"]}</p>'
    elif k == "end":
        inner = f'<h3>{s["h"]}</h3><p class="handle">@gesundheitsakte</p>'
    else:
        inner = f'<h2>{s["h"]}</h2><div class="ul"></div><p class="sub">{s["sub"]}</p>'
    return (f'<div class="card"><div class="lock">{MARK}'
            f'<span class="wm">Gesundheitsakte</span></div>'
            f'<div class="txt">{inner}</div></div>')

async def baue_karten(beats, outdir):
    body = "\n".join(card(s) for *_, s in beats)
    html = f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"
    os.makedirs(f"{outdir}/karten", exist_ok=True)
    p = f"{outdir}/karten.html"
    open(p, "w", encoding="utf-8").write(html)
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        b = await pw.chromium.launch(args=["--force-color-profile=srgb"])
        pg = await b.new_page(viewport={"width": W, "height": H})
        await pg.goto("file://" + os.path.abspath(p))
        await pg.wait_for_timeout(2000)
        for i, el in enumerate(await pg.query_selector_all(".card"), 1):
            await el.screenshot(path=f"{outdir}/karten/{i:02d}.png", omit_background=True)
        await b.close()

# ── Montage ───────────────────────────────────────────────────────────
def montage(beats, outdir, name):
    ins, chain = [], []
    for img, _, dur, _, _ in beats:
        ins.append(f"-loop 1 -t {dur} -i {outdir}/echt/{img}.jpg")
    for i, (_, _, dur, _, _) in enumerate(beats, 1):
        ins.append(f"-loop 1 -t {dur} -i {outdir}/karten/{i:02d}.png")
    nb = len(beats)
    for i, (_, _, dur, zdir, _) in enumerate(beats, 1):
        n = int(dur * FPS)
        z = f"1.05+0.09*on/{n}" if zdir == "in" else f"1.14-0.09*on/{n}"
        # select=eq(n,0) ist Pflicht: sonst bekommt zoompan dur*fps Eingangsbilder
        chain.append(
            f"[{i-1}:v]select='eq(n,0)',scale={int(W*1.25)}:{int(H*1.25)},"
            f"zoompan=z='{z}':d={n}:s={W}x{H}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':fps={FPS}[b{i}]")
        chain.append(
            f"[{nb+i-1}:v]select='eq(n,0)',fps={FPS},format=rgba,fade=t=in:st=0:d=0.4:alpha=1,"
            f"fade=t=out:st={dur-0.3:.2f}:d=0.3:alpha=1[k{i}]")
        chain.append(f"[b{i}][k{i}]overlay=0:0:format=auto[s{i}]")
    chain.append("".join(f"[s{i}]" for i in range(1, nb + 1))
                 + f"concat=n={nb}:v=1:a=0,format=yuv420p[v]")
    cmd = (f"ffmpeg -y -loglevel error {' '.join(ins)} "
           f"-filter_complex \"{';'.join(chain)}\" -map \"[v]\" -r {FPS} "
           f"-c:v libx264 -crf 20 -preset veryfast -pix_fmt yuv420p "
           f"-movflags +faststart {outdir}/{name}_reel.mp4")
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-2000:]); sys.exit(1)
    subprocess.run(f"ffmpeg -y -loglevel error -i {outdir}/{name}_reel.mp4 -ss 1.6 "
                   f"-frames:v 1 -q:v 2 {outdir}/{name}_cover.jpg", shell=True, check=True)

def baue_reel(beats, outdir, name):
    baue_hintergruende(outdir, len(beats))
    asyncio.run(baue_karten(beats, outdir))
    montage(beats, outdir, name)
    total = beats[-1][1] + beats[-1][2]
    print(f"{name}: {len(beats)} Beats, {total:g} Sek -> {outdir}/{name}_reel.mp4")

# ── Musik ─────────────────────────────────────────────────────────────
# Vier lizenzfreie Betten, je 35 Sek, auf -15 LUFS normalisiert.
# Liegen im Asset-Repo, damit auch die Composio-Sandbox sie ziehen kann.
BETT_URL = ("https://raw.githubusercontent.com/saschakbusiness1-beep/"
            "ga-assets/main/bett-{}.m4a")
BETTEN = ("demons", "piano", "neon", "reality")

def _dauer(pfad):
    import re
    r = subprocess.run(f"ffmpeg -hide_banner -i {pfad}", shell=True,
                       capture_output=True, text=True)
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)

def hol_bett(name, ziel):
    """Bett einmal herunterladen, danach aus dem Cache."""
    import urllib.request
    p = f"{ziel}/bett-{name}.m4a"
    if not os.path.exists(p):
        os.makedirs(ziel, exist_ok=True)
        urllib.request.urlretrieve(BETT_URL.format(name), p)
    return p

def vertone(video, bett, out, ein=0.6, aus=1.4):
    """Bett unter das fertige Video legen: Video bleibt unberuehrt (copy)."""
    d = _dauer(video)
    af = (f"atrim=0:{d:.2f},asetpts=PTS-STARTPTS,"
          f"afade=t=in:st=0:d={ein},afade=t=out:st={d-aus:.2f}:d={aus}")
    cmd = (f'ffmpeg -y -loglevel error -i {video} -i {bett} '
           f'-filter_complex "[1:a]{af}[a]" -map 0:v -map "[a]" '
           f'-c:v copy -c:a aac -b:a 128k -movflags +faststart -shortest {out}')
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-1500:]); sys.exit(1)
    return out
