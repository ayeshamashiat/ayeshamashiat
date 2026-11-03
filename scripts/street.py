#!/usr/bin/env python3
"""
Draws assets/street.svg: a Dhaka street at night during load shedding.

One building per night for the last six weeks, Dhaka style: shops on the ground floor, flats
above. A night I contributed on GitHub has its flats lit, more of them the busier the day. A night I didn't is
a blackout upstairs. Release nights get fireworks.

The shops run along the street under Bangla signboards, each sign and storefront spanning a few
buildings the way real ones do. They stay open through load shedding on IPS, and the cha stall
on a hurricane lantern. Around them: crows on the wires, laundry
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
# what you see inside.
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


def building(x, d, n, level, released):
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
    tip = (f"{d.strftime('%a %d %b')}: {n} contribution{'s' if n != 1 else ''}" if n else f"{d.strftime('%a %d %b')}: load shedding") \
        + (" · release night" if released else "")
    o.append(f'<rect x="{x}" y="{top - 10}" width="{BW}" height="{BASE - top + 10}" fill="transparent"><title>{tip}</title></rect>')
    if released:
        o.append(firework(x + BW / 2, top - 26, d))
    return "".join(o)


def storefront(xs, w, kind):
    """One shop's whole front, open the full width of its span. Dhaka shops run on IPS through
    load shedding, so they stay lit whatever the flats above are doing."""
    top, bot = BASE - FRONT, BASE - 2                 # the opening; a concrete step below
    x0, x1 = xs + 1.5, xs + w - 1.5
    light, glow = INSIDE.get(kind, ("#e0a552", ".6"))
    clip = f"in{int(xs)}"
    o = [f'<rect x="{xs - 1.5:.1f}" y="{BASE - GF + SIGN_H + 1}" width="{w + 3:.1f}" height="{GF - SIGN_H - 1}" fill="#1c2028"/>',
         f'<rect x="{x0 - 1:.1f}" y="{bot}" width="{x1 - x0 + 2:.1f}" height="2" fill="#3a3f48"/>',
         f'<clipPath id="{clip}"><rect x="{x0:.1f}" y="{top}" width="{x1 - x0:.1f}" height="{bot - top}"/></clipPath>',
         f'<g clip-path="url(#{clip})"><rect x="{x0:.1f}" y="{top}" width="{x1 - x0:.1f}" height="{bot - top}" '
         f'fill="{light}" fill-opacity="{glow}"/>', INTERIORS[kind](x0, x1, top, bot)]
    for tx in range(int(x0 + 3), int(x1 - 10), 24):  # tube lights along the ceiling
        o.append(f'<rect x="{tx}" y="{top + 0.6}" width="12" height=".9" fill="#f4fbff" fill-opacity=".9"/>')
    o.append('</g>')
    o.append(f'<rect x="{x0 - 0.5:.1f}" y="{top - 0.5}" width="{x1 - x0 + 1:.1f}" height="1.4" fill="#454b55"/>')  # the shutter box, rolled up
    return "".join(o)


def _glass_door(x, top, bot, w=11):
    """A two-leaf glass door in an aluminium frame."""
    return (f'<rect x="{x:.1f}" y="{top + 2}" width="{w}" height="{bot - top - 2}" fill="#b9d6e3" fill-opacity=".35" '
            f'stroke="#9aa3ad" stroke-width=".8"/>'
            f'<line x1="{x + w / 2:.1f}" y1="{top + 2}" x2="{x + w / 2:.1f}" y2="{bot}" stroke="#9aa3ad" stroke-width=".7"/>'
            f'<line x1="{x + 1.5:.1f}" y1="{top + 4}" x2="{x + 3.5:.1f}" y2="{top + 8}" stroke="#ffffff" stroke-opacity=".5" stroke-width=".5"/>'
            f'<rect x="{x + w / 2 - 1.6:.1f}" y="{(top + bot) / 2:.1f}" width=".7" height="3" fill="#d8dde3"/>'
            f'<rect x="{x + w / 2 + 0.9:.1f}" y="{(top + bot) / 2:.1f}" width=".7" height="3" fill="#d8dde3"/>')


def _biryani(x0, x1, top, bot):
    o = [f'<rect x="{x0:.1f}" y="{top}" width="{x1 - x0:.1f}" height="{bot - top - 6}" fill="#f2ead8" fill-opacity=".35"/>']
    o += [f'<line x1="{x0:.1f}" y1="{y}" x2="{x1:.1f}" y2="{y}" stroke="#c9b48e" stroke-opacity=".35" stroke-width=".4"/>'
          for y in range(top + 3, bot - 6, 3)]
    o.append(f'<rect x="{x0:.1f}" y="{bot - 6}" width="34" height="6" fill="#8a2b1f"/>')         # the red counter
    for cx in (x0 + 9, x0 + 24):                                                                 # two degs on it
        o.append(f'<ellipse cx="{cx:.1f}" cy="{bot - 10}" rx="6.5" ry="4.2" fill="#a86b32"/>'
                 f'<rect x="{cx - 4:.1f}" y="{bot - 15.5}" width="8" height="2.4" fill="#c99a5b"/>'
                 f'<rect x="{cx - 4.6:.1f}" y="{bot - 13.4}" width="9.2" height="1.4" fill="#c0392b"/>')
    for tx in range(int(x0 + 40), int(x1 - 9), 15):                                              # tables
        o.append(f'<rect x="{tx}" y="{bot - 6}" width="11" height="1.3" fill="#6b4423"/>'
                 f'<line x1="{tx + 1}" y1="{bot - 4.7}" x2="{tx + 1}" y2="{bot}" stroke="#6b4423" stroke-width=".8"/>'
                 f'<line x1="{tx + 10}" y1="{bot - 4.7}" x2="{tx + 10}" y2="{bot}" stroke="#6b4423" stroke-width=".8"/>'
                 f'<ellipse cx="{tx + 3.5}" cy="{bot - 6.4}" rx="2.2" ry=".7" fill="#f6f2e8"/>'
                 f'<rect x="{tx + 7}" y="{bot - 9.6}" width="1.8" height="3.3" rx=".5" fill="#8fb4d9"/>')
    o.append(f'<rect x="{x1 - 12:.1f}" y="{top + 4}" width="10" height="7" fill="#1d2a22"/>'          # menu board
             + "".join(f'<line x1="{x1 - 11:.1f}" y1="{top + 5.8 + r * 1.6:.1f}" x2="{x1 - 4:.1f}" y2="{top + 5.8 + r * 1.6:.1f}" '
                       f'stroke="#e8e2d0" stroke-width=".5"/>' for r in range(3)))
    return "".join(o)


def _pharmacy(x0, x1, top, bot):
    o = []
    colors = ["#d64545", "#3a7bd5", "#f2c94c", "#2f9e6a", "#ffffff", "#9b59b6"]
    for r in range(3):
        sy = top + 6 + r * 3.6
        o.append(f'<rect x="{x0:.1f}" y="{sy:.1f}" width="{x1 - x0:.1f}" height=".7" fill="#7f978a"/>')
        k, bx = 0, x0 + 1
        while bx < x1 - 2:
            o.append(f'<rect x="{bx:.1f}" y="{sy - 2.4:.1f}" width="2.2" height="2.4" fill="{colors[(k * 7 + r * 3) % 6]}"/>')
            bx, k = bx + 2.7, k + 1
    o.append(f'<rect x="{x0:.1f}" y="{bot - 5}" width="{x1 - x0:.1f}" height="5" fill="#cfe3ec" fill-opacity=".55" '
             f'stroke="#f2fbff" stroke-opacity=".7" stroke-width=".5"/>')                         # glass counter
    cx = (x0 + x1) / 2
    o.append(f'<path d="M{cx:.1f} {bot - 4.4} V{bot - 0.6} M{cx - 1.9:.1f} {bot - 2.5} H{cx + 1.9:.1f}" stroke="#1f9e5a" stroke-width="1.2"/>')
    o.append(f'<rect x="{x1 - 13:.1f}" y="{top + 2}" width="11" height="{bot - top - 2}" fill="#e4f2ea"/>' + _glass_door(x1 - 13, top, bot))
    return "".join(o)


def _library(x0, x1, top, bot):
    o = [_glass_door(x0 + 2, top, bot, 14)]
    x0 += 18                                                                                      # shelves start after the door
    spines = ["#b4442a", "#3456a8", "#2f7d4f", "#c08a1e", "#7a4fa3", "#e8e2d0", "#1f1f1f"]
    for r in range(3):
        sy = top + 6.5 + r * 3.8
        o.append(f'<rect x="{x0:.1f}" y="{sy:.1f}" width="{x1 - x0:.1f}" height=".8" fill="#5a3a1a"/>')
        k, bx = 0, x0 + 0.5
        while bx < x1 - 1.5:
            h = 2.2 + 1.2 * _h("spine", r, k)
            o.append(f'<rect x="{bx:.1f}" y="{sy - h:.1f}" width="1.4" height="{h:.1f}" fill="{spines[int(_h("sc", r, k) * 7)]}"/>')
            bx, k = bx + 1.8, k + 1
    o.append(f'<rect x="{x0:.1f}" y="{bot - 4}" width="{x1 - x0:.1f}" height="4" fill="#6b4423"/>')            # counter
    for k, c in enumerate(["#e8e2d0", "#f2c94c", "#3a7bd5", "#e8e2d0"]):                                    # notebooks on it
        o.append(f'<rect x="{x0 + 4 + k * 5:.1f}" y="{bot - 5.2 - (k % 2) * 0.6:.1f}" width="4" height="1.2" fill="{c}"/>')
    return "".join(o)


def _garage(x0, x1, top, bot, cng=False):
    o = [f'<rect x="{x0:.1f}" y="{top + 3}" width="{x1 - x0:.1f}" height="{bot - top - 9}" fill="#3a3a36" fill-opacity=".45"/>']
    for k, tx in enumerate(range(int(x0 + 4), int(x1 - 4), 9)):                                  # tools on the pegboard
        if k % 3 == 2:
            continue
        o.append(f'<path d="M{tx} {top + 5} V{top + 11} M{tx - 1.4} {top + 5.4} H{tx + 1.4}" stroke="#6c727c" stroke-width=".9"/>')
    o.append(f'<circle cx="{x1 - 6:.1f}" cy="{top + 8}" r="3.4" fill="none" stroke="#151515" stroke-width="1.8"/>')  # a tyre on the wall
    o.append(f'<rect x="{x0:.1f}" y="{bot - 1.5}" width="{x1 - x0:.1f}" height="1.5" fill="#2b2a28"/>')           # oily floor
    if cng:   # batteries and oil cans on the bench
        o.append(f'<rect x="{x0 + 2:.1f}" y="{bot - 6}" width="22" height="1.5" fill="#5a3a1a"/>'
                 f'<rect x="{x0 + 4:.1f}" y="{bot - 9}" width="5" height="3" fill="#1f1f1f"/>'
                 f'<rect x="{x0 + 11:.1f}" y="{bot - 10}" width="3" height="4" rx=".5" fill="#c0392b"/>'
                 f'<rect x="{x0 + 16:.1f}" y="{bot - 10}" width="3" height="4" rx=".5" fill="#e0a520"/>')
    else:     # a motorbike in for repairs
        mx = (x0 + x1) / 2 - 8
        o.append(f'<circle cx="{mx:.1f}" cy="{bot - 3}" r="2.8" fill="none" stroke="#111" stroke-width="1.2"/>'
                 f'<circle cx="{mx + 14:.1f}" cy="{bot - 3}" r="2.8" fill="none" stroke="#111" stroke-width="1.2"/>'
                 f'<path d="M{mx:.1f} {bot - 3} L{mx + 4:.1f} {bot - 7} H{mx + 10:.1f} L{mx + 14:.1f} {bot - 3} M{mx + 11:.1f} {bot - 7} L{mx + 12.5:.1f} {bot - 9.5}" '
                 f'fill="none" stroke="#b3342a" stroke-width="1.6" stroke-linecap="round"/>')
    return "".join(o)


def _store(x0, x1, top, bot):
    """মায়ের দোয়া is a departmental store: a glass front, aisles of shelves, a checkout."""
    o = []
    goods = ["#e63946", "#f4a261", "#2a9d8f", "#e9c46a", "#457b9d", "#8338ec", "#f1faee"]
    for r in range(4):                                                                            # aisles, back to front
        sy = top + 4 + r * 3.4
        o.append(f'<rect x="{x0:.1f}" y="{sy + 2.2:.1f}" width="{x1 - x0:.1f}" height=".6" fill="#8a929c"/>')
        k, gx = 0, x0 + 0.5
        while gx < x1 - 1:
            o.append(f'<rect x="{gx:.1f}" y="{sy:.1f}" width="1.6" height="2.2" fill="{goods[(k * 5 + r * 2) % 7]}"/>')
            gx, k = gx + 2, k + 1
    o.append(f'<rect x="{x0 + 3:.1f}" y="{bot - 4.5}" width="14" height="4.5" fill="#d8dde3"/>'      # checkout and till
             f'<rect x="{x0 + 5:.1f}" y="{bot - 7}" width="4" height="2.5" fill="#2b2f36"/>'
             f'<rect x="{x0 + 10:.1f}" y="{bot - 5.6}" width="5" height="1.1" fill="#c0392b"/>')
    door = (x0 + x1) / 2 + 6
    o.append(f'<rect x="{door:.1f}" y="{top + 2}" width="12" height="{bot - top - 2}" fill="#f2efe6" fill-opacity=".5"/>'
             + _glass_door(door, top, bot, 12))
    mx = x0 + 12                                                                                  # glass front: mullions and a sheen
    while mx < x1 - 2:
        if not door - 1 < mx < door + 13:
            o.append(f'<line x1="{mx:.1f}" y1="{top + 2}" x2="{mx:.1f}" y2="{bot}" stroke="#9aa3ad" stroke-width=".6"/>')
        mx += 12
    o.append(f'<rect x="{x0:.1f}" y="{top + 2}" width="{x1 - x0:.1f}" height="{bot - top - 2}" fill="#cfe7f2" fill-opacity=".12"/>')
    return "".join(o)


def _sweets(x0, x1, top, bot):
    o = [f'<rect x="{x0:.1f}" y="{top}" width="{x1 - x0:.1f}" height="{bot - top - 9}" fill="#fbf4ea" fill-opacity=".35"/>']
    bx = x0 + 2
    while bx < x1 - 6:                                                                            # mishti boxes up top
        o.append(f'<rect x="{bx:.1f}" y="{top + 4}" width="5" height="3" fill="#fbf6ea"/>'
                 f'<rect x="{bx:.1f}" y="{top + 5}" width="5" height=".8" fill="#c0392b"/>')
        bx += 7
    o.append(f'<rect x="{x0:.1f}" y="{bot - 9}" width="{x1 - x0:.1f}" height="9" fill="#d8eef5" fill-opacity=".35" '
             f'stroke="#f2fbff" stroke-opacity=".7" stroke-width=".5"/>')                         # the long glass case
    kinds = ["#fbf6ea", "#5a2a14", "#f2b632", "#e8742a"]                                          # rosogolla, kalojam, laddoo, jilapi
    for r in range(2):
        k, sx = 0, x0 + 2
        while sx < x1 - 1:
            o.append(f'<circle cx="{sx:.1f}" cy="{bot - 6.5 + r * 3.6:.1f}" r="1.1" fill="{kinds[(k // 3 + r) % 4]}"/>')
            sx, k = sx + 2.6, k + 1
    return "".join(o)


def _tailor(x0, x1, top, bot):
    o = []
    k, bx = 0, x0 + 1
    while bx < x1 - 2:                                                                            # bolts of cloth
        o.append(f'<rect x="{bx:.1f}" y="{top + 4}" width="2.2" height="8" fill="{CLOTH[k % len(CLOTH)]}"/>')
        bx, k = bx + 2.8, k + 1
    o.append(f'<rect x="{x0:.1f}" y="{top + 12}" width="{x1 - x0:.1f}" height=".7" fill="#5a3a1a"/>')
    for mx, c in ((x1 - 8, "#e8e2d0"), (x1 - 20, "#2f6d8a")):                                     # mannequins in panjabis
        o.append(f'<circle cx="{mx:.1f}" cy="{top + 5}" r="1.4" fill="#d9c7a8"/>'
                 f'<path d="M{mx - 2.6:.1f} {top + 6.8} H{mx + 2.6:.1f} L{mx + 2:.1f} {bot - 3} H{mx - 2:.1f} Z" fill="{c}"/>'
                 f'<line x1="{mx:.1f}" y1="{bot - 3}" x2="{mx:.1f}" y2="{bot}" stroke="#3a2a1a" stroke-width=".6"/>')
    o.append(f'<rect x="{x0 + 2:.1f}" y="{bot - 5}" width="22" height="1.3" fill="#6b4423"/>'                # cutting table
             f'<path d="M{x0 + 5:.1f} {bot - 5} V{bot - 9.5} H{x0 + 12:.1f} V{bot - 8} H{x0 + 7:.1f} V{bot - 5}" fill="#1f1f1f"/>'
             f'<line x1="{x0 + 14:.1f}" y1="{bot - 5.5}" x2="{x0 + 23:.1f}" y2="{bot - 5.5}" stroke="#f2c94c" stroke-width=".7"/>')
    return "".join(o)


INTERIORS = {"biryani": _biryani, "pharmacy": _pharmacy, "library": _library, "garage": _garage,
             "cng": lambda *a: _garage(*a, cng=True), "store": _store, "sweets": _sweets, "tailor": _tailor}

# how each shop is lit inside: warm bulbs mostly, white tube lights at the pharmacy and the sweet shop
INSIDE = {"pharmacy": ("#e4f2ea", ".8"), "store": ("#f4f1e8", ".75"), "sweets": ("#f6dcc0", ".75"), "garage": ("#c98c3e", ".5"),
          "cng": ("#c98c3e", ".5"), "library": ("#e7b665", ".6")}


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


def wheel(cx, cy, r, spokes=10):
    o = [f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="none" stroke="#15171b" stroke-width="1.8"/>',
         f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r - 1.1:.1f}" fill="none" stroke="#9aa3ad" stroke-width=".5"/>']
    for k in range(spokes):
        a = math.pi * k / spokes
        dx, dy = (r - 1.2) * math.cos(a), (r - 1.2) * math.sin(a)
        o.append(f'<line x1="{cx - dx:.1f}" y1="{cy - dy:.1f}" x2="{cx + dx:.1f}" y2="{cy + dy:.1f}" stroke="#9aa3ad" stroke-width=".3"/>')
    o.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="1.1" fill="#c8ced6"/>')
    return "".join(o)


def rickshaw(x):
    """A cycle rickshaw parked facing right: big spoked rear wheel, the folded hood with its
    painted panels and tassels, a red seat, the puller's saddle and a small front wheel."""
    g = BASE + 20                                   # where the tyres meet the road
    steel = 'stroke="#aab2bc" stroke-width="1.1" fill="none" stroke-linecap="round" stroke-linejoin="round"'
    rx, fx = x + 13, x + 48                         # rear and front axles
    o = ['<g>']
    o.append(f'<path d="M{rx} {g - 8} L{x + 34} {g - 8} L{fx - 3} {g - 18} M{fx} {g - 6} L{fx - 3} {g - 18} L{fx - 4} {g - 22} '
             f'M{fx - 7} {g - 22} H{fx - 1} M{x + 34} {g - 8} L{x + 33} {g - 17} M{x + 30} {g - 17.5} H{x + 36}" {steel}/>')
    o.append(f'<line x1="{x + 34}" y1="{g - 8}" x2="{rx}" y2="{g - 8}" stroke="#55606b" stroke-width=".6" stroke-dasharray="1 .6"/>')  # chain
    o.append(wheel(rx, g - 8, 8))
    o.append(wheel(fx, g - 6, 6, 8))
    o.append(f'<rect x="{x + 2}" y="{g - 17}" width="22" height="7" rx="1.5" fill="#1d4e89"/>')          # the body, side panel
    o.append(f'<path d="M{x + 3} {g - 13.5} H{x + 23}" stroke="#f0b44c" stroke-width=".8" stroke-dasharray="1.6 1"/>'
             + "".join(f'<circle cx="{x + 6 + k * 5}" cy="{g - 15.4}" r=".9" fill="{c}"/>'
                       for k, c in enumerate(["#ff8fb3", "#5fc28a", "#ffd27a", "#ff8fb3"])))
    o.append(f'<rect x="{x + 5}" y="{g - 21}" width="15" height="4" rx="1.5" fill="#c0392b"/>'            # the seat
             f'<rect x="{x + 4}" y="{g - 25}" width="3" height="8" rx="1" fill="#c0392b"/>')
    # the hood, folded back: red canvas, a painted band, chrome studs and tassels
    o.append(f'<path d="M{x + 2} {g - 17} Q{x} {g - 33} {x + 12} {g - 35} Q{x + 24} {g - 35} {x + 24} {g - 22} L{x + 21} {g - 20} '
             f'Q{x + 21} {g - 31} {x + 12} {g - 31} Q{x + 5} {g - 30} {x + 6} {g - 17} Z" fill="#a8241c"/>')
    o.append(f'<path d="M{x + 3.4} {g - 24} Q{x + 3} {g - 32} {x + 12} {g - 33.2} Q{x + 22} {g - 33} {x + 22.5} {g - 24}" '
             f'fill="none" stroke="#f0b44c" stroke-width="1" stroke-dasharray="1.4 1"/>')
    for k in range(5):
        tx = x + 6 + k * 4
        o.append(f'<line x1="{tx}" y1="{g - 34.5 + abs(k - 2) * 0.6:.1f}" x2="{tx}" y2="{g - 37 + abs(k - 2) * 0.6:.1f}" '
                 f'stroke="{["#ff8fb3", "#5fc28a", "#ffd27a", "#5fc28a", "#ff8fb3"][k]}" stroke-width=".9"/>')
    o.append(f'<circle cx="{x + 22.8}" cy="{g - 21.5}" r="1.3" fill="#d8dde3"/>')                         # a little mirror
    o.append('</g>')
    return "".join(o)


def cng(x):
    """A green CNG auto-rickshaw, cage doors and all, facing left."""
    g = BASE + 20
    o = ['<g>',
         f'<path d="M{x} {g - 4} V{g - 15} Q{x} {g - 24} {x + 10} {g - 24} H{x + 30} Q{x + 36} {g - 24} {x + 37} {g - 15} V{g - 4} Z" fill="#2e8b57"/>',
         f'<path d="M{x + 1} {g - 18} Q{x + 2} {g - 25} {x + 10} {g - 25.5} H{x + 30} Q{x + 36} {g - 25.5} {x + 36.5} {g - 18}" '
         f'fill="none" stroke="#111" stroke-width="2.2"/>',
         f'<rect x="{x + 2}" y="{g - 20}" width="8" height="6" rx="1" fill="#a9d8c6" fill-opacity=".55"/>',  # windscreen
         f'<rect x="{x + 13}" y="{g - 21}" width="20" height="13" fill="none" stroke="#163b26" stroke-width=".8"/>']
    for k in range(5):                                                                            # the cage doors
        o.append(f'<line x1="{x + 15 + k * 4}" y1="{g - 21}" x2="{x + 15 + k * 4}" y2="{g - 8}" stroke="#163b26" stroke-width=".7"/>')
    o.append(f'<line x1="{x + 13}" y1="{g - 14.5}" x2="{x + 33}" y2="{g - 14.5}" stroke="#163b26" stroke-width=".7"/>'
             f'<circle cx="{x + 1.5}" cy="{g - 9}" r="1.5" fill="#ffe9a8"/>'                         # headlight
             f'<rect x="{x + 3}" y="{g - 7}" width="10" height="2" fill="#111"/>')
    o.append(wheel(x + 7, g - 3.5, 3.5, 6))
    o.append(wheel(x + 30, g - 3.5, 3.5, 6))
    o.append('</g>')
    return "".join(o)


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
         sky(), mosque(250)]

    # the street, under everything that stands on it
    o.append(f'<rect y="{BASE}" width="{W}" height="22" fill="#0c0f14"/>')
    o.append(f'<line x1="0" y1="{BASE + 11}" x2="{W}" y2="{BASE + 11}" stroke="#2a2f38" stroke-dasharray="10 12"/>')
    for k, (d, n) in enumerate(zip(nights, counts)):
        o.append(building(col_x(k), d, n, lvl(n), d in release_days))
    for a, b, (bangla, _, _, bg, fg, kind) in spans:
        xs, w = col_x(a), (b - a) * (BW + GAP) - GAP
        cha = kind == "cha"
        if cha:
            o.append(cha_stall(xs, w))
        else:
            o.append(storefront(xs, w, kind))
        o.append(signboard(xs, w, bangla, bg, fg, lit=True, size=12 if cha else 10))  # the stall's name is short; bigger letters fill its board

    # the only things on the street: a CNG and a rickshaw, somewhere new each day, never on top of each other
    cx = 40 + int(_h(day, "cng") * (W - 120))
    spots = [x for x in range(20, W - 70, 4) if not cx - 62 < x < cx + 45]
    o.append(cng(cx))
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
    legend = [("release", "#ff8fb3"), ("contributed", WARM[0]), ("load shedding", DARK_WINDOW)]  # short, so it never meets the stats
    for text, color in legend:
        tw = len(text) * 6.2
        o.append(f'<text class="m" x="{lx:.0f}" y="{H - 18}" font-size="9.5" fill="{MUTED}" text-anchor="end">{text}</text>')
        o.append(f'<rect x="{lx - tw - 12:.0f}" y="{H - 26}" width="6" height="8" fill="{color}" stroke="#2b313c" stroke-width=".5"/>')
        lx -= tw + 26
    o.append("</g>")
    o.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="{EDGE}"/>')
    o.append("</svg>")

    alt = (f"Load-shedding street: one building for each of the last {NIGHTS} nights in Dhaka. "
           f"Lit windows mean I contributed on GitHub that day; dark flats mean I didn't. "
           f"Lights on {on} of {NIGHTS} nights, longest run {run}"
           + (f", brightest night {busiest[1].strftime('%d %b')} with {busiest[0]} contributions" if busiest else "")
           + (f", {shipped} release night{'s' if shipped != 1 else ''} with fireworks" if shipped else "")
           + ". Shops run along the ground floor with flats above, open and lit on IPS through the load shedding. "
           "The shops have Bangla signboards: " + ", ".join(shop[1] for shop in SHOPS) + ". "
           "Each shop looks like itself: degs and tables at the biryani house, shelves of medicine at the pharmacy, "
           "a library with a glass door, a departmental store with a glass front and aisles, garages full of tools, "
           "a glass case of sweets, and a tailor's with mannequins. "
           "The cha stall never closes; it runs on a hurricane lantern. Also: crows on the electric wires, "
           "laundry drying on the roofs, a mosque behind, and on the street just a green CNG and a cycle rickshaw with a painted hood.")
    return "\n".join(o).replace("__ALT__", html.escape(alt)), alt
