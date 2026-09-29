# -*- coding: utf-8 -*-
"""Slide-Renderer @gesundheitsakte — reines PIL, laeuft in der Composio-Sandbox.

Ersetzt builder.py (Playwright). Gleiche Masse, gleiche Typografie.
Der Container kann nicht ins Repo schreiben, die Sandbox schon — deshalb muss
alles, was veroeffentlicht wird, hier entstehen.

Slide-Arten: cover, befund, payoff, cta, panel, erkenntnis, objekt
Reel-Karten:  hook, line, end   (1080x1920, siehe karte())
"""
import os, urllib.request
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
NAVY   = (13, 20, 41)
ROT    = (232, 51, 90)
VIOLETT= (167, 139, 250)
LILA   = (123, 53, 232)
SUB    = (209, 213, 219)
BELEG  = (182, 190, 205)
DONT   = (138, 147, 168)

BASIS = "https://raw.githubusercontent.com/saschakbusiness1-beep/ga-assets/main"
CACHE = "/tmp/ga"

def _font_datei(name):
    os.makedirs(CACHE, exist_ok=True)
    p = f"{CACHE}/{name}"
    if not os.path.exists(p):
        urllib.request.urlretrieve(f"{BASIS}/{name}", p)
    return p

_cache = {}
def anton(size):
    k = ("A", size)
    if k not in _cache:
        _cache[k] = ImageFont.truetype(_font_datei("Anton-Regular.ttf"), size)
    return _cache[k]

def pjs(size, weight=400):
    k = ("P", size, weight)
    if k not in _cache:
        f = ImageFont.truetype(_font_datei("PlusJakartaSans.ttf"), size)
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
        _cache[k] = f
    return _cache[k]

# ── Textwerkzeuge ─────────────────────────────────────────────────────
_mess = ImageDraw.Draw(Image.new("RGB", (8, 8)))

def breite(txt, f, sperr=0.0):
    if not sperr:
        return _mess.textlength(txt, font=f)
    return sum(_mess.textlength(c, font=f) + sperr for c in txt) - (sperr if txt else 0)

def tief(txt, f):
    """Unterkante der Tinte — NICHT getmetrics benutzen, sonst rutscht die
    rote Linie in die letzte Headline-Zeile."""
    return _mess.textbbox((0, 0), txt, font=f)[3]

def umbruch(txt, f, maxbreite):
    zeilen, akt = [], ""
    for wort in txt.split():
        probe = (akt + " " + wort).strip()
        if breite(probe, f) <= maxbreite or not akt:
            akt = probe
        else:
            zeilen.append(akt); akt = wort
    if akt:
        zeilen.append(akt)
    return zeilen

def schreib(d, xy, txt, f, farbe, sperr=0.0):
    if not sperr:
        d.text(xy, txt, font=f, fill=farbe); return
    x, y = xy
    for c in txt:
        d.text((x, y), c, font=f, fill=farbe)
        x += _mess.textlength(c, font=f) + sperr

# ── Signet ────────────────────────────────────────────────────────────
def signet(hoehe=34, s=4):
    """Zeichnet das Marken-Signet nach. viewBox '3 12.5 58 39'."""
    sk = hoehe / 39.0 * s
    bw, bh = int(58 * sk), int(39 * sk)
    im = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    def R(x, y, w, h, r, farbe, dicke):
        x = (x - 3) * sk; y = (y - 12.5) * sk
        d.rounded_rectangle([x, y, x + w * sk, y + h * sk], radius=r * sk,
                            outline=farbe, width=max(1, int(dicke * sk)))
    # hinteres (rotes) Rechteck, danach durch die Maske ausgestanzt
    hinten = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    dh = ImageDraw.Draw(hinten)
    x = (16 - 3) * sk; y = (14.5 - 12.5) * sk
    dh.rounded_rectangle([x, y, x + 43 * sk, y + 28 * sk], radius=7 * sk,
                         outline=ROT + (255,), width=max(1, int(4 * sk)))
    maske = Image.new("L", (bw, bh), 255)
    dm = ImageDraw.Draw(maske)
    mx = (2.3 - 3) * sk; my = (18.8 - 12.5) * sk
    dm.rounded_rectangle([mx, my, mx + 48.4 * sk, my + 33.4 * sk], radius=9 * sk, fill=0)
    hinten.putalpha(Image.composite(hinten.getchannel("A"),
                                    Image.new("L", (bw, bh), 0), maske))
    im = Image.alpha_composite(im, hinten)
    d = ImageDraw.Draw(im)
    R(5, 21.5, 43, 28, 7, VIOLETT + (255,), 4)
    p = [(10, 35.5), (16, 35.5), (19, 28.5), (23, 42.5), (26.5, 35.5), (43, 35.5)]
    d.line([((a - 3) * sk, (b - 12.5) * sk) for a, b in p],
           fill=(255, 255, 255, 255), width=max(1, int(3.12 * sk)), joint="curve")
    return im.resize((int(58 * hoehe / 39), hoehe), Image.LANCZOS)

# ── Grundgeruest ──────────────────────────────────────────────────────
def verlauf(im, anteil=0.64):
    """Navy-Verlauf von unten, damit der Text sicher steht."""
    w, h = im.size
    hh = int(h * anteil)
    maske = Image.new("L", (1, hh))
    px = maske.load()
    for y in range(hh):
        t = y / (hh - 1)            # 0 = oben, 1 = unten
        if t < 0.52:
            a = (t / 0.52) * 0.80
        elif t < 0.78:
            a = 0.80 + (t - 0.52) / 0.26 * 0.17
        else:
            a = 0.97 + (t - 0.78) / 0.22 * 0.03
        px[0, y] = int(a * 255)
    maske = maske.resize((w, hh))
    voll = Image.new("L", (w, h), 0)
    voll.paste(maske, (0, h - hh))
    return Image.composite(Image.new("RGB", (w, h), NAVY), im, voll)

def kopfzeile(im, rechts):
    d = ImageDraw.Draw(im)
    sig = signet(34)
    im.paste(sig, (40, 40), sig)
    schreib(d, (40 + sig.width + 12, 44), "GESUNDHEITSAKTE", anton(20),
            (255, 255, 255), sperr=20 * 0.12)
    f = pjs(17, 600)
    b = breite(rechts, f, 17 * 0.16)
    schreib(d, (W - 40 - b, 44), rechts, f, ROT, sperr=17 * 0.16)

def fortschritt(im, i, total):
    d = ImageDraw.Draw(im)
    x0, x1, y = 64, W - 64, 1350 - 52
    d.rounded_rectangle([x0, y, x1, y + 5], radius=3, fill=(60, 66, 84))
    d.rounded_rectangle([x0, y, x0 + (x1 - x0) * i / total, y + 5], radius=3, fill=LILA)

# ── Textblock ─────────────────────────────────────────────────────────
class Block:
    """Sammelt Zeilen und Linien, misst die Hoehe und zeichnet von unten nach oben."""
    def __init__(self):
        self.teile = []   # ("text", zeilen, font, zeilenhoehe, farbe, sperr) | ("linie", h, b, farbe, oben, unten)
    def text(self, zeilen, f, lh, farbe, sperr=0.0):
        self.teile.append(("text", zeilen, f, lh, farbe, sperr)); return self
    def zwei(self, erst, erstfarbe, rest, restfarbe, f, lh):
        """Erste Zeile zweifarbig ('NICHT' grau, der Rest rot), Folgezeilen in restfarbe."""
        self.teile.append(("zwei", erst, erstfarbe, rest, restfarbe, f, lh)); return self
    def linie(self, hoehe, bre, farbe, oben, unten):
        self.teile.append(("linie", hoehe, bre, farbe, oben, unten)); return self
    def abstand(self, px):
        self.teile.append(("luft", px)); return self
    def hoehe(self):
        h = 0
        for t in self.teile:
            if t[0] == "text":
                _, zeilen, f, lh, _, _ = t
                h += lh * (len(zeilen) - 1) + tief(zeilen[-1] or "X", f)
            elif t[0] == "zwei":
                _, erst, _, rest, _, f, lh = t
                h += lh * (len(rest) - 1) + tief(rest[-1] or erst, f)
            elif t[0] == "linie":
                h += t[4] + t[1] + t[5]
            else:
                h += t[1]
        return h
    def zeichne(self, d, x, y):
        for t in self.teile:
            if t[0] == "text":
                _, zeilen, f, lh, farbe, sperr = t
                for k, z in enumerate(zeilen):
                    schreib(d, (x, y + k * lh), z, f, farbe, sperr)
                y += lh * (len(zeilen) - 1) + tief(zeilen[-1] or "X", f)
            elif t[0] == "zwei":
                _, erst, erstfarbe, rest, restfarbe, f, lh = t
                schreib(d, (x, y), erst, f, erstfarbe)
                vor = breite(erst + " ", f)
                schreib(d, (x + vor, y), rest[0], f, restfarbe)
                for k, z in enumerate(rest[1:], 1):
                    schreib(d, (x, y + k * lh), z, f, restfarbe)
                y += lh * (len(rest) - 1) + tief(rest[-1] or erst, f)
            elif t[0] == "linie":
                _, hoehe, bre, farbe, oben, unten = t
                y += oben
                d.rectangle([x, y, x + bre, y + hoehe], fill=farbe)
                y += hoehe + unten
            else:
                y += t[1]

def _zeilen(txt, gross=True):
    z = [t.strip() for t in txt.split("<br>")]
    return [t.upper() for t in z] if gross else z

def block_fuer(s):
    k = s.get("kind", "befund")
    b = Block()
    if k == "cover":
        b.text(_zeilen(s["h"]), anton(82), 80, (255, 255, 255))
        b.linie(5, 104, ROT, 26, 24)
        b.text(umbruch(s["sub"], pjs(32), 952), pjs(32), 45, SUB)
    elif k == "cta":
        b.text(_zeilen(s["h"]), anton(60), 64, (255, 255, 255))
        b.abstand(34)
        b.text(["@GESUNDHEITSAKTE"], anton(38), 42, VIOLETT, sperr=38 * 0.06)
    elif k == "payoff":
        b.text(_zeilen(s["h"]), anton(58), 60, (255, 255, 255))
        b.linie(5, 104, ROT, 26, 0)
    elif k == "panel":
        b.text(_zeilen(s["do"]), anton(78), 76, (255, 255, 255))
        b.linie(4, 130, ROT, 28, 26)
        b.zwei("NICHT", DONT, _zeilen(s["dont"]), ROT, anton(46), 48)
        if s.get("beleg"):
            b.abstand(24)
            b.text(umbruch(s["beleg"], pjs(27), 840), pjs(27), 37, BELEG)
    elif k == "erkenntnis":
        b.text(_zeilen(s["h"]), anton(52), 57, (255, 255, 255))
        b.linie(5, 104, ROT, 26, 0)
    elif k == "objekt":
        return None
    else:  # befund
        b.text(_zeilen(s["h"]), anton(56), 58, (255, 255, 255))
        if s.get("b"):
            b.linie(5, 104, ROT, 26, 24)
            b.text(umbruch(s["b"], pjs(30), 880), pjs(30), 44, SUB)
        else:
            b.linie(5, 104, ROT, 26, 0)
    return b

# ── Slide ─────────────────────────────────────────────────────────────
def fuellen(pfad, w=W, h=H):
    im = Image.open(pfad).convert("RGB")
    s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    l, t = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((l, t, l + w, t + h))

def slide(bildpfad, s, akte, i, total):
    kind = s.get("kind", "befund")
    im = fuellen(bildpfad)
    im = verlauf(im, 0.74 if kind in ("panel", "erkenntnis") else 0.64)
    if kind in ("cover", "objekt"):
        kopfzeile(im, f"AKTE {akte:03d}")
    else:
        kopfzeile(im, f"{i:02d} / {total:02d}")
        fortschritt(im, i, total)
    b = block_fuer(s)
    if b:
        d = ImageDraw.Draw(im)
        b.zeichne(d, 64, H - 104 - b.hoehe())
    return im

def karussell(akte, eintraege, outdir):
    """eintraege: Liste von (bildpfad, slide-dict). Gibt die Dateipfade zurueck."""
    os.makedirs(outdir, exist_ok=True)
    total = len(eintraege)
    raus = []
    for i, (bp, s) in enumerate(eintraege, 1):
        p = f"{outdir}/a{akte:03d}_{i:02d}.jpg"
        slide(bp, s, akte, i, total).save(p, "JPEG", quality=92)
        raus.append(p)
    return raus

# ══ Reels ═════════════════════════════════════════════════════════════
RW, RH, FPS = 1080, 1920, 30
D6 = (214, 219, 230)

LICHT = [(0.26,0.18,0.40),(0.74,0.26,0.34),(0.20,0.40,0.37),
         (0.80,0.20,0.32),(0.50,0.14,0.43),(0.34,0.30,0.36)]
TON   = [(123,53,232),(90,60,210),(123,53,232),(72,66,200),(140,60,235),(105,58,224)]

def hintergrund(seed, cx, cy, kraft, ton):
    """Marken-Hintergrund. ImageChops.add statt Pixelschleife — die Sandbox
    hat einen Kern, eine Schleife ueber 2 Mio Pixel dauert dort Minuten."""
    from PIL import ImageChops, ImageFilter
    import random
    base = Image.new("RGB", (RW, RH), NAVY)
    glow = Image.new("RGB", (RW, RH), (0, 0, 0))
    d = ImageDraw.Draw(glow)
    px, py = cx * RW, cy * RH
    r, schritte = int(RW * 1.05), 90
    for s in range(schritte, 0, -1):
        f = s / schritte
        rad = int(r * f)
        a = (1 - f) ** 2.4 * kraft
        d.ellipse([px-rad, py-rad*1.25, px+rad, py+rad*1.25],
                  fill=tuple(int(c * a) for c in ton))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    out = ImageChops.add(base, glow)
    grad = Image.new("L", (1, RH)); gd = grad.load()
    for y in range(RH):
        t = max(0.0, (y / RH - 0.24) / 0.76)
        gd[0, y] = int(238 * (t ** 1.25))
    out = Image.composite(Image.new("RGB", (RW, RH), NAVY), out, grad.resize((RW, RH)))
    rnd = random.Random(4000 + seed)
    k = Image.new("L", (RW//2, RH//2))
    k.putdata([rnd.randint(112, 143) for _ in range(RW//2 * RH//2)])
    k = k.resize((RW, RH), Image.BILINEAR).filter(ImageFilter.GaussianBlur(0.4))
    return Image.blend(out, Image.merge("RGB", (k, k, k)), 0.012)   # 0.055 blaeht die Datei auf

def reel_hintergruende(outdir, n):
    os.makedirs(f"{outdir}/echt", exist_ok=True)
    for i in range(1, n+1):
        cx, cy, kr = LICHT[(i-1) % len(LICHT)]
        hintergrund(i, cx, cy, kr, TON[(i-1) % len(TON)]).save(
            f"{outdir}/echt/{i:02d}.jpg", "JPEG", quality=94)

def karte(s):
    """Transparente Textkarte 1080x1920 fuer einen Reel-Beat."""
    im = Image.new("RGBA", (RW, RH), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # Verlauf nur unten, damit das Bild oben frei bleibt
    hh = int(RH * 0.56)
    m = Image.new("L", (1, hh)); mp = m.load()
    for y in range(hh):
        t = y / (hh - 1)
        if t < 0.60:   a = t / 0.60 * 0.88
        elif t < 0.88: a = 0.88 + (t - 0.60) / 0.28 * 0.09
        else:          a = 0.97
        mp[0, y] = int(a * 255)
    sch = Image.new("RGBA", (RW, hh), NAVY + (0,))
    sch.putalpha(m.resize((RW, hh)))
    im.alpha_composite(sch, (0, RH - hh))
    d = ImageDraw.Draw(im)
    sig = signet(40)
    im.paste(sig, (64, 96), sig)
    schreib(d, (64 + sig.width + 14, 100), "GESUNDHEITSAKTE", anton(24),
            (255, 255, 255, 240), sperr=24 * 0.12)
    k = s.get("kind", "line")
    b = Block()
    if k == "hook":
        b.text(_zeilen(s["h"]), anton(96), 92, (255,255,255,255))
        b.linie(6, 120, ROT + (255,), 34, 30)
        b.text(umbruch(s["sub"], pjs(40), 900), pjs(40), 54, D6 + (255,))
    elif k == "end":
        b.text(_zeilen(s["h"]), anton(82), 85, (255,255,255,255))
        b.abstand(40)
        b.text(["@GESUNDHEITSAKTE"], anton(46), 50, VIOLETT + (255,), sperr=46*0.06)
    else:
        b.text(_zeilen(s["h"]), anton(74), 74, (255,255,255,255))
        b.linie(6, 120, ROT + (255,), 34, 30)
        b.text(umbruch(s["sub"], pjs(40), 900), pjs(40), 54, D6 + (255,))
    b.zeichne(d, 64, (RH - 470) - b.hoehe())
    return im

def reel_karten(beats, outdir):
    os.makedirs(f"{outdir}/karten", exist_ok=True)
    for i, b in enumerate(beats, 1):
        karte(b[-1]).save(f"{outdir}/karten/{i:02d}.png")

def reel_montage(beats, outdir, name, ff=None):
    """Ken-Burns plus Textkarten. Jeder Beat wird in Stuecke unter 75 Bildern
    zerlegt — die Sandbox hat 985 MB und kippt sonst mit Exit 137."""
    import subprocess, gc
    if ff is None:
        import imageio_ffmpeg; ff = imageio_ffmpeg.get_ffmpeg_exe()
    os.makedirs(f"{outdir}/teile", exist_ok=True)
    liste, nr = [], 0
    for i, (bild, _, dur, zdir, _) in enumerate(beats, 1):
        ges = int(dur * FPS)
        z0, z1 = (1.05, 1.14) if zdir == "in" else (1.14, 1.05)
        rest, off = ges, 0
        while rest > 0:
            n = min(70, rest)
            za = z0 + (z1 - z0) * off / ges
            zb = z0 + (z1 - z0) * (off + n) / ges
            teil = f"{outdir}/teile/{nr:03d}.mp4"
            fc = (f"[0:v]select=eq(n\\,0),scale=1188:2112,"
                  f"zoompan=z='{za}+({zb}-{za})*on/{n}':d={n}:s={RW}x{RH}:"
                  f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':fps={FPS}[b];"
                  f"[1:v]select=eq(n\\,0),fps={FPS},format=rgba[k];"
                  f"[b][k]overlay=0:0,format=yuv420p[v]")
            cmd = (f'{ff} -y -loglevel error -threads 1 -loop 1 -t {n/FPS:.3f} '
                   f'-i {outdir}/echt/{bild}.jpg -loop 1 -t {n/FPS:.3f} '
                   f'-i {outdir}/karten/{i:02d}.png -filter_complex "{fc}" -map "[v]" '
                   f'-frames:v {n} -r {FPS} -c:v libx264 -crf 18 -preset ultrafast '
                   f'-pix_fmt yuv420p {teil}')
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if r.returncode:
                raise RuntimeError(r.stderr[-1200:])
            liste.append(teil); nr += 1; off += n; rest -= n
            gc.collect()
    with open(f"{outdir}/teile/liste.txt", "w") as f:
        for p in liste:
            f.write(f"file '{os.path.abspath(p)}'\n")
    roh = f"{outdir}/{name}_roh.mp4"
    subprocess.run(f"{ff} -y -loglevel error -f concat -safe 0 "
                   f"-i {outdir}/teile/liste.txt -c copy {roh}", shell=True, check=True)
    fertig = f"{outdir}/{name}_reel.mp4"
    # ultrafast liefert 8 MB — Composio bricht ueber 3 MB mit 413 ab, deshalb einmal nachkodieren
    subprocess.run(f"{ff} -y -loglevel error -i {roh} -threads 1 -c:v libx264 -crf 25 "
                   f"-preset faster -pix_fmt yuv420p -movflags +faststart {fertig}",
                   shell=True, check=True)
    return fertig

BETTEN = ("demons", "piano", "neon", "reality")

def vertone(video, bett, out, ff=None):
    """Musikbett unter das fertige Video legen. Video bleibt unberuehrt."""
    import subprocess, re, urllib.request
    if ff is None:
        import imageio_ffmpeg; ff = imageio_ffmpeg.get_ffmpeg_exe()
    os.makedirs(CACHE, exist_ok=True)
    bp = f"{CACHE}/bett-{bett}.m4a"
    if not os.path.exists(bp):
        urllib.request.urlretrieve(f"{BASIS}/bett-{bett}.m4a", bp)
    r = subprocess.run(f"{ff} -hide_banner -i {video}", shell=True,
                       capture_output=True, text=True)
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr).groups()
    dur = int(h)*3600 + int(m)*60 + float(s)
    af = (f"atrim=0:{dur:.2f},asetpts=PTS-STARTPTS,"
          f"afade=t=in:st=0:d=0.6,afade=t=out:st={dur-1.4:.2f}:d=1.4")
    subprocess.run(f'{ff} -y -loglevel error -i {video} -i {bp} '
                   f'-filter_complex "[1:a]{af}[a]" -map 0:v -map "[a]" -c:v copy '
                   f'-c:a aac -b:a 128k -movflags +faststart -shortest {out}',
                   shell=True, check=True)
    return out

def reel(beats, outdir, name, bett=None):
    reel_hintergruende(outdir, len(beats))
    reel_karten(beats, outdir)
    v = reel_montage(beats, outdir, name)
    if bett:
        v = vertone(v, bett, f"{outdir}/{name}_ton.mp4")
    return v
