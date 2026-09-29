# -*- coding: utf-8 -*-
"""Slide-Renderer @gesundheitsakte — Formate A (Fall), B (Zwei-Panel), C (Objekt)."""
import base64, os, asyncio, sys

W, H = 1080, 1350

def font_uri(p):
    return "data:font/woff2;base64," + base64.b64encode(open(p, "rb").read()).decode()
ANTON = font_uri("node_modules/@fontsource/anton/files/anton-latin-400-normal.woff2")
PJS = {w: font_uri(f"node_modules/@fontsource/plus-jakarta-sans/files/plus-jakarta-sans-latin-{w}-normal.woff2")
       for w in (400, 600, 700)}

MARK = '''<svg viewBox="3 12.5 58 39" class="mk"><g>
<mask id="m"><rect x="0" y="0" width="64" height="64" fill="#fff"/><rect x="2.3" y="18.8" width="48.4" height="33.4" rx="9" fill="#000"/></mask>
<rect x="16" y="14.5" width="43" height="28" rx="7" fill="none" stroke="#E8335A" stroke-width="4" mask="url(#m)"/>
<rect x="5" y="21.5" width="43" height="28" rx="7" fill="none" stroke="#A78BFA" stroke-width="4"/>
<path d="M10 35.5 h6 l3 -7 4 14 3.5 -7 H43" fill="none" stroke="#fff" stroke-width="3.12" stroke-linecap="round" stroke-linejoin="round"/>
</g></svg>'''

CSS = f'''
@font-face{{font-family:Anton;src:url({ANTON}) format("woff2");font-weight:400}}
@font-face{{font-family:PJS;src:url({PJS[400]}) format("woff2");font-weight:400}}
@font-face{{font-family:PJS;src:url({PJS[600]}) format("woff2");font-weight:600}}
@font-face{{font-family:PJS;src:url({PJS[700]}) format("woff2");font-weight:700}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#000}}
.slide{{position:relative;width:{W}px;height:{H}px;background-size:cover;background-position:center;
  overflow:hidden;font-family:PJS,sans-serif;color:#fff}}
.slide::after{{content:"";position:absolute;left:0;right:0;bottom:0;height:64%;z-index:1;
  background:linear-gradient(to top,#0d1429 4%,rgba(13,20,41,.97) 22%,rgba(13,20,41,.80) 48%,rgba(13,20,41,0) 100%)}}
.slide.panel::after{{height:74%;
  background:linear-gradient(to top,#0d1429 6%,rgba(13,20,41,.98) 30%,rgba(13,20,41,.86) 56%,rgba(13,20,41,0) 100%)}}
.lock{{position:absolute;top:40px;left:40px;display:flex;align-items:center;gap:12px;z-index:3}}
.mk{{height:34px;width:{34*58/39:.1f}px;display:block}}
.wm{{font-family:Anton;font-size:20px;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.92);line-height:1}}
.akte{{position:absolute;top:44px;right:40px;z-index:3;font-family:PJS;font-weight:600;font-size:17px;
  letter-spacing:.16em;color:#E8335A}}
.txt{{position:absolute;left:64px;right:64px;bottom:104px;z-index:2}}
h1{{font-family:Anton;font-weight:400;text-transform:uppercase;font-size:82px;line-height:.98}}
h2{{font-family:Anton;font-weight:400;text-transform:uppercase;font-size:56px;line-height:1.04}}
h2.pay{{font-size:58px}}
h2.ctah{{font-size:60px;line-height:1.06}}
.ul{{height:5px;width:104px;background:#E8335A;margin:26px 0 24px}}
.sub{{font-size:32px;line-height:1.4;color:#D1D5DB}}
.body{{font-size:30px;line-height:1.45;color:#D1D5DB;max-width:880px}}
.handle{{font-family:Anton;font-size:38px;letter-spacing:.06em;color:#A78BFA;margin-top:34px}}
.prog{{position:absolute;left:64px;right:64px;bottom:52px;z-index:3}}
.prog i{{display:block;height:5px;background:rgba(255,255,255,.16);border-radius:3px}}
.prog i b{{display:block;height:5px;background:#7B35E8;border-radius:3px}}
/* Zwei-Panel */
.do{{font-family:Anton;text-transform:uppercase;font-size:78px;line-height:.98;color:#fff}}
.split{{height:4px;width:130px;background:#E8335A;margin:28px 0 26px}}
.dont{{font-family:Anton;text-transform:uppercase;font-size:46px;line-height:1.05;color:#8A93A8}}
.dont em{{font-style:normal;color:#E8335A}}
.beleg{{font-size:27px;line-height:1.38;color:#B6BECD;margin-top:24px;max-width:840px}}
h2.erk{{font-size:52px;line-height:1.1}}
'''

def lock():
    return f'<div class="lock">{MARK}<span class="wm">Gesundheitsakte</span></div>'

def render_slide(i, total, img, s, akte):
    kind = s.get("kind", "befund")
    tr = f"AKTE {akte:03d}" if kind == "cover" else f"{i:02d} / {total}"
    prog = "" if kind == "cover" else f'<div class="prog"><i><b style="width:{i/total*100:.1f}%"></b></i></div>'
    cls = "slide"
    if kind == "cover":
        inner = f'<h1>{s["h"]}</h1><div class="ul"></div><p class="sub">{s["sub"]}</p>'
    elif kind == "cta":
        inner = f'<h2 class="ctah">{s["h"]}</h2><p class="handle">@gesundheitsakte</p>'
    elif kind == "payoff":
        inner = f'<h2 class="pay">{s["h"]}</h2><div class="ul"></div>'
    elif kind == "panel":
        cls = "slide panel"
        beleg = f'<p class="beleg">{s["beleg"]}</p>' if s.get("beleg") else ""
        inner = (f'<div class="do">{s["do"]}</div><div class="split"></div>'
                 f'<div class="dont">nicht <em>{s["dont"]}</em></div>{beleg}')
    elif kind == "erkenntnis":
        cls = "slide panel"
        inner = f'<h2 class="erk">{s["h"]}</h2><div class="ul"></div>'
    elif kind == "objekt":
        inner = ""
        prog = ""
        tr = f"AKTE {akte:03d}"
    else:
        b = f'<div class="ul"></div><p class="body">{s["b"]}</p>' if s.get("b") else '<div class="ul"></div>'
        inner = f'<h2>{s["h"]}</h2>{b}'
    txt = f'<div class="txt">{inner}</div>' if inner else ""
    return f'''<div class="{cls}" style="background-image:url({img})">
  {lock()}<span class="akte">{tr}</span>{txt}{prog}
</div>'''

async def build(akte, items, outdir, prefix):
    total = len(items)
    body = "\n".join(render_slide(i, total, img, s, akte) for i, (img, s) in enumerate(items, 1))
    html = f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"
    os.makedirs(outdir, exist_ok=True)
    path = f"{outdir}/slides.html"
    open(path, "w", encoding="utf-8").write(html)
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": W, "height": H})
        await pg.goto("file://" + os.path.abspath(path))
        await pg.wait_for_timeout(2500)
        els = await pg.query_selector_all(".slide")
        for i, el in enumerate(els, 1):
            await el.screenshot(path=f"{outdir}/{prefix}_{i:02d}.png")
        await b.close()
    print(f"Akte {akte:03d}: {len(els)} Slides -> {outdir}")
