"""One-shot generator for video/ scene files. The generated HTML is the source of truth afterwards."""
import json, pathlib, sys

OUT = pathlib.Path(sys.argv[1])
W, H = 1080, 1920
FPS = 30

# ---------------------------------------------------------------- shared look
def teeth(n=40, depth=12):
    pts = ["0 0", "100% 0", f"100% calc(100% - {depth}px)"]
    for i in range(n, -1, -1):
        x = 100 * i / n
        y = "100%" if i % 2 else f"calc(100% - {depth}px)"
        pts.append(f"{x:.3f}% {y}")
    return "polygon(" + ", ".join(pts) + ")"

NOISE = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E"
         "%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E"
         "%3CfeColorMatrix values='0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1.4 -0.45'/%3E%3C/filter%3E"
         "%3Crect width='300' height='300' filter='url(%23n)'/%3E%3C/svg%3E")

SHARED_CSS = f"""
@font-face {{ font-family: 'Pretendard'; font-weight: 800; src: url('assets/fonts/Pretendard-ExtraBold.woff2') format('woff2'); }}
@font-face {{ font-family: 'Pretendard'; font-weight: 600; src: url('assets/fonts/Pretendard-SemiBold.woff2') format('woff2'); }}
#root {{ --ink: #1E1A15; --paper: #FBFAF6; --red: #D2362B; --pink: #E1306C; --green: #2E8B57; position: absolute; inset: 0; overflow: hidden; font-family: 'Pretendard', sans-serif; color: var(--ink); }}
#root * {{ box-sizing: border-box; }}
.card {{ position: absolute; left: 300px; top: 190px; width: 480px; padding: 16px 16px 14px; background: var(--paper);
  border-radius: 20px; box-shadow: 0 18px 40px rgba(40,20,0,0.30); z-index: 5; }}
.card .photo {{ position: relative; width: 448px; height: 448px; border-radius: 8px; background: #ECE6DA; overflow: hidden; }}
.card .photo img {{ display: block; width: 100%; height: 100%; object-fit: cover; }}
.card .slot {{ position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  font: 500 32px 'JetBrains Mono', monospace; color: #6F6555; }}
.card .cap {{ margin-top: 12px; font-weight: 600; font-size: 28px; line-height: 36px; letter-spacing: -0.01em; }}
.slipwrap {{ position: absolute; filter: drop-shadow(0 12px 16px rgba(40,20,0,0.28)); z-index: 3; }}
.slip {{ background: var(--paper); padding: 24px 32px 36px; clip-path: {teeth()};
  font: 500 34px/1.4 'JetBrains Mono', 'Pretendard', monospace; color: var(--ink); white-space: pre; }}
.slip .ln {{ display: block; }}
.dim {{ color: #8A8172; }}
.red {{ color: var(--red); }}
.green {{ color: var(--green); }}
.pink {{ color: var(--pink); }}
.stamp {{ position: absolute; border: 6px solid var(--red); color: var(--red); border-radius: 8px; padding: 8px 22px;
  font: 700 44px 'JetBrains Mono', monospace; white-space: nowrap; z-index: 8; background: rgba(251,250,246,0.82); }}
.clock {{ position: absolute; border-radius: 50%; background: #FBFAF6; border: 14px solid #2A241D;
  box-shadow: 0 16px 34px rgba(40,20,0,0.32); z-index: 4; }}
.clock .num {{ position: absolute; font: 600 34px 'Pretendard'; width: 60px; text-align: center; }}
.clock .hand {{ position: absolute; left: 50%; bottom: 50%; background: #1E1A15; border-radius: 6px; transform-origin: 50% 100%; }}
.clock .pin {{ position: absolute; left: 50%; top: 50%; width: 22px; height: 22px; margin: -11px 0 0 -11px; border-radius: 50%; background: #1E1A15; }}
.door {{ position: absolute; width: 300px; height: 400px; z-index: 4; }}
.door .frame {{ position: absolute; inset: -18px -18px 0 -18px; background: #5A3A1E; border-radius: 10px 10px 0 0;
  box-shadow: 0 16px 30px rgba(40,20,0,0.35); }}
.door .inside {{ position: absolute; inset: 0; background: #2E1C0E; }}
.door .slab {{ position: absolute; inset: 0; background: #7A4E28; transform-origin: 0% 50%; z-index: 6; }}
.door .slab .pnl {{ position: absolute; left: 34px; right: 34px; border: 6px solid #6A4220; border-radius: 6px; }}
.door .slab .knob {{ position: absolute; right: 30px; top: 205px; width: 34px; height: 34px; border-radius: 50%; background: #C9A227;
  box-shadow: inset -4px -4px 0 rgba(0,0,0,0.25); }}
.door .sign {{ position: absolute; left: 40px; right: 40px; top: 150px; padding: 12px 0; background: var(--red); color: var(--paper);
  font: 700 40px 'JetBrains Mono', monospace; text-align: center; border-radius: 6px; }}
"""

def font_face_ok():
    return SHARED_CSS

def card(cid, photo=True, extra_style=""):
    img_style = "" if photo else ' style="clip-path: inset(0 0 100% 0)"'
    slot = "" if photo else f'<div class="slot" id="{cid}-slot">image_url</div>'
    return (f'<div class="card" id="{cid}"{extra_style}><div class="photo">'
            f'<img id="{cid}-img" src="assets/img/post-photo.jpg" alt=""{img_style} />{slot}</div>'
            f'<div class="cap" data-layout-ignore>자동으로 올라간 첫 번째 글<br />#autopost</div></div>')

def slip(sid, left, top, width, lines_html, font_px=34):
    lines = "".join(f'<span class="ln" id="{sid}-l{i}">{l}</span>' for i, l in enumerate(lines_html))
    return (f'<div class="slipwrap" id="{sid}" style="left:{left}px; top:{top}px; width:{width}px;">'
            f'<div class="slip" style="font-size:{font_px}px;">{lines}</div></div>')

def clock(cid, left, top, size, hour_deg, min_deg, inner=""):
    s = size - 28
    nums = ""
    for n, (x, y) in {"12": (0.5, 0.12), "3": (0.88, 0.5), "6": (0.5, 0.88), "9": (0.12, 0.5)}.items():
        nums += f'<div class="num" style="left:{x*s-30:.0f}px; top:{y*s-22:.0f}px;">{n}</div>'
    hl, ml = s * 0.26, s * 0.38
    return (f'<div class="clock" id="{cid}" style="left:{left}px; top:{top}px; width:{size}px; height:{size}px;">{nums}{inner}'
            f'<div class="hand" id="{cid}-h" style="width:12px; height:{hl:.0f}px; margin-left:-6px;"></div>'
            f'<div class="hand" id="{cid}-m" style="width:8px; height:{ml:.0f}px; margin-left:-4px;"></div>'
            f'<div class="pin"></div></div>')

def door(did, left, top, sign=False):
    sign_html = f'<div class="sign" id="{did}-sign">code 190</div>' if sign else ""
    return (f'<div class="door" id="{did}" style="left:{left}px; top:{top}px;"><div class="frame"></div><div class="inside"></div>'
            f'<div class="slab" id="{did}-slab"><div class="pnl" style="top:30px; height:150px;"></div>'
            f'<div class="pnl" style="top:240px; height:130px;"></div><div class="knob"></div>{sign_html}</div></div>')

def scene(sid, dur, css, body, js):
    return f"""<template>
  <style>{SHARED_CSS}{css}
  </style>
  <div id="root" data-composition-id="{sid}" data-width="{W}" data-height="{H}">
{body}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{js}
    window.__timelines["{sid}"] = tl;
  </script>
</template>
"""

ENTER = "expo.out"
REST_CARD = "y: 0, x: 0, scale: 1, rotation: 0"

def exit_up(sel, t, stagger=0):
    st = f", stagger: {stagger}" if stagger else ""
    return f'    tl.to({sel}, {{ y: -1300, duration: 0.4, ease: "power3.in"{st} }}, {t});\n'

def enter_up(sel, t, dist=1300, dur=0.5):
    return f'    tl.fromTo({sel}, {{ y: {dist} }}, {{ y: 0, duration: {dur}, ease: "{ENTER}" }}, {t});\n'

def print_lines(sid, idxs, t, gap=0.1):
    out = ""
    for k, i in enumerate(idxs):
        out += f'    tl.fromTo("#{sid}-l{i}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.04, ease: "none" }}, {t + k*gap:.3f});\n'
    return out

scenes = []  # (id, start, dur)

# ---------------------------------------------------------------- s01 hook (0 - 4.667)
sid = "s01"
body = card("s01-card", photo=False) + slip("s01-slip", 90, 800, 900, [
    '<span class="dim">$ git log</span>', "fatal: 현재 'main' 브랜치에", "아직 아무 커밋도 없습니다"])
js = """    tl.fromTo("#s01-card", { y: -70, scale: 1.06, rotation: -6, boxShadow: "0 40px 70px rgba(40,20,0,0.35)" },
      { y: 0, scale: 1, rotation: 0, boxShadow: "0 18px 40px rgba(40,20,0,0.30)", duration: 0.6, ease: "elastic.out(1, 0.6)" }, 0);
"""
js += exit_up('"#s01-slip"', 2.0)
js += """    tl.fromTo("#s01-card-slot", { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.17, ease: "power2.out" }, 2.2);
    tl.to("#s01-card", { scale: 1.15, duration: 2.0, ease: "power2.inOut" }, 2.2);
    tl.to("#s01-card", { scale: 1, duration: 0.3, ease: "power3.in" }, 4.3);
"""
scenes.append((sid, 0, 140/30, scene(sid, 140/30, "", body, js)))

# ---------------------------------------------------------------- s02 test first (4.667 - 8.667)
sid = "s02"
body = card("s02-card", photo=False) + slip("s02-slip", 90, 800, 900, [
    '<span class="dim">$ uv run pytest</span>',
    '<span class="red">E ModuleNotFoundError:</span>',
    '<span class="red">  No module named</span>',
    '<span class="red">  \'autopost.scheduler\'</span>'])
body += '<div id="s02-pass" style="position:absolute; left:122px; top:880px; z-index:4; font:700 64px \'JetBrains Mono\', monospace; color:var(--green);">1 passed</div>'
js = enter_up('"#s02-slip"', 0)
js += print_lines("s02-slip", [0, 1, 2, 3], 0.35)
js += """    tl.to(["#s02-slip-l1", "#s02-slip-l2", "#s02-slip-l3"], { opacity: 0, filter: "blur(8px)", duration: 0.15, ease: "power2.in" }, 2.05);
    tl.fromTo("#s02-pass", { opacity: 0, scale: 1.25 }, { opacity: 1, scale: 1, duration: 0.2, ease: "power4.out" }, 2.2);
    tl.to("#s02-card-slot", { opacity: 0, duration: 0.1 }, 3.2);
    tl.fromTo("#s02-card-img", { clipPath: "inset(0% 0% 100% 0%)" }, { clipPath: "inset(0% 0% 0% 0%)", duration: 0.45, ease: "steps(9)" }, 3.2);
"""
js += exit_up('["#s02-slip", "#s02-pass"]', 3.5)
scenes.append((sid, 140/30, 4, scene(sid, 4, "", body, js)))

# ---------------------------------------------------------------- s03 double post (8.667 - 12.667)
sid = "s03"
body = (f'<div id="s03-bgrp" style="position:absolute; inset:0; z-index:4;">{card("s03-cardb")}'
        f'<div class="stamp" id="s03-stamp" style="left:548px; top:428px;">assert 2 == 1</div></div>'
        + card("s03-carda", extra_style=' style="z-index:6;"'))
js = """    gsap.set("#s03-stamp", { rotation: -6 });
    tl.to("#s03-carda", { x: -205, scale: 0.8, duration: 0.45, ease: "power3.out" }, 0.3);
    tl.to("#s03-cardb", { x: 205, scale: 0.8, rotation: 3, duration: 0.45, ease: "power3.out" }, 0.3);
    tl.fromTo("#s03-stamp", { opacity: 0, scale: 1.4 }, { opacity: 1, scale: 1, duration: 0.13, ease: "power4.out" }, 1.0);
    tl.fromTo("#s03-cardb", { y: 0 }, { y: 3, duration: 0.07, yoyo: true, repeat: 1, ease: "power1.out" }, 1.1);
    tl.to("#s03-bgrp", { y: -1300, rotation: 10, duration: 0.45, ease: "power3.in" }, 2.7);
    tl.to("#s03-carda", { x: 0, scale: 1, duration: 0.5, ease: "power2.inOut" }, 3.0);
"""
scenes.append((sid, 260/30, 4, scene(sid, 4, "", body, js)))

# ---------------------------------------------------------------- s04 timezone clock (12.667 - 17.333)
sid = "s04"
ghosts = "".join(card(f"s04-g{k}", extra_style=f' data-layout-ignore style="z-index:{4-k}; left:{300+30*k}px; top:{190-22*k}px;"') for k in (1, 2, 3))
inner = ('<div style="position:absolute; left:180px; top:64px; width:108px; text-align:center; font:700 34px \'JetBrains Mono\', monospace;">20:00</div>'
         '<div style="position:absolute; left:180px; top:106px; width:108px; text-align:center; font:500 28px \'JetBrains Mono\', monospace; color:#6F6555;">+??:??</div>')
body = ghosts + card("s04-card") + clock("s04-clock", 90, 800, 340, 240, 0, inner) + slip("s04-slip", 470, 812, 540, [
    '<span class="red">TypeError:</span>', '<span class="red">can\'t compare</span>',
    '<span class="red">offset-naive and</span>', '<span class="red">offset-aware datetimes</span>'], font_px=32)
js = """    gsap.set("#s04-clock-h", { rotation: 240 });
    gsap.set("#s04-clock-m", { rotation: 0 });
"""
js += enter_up('"#s04-clock"', 0)
js += """    tl.fromTo(["#s04-g1", "#s04-g2", "#s04-g3"], { x: 760 }, { x: 0, duration: 0.55, ease: "power3.in", stagger: 0.04 }, 0.15);
    tl.fromTo(["#s04-card", "#s04-g1", "#s04-g2", "#s04-g3"], { x: 0 }, { x: 10, duration: 0.033, yoyo: true, repeat: 3, ease: "none" }, 0.8);
"""
js += enter_up('"#s04-slip"', 1.0)
js += print_lines("s04-slip", [0, 1, 2, 3], 1.1)
js += exit_up('["#s04-clock", "#s04-slip", "#s04-g3", "#s04-g2", "#s04-g1"]', 4.15, 0.03)
scenes.append((sid, 380/30, 140/30, scene(sid, 140/30, "", body, js)))

# ---------------------------------------------------------------- s05 container box + forever clock (17.333 - 24)
sid = "s05"
css = """
#s05-box { position:absolute; left:340px; top:800px; width:400px; height:260px; z-index:2; }
#s05-back { position:absolute; left:0; right:0; top:-34px; height:40px; background:#9E7444; border-radius:4px 4px 0 0; }
#s05-front { position:absolute; inset:0; background:#C79A62; border-radius:4px; box-shadow:0 18px 34px rgba(40,20,0,0.32); z-index:7; }
#s05-tape { position:absolute; left:170px; width:60px; top:0; height:80px; background:#E8D9B5; opacity:0.9; }
#s05-lid { position:absolute; left:-8px; right:-8px; top:-40px; height:44px; background:#B48650; border-radius:4px; z-index:8;
  box-shadow:0 6px 10px rgba(40,20,0,0.25); }
#s05-label { position:absolute; left:60px; right:60px; top:130px; height:76px; background:var(--paper); border-radius:6px;
  font:700 36px 'JetBrains Mono', monospace; z-index:8; }
#s05-label span { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; }
"""
body = (card("s05-card", extra_style=' style="z-index:1;"') +
        '<div id="s05-box"><div id="s05-back"></div><div id="s05-front"><div id="s05-tape"></div></div><div id="s05-lid"></div>'
        '<div id="s05-label"><span id="s05-prog">IN_PROGRESS</span><span id="s05-err" class="red">ERROR</span></div></div>'
        + clock("s05-clock", 370, 280, 340, 300, 0)
        + slip("s05-slip", 200, 1068, 680, ["IndexError: pop from empty list"], font_px=30))
css += "#s05-slip .slip { padding: 14px 28px 26px; }\n"
js = """    gsap.set("#s05-err", { opacity: 0 });
    gsap.set("#s05-lid", { opacity: 0 });
    gsap.set("#s05-clock-h", { rotation: 300 });
"""
js += enter_up('"#s05-box"', 0)
js += """    tl.to("#s05-card", { y: 455, scale: 0.42, duration: 0.5, ease: "power3.in" }, 0.5);
    tl.fromTo("#s05-lid", { opacity: 0, y: -90, rotation: -14 }, { opacity: 1, y: 0, rotation: 0, duration: 0.15, ease: "power4.in" }, 1.0);
    tl.to("#s05-label", { opacity: 0.25, duration: 0.08, yoyo: true, repeat: 1 }, 1.5);
    tl.to("#s05-label", { opacity: 0.25, duration: 0.08, yoyo: true, repeat: 1 }, 2.17);
    tl.to("#s05-label", { opacity: 0.25, duration: 0.08, yoyo: true, repeat: 1 }, 2.83);
    tl.set("#s05-prog", { opacity: 0 }, 3.333);
    tl.set("#s05-err", { opacity: 1 }, 3.333);
    tl.fromTo("#s05-clock", { scale: 0.6, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.45, ease: "back.out(1.6)" }, 3.3);
    tl.fromTo("#s05-clock-m", { rotation: 0 }, { rotation: 1800, duration: 2.6, ease: "power2.in" }, 3.4);
    tl.fromTo("#s05-clock-h", { rotation: 300 }, { rotation: 450, duration: 2.6, ease: "power2.in" }, 3.4);
    tl.fromTo("#s05-slip", { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.15, ease: "power2.out" }, 3.67);
    tl.to("#s05-clock", { y: -1300, duration: 0.4, ease: "power3.in" }, 5.95);
    tl.to("#s05-slip", { opacity: 0, filter: "blur(8px)", duration: 0.15 }, 5.9);
    tl.to("#s05-lid", { y: -70, rotation: 18, opacity: 0, duration: 0.2, ease: "power2.out" }, 6.0);
    tl.to("#s05-card", { y: 0, scale: 1, duration: 0.5, ease: "expo.out" }, 6.08);
    tl.to("#s05-box", { y: -1300, duration: 0.4, ease: "power3.in" }, 6.2);
"""
scenes.append((sid, 520/30, 200/30, scene(sid, 200/30, css, body, js)))

# ---------------------------------------------------------------- s06 door slams (24 - 28)
sid = "s06"
body = (door("s06-door", 390, 770, sign=True) + card("s06-card", extra_style=' style="z-index:9;"')
        + slip("s06-slip", 712, 836, 340, ["Invalid OAuth", "access token"], font_px=30))
js = """    gsap.set("#s06-door-slab", { rotationY: -72, transformPerspective: 900 });
    gsap.set("#s06-door-sign", { opacity: 0 });
"""
js += enter_up('"#s06-door"', 0)
js += """    tl.to("#s06-card", { y: 330, scale: 0.5, duration: 0.27, ease: "power3.in" }, 0.5);
    tl.to("#s06-door-slab", { rotationY: 0, duration: 0.12, ease: "power4.in" }, 0.68);
    tl.fromTo("#s06-door-sign", { opacity: 0, scale: 1.2 }, { opacity: 1, scale: 1, duration: 0.13, ease: "power4.out" }, 0.8);
    tl.to("#s06-card", { y: 0, scale: 1, rotation: -5, duration: 0.47, ease: "back.out(1.6)" }, 0.8);
    tl.to("#s06-card", { rotation: 0, duration: 0.3, ease: "power2.out" }, 1.27);
"""
js += enter_up('"#s06-slip"', 1.3)
js += print_lines("s06-slip", [0, 1], 1.4)
js += exit_up('["#s06-door", "#s06-slip"]', 3.55, 0.04)
scenes.append((sid, 24, 4, scene(sid, 4, "", body, js)))

# ---------------------------------------------------------------- s07 walls + key (28 - 34)
sid = "s07"
css = f"""
#s07-wall1 {{ position:absolute; left:90px; top:790px; width:900px; height:330px; background:#D8D0C2; border-radius:6px; z-index:3;
  box-shadow:0 18px 34px rgba(40,20,0,0.32); }}
#s07-wall1::after {{ content:""; position:absolute; inset:0; background-image:url("{NOISE}"); opacity:0.18; border-radius:6px; }}
#s07-note {{ position:absolute; left:110px; top:95px; width:680px; padding:30px 0; background:var(--paper); text-align:center;
  font-weight:600; font-size:46px; box-shadow:0 6px 12px rgba(40,20,0,0.2); }}
#s07-menu {{ position:absolute; left:90px; top:820px; width:900px; height:290px; background:#FFFFFF; border-radius:18px; z-index:3;
  box-shadow:0 18px 34px rgba(40,20,0,0.32); font-family:'Inter', sans-serif; }}
.s07-row {{ position:absolute; left:48px; right:48px; height:110px; display:flex; align-items:center; font:600 38px 'Inter', sans-serif; }}
#s07-strike {{ position:absolute; left:44px; width:640px; top:86px; height:6px; background:var(--red); transform-origin:0% 50%; }}
#s07-gitbox {{ position:absolute; left:600px; top:860px; width:390px; height:240px; background:#4A2F18; border-radius:10px; z-index:3;
  box-shadow:0 18px 34px rgba(40,20,0,0.35); }}
#s07-slot {{ position:absolute; left:-2px; top:96px; width:26px; height:56px; background:#1A0F07; border-radius:3px; }}
#s07-gitlabel {{ position:absolute; left:60px; top:40px; font:600 40px 'JetBrains Mono', monospace; color:#F1E6CF; }}
#s07-plate {{ position:absolute; left:60px; top:130px; padding:12px 22px; background:#C9A227; border-radius:6px;
  font:700 36px 'JetBrains Mono', monospace; color:#1E1A15; }}
#s07-key {{ position:absolute; left:110px; top:910px; width:330px; height:130px; z-index:4; filter:drop-shadow(0 10px 10px rgba(40,20,0,0.35)); }}
"""
key_svg = ('<svg id="s07-key" viewBox="0 0 330 130"><circle cx="62" cy="65" r="52" fill="#C9A227"/><circle cx="62" cy="65" r="20" fill="#A9743E"/>'
           '<rect x="108" y="52" width="210" height="26" rx="6" fill="#C9A227"/><rect x="250" y="78" width="20" height="30" fill="#C9A227"/>'
           '<rect x="286" y="78" width="20" height="40" fill="#C9A227"/></svg>')
body = (card("s07-card", extra_style=' style="z-index:9;"')
        + '<div id="s07-wall1"><div id="s07-note">개인 계정 → API 사용 불가</div></div>'
        + '<div id="s07-menu"><div class="s07-row" style="top:30px;">API setup with Instagram login</div><div id="s07-strike"></div>'
          '<div class="s07-row" id="s07-row2" style="top:150px;">API setup with unified login</div></div>'
        + '<div id="s07-gitbox"><div id="s07-slot"></div><div id="s07-gitlabel">git commit</div><div id="s07-plate">gitleaks</div></div>'
        + key_svg)
js = """    gsap.set("#s07-note", { rotation: -2 });
    gsap.set(["#s07-menu", "#s07-gitbox"], { y: 1300 });
    gsap.set("#s07-key", { x: -720 });
    tl.fromTo("#s07-wall1", { y: 1300 }, { y: 0, duration: 0.35, ease: "power3.out" }, 0);
    tl.fromTo("#s07-card", { y: 0 }, { y: -14, duration: 0.07, yoyo: true, repeat: 1, ease: "power2.out" }, 0.33);
"""
js += exit_up('"#s07-wall1"', 1.85)
js += """    tl.fromTo("#s07-menu", { y: 1300 }, { y: 0, duration: 0.35, ease: "power3.out", immediateRender: false }, 2.0);
    tl.fromTo("#s07-card", { y: 0 }, { y: -10, duration: 0.07, yoyo: true, repeat: 1, ease: "power2.out", immediateRender: false }, 2.33);
    tl.fromTo("#s07-strike", { scaleX: 0 }, { scaleX: 1, duration: 0.2, ease: "power2.inOut" }, 2.38);
    tl.fromTo("#s07-row2", { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.17, ease: "power2.out" }, 2.5);
"""
js += exit_up('"#s07-menu"', 4.0)
js += """    tl.fromTo("#s07-gitbox", { y: 1300 }, { y: 0, duration: 0.5, ease: "expo.out", immediateRender: false }, 4.1);
    tl.fromTo("#s07-key", { y: 0, x: -720 }, { x: 0, duration: 0.45, ease: "expo.out", immediateRender: false }, 4.2);
    tl.to("#s07-key", { x: 150, duration: 0.33, ease: "power2.in" }, 4.72);
    tl.to("#s07-key", { x: 132, rotation: -3, duration: 0.2, ease: "back.out(2)" }, 5.05);
"""
js += exit_up('["#s07-key", "#s07-gitbox"]', 5.58, 0.04)
scenes.append((sid, 28, 6, scene(sid, 6, css, body, js)))

# ---------------------------------------------------------------- s08 same door opens (34 - 38)
sid = "s08"
body = (door("s08-door", 120, 770) + card("s08-card", extra_style=' style="z-index:9;"')
        + slip("s08-slip", 450, 800, 590, ['<span class="dim">@</span>d2d_devtoday', '<span class="dim">quota_usage</span>',
                                           '<span class="pink" style="font-size:78px; font-weight:700;">0 / 100</span>'], font_px=34))
js = enter_up('"#s08-door"', 0)
js += """    gsap.set("#s08-door-slab", { transformPerspective: 900 });
    tl.fromTo("#s08-door-slab", { rotationY: 0 }, { rotationY: -72, duration: 0.4, ease: "power2.inOut" }, 0.6);
    tl.fromTo("#s08-slip", { x: -330, opacity: 0 }, { x: 0, opacity: 1, duration: 0.5, ease: "expo.out" }, 0.95);
"""
js += exit_up('"#s08-slip"', 3.55)
scenes.append((sid, 34, 4, scene(sid, 4, "", body, js)))

# ---------------------------------------------------------------- s09 first post (38 - 48)
sid = "s09"
css = """
#s09-phone { position:absolute; left:280px; top:190px; width:520px; height:924px; background:#1E1A15; border-radius:64px; padding:18px; z-index:6;
  box-shadow:0 26px 50px rgba(40,20,0,0.40); transform-origin:50% 45%; }
#s09-screen { position:relative; width:100%; height:100%; background:#FFFFFF; border-radius:48px; overflow:hidden; }
#s09-notch { position:absolute; left:50%; top:14px; width:120px; height:30px; margin-left:-60px; background:#1E1A15; border-radius:15px; z-index:3; }
#s09-shot { position:absolute; left:0; top:70px; width:484px; }
.s09-sk { position:absolute; background:#ECE8E1; border-radius:8px; }
#s09-card2 { left:300px; top:190px; z-index:7; }
"""
body = (door("s09-door", 120, 770) + card("s09-card", extra_style=' style="z-index:5;"')
        + slip("s09-slip", 90, 520, 900, ['<span class="dim">$ uv run autopost queue.json</span>',
                                          '<span style="font-size:44px; font-weight:700;">first-post: posted</span>',
                                          '(18233985166331147)'], font_px=34)
        + '<div id="s09-phone"><div id="s09-screen"><div id="s09-notch"></div>'
          '<div class="s09-sk" style="left:24px; top:90px; width:60px; height:60px; border-radius:30px;"></div>'
          '<div class="s09-sk" style="left:100px; top:105px; width:180px; height:28px;"></div>'
          '<div class="s09-sk" style="left:0; top:170px; width:484px; height:484px; border-radius:0;"></div>'
          '<div class="s09-sk" style="left:24px; top:690px; width:300px; height:26px;"></div>'
          '<img id="s09-shot" src="assets/img/post-screen.png" alt="" /></div></div>'
        + card("s09-card2").replace('id="s09-card2"', 'id="s09-card2"'))
js = """    gsap.set("#s09-door-slab", { rotationY: -72, transformPerspective: 900 });
    gsap.set("#s09-phone", { y: 1800 });
    gsap.set("#s09-slip", { y: 1500 });
    gsap.set("#s09-shot", { opacity: 0 });
    gsap.set("#s09-card2", { y: -900, opacity: 1 });
    tl.to("#s09-card", { x: -270, y: 501, scale: 0.36, duration: 0.5, ease: "power3.in" }, 0.1);
    tl.set("#s09-card", { opacity: 0 }, 0.62);
    tl.to("#s09-door-slab", { rotationY: 0, duration: 0.15, ease: "power4.in" }, 0.6);
    tl.to("#s09-door", { y: -1300, duration: 0.4, ease: "power3.in" }, 0.85);
    tl.fromTo("#s09-slip", { y: 1500 }, { y: 0, duration: 0.45, ease: "expo.out", immediateRender: false }, 0.75);
"""
js += print_lines("s09-slip", [0, 1, 2], 0.85, 0.15)
js += """    tl.to("#s09-slip", { y: -1300, duration: 0.35, ease: "power3.in" }, 1.6);
    tl.fromTo("#s09-phone", { y: 1800 }, { y: 0, duration: 0.5, ease: "expo.out", immediateRender: false }, 1.45);
    tl.to("#s09-card2", { y: 120, scale: 0.9, duration: 0.25, ease: "power3.in" }, 1.75);
    tl.set("#s09-card2", { opacity: 0 }, 2.0);
    tl.set("#s09-shot", { opacity: 1 }, 2.0);
    tl.fromTo("#s09-phone", { scale: 1 }, { scale: 1.12, duration: 7.2, ease: "power2.inOut" }, 2.4);
"""
scenes.append((sid, 38, 10, scene(sid, 10, css, body, js)))

# ---------------------------------------------------------------- s10 every 15 minutes (48 - 54)
sid = "s10"
css = css.replace("#s09", "#s10").replace(".s09", ".s10")
body = ('<div id="s10-phone"><div id="s10-screen"><div id="s10-notch"></div>'
        '<img id="s10-shot" src="assets/img/post-screen.png" alt="" /></div></div>'
        + clock("s10-clock", 640, 380, 330, 0, 0)
        + slip("s10-slip", 600, 770, 420, ["*/15 * * * *"], font_px=44))
js = """    gsap.set("#s10-phone", { scale: 1.12 });
    gsap.set(["#s10-clock-h", "#s10-clock-m"], { rotation: 0 });
    tl.to("#s10-phone", { scale: 0.66, x: -235, duration: 0.6, ease: "power2.inOut" }, 0.2);
"""
js += enter_up('"#s10-clock"', 0.6)
js += enter_up('"#s10-slip"', 0.9)
for k, t in enumerate((1.4, 2.6, 3.8, 5.0)):
    js += f'    tl.to("#s10-clock-m", {{ rotation: {90*(k+1)}, duration: 0.5, ease: "power2.inOut" }}, {t});\n'
    js += f'    tl.to("#s10-clock-h", {{ rotation: {7.5*(k+1)}, duration: 0.5, ease: "power2.inOut" }}, {t});\n'
js += exit_up('["#s10-phone", "#s10-clock", "#s10-slip"]', 5.55, 0.04)
scenes.append((sid, 48, 6, scene(sid, 6, css, body, js)))

# ---------------------------------------------------------------- s11 end card (54 - 60)
sid = "s11"
css = """
#s11-card { position:absolute; left:110px; top:600px; width:860px; padding:70px 64px 64px; background:var(--paper); border-radius:24px;
  box-shadow:0 22px 46px rgba(40,20,0,0.32); }
#s11-title { font-weight:800; font-size:80px; line-height:1.15; letter-spacing:-0.02em; }
#s11-sub { margin-top:36px; font-weight:600; font-size:40px; color:#6B6155; }
"""
body = '<div id="s11-card"><div id="s11-title">인스타 자동 포스팅<br />제작기</div><div id="s11-sub">테스트 19개 · 실제 게시 1건</div></div>'
js = """    tl.fromTo("#s11-card", { y: -90, scale: 1.06, rotation: -4, boxShadow: "0 44px 80px rgba(40,20,0,0.35)" },
      { y: 0, scale: 1, rotation: -1.5, boxShadow: "0 22px 46px rgba(40,20,0,0.32)", duration: 0.6, ease: "elastic.out(1, 0.6)" }, 0.1);
"""
scenes.append((sid, 54, 6, scene(sid, 6, css, body, js)))

# ---------------------------------------------------------------- captions
CAPS = [
    (0.2, 2.0, "글 하나 자동으로 올리기"),
    (2.2, 4.667, "인스타는 글만 올릴 수 없다"),
    (5.0, 8.667, "코드보다 테스트가 먼저"),
    (9.667, 12.667, "같은 글이 두 번 올라갔다"),
    (14.0, 17.333, "20시는 어느 나라의 20시?"),
    (17.667, 20.667, "인스타는 바로 올리지 않는다"),
    (21.333, 24.0, "영원히 기다리는 코드"),
    (25.333, 28.0, "첫 응답은 거절이었다"),
    (28.167, 30.0, "코드는 됐는데, 계정이 막혔다"),
    (30.167, 32.0, "문서대로 했는데 메뉴가 없다"),
    (32.167, 34.0, "토큰은 커밋 전에 막는다"),
    (35.0, 38.0, "같은 서버가, 이번엔 대답했다"),
    (43.333, 48.0, "한 번에 올라갔다"),
    (48.333, 54.0, "이제 15분마다, 알아서"),
]
cap_css = SHARED_CSS + """
.capline { position:absolute; left:0; right:0; bottom:630px; display:flex; justify-content:center; z-index:50; }
.capline span { display:block; max-width:960px; padding:16px 36px 18px; background:var(--paper); border-radius:14px;
  font-weight:800; font-size:64px; line-height:1.2; letter-spacing:-0.02em; text-align:center; word-break:keep-all;
  box-shadow:0 10px 22px rgba(40,20,0,0.25); }
"""
cap_body, cap_js = "", ""
for i, (a, b, text) in enumerate(CAPS, 1):
    cid = f"cap{i:02d}"
    cap_body += f'    <div class="capline clip" id="{cid}" data-start="{a:.3f}" data-duration="{b-a:.3f}"><span id="{cid}-t">{text}</span></div>\n'
    cap_js += f'    tl.fromTo("#{cid}-t", {{ opacity: 0, filter: "blur(8px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.17, ease: "power2.out" }}, {a:.3f});\n'
    cap_js += f'    tl.to("#{cid}-t", {{ opacity: 0, filter: "blur(8px)", duration: 0.1, ease: "power2.in" }}, {b-0.12:.3f});\n'
captions = f"""<template>
  <style>{cap_css}
  </style>
  <div id="root" data-composition-id="captions" data-width="{W}" data-height="{H}">
{cap_body}  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{cap_js}    window.__timelines["captions"] = tl;
  </script>
</template>
"""

# ---------------------------------------------------------------- sound cues: (file, picture time, media start, dur, peak rel. media start, volume, rate)
F = 1 / FPS
CUES = [
    ("thud", 0.45, 0, 0.38, 0.004, 0.9, 1),
    ("printer", 4.667 + 0.35, 0.3, 0.8, 0.0, 0.5, 1),
    ("pop", 4.667 + 2.2, 0, 0.45, 0.105, 0.7, 1),
    ("printer", 4.667 + 3.2, 1.6, 0.7, 0.0, 0.5, 1),
    ("whoosh", 8.667 + 0.45, 0, 1.2, 0.649, 0.45, 1),
    ("stamp", 8.667 + 1.0, 0, 1.0, 0.318, 0.9, 1),
    ("thud", 12.667 + 0.8, 0, 0.38, 0.004, 0.8, 1),
    ("printer", 12.667 + 1.1, 0.3, 0.8, 0.0, 0.5, 1),
    ("box", 17.333 + 1.15, 3.5, 0.35, 0.147, 0.9, 1),
    ("tick", 17.333 + 3.4, 0, 2.6, 0.033, 0.7, 1.6),
    ("box", 17.333 + 6.0, 0, 0.6, 0.07, 0.6, 1),
    ("door", 24 + 0.8, 0, 1.6, 0.453, 0.9, 1),
    ("thud", 24 + 0.82, 0, 0.38, 0.004, 0.7, 1),
    ("thud", 28 + 0.35, 0, 0.38, 0.004, 0.9, 0.8),
    ("thud", 28 + 2.35, 0, 0.38, 0.004, 0.8, 0.9),
    ("latch", 28 + 5.05, 0, 0.3, 0.034, 0.9, 1),
    ("door", 34 + 0.8, 0, 1.6, 0.453, 0.6, 1.1),
    ("whoosh", 34 + 1.1, 0, 1.2, 0.649, 0.35, 1.15),
    ("door", 38 + 0.75, 0, 1.2, 0.453, 0.6, 1),
    ("printer", 38 + 0.85, 0.3, 0.8, 0.0, 0.5, 1),
    ("pop", 40.0, 0, 0.45, 0.105, 0.9, 0.8),
    ("tick", 48 + 1.9, 0, 0.3, 0.033, 0.7, 1),
    ("tick", 48 + 3.1, 0, 0.3, 0.033, 0.7, 1),
    ("tick", 48 + 4.3, 0, 0.3, 0.033, 0.7, 1),
    ("tick", 48 + 5.5, 0, 0.3, 0.033, 0.7, 1),
    ("thud", 54 + 0.55, 0, 0.38, 0.004, 0.9, 1),
]
EXT = {"stamp": "wav"}
audio_html = ""
for i, (name, pic, ms, dur, peak, vol, rate) in enumerate(CUES, 1):
    start = max(0.0, pic + F - peak / rate)
    rate_attr = f' data-playback-rate="{rate}"' if rate != 1 else ""
    audio_html += (f'      <audio id="sfx{i:02d}-{name}" src="assets/audio/{name}.{EXT.get(name, "mp3")}" data-start="{start:.3f}" '
                   f'data-duration="{dur}" data-media-start="{ms}" data-volume="{vol}"{rate_attr} data-track-index="{20 + i % 3}"></audio>\n')

# ---------------------------------------------------------------- root
BOUNDS = [s[1] for s in scenes[1:]]
hosts = ""
for i, (sid, start, dur, _) in enumerate(scenes):
    hosts += (f'      <div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-start="{start:.3f}" '
              f'data-duration="{dur:.3f}" data-track-index="1" data-track-kind="graphics" data-width="{W}" data-height="{H}" style="z-index:10;"></div>\n')
desk_js = ""
for k, b in enumerate(BOUNDS, 1):
    desk_js += f'      tl.to("#desk", {{ backgroundPositionY: "{-540*k}px", duration: 0.55, ease: "power2.inOut" }}, {max(0, b-0.1):.3f});\n'

WOOD = ("repeating-linear-gradient(180deg, transparent 0 536px, rgba(110,69,34,0.45) 536px 540px), "
        "repeating-linear-gradient(180deg, rgba(142,94,47,0.18) 0 3px, transparent 3px 11px, rgba(142,94,47,0.12) 11px 12px, transparent 12px 27px)")
index = f"""<!doctype html>
<html lang="ko" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      :root {{
        --ground: #A9743E;
        --ink: #1E1A15;
        --paper: #FBFAF6;
        --red: #D2362B;
        --pink: #E1306C;
        --green: #2E8B57;
      }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: {W}px; height: {H}px; overflow: hidden; background: var(--ground); }}
      #root {{ position: relative; width: 100%; height: 100%; }}
      #desk {{ position: absolute; inset: 0; background-color: var(--ground); background-image: {WOOD}; background-position: 0 0; }}
      #grain {{ position: absolute; inset: 0; background-image: url("{NOISE}"); opacity: 0.03; z-index: 90; pointer-events: none; }}
      #vignette {{ position: absolute; inset: 0; background: radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 60%, rgba(40,20,0,0.08) 100%);
        z-index: 91; pointer-events: none; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="60" data-width="{W}" data-height="{H}">
      <div id="desk"></div>
{hosts}      <div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0"
        data-duration="60" data-track-index="2" data-track-kind="captions" data-width="{W}" data-height="{H}" style="z-index:50;"></div>
      <div id="grain"></div>
      <div id="vignette"></div>
{audio_html}    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
{desk_js}      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""

(OUT / "compositions").mkdir(exist_ok=True)
for sid, _, _, html in scenes:
    (OUT / "compositions" / f"{sid}.html").write_text(html, encoding="utf-8")
(OUT / "compositions" / "captions.html").write_text(captions, encoding="utf-8")
(OUT / "index.html").write_text(index, encoding="utf-8")
print("wrote", len(scenes), "scenes")
