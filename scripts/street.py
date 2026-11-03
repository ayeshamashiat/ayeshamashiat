#!/usr/bin/env python3
"""
Draws assets/street.svg: a Dhaka street at night during load shedding.

One building per night for the last six weeks, Dhaka style: shops on the ground floor, flats
above. A night I committed has its lights on: its shopfront open, and the busier the day, the
more flats lit. A night I didn't is a blackout, shutter down. Release nights get fireworks.

The shops run along the street under Bangla signboards, each sign spanning a few buildings the
way real ones do; a sign is lit if any shop under it is open. The cha stall is one of them and
never closes, because it runs on a hurricane lantern. Around them: crows on the wires, laundry
on the roofs, a mosque behind, and a rickshaw with a painted hood.

Called by activity.py; nothing here touches the network. Standard library only.
"""
import datetime as dt
import hashlib
import html
import math

from sections import AMBER, CARD, EDGE, MONO, MUTED, SANS, TEXT

W, H = 880, 356
NIGHTS = 42
BW, GAP = 17, 3                  # building width, gap between buildings
BASE = 276                       # where buildings meet the street
FLOOR = 14                       # a floor of flats
GF = 36                          # the ground floor: signboard on top, shopfront below
SIGN_H = 14
FRONT = 20                       # shopfront (or shutter) height
BANGLA = "'Noto Sans Bengali', 'Hind Siliguri', 'Nirmala UI', 'Bangla Sangam MN', 'Bangla MN', sans-serif"

# Left to right along the street: (Bangla sign, English name for the alt text, buildings it
# spans, board colour, letter colour). The spans must add up to NIGHTS, and roughly follow the
# length of each name so no sign gets squashed. "cha" marks the stall.
SHOPS = [
    ("আল্লাহর দান বিরিয়ানি হাউস", "Allah'r Daan Biryani House", 6, "#1f6b45", "#ffe7a0"),
    ("মামার চা স্টল", "Mamar Cha Stall", 4, "#2a1d12", "#f0b44c", "cha"),
    ("ভাই ভাই ফার্মেসী", "Bhai Bhai Pharmacy", 4, "#eef0e8", "#1d6b3f"),
    ("প্রিয় লাইব্রেরি এন্ড স্টেশনারি", "Priyo Library & Stationery", 6, "#a8321f", "#ffe08a"),
    ("বিসমিল্লাহ অটো রিপেয়ার্স", "Bismillah Auto Repairs", 6, "#23508f", "#ffffff"),
    ("মায়ের দোয়া স্টোর", "Mayer Doa Store", 4, "#b8336a", "#fff1f6"),
    ("মদিনা সুইটস", "Madina Sweets", 3, "#d0682a", "#fff6e0"),
    ("আব্বাস অটো রিপেয়ার", "Abbas Auto Repair", 5, "#d9a521", "#3a1a0a"),
    ("নিউ মডার্ন টেইলার্স", "New Modern Tailors", 4, "#1e3a6e", "#cfe6ff"),
]
WIRES = [(18, 40), (27, 34), (11, 54)]  # (height at the poles, sag in the middle)
WARM = ["#f6c56b", "#f0b44c", "#ffd98a", "#f3b95f"]
DARK_WINDOW = "#141821"
CLOTH = ["#b4442a", "#b8336a", "#2f7d4f", "#3456a8", "#c08a1e", "#7a4fa3"]  # sarees, lungis, gamchas


def _h(*parts):
    """Stable number in [0, 1) from any inputs, so a night always looks the same."""
    return int(hashlib.md5("|".join(map(str, parts)).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def wire_y(x, y0, sag):
    """Height of a wire at x: the quadratic drawn in sky() dips by `sag` in the middle."""
    t = x / W
    return y0 + 4 * t * (1 - t) * sag


def levels(counts):
    """0 for a blackout, else 1-4 by quartile of the non-zero nights shown."""
    nz = sorted(c for c in counts if c > 0)
    if not nz:
        return lambda c: 0
    q = [nz[min(len(nz) - 1, int(len(nz) * f))] for f in (0.25, 0.5, 0.75)]
    return lambda c: 0 if c <= 0 else 1 if c <= q[0] else 2 if c <= q[1] else 3 if c <= q[2] else 4


def longest_run(counts):
    best = cur = 0
    for c in counts:
        cur = cur + 1 if c > 0 else 0
        best = max(best, cur)
    return best


def building(x, d, n, level, released, cha=False):
    floors = 3 + int(_h(d, "floors") * 5)                    # 3-7 floors of flats over the shops
    top = BASE - GF - floors * FLOOR - 6
    shade = ["#1a1f28", "#1d222b", "#181c24", "#1f2530"][int(_h(d, "shade") * 4)]
    o = []
    if level:  # warm spill on the street and a soft halo behind
        o.append(f'<ellipse cx="{x + BW / 2:.1f}" cy="{BASE + 4}" rx="{BW * 1.1:.1f}" ry="7" fill="{AMBER}" '
                 f'fill-opacity="{0.05 + 0.05 * level:.2f}"/>')
        o.append(f'<rect x="{x - 2}" y="{top - 2}" width="{BW + 4}" height="{BASE - top + 2}" rx="3" '
                 f'fill="{AMBER}" fill-opacity="{0.02 + 0.025 * level:.3f}" filter="url(#halo)"/>')
    o.append(f'<rect x="{x}" y="{top}" width="{BW}" height="{BASE - top}" fill="{shade}"/>')
    o.append(f'<rect x="{x}" y="{top}" width="{BW}" height="2" fill="#262c37"/>')
    roof = _h(d, "roof")
    if roof < 0.35:    # water tank
        o.append(f'<rect x="{x + 4}" y="{top - 6}" width="7" height="6" rx="1" fill="{shade}" stroke="#262c37" stroke-width=".6"/>')
    elif roof < 0.55:  # antenna
        o.append(f'<path d="M{x + 12} {top} V{top - 9} M{x + 9} {top - 6} H{x + 15}" stroke="#2b313c" stroke-width=".8"/>')
    elif roof < 0.75:  # washing out on the roof
        o.append(f'<path d="M{x + 1} {top} V{top - 7} M{x + BW - 1} {top} V{top - 7} M{x + 1} {top - 6} H{x + BW - 1}" '
                 f'stroke="#2b313c" stroke-width=".6"/>')
        for k in range(1 + int(_h(d, "cloth") * 3)):
            o.append(f'<rect x="{x + 2 + k * 4}" y="{top - 6}" width="3" height="{3 + int(_h(d, "len", k) * 3)}" '
                     f'fill="{CLOTH[int(_h(d, "col", k) * len(CLOTH))]}" fill-opacity=".7"/>')

    if not cha:  # the stall draws its own front
        o.append(shopfront(x, level))
    windows = [(x + 3 + c * 6, BASE - GF - (f + 1) * FLOOR + 3) for f in range(floors) for c in range(2)]
    lit = math.ceil(len(windows) * level / 4)
    order = sorted(range(len(windows)), key=lambda i: _h(d, "w", i))
    on = set(order[:lit])
    flicker = order[0] if level and _h(d, "flicker") < 0.25 else None  # the one tube light that won't settle
    for i, (wx, wy) in enumerate(windows):
        if i in on:
            cls = ' class="tube"' if i == flicker else ""
            o.append(f'<rect{cls} x="{wx}" y="{wy}" width="5" height="6" fill="{WARM[int(_h(d, "c", i) * 4)]}"/>')
        else:
            o.append(f'<rect x="{wx}" y="{wy}" width="5" height="6" fill="{DARK_WINDOW}"/>')
    tip = (f"{d.strftime('%a %d %b')}: {n} commit{'s' if n != 1 else ''}" if n else f"{d.strftime('%a %d %b')}: load shedding") \
        + (" · release night" if released else "")
    o.append(f'<rect x="{x}" y="{top - 10}" width="{BW}" height="{BASE - top + 10}" fill="transparent"><title>{tip}</title></rect>')
    if released:
        o.append(firework(x + BW / 2, top - 26, d))
    return "".join(o)


def shopfront(x, level):
    """One building's shop: open and lit on a night with commits, shutter down in a blackout."""
    y = BASE - FRONT
    if level:
        return (f'<rect x="{x + 2}" y="{y}" width="{BW - 4}" height="{FRONT}" fill="#e0a552" fill-opacity=".6"/>'
                f'<rect x="{x + 3}" y="{y + 6}" width="{BW - 6}" height="1.3" fill="#7a4a1c" fill-opacity=".8"/>'
                f'<rect x="{x + 3}" y="{y + 12}" width="{BW - 6}" height="1.3" fill="#7a4a1c" fill-opacity=".8"/>'
                f'<circle cx="{x + BW / 2:.1f}" cy="{y + 2.5}" r="1" fill="#fff3c4"/>')
    return (f'<rect x="{x + 2}" y="{y}" width="{BW - 4}" height="{FRONT}" fill="#252a32"/>'
            + "".join(f'<line x1="{x + 2}" y1="{y + 2 + k * 2.5}" x2="{x + BW - 2}" y2="{y + 2 + k * 2.5}" '
                      f'stroke="#1b1f26" stroke-width=".7"/>' for k in range(7)))


def signboard(x, w, bangla, bg, fg, lit, size=10):
    """A Bangla signboard over a few shopfronts. textLength keeps it inside the board whatever
    Bangla font the viewer has."""
    y = BASE - GF + 1
    glow = ' filter="url(#neon)"' if lit else ""
    return (f'<g opacity="{1 if lit else 0.32}">'
            f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{SIGN_H}" rx="1.5" fill="{bg}" '
            f'stroke="#000" stroke-opacity=".35" stroke-width=".6"{glow}/>'
            f'<text x="{x + w / 2:.1f}" y="{y + 7 + size * 0.36:.1f}" font-size="{size}" font-weight="700" fill="{fg}" text-anchor="middle" '
            f'font-family="{BANGLA}" textLength="{w - 8:.1f}" lengthAdjust="spacingAndGlyphs">{html.escape(bangla)}</text></g>')


def firework(cx, cy, d):
    rays = []
    for k in range(10):
        a = 2 * math.pi * k / 10 + _h(d, "fw")
        r1, r2 = 4, 13 + 3 * _h(d, "fw", k)
        rays.append(f'M{cx + r1 * math.cos(a):.1f} {cy + r1 * math.sin(a):.1f} '
                    f'L{cx + r2 * math.cos(a):.1f} {cy + r2 * math.sin(a):.1f}')
    return (f'<g class="burst" style="transform-origin:{cx:.1f}px {cy:.1f}px">'
            f'<path d="{" ".join(rays)}" stroke="#ff8fb3" stroke-width="1.3" stroke-linecap="round"/>'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="2" fill="#ffe3a3"/></g>')


def sky():
    o = []
    for k in range(46):
        x, y = _h("star", k) * W, 8 + _h("star-y", k) * 150
        r = 0.5 + _h("star-r", k) * 0.8
        o.append(f'<circle class="star" cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="#cfd6e4" '
                 f'style="animation-delay:{-_h("star-d", k) * 5:.1f}s"/>')
    o.append('<circle cx="822" cy="44" r="15" fill="#efe3c2"/><circle cx="830" cy="39" r="14" fill="url(#sky)"/>')
    for y0, sag in WIRES:
        o.append(f'<path d="M0 {y0} Q{W / 2} {y0 + 2 * sag} {W} {y0}" fill="none" stroke="#2b3039" stroke-width="1.1"/>')
    for k in range(5):  # the tangle every Dhaka pole has
        cx = 560 + k * 5
        o.append(f'<ellipse cx="{cx}" cy="{wire_y(cx, 18, 40) + 3:.1f}" rx="{6 + k}" ry="{3 + k / 2:.1f}" fill="none" '
                 f'stroke="#2b3039" stroke-width=".9"/>')
    return "".join(o)


def rickshaw(x):
    """Small enough to stay on the road, so it never covers anyone's ground floor."""
    y = BASE + 17
    steel = 'fill="none" stroke="#4a505b" stroke-width="1"'
    return (f'<g><circle cx="{x}" cy="{y}" r="4" {steel}/><circle cx="{x + 20}" cy="{y}" r="4" {steel}/>'
            f'<circle cx="{x + 34}" cy="{y}" r="3.5" {steel}/>'
            f'<path d="M{x} {y} L{x + 8} {y - 7} H{x + 20} V{y} M{x + 20} {y - 4} L{x + 34} {y} M{x + 31} {y - 9} L{x + 34} {y}" {steel}/>'
            # the painted hood: red, with a band of rickshaw-art colours
            f'<path d="M{x + 7} {y - 7} Q{x + 6} {y - 16} {x + 14} {y - 16} Q{x + 21} {y - 15} {x + 20} {y - 7} Z" fill="#a8321f"/>'
            f'<path d="M{x + 8} {y - 11} H{x + 20}" stroke="#f0b44c" stroke-width="1.2" stroke-dasharray="2 1.5"/>'
            f'<circle cx="{x + 12}" cy="{y - 14}" r=".9" fill="#5fc28a"/><circle cx="{x + 16}" cy="{y - 14}" r=".9" fill="#ff8fb3"/>'
            f'<rect x="{x + 18}" y="{y - 5}" width="3" height="3" fill="#3f8fd8"/></g>')


def mosque(cx):
    """A silhouette behind the buildings, rim-lit by the moon, so the dome and minarets show
    over the short ones."""
    dark, rim = "#0b0e13", 'stroke="#2c3340" stroke-width=".8"'
    o = [f'<rect x="{cx - 26}" y="160" width="52" height="{BASE - 160}" fill="{dark}" {rim}/>',
         f'<path d="M{cx - 22} 162 Q{cx - 22} 132 {cx} 124 Q{cx + 22} 132 {cx + 22} 162 Z" fill="{dark}" {rim}/>',
         f'<line x1="{cx}" y1="124" x2="{cx}" y2="115" stroke="#2c3340" stroke-width="1"/>',
         f'<circle cx="{cx + 0.5}" cy="111" r="3.4" fill="#e6d6a8" fill-opacity=".75"/>'
         f'<circle cx="{cx + 2.2}" cy="110.2" r="3" fill="#10141b"/>']
    for mx in (cx - 36, cx + 36):
        o.append(f'<rect x="{mx - 3}" y="104" width="6" height="{BASE - 104}" fill="{dark}" {rim}/>'
                 f'<rect x="{mx - 4.5}" y="124" width="9" height="2.5" fill="{dark}" {rim}/>'
                 f'<path d="M{mx - 3} 104 L{mx} 90 L{mx + 3} 104 Z" fill="{dark}" {rim}/>'
                 f'<rect x="{mx - 1}" y="112" width="2" height="4" rx="1" fill="#2c3340"/>')
    return "".join(o)


def crows(day):
    """A few crows on the middle wire, where the sign doesn't hang."""
    y0, sag = WIRES[1]
    o = []
    for k, x in enumerate([560 + 70 * _h(day, "crow", 0), 600 + 40 * _h(day, "crow", 1), 730 + 30 * _h(day, "crow", 2)]):
        y = wire_y(x, y0, sag) - 0.5  # sitting right on the wire
        f = -1 if k == 1 else 1
        o.append(f'<g transform="translate({x:.1f} {y:.1f}) scale({1.5 * f} 1.5)" fill="#05070a">'
                 f'<ellipse cx="0" cy="-3" rx="3.4" ry="2.3"/><circle cx="3" cy="-5" r="1.7"/>'
                 f'<path d="M4.4 -5.4 L6.6 -4.8 L4.4 -4.3 Z M-3 -3 L-6.5 -1.2 L-2.6 -2 Z"/></g>')
    return "".join(o)


def cha_stall(xs, w):
    """মামার চা স্টল: a tin awning under its sign, a counter, biscuit jars, a kettle on a clay
    chula, and a hurricane lantern, so it stays open through any load shedding."""
    xe, y = xs + w, BASE - FRONT
    o = [f'<rect x="{xs + 2}" y="{y}" width="{w - 4}" height="{FRONT}" fill="#17140f"/>']
    n = int((w + 4) // 9)
    for k in range(n):                                                                    # striped tin awning
        x = xs - 2 + k * (w + 4) / n
        c = "#7d2a1d" if k % 2 else "#1f4e37"
        o.append(f'<path d="M{x:.1f} {y - 2} H{x + (w + 4) / n:.1f} L{x + (w + 4) / n + 1:.1f} {y + 3} H{x + 1:.1f} Z" fill="{c}"/>'
                 f'<circle cx="{x + (w + 4) / n / 2 + 1:.1f}" cy="{y + 3}" r="{(w + 4) / n / 2:.1f}" fill="{c}"/>')
    lx = xe - 10                                                                          # the lantern
    o.append(f'<circle cx="{lx}" cy="{y + 10}" r="22" fill="#f0b44c" fill-opacity=".12" filter="url(#halo)"/>'
             f'<line x1="{lx}" y1="{y + 4}" x2="{lx}" y2="{y + 6}" stroke="#5b4a33" stroke-width=".8"/>'
             f'<path d="M{lx - 3} {y + 6} H{lx + 3} L{lx + 2} {y + 7.5} H{lx - 2} Z" fill="#5b4a33"/>'
             f'<ellipse class="lantern" cx="{lx}" cy="{y + 11}" rx="3" ry="3.8" fill="#ffd27a"/>'
             f'<path d="M{lx - 3} {y + 14.5} H{lx + 3} L{lx + 2} {y + 16} H{lx - 2} Z" fill="#5b4a33"/>')
    o.append(f'<rect x="{xs + 2}" y="{BASE - 6}" width="{w - 4}" height="6" fill="#2a1d12"/>')    # counter
    for k, lid in enumerate(["#c0392b", "#2f7d4f", "#c08a1e"]):                           # biscuit jars
        x = xs + 6 + k * 9
        o.append(f'<rect x="{x}" y="{BASE - 13}" width="7" height="7" rx="1.5" fill="#9fb3c8" fill-opacity=".22" '
                 f'stroke="#9fb3c8" stroke-opacity=".35" stroke-width=".5"/>'
                 f'<rect x="{x + 1}" y="{BASE - 14.5}" width="5" height="2" rx="1" fill="{lid}"/>'
                 f'<rect x="{x + 1.5}" y="{BASE - 10.5}" width="4" height="3.5" rx="1" fill="#d9a35b" fill-opacity=".6"/>')
    kx = xs + 46                                                                          # chula and kettle
    o.append(f'<rect x="{kx - 7}" y="{BASE - 9}" width="15" height="3" rx="1" fill="#4a2c1c"/>'
             f'<rect x="{kx - 5}" y="{BASE - 8.3}" width="11" height="1.6" rx=".8" fill="#ff7a2f" class="ember"/>'
             f'<ellipse cx="{kx}" cy="{BASE - 12}" rx="5" ry="3.3" fill="#79808c"/>'
             f'<path d="M{kx + 4.5} {BASE - 13} L{kx + 8} {BASE - 15.5}" stroke="#79808c" stroke-width="1.4" stroke-linecap="round"/>'
             f'<path d="M{kx - 3.5} {BASE - 14} Q{kx} {BASE - 18} {kx + 3.5} {BASE - 14}" fill="none" stroke="#5c626d" stroke-width=".9"/>')
    for k, dx in enumerate((0, 3)):                                                       # steam
        o.append(f'<path class="steam" style="animation-delay:{-k * 1.3}s" d="M{kx + 8 + dx} {BASE - 16} q-2 -2 0 -4" '
                 f'fill="none" stroke="#cfd6e4" stroke-opacity=".55" stroke-width=".8" stroke-linecap="round"/>')
    o.append(f'<rect x="{xs + 6}" y="{BASE + 6}" width="40" height="2.5" rx="1" fill="#4a3420"/>'   # bench
             f'<line x1="{xs + 9}" y1="{BASE + 8.5}" x2="{xs + 9}" y2="{BASE + 14}" stroke="#4a3420" stroke-width="1.8"/>'
             f'<line x1="{xs + 43}" y1="{BASE + 8.5}" x2="{xs + 43}" y2="{BASE + 14}" stroke="#4a3420" stroke-width="1.8"/>')
    dx = xs + 66                                                                          # a dog, asleep
    o.append(f'<ellipse cx="{dx}" cy="{BASE + 15}" rx="7" ry="3.2" fill="#4b4036"/>'
             f'<circle cx="{dx + 6}" cy="{BASE + 13}" r="2.5" fill="#4b4036"/>'
             f'<path d="M{dx + 6.5} {BASE + 10.8} L{dx + 8.3} {BASE + 9.5} L{dx + 7.8} {BASE + 12.2} Z" fill="#3a3129"/>'
             f'<path d="M{dx - 7} {BASE + 15} Q{dx - 10} {BASE + 13} {dx - 8} {BASE + 11}" fill="none" stroke="#4b4036" '
             f'stroke-width="1.3" stroke-linecap="round"/>')
    return "".join(o)


def draw(per_day, release_days, day):
    """Returns (svg, alt text) for the NIGHTS nights ending on `day`."""
    nights = [day - dt.timedelta(days=NIGHTS - 1 - k) for k in range(NIGHTS)]
    counts = [per_day.get(d, 0) for d in nights]
    lvl = levels(counts)
    x0 = (W - (NIGHTS * (BW + GAP) - GAP)) / 2
    col_x = lambda k: x0 + k * (BW + GAP)
    spans, k = [], 0
    for shop in SHOPS:
        spans.append((k, k + shop[2], shop))
        k += shop[2]
    assert k == NIGHTS, "shop spans must cover every building"
    cha_cols = {c for a, b, shop in spans if shop[5:] == ("cha",) for c in range(a, b)}

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="__ALT__">',
         f"""<style>
  .m {{ font-family: {MONO}; }} .s {{ font-family: {SANS}; }}
  .star {{ animation: twinkle 5s ease-in-out infinite; }}
  @keyframes twinkle {{ 50% {{ opacity: .25; }} }}
  .tube {{ animation: tube 7s steps(1) infinite; }}
  @keyframes tube {{ 0%, 88%, 92%, 96% {{ opacity: 1; }} 90%, 94% {{ opacity: .15; }} }}
  .steam {{ animation: steam 3s ease-out infinite; }}
  @keyframes steam {{ 0%, 100% {{ opacity: 1; transform: translateY(0); }} 45% {{ opacity: 0; transform: translateY(-4px); }} 46% {{ opacity: 0; transform: translateY(3px); }} }}
  .lantern, .ember {{ animation: lantern 2.6s ease-in-out infinite; }}
  @keyframes lantern {{ 50% {{ opacity: .78; }} }}
  .burst {{ animation: burst 3.2s ease-out infinite; }}
  @keyframes burst {{ 0%, 55% {{ opacity: 1; transform: scale(1); }} 75% {{ opacity: 0; transform: scale(1.15); }} 76% {{ opacity: 0; transform: scale(.3); }} 92%, 100% {{ opacity: 1; transform: scale(1); }} }}
  @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
</style>""",
         '<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
         '<stop offset="0" stop-color="#0a0d13"/><stop offset="1" stop-color="#161b26"/></linearGradient>'
         '<filter id="halo" x="-50%" y="-20%" width="200%" height="140%"><feGaussianBlur stdDeviation="4"/></filter>'
         '<filter id="neon" x="-10%" y="-30%" width="120%" height="160%"><feDropShadow dx="0" dy="0" stdDeviation="3" '
         f'flood-color="{AMBER}" flood-opacity=".35"/></filter>'
         f'<clipPath id="frame"><rect width="{W}" height="{H}" rx="14"/></clipPath></defs>',
         '<g clip-path="url(#frame)">',
         f'<rect width="{W}" height="{BASE}" fill="url(#sky)"/>',
         f'<rect y="{BASE}" width="{W}" height="{H - BASE}" fill="{CARD}"/>',
         sky(), mosque(640)]

    for k, (d, n) in enumerate(zip(nights, counts)):
        o.append(building(col_x(k), d, n, lvl(n), d in release_days, cha=k in cha_cols))
    for a, b, (bangla, _, _, bg, fg, *kind) in spans:
        xs, w = col_x(a), (b - a) * (BW + GAP) - GAP
        if kind:
            o.append(cha_stall(xs, w))
        o.append(signboard(xs, w, bangla, bg, fg, lit=bool(kind) or any(counts[c] for c in range(a, b)),
                           size=12 if kind else 10))  # the stall's name is short; bigger letters fill its board

    # the street
    o.append(f'<rect y="{BASE}" width="{W}" height="22" fill="#0c0f14"/>')
    o.append(f'<line x1="0" y1="{BASE + 11}" x2="{W}" y2="{BASE + 11}" stroke="#2a2f38" stroke-dasharray="10 12"/>')
    stall = next((col_x(a) - 50, col_x(b) + 10) for a, b, shop in spans if shop[5:] == ("cha",))
    spots = [x for x in range(30, W - 60, 10) if not stall[0] < x < stall[1]]  # not over the bench and the dog
    o.append(rickshaw(spots[int(_h(day, "rickshaw") * len(spots))]))
    o.append(crows(day))

    for k in range(NIGHTS - 1, -1, -7):  # a date under every seventh night, counting back from yesterday
        x = col_x(k) + BW / 2
        label = "yesterday" if k == NIGHTS - 1 else nights[k].strftime("%b %-d")
        o.append(f'<text class="m" x="{x:.0f}" y="{BASE + 38}" font-size="9.5" fill="{MUTED}" text-anchor="middle">{label}</text>')

    on = sum(c > 0 for c in counts)
    run = longest_run(counts)
    shipped = sum(d in release_days for d in nights)
    busiest = max(zip(counts, nights)) if on else None
    stats = (f'lights on <tspan fill="{TEXT}">{on}</tspan> of {NIGHTS} nights  ·  '
             f'longest run <tspan fill="{TEXT}">{run}</tspan>')
    if busiest:
        stats += f'  ·  brightest <tspan fill="{TEXT}">{busiest[1].strftime("%b %-d")}</tspan> ({busiest[0]})'
    o.append(f'<text class="m" x="24" y="{H - 18}" font-size="10.5" fill="{MUTED}" xml:space="preserve">{stats}</text>')
    lx = W - 24
    legend = [("fireworks: a release", "#ff8fb3"), ("lit: commits", WARM[0]), ("dark: load shedding", DARK_WINDOW)]
    for text, color in legend:
        tw = len(text) * 6.2
        o.append(f'<text class="m" x="{lx:.0f}" y="{H - 18}" font-size="9.5" fill="{MUTED}" text-anchor="end">{text}</text>')
        o.append(f'<rect x="{lx - tw - 12:.0f}" y="{H - 26}" width="6" height="8" fill="{color}" stroke="#2b313c" stroke-width=".5"/>')
        lx -= tw + 26
    o.append("</g>")
    o.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="{EDGE}"/>')
    o.append("</svg>")

    alt = (f"Load-shedding street: one building for each of the last {NIGHTS} nights in Dhaka. "
           f"Lit windows mean I committed that day; dark buildings mean I didn't. "
           f"Lights on {on} of {NIGHTS} nights, longest run {run}"
           + (f", brightest night {busiest[1].strftime('%d %b')} with {busiest[0]} commits" if busiest else "")
           + (f", {shipped} release night{'s' if shipped != 1 else ''} with fireworks" if shipped else "")
           + ". Every building has a shop on the ground floor and flats above; in a blackout the shutter is down. "
           "The shops have Bangla signboards: " + ", ".join(shop[1] for shop in SHOPS) + ". "
           "The cha stall never closes; it runs on a hurricane lantern. Also: crows on the electric wires, "
           "laundry drying on the roofs, a mosque behind, and a rickshaw with a painted hood.")
    return "\n".join(o).replace("__ALT__", html.escape(alt)), alt
