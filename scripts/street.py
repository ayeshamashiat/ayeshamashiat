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
# length of each name so no sign gets squashed. The last field picks the shop's character:
# what you see inside when it's open, and what it leaves out on the pavement.
SHOPS = [
    ("আল্লাহর দান বিরিয়ানি হাউস", "Allah'r Daan Biryani House", 6, "#1f6b45", "#ffe7a0", "biryani"),
    ("মামার চা স্টল", "Mamar Cha Stall", 4, "#2a1d12", "#f0b44c", "cha"),
    ("ভাই ভাই ফার্মেসী", "Bhai Bhai Pharmacy", 4, "#eef0e8", "#1d6b3f", "pharmacy"),
    ("প্রিয় লাইব্রেরি এন্ড স্টেশনারি", "Priyo Library & Stationery", 6, "#a8321f", "#ffe08a", "library"),
    ("বিসমিল্লাহ অটো রিপেয়ার্স", "Bismillah Auto Repairs", 6, "#23508f", "#ffffff", "garage"),
    ("মায়ের দোয়া স্টোর", "Mayer Doa Store", 4, "#b8336a", "#fff1f6", "store"),
    ("মদিনা সুইটস", "Madina Sweets", 3, "#d0682a", "#fff6e0", "sweets"),
    ("আব্বাস অটো রিপেয়ার", "Abbas Auto Repair", 5, "#d9a521", "#3a1a0a", "cng"),
    ("নিউ মডার্ন টেইলার্স", "New Modern Tailors", 4, "#1e3a6e", "#cfe6ff", "tailor"),
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


def building(x, d, n, level, released, kind="store", slot=0):
    floors = 3 + int(_h(d, "floors") * 5)                    # 3-7 floors of flats over the shops
    top = BASE - GF - floors * FLOOR - 6
    shade = ["#1a1f28", "#1d222b", "#181c24", "#1f2530"][int(_h(d, "shade") * 4)]
    o = []
    if level:  # warm spill on the street and a soft halo behind
        o.append(f'<ellipse cx="{x + BW / 2:.1f}" cy="{BASE + 2}" rx="{BW * 0.8:.1f}" ry="3" fill="{AMBER}" '
                 f'fill-opacity="{0.04 + 0.03 * level:.2f}" filter="url(#halo)"/>')
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

    if kind != "cha":  # the stall draws its own front
        o.append(shopfront(x, level, kind, slot))
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


def shopfront(x, level, kind="store", slot=0):
    """One building's shop. Open on a night with commits, and every kind of shop looks like
    itself inside; shutter down in a blackout, whatever it sells. `slot` is which of the shop's
    fronts this is, so a long shop doesn't repeat itself."""
    y, ix, iw = BASE - FRONT, x + 2, BW - 4
    if not level:
        return (f'<rect x="{ix}" y="{y}" width="{iw}" height="{FRONT}" fill="#252a32"/>'
                + "".join(f'<line x1="{ix}" y1="{y + 2 + k * 2.5}" x2="{ix + iw}" y2="{y + 2 + k * 2.5}" '
                          f'stroke="#1b1f26" stroke-width=".7"/>' for k in range(7)))
    light, glow = INSIDE.get(kind, ("#e0a552", ".6"))
    o = [f'<rect x="{ix}" y="{y}" width="{iw}" height="{FRONT}" fill="{light}" fill-opacity="{glow}"/>',
         f'<circle cx="{x + BW / 2:.1f}" cy="{y + 2}" r="1" fill="#fff3c4"/>']
    cx = x + BW / 2
    if kind == "biryani":            # a big deg on the counter, and diners
        if slot % 2 == 0:
            o.append(f'<path d="M{cx - 5} {BASE - 9} Q{cx - 6} {BASE - 2} {cx} {BASE - 2} Q{cx + 6} {BASE - 2} {cx + 5} {BASE - 9} Z" fill="#9a6a33"/>'
                     f'<ellipse cx="{cx}" cy="{BASE - 9}" rx="5.5" ry="1.6" fill="#c08a4a"/>'
                     f'<rect x="{cx - 1}" y="{BASE - 11.5}" width="2" height="1.6" rx=".8" fill="#c08a4a"/>')
        else:
            o.append(f'<rect x="{ix + 1}" y="{BASE - 6}" width="{iw - 2}" height="1.4" fill="#8a2b2b"/>'   # a table, plates, a jug
                     f'<line x1="{ix + 2}" y1="{BASE - 4.6}" x2="{ix + 2}" y2="{BASE}" stroke="#5a3a1a"/>'
                     f'<line x1="{ix + iw - 2}" y1="{BASE - 4.6}" x2="{ix + iw - 2}" y2="{BASE}" stroke="#5a3a1a"/>'
                     f'<ellipse cx="{ix + 3.5}" cy="{BASE - 6.6}" rx="2.2" ry=".8" fill="#f2efe6"/>'
                     f'<ellipse cx="{ix + iw - 5}" cy="{BASE - 6.6}" rx="2.2" ry=".8" fill="#f2efe6"/>'
                     f'<rect x="{ix + iw - 2.6}" y="{BASE - 10}" width="1.8" height="3.4" rx=".6" fill="#9fb3c8"/>')
    elif kind == "pharmacy":         # cool tube light, shelves of little boxes
        for r in range(3):
            sy = y + 6 + r * 5
            o.append(f'<rect x="{ix + 1}" y="{sy}" width="{iw - 2}" height=".9" fill="#6f8a7c"/>')
            for b in range(3):
                o.append(f'<rect x="{ix + 1.5 + b * 3.6:.1f}" y="{sy - 2.4}" width="2.6" height="2.4" '
                         f'fill="{["#d64545", "#3a7bd5", "#f2c94c", "#2f9e6a", "#ffffff"][(r * 3 + b + slot) % 5]}"/>')
        if slot == 0:
            o.append(f'<rect x="{ix + iw - 5}" y="{y + 1}" width="5" height="5" fill="#1f9e5a"/>'
                     f'<path d="M{ix + iw - 2.5} {y + 1.8} V{y + 5.2} M{ix + iw - 4.2} {y + 3.5} H{ix + iw - 0.8}" stroke="#fff" stroke-width="1"/>')
    elif kind == "library":          # shelves of book spines
        for r in range(3):
            sy = y + 7 + r * 5.5
            o.append(f'<rect x="{ix + 1}" y="{sy}" width="{iw - 2}" height=".9" fill="#5a3a1a"/>')
            bx = ix + 1.3
            for b in range(5):
                h = 2.6 + 1.6 * _h(slot, r, b)
                o.append(f'<rect x="{bx:.1f}" y="{sy - h:.1f}" width="1.7" height="{h:.1f}" '
                         f'fill="{["#b4442a", "#3456a8", "#2f7d4f", "#c08a1e", "#7a4fa3", "#e8e2d0"][int(_h(slot, r, b, "c") * 6)]}"/>')
                bx += 2.1
    elif kind in ("garage", "cng"):  # a pegboard of tools and a tyre on the wall
        o.append(f'<circle cx="{ix + 4}" cy="{y + 7}" r="3" fill="none" stroke="#2a2a2a" stroke-width="1.6"/>'
                 f'<path d="M{ix + 8} {y + 4} V{y + 11} M{ix + 10.5} {y + 4} V{y + 10} M{ix + 7} {y + 4.5} H{ix + 9}" '
                 f'stroke="#4a4f57" stroke-width="1"/>'
                 f'<rect x="{ix + 1}" y="{BASE - 5}" width="{iw - 2}" height="5" fill="#3b3f46"/>'
                 f'<rect x="{ix + 2}" y="{BASE - 7}" width="3" height="2" fill="#c0392b"/>')
    elif kind == "store":            # chips packets hanging in strips, sacks below
        for c in range(3):
            for r in range(3):
                o.append(f'<rect x="{ix + 1 + c * 4}" y="{y + 1 + r * 3.4:.1f}" width="3" height="3" '
                         f'fill="{["#e63946", "#f4a261", "#2a9d8f", "#e9c46a", "#457b9d"][(c + r * 2 + slot) % 5]}"/>')
        o.append(f'<path d="M{ix + 1} {BASE} V{BASE - 5} Q{ix + 3.5} {BASE - 7} {ix + 6} {BASE - 5} V{BASE} Z" fill="#cdb48a"/>'
                 f'<path d="M{ix + 7} {BASE} V{BASE - 5} Q{ix + 9.5} {BASE - 7} {ix + 12} {BASE - 5} V{BASE} Z" fill="#b89a6a"/>')
    elif kind == "sweets":           # a glass case of rosogolla and kalojam
        o.append(f'<rect x="{ix + 0.5}" y="{BASE - 9}" width="{iw - 1}" height="9" fill="#cfe3ec" fill-opacity=".35" '
                 f'stroke="#e8f4f8" stroke-opacity=".6" stroke-width=".5"/>')
        for r in range(2):
            for c in range(4):
                o.append(f'<circle cx="{ix + 2 + c * 3:.1f}" cy="{BASE - 6.5 + r * 3.5}" r="1.2" '
                         f'fill="{"#fbf6ea" if (c + r) % 2 else "#5a2a14"}"/>')
    elif kind == "tailor":           # bolts of cloth, a mannequin, a sewing machine
        if slot % 2 == 0:
            for k in range(3):
                o.append(f'<rect x="{ix + 1 + k * 2.4:.1f}" y="{y + 3}" width="2" height="{FRONT - 4}" '
                         f'fill="{CLOTH[(k + slot) % len(CLOTH)]}"/>')
            o.append(f'<circle cx="{ix + iw - 3}" cy="{y + 5}" r="1.5" fill="#d9c7a8"/>'
                     f'<path d="M{ix + iw - 5.5} {y + 7} H{ix + iw - 0.5} L{ix + iw - 1.5} {y + 14} H{ix + iw - 4.5} Z" fill="#3456a8"/>'
                     f'<line x1="{ix + iw - 3}" y1="{y + 14}" x2="{ix + iw - 3}" y2="{BASE}" stroke="#3a2a1a"/>')
        else:
            o.append(f'<rect x="{ix + 1}" y="{BASE - 6}" width="{iw - 2}" height="1.3" fill="#5a3a1a"/>'
                     f'<path d="M{ix + 3} {BASE - 6} V{BASE - 11} H{ix + 9} V{BASE - 9.5} H{ix + 5} V{BASE - 6}" fill="#1f1f1f"/>'
                     f'<circle cx="{ix + 9.5}" cy="{BASE - 8}" r="1" fill="#b0b0b0"/>')
    return "".join(o)


# how each shop is lit inside: warm bulbs mostly, a tube light at the pharmacy
INSIDE = {"pharmacy": ("#e4f2ea", ".8"), "sweets": ("#f3c99a", ".7"), "garage": ("#c98c3e", ".5"),
          "cng": ("#c98c3e", ".5"), "library": ("#e7b665", ".6")}


def pavement(xs, w, kind, d):
    """What each shop leaves out on the pavement, lit or not."""
    y = BASE + 1
    if kind == "biryani":   # the deg on its own stove, steaming
        cx = xs + w - 18
        return (f'<rect x="{cx - 8}" y="{y + 6}" width="16" height="4" rx="1" fill="#4a2c1c"/>'
                f'<rect x="{cx - 6}" y="{y + 7}" width="12" height="1.6" fill="#ff7a2f" class="ember"/>'
                f'<path d="M{cx - 7} {y + 6} Q{cx - 8} {y - 2} {cx} {y - 2} Q{cx + 8} {y - 2} {cx + 7} {y + 6} Z" fill="#9a6a33"/>'
                f'<ellipse cx="{cx}" cy="{y - 1.5}" rx="7.5" ry="2" fill="#c08a4a"/>'
                + "".join(f'<path class="steam" style="animation-delay:{-k * 1.1}s" d="M{cx - 2 + k * 4} {y - 4} q-2 -2 0 -4" '
                          f'fill="none" stroke="#cfd6e4" stroke-opacity=".55" stroke-width=".8"/>' for k in range(2)))
    if kind == "pharmacy":  # a green cross on a stand
        cx = xs + w - 10
        return (f'<line x1="{cx}" y1="{y + 2}" x2="{cx}" y2="{y + 10}" stroke="#4a505b" stroke-width="1"/>'
                f'<rect x="{cx - 4.5}" y="{y - 7}" width="9" height="9" rx="1" fill="#1f9e5a" filter="url(#neon)"/>'
                f'<path d="M{cx} {y - 5.5} V{y + 0.5} M{cx - 3} {y - 2.5} H{cx + 3}" stroke="#fff" stroke-width="1.6"/>')
    if kind == "library":   # a newspaper rack
        x = xs + w - 20
        return (f'<rect x="{x}" y="{y}" width="14" height="10" fill="none" stroke="#5a5f68" stroke-width=".8"/>'
                + "".join(f'<rect x="{x + 1.5 + k * 4}" y="{y + 1 + (k % 2)}" width="3" height="6" fill="{c}"/>'
                          for k, c in enumerate(["#e8e2d0", "#b4442a", "#e8e2d0"])))
    if kind == "garage":    # a stack of tyres
        x = xs + w - 16
        return "".join(f'<ellipse cx="{x + 6}" cy="{y + 9 - k * 3.2:.1f}" rx="6" ry="2" fill="#1a1a1a" stroke="#4a4f57" stroke-width=".8"/>'
                       for k in range(3))
    if kind == "store":     # rice and dal in open sacks
        x = xs + w - 26
        return "".join(f'<path d="M{x + k * 9} {y + 10} V{y + 3} Q{x + k * 9 + 4} {y + 1} {x + k * 9 + 8} {y + 3} V{y + 10} Z" fill="#cdb48a"/>'
                       f'<ellipse cx="{x + k * 9 + 4}" cy="{y + 3}" rx="4" ry="1.3" fill="{c}"/>'
                       for k, c in enumerate(["#f4efe2", "#e2a93b", "#c47a3a"]))
    if kind == "sweets":    # clay pots of mishti doi
        x = xs + w - 18
        return "".join(f'<path d="M{x + k * 6} {y + 4} Q{x + k * 6} {y + 10} {x + k * 6 + 2.5} {y + 10} '
                       f'Q{x + k * 6 + 5} {y + 10} {x + k * 6 + 5} {y + 4} Z" fill="#a8532a"/>'
                       f'<ellipse cx="{x + k * 6 + 2.5}" cy="{y + 4}" rx="2.6" ry=".9" fill="#f4ead2"/>' for k in range(3))
    if kind == "cng":       # a green CNG waiting for Abbas bhai
        x = xs + w - 34
        return (f'<path d="M{x} {y + 9} V{y + 1} Q{x} {y - 6} {x + 10} {y - 6} H{x + 20} Q{x + 26} {y - 6} {x + 26} {y + 2} V{y + 9} Z" fill="#2e8b57"/>'
                f'<path d="M{x + 1} {y - 2.5} Q{x + 2} {y - 7} {x + 10} {y - 7} H{x + 20} Q{x + 25} {y - 7} {x + 25.5} {y - 2.5}" fill="none" stroke="#111" stroke-width="1.6"/>'
                f'<path d="M{x + 12} {y - 5} V{y + 6} M{x + 16} {y - 5} V{y + 6} M{x + 20} {y - 5} V{y + 6}" stroke="#1a3a28" stroke-width=".8"/>'
                f'<rect x="{x + 2}" y="{y - 3}" width="7" height="5" rx="1" fill="#9fd3c0" fill-opacity=".5"/>'
                f'<circle cx="{x + 5}" cy="{y + 10}" r="2.6" fill="#111"/><circle cx="{x + 22}" cy="{y + 10}" r="2.6" fill="#111"/>')
    if kind == "tailor":    # a shirt on a hanger outside, for show
        x = xs + w - 12
        return (f'<line x1="{x}" y1="{y - 1}" x2="{x}" y2="{y + 10}" stroke="#4a505b" stroke-width=".8"/>'
                f'<path d="M{x - 5} {y + 1} L{x - 2} {y - 1} H{x + 2} L{x + 5} {y + 1} L{x + 4} {y + 3} L{x + 3} {y + 2.5} V{y + 8} H{x - 3} V{y + 2.5} L{x - 4} {y + 3} Z" '
                f'fill="{CLOTH[int(_h(d, "shirt") * len(CLOTH))]}"/>')
    return ""


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
    o.append(f'<rect x="{xs + 6}" y="{BASE + 6}" width="40" height="2.5" rx="1" fill="#7a5532"/>'   # bench
             f'<line x1="{xs + 9}" y1="{BASE + 8.5}" x2="{xs + 9}" y2="{BASE + 14}" stroke="#7a5532" stroke-width="1.8"/>'
             f'<line x1="{xs + 43}" y1="{BASE + 8.5}" x2="{xs + 43}" y2="{BASE + 14}" stroke="#7a5532" stroke-width="1.8"/>')
    dx = xs + 66                                                                          # a dog, asleep
    o.append(f'<ellipse cx="{dx}" cy="{BASE + 15}" rx="7" ry="3.2" fill="#7d6a57"/>'
             f'<circle cx="{dx + 6}" cy="{BASE + 13}" r="2.5" fill="#7d6a57"/>'
             f'<path d="M{dx + 6.5} {BASE + 10.8} L{dx + 8.3} {BASE + 9.5} L{dx + 7.8} {BASE + 12.2} Z" fill="#5e4f40"/>'
             f'<path d="M{dx - 7} {BASE + 15} Q{dx - 10} {BASE + 13} {dx - 8} {BASE + 11}" fill="none" stroke="#7d6a57" '
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
    kind_of = {c: (shop[5], c - a) for a, b, shop in spans for c in range(a, b)}

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

    # the street first, so the stall's bench and dog sit on top of it
    o.append(f'<rect y="{BASE}" width="{W}" height="22" fill="#0c0f14"/>')
    o.append(f'<line x1="0" y1="{BASE + 11}" x2="{W}" y2="{BASE + 11}" stroke="#2a2f38" stroke-dasharray="10 12"/>')
    for k, (d, n) in enumerate(zip(nights, counts)):
        o.append(building(col_x(k), d, n, lvl(n), d in release_days, *kind_of[k]))
    props = []
    for a, b, (bangla, _, _, bg, fg, kind) in spans:
        xs, w = col_x(a), (b - a) * (BW + GAP) - GAP
        cha = kind == "cha"
        if cha:
            o.append(cha_stall(xs, w))
            props.append((xs - 50, xs + w + 10))
        else:
            out = pavement(xs, w, kind, day)
            if out:
                o.append(out)
                props.append((xs + w - 40, xs + w + 4))
        o.append(signboard(xs, w, bangla, bg, fg, lit=cha or any(counts[c] for c in range(a, b)),
                           size=12 if cha else 10))  # the stall's name is short; bigger letters fill its board

    spots = [x for x in range(20, W - 60, 4)
             if not any(lo - 36 < x < hi for lo, hi in props)]  # never parked on top of a shop's things
    if spots:
        o.append(rickshaw(spots[int(_h(day, "rickshaw") * len(spots))]))
    o.append(crows(day))

    for k in range(NIGHTS - 1, -1, -7):  # a date under every seventh night, counting back from yesterday
        x = col_x(k) + BW / 2
        label = "yesterday" if k == NIGHTS - 1 else nights[k].strftime("%b %-d")
        anchor = "end" if k == NIGHTS - 1 else "middle"  # "yesterday" would run off the edge
        x = col_x(k) + BW if k == NIGHTS - 1 else x
        o.append(f'<text class="m" x="{x:.0f}" y="{BASE + 38}" font-size="9.5" fill="{MUTED}" text-anchor="{anchor}">{label}</text>')

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
           "Each shop looks like itself: a biryani deg steaming out front, a pharmacy's green cross, a newspaper rack, "
           "stacked tyres, sacks of rice and dal, clay pots of mishti doi, a green CNG at Abbas's, a shirt outside the tailor's. "
           "The cha stall never closes; it runs on a hurricane lantern. Also: crows on the electric wires, "
           "laundry drying on the roofs, a mosque behind, and a rickshaw with a painted hood.")
    return "\n".join(o).replace("__ALT__", html.escape(alt)), alt
