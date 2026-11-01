#!/usr/bin/env python3
"""
Draws assets/desktop.svg: a deliberately messy desktop with six windows, one per folder.
A spotlight (and a cursor) visits each window in turn.

  python scripts/desktop.py

Edit the data blocks below (recipe, incidents, dilemmas, books) and re-run.
Standard library only.
"""
import html

W, H = 880, 640
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"
SANS = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
AMBER, TEAL, MUTED, DIM, TEXT = "#f0b44c", "#7aa7b8", "#6f7680", "#3b4048", "#e4e2dd"
CARD, DESK, EDGE = "#0f1216", "#0b0d10", "#232830"
PAPER, INK = "#efe3c0", "#3a2f14"

# ------------------------------------------------------------------ the stuff on the desktop
RECIPE = [
    "1 cup water",
    "1½ spoons sugar / honey",
    "1 cardamom",
    "a pinch of cinnamon",
    "a handful of mint",
    "some squeezed lime",
]

INCIDENTS = [  # (INES level, place, year)
    (7, "Chernobyl", "1986"),
    (7, "Fukushima Daiichi", "2011"),
    (6, "Kyshtym", "1957"),
    (5, "Three Mile Island", "1979"),
    (5, "Windscale", "1957"),
    (5, "Goiânia", "1987"),
    (4, "Tokaimura", "1999"),
]
INES_COLOR = {7: "#e06c5f", 6: "#e8935a", 5: AMBER, 4: "#8fa7b0"}

DILEMMAS = [  # (checked, text)
    (False, "sleep"),
    (True, "one more chapter (2 a.m.)"),
    (True, "rewrite it from scratch"),
    (True, "push --force, friday 6pm"),
    (False, "close a tab. which one?"),
    (True, '"works on my machine"'),
]

SPINES = [(16, 74, TEAL), (13, 58, AMBER), (20, 82, DIM), (14, 64, "#c9605a"), (18, 78, "#5d8a72"),
          (12, 54, AMBER), (17, 70, TEAL), (15, 60, MUTED), (13, 76, DIM)]

LIT_TABS = {1: 10.4, 2: 2.4, 3: 18.4, 5: 10.4, 7: 2.4, 8: 18.4, 9: 2.4, 11: 10.4, 12: 18.4, 13: 18.4, 14: 2.4, 16: 10.4}

# window: key -> (x, y, w, h, rotation)
LAYOUT = {
    "coding": (24, 50, 330, 214, -1.0),
    "reading": (368, 58, 236, 228, 1.3),
    "cha": (618, 46, 238, 218, 2.2),
    "ml": (24, 284, 300, 232, -0.8),
    "nuclear": (338, 292, 290, 232, 0.9),
    "decisions": (642, 278, 214, 232, -1.8),
}
ORDER = ["coding", "reading", "cha", "ml", "nuclear", "decisions"]
SPOT = {k: 2.4 + 4 * i for i, k in enumerate(ORDER)}  # seconds, one 4s turn each in a 24s loop
CURSOR = [(322, 206), (572, 238), (824, 214), (262, 466), (598, 500), (822, 404)]


def esc(s):
    return html.escape(s, quote=False)


# ------------------------------------------------------------------ pieces
def window(key, title, body, extra=""):
    x, y, w, h, rot = LAYOUT[key]
    bar = f"M0 10 a10 10 0 0 1 10 -10 h{w - 20} a10 10 0 0 1 10 10 v18 h-{w} z"
    return (
        f'<g transform="translate({x} {y}) rotate({rot} {w / 2} {h / 2})">'
        f'<g class="in" style="animation-delay:{0.15 * ORDER.index(key):.2f}s">'
        f'<g class="w" style="animation-delay:{SPOT[key]}s">'
        f'<rect width="{w}" height="{h}" rx="10" fill="{CARD}" filter="url(#sh)"/>'
        f'<path d="{bar}" fill="{DESK}"/><line x1="0" y1="28.5" x2="{w}" y2="28.5" stroke="#1e2229"/>'
        f'<circle cx="15" cy="14" r="3.5" fill="#2a2f36"/><circle cx="28" cy="14" r="3.5" fill="#2a2f36"/>'
        f'<circle cx="41" cy="14" r="3.5" fill="#2a2f36"/>'
        f'<text x="{w / 2}" y="18" font-size="10.5" fill="{MUTED}" text-anchor="middle">{esc(title)}</text>'
        f'{body}'
        f'<rect class="frame" width="{w}" height="{h}" rx="10" fill="none" stroke="{EDGE}" '
        f'style="animation-delay:{SPOT[key]}s"/>'
        f'</g></g></g>{extra}'
    )


def coding():
    k, s, c = AMBER, TEAL, DIM
    code = [
        f'<tspan fill="{k}">@app.post</tspan>(<tspan fill="{s}">"/check"</tspan>)',
        f'<tspan fill="{k}">async def</tspan> check(skill: Skill):',
        '    path = graph.hops(skill, MALWARE)',
        f'    return decide(path)  <tspan fill="{c}"># ALLOW/ASK/BLOCK</tspan>',
    ]
    o = []
    for i, ln in enumerate(code):
        y = 54 + 17 * i
        o.append(f'<text x="24" y="{y}" font-size="10.5" fill="{DIM}" text-anchor="end">{i + 1}</text>')
        o.append(f'<text x="34" y="{y}" font-size="10.5" fill="{TEXT}" xml:space="preserve">{ln}</text>')
    o.append(f'<line x1="14" y1="128.5" x2="316" y2="128.5" stroke="#1e2229"/>')
    o.append(f'<text x="14" y="150" font-size="10.5" fill="{MUTED}">$ uvicorn main:app --reload</text>')
    o.append(f'<circle class="pulse" cx="18" cy="167" r="3.5" fill="{AMBER}"/>')
    o.append(f'<text x="30" y="171" font-size="10.5" fill="{AMBER}">dev open</text>'
             f'<text x="88" y="171" font-size="10.5" fill="{MUTED}">http://127.0.0.1:8000</text>')
    o.append(f'<text x="14" y="190" font-size="10.5" fill="{DIM}">INFO  application startup complete.</text>')
    o.append(f'<text x="14" y="206" font-size="10.5" fill="{MUTED}">$ </text>'
             f'<rect class="blink" x="26" y="196" width="6" height="11" fill="{AMBER}"/>')
    return window("coding", "~/projects/bouncer — nvim", "".join(o))


BOOKS = [  # (title, author and genre, one-line take)
    ("As Long As the Lemon Trees Grow", "Zoulfa Katouh · war fiction, Syria", ["incredible."]),
    ("Mornings in Jenin", "Susan Abulhawa · historical fiction", ["Palestine, pre-Nakba to the 2000s.", "heart-wrenching."]),
]


def reading():
    o, x, base, k = [], 18, 76, 0.5
    for i, (w, h, col) in enumerate(SPINES):
        h = h * k
        if i == len(SPINES) - 1:  # the last one leans
            o.append(f'<g transform="rotate(14 {x + w} {base})"><rect x="{x}" y="{base - h}" width="{w}" height="{h}" rx="2" '
                     f'fill="{col}" fill-opacity=".85"/></g>')
        else:
            o.append(f'<rect x="{x}" y="{base - h}" width="{w}" height="{h}" rx="2" fill="{col}" fill-opacity=".85"/>')
            o.append(f'<rect x="{x}" y="{base - h + 7}" width="{w}" height="2" fill="#0b0d10" fill-opacity=".45"/>')
        x += w + 3
    o.append(f'<line x1="12" y1="{base + .5}" x2="224" y2="{base + .5}" stroke="{EDGE}" stroke-width="2"/>')
    o.append(f'<path d="M206 29 v26 l8 -6 l8 6 v-26 z" fill="{AMBER}"/>')  # bookmark ribbon
    o.append(f'<text x="18" y="98" font-size="9.5" letter-spacing="1.4" fill="{MUTED}">READ &amp; LOVED</text>')
    y = 116
    for title, by, take in BOOKS:
        o.append(f'<text x="18" y="{y}" font-size="10.5" font-weight="700" fill="{TEXT}">{esc(title)}</text>')
        o.append(f'<text x="18" y="{y + 14}" font-size="9" fill="{MUTED}">{esc(by)}</text>')
        for j, line in enumerate(take):
            o.append(f'<text x="18" y="{y + 27 + 13 * j}" font-size="9" font-style="italic" fill="{AMBER}">{esc(line)}</text>')
        y += 14 + 13 * len(take) + 24
    return window("reading", "shelf.md", "".join(o))


def cha():
    x, y, w, h, rot = LAYOUT["cha"]
    o = [f'<rect width="{w}" height="{h}" rx="4" fill="{PAPER}" filter="url(#sh)"/>',
         f'<rect x="{w / 2 - 36}" y="-8" width="72" height="18" fill="#ffffff" fill-opacity=".22" transform="rotate(-3 {w / 2} 0)"/>',
         f'<text x="20" y="44" font-size="22" font-weight="800" font-family="{SANS}" fill="{INK}">lebu-cha</text>']
    for i, ln in enumerate(RECIPE):
        yy = 76 + 22 * i
        o.append(f'<text x="20" y="{yy}" font-size="12" fill="{INK}" xml:space="preserve">'
                 f'<tspan fill="{INK}" fill-opacity=".45">–  </tspan>{esc(ln)}</text>')
    o.append(f'<text x="20" y="{h - 16}" font-size="9" font-style="italic" fill="{INK}" fill-opacity=".6">'
             f"kettle's on. everything else can wait.</text>")
    mug = (f'<g transform="translate({w - 44} 22)" fill="none" stroke="{INK}" stroke-width="1.6" '
           f'stroke-linecap="round" stroke-linejoin="round">'
           f'<path d="M0 8 H20 V18 a8 8 0 0 1 -8 8 H8 a8 8 0 0 1 -8 -8 Z"/><path d="M20 11 h3 a4 4 0 0 1 0 8 h-3"/>'
           f'<path class="steam" d="M6 4 q-3 -3 0 -7"/><path class="steam b" d="M13 4 q-3 -3 0 -7"/></g>')
    o.append(mug)
    return (f'<g transform="translate({x} {y}) rotate({rot} {w / 2} {h / 2})">'
            f'<g class="in" style="animation-delay:{0.15 * ORDER.index("cha"):.2f}s">'
            f'<g class="w" style="animation-delay:{SPOT["cha"]}s">{"".join(o)}'
            f'<rect class="frame" width="{w}" height="{h}" rx="4" fill="none" stroke="{PAPER}" stroke-opacity="0" '
            f'style="animation-delay:{SPOT["cha"]}s"/></g></g></g>')


def ml():
    curve = "M26 104 C 70 108, 92 150, 140 156 S 220 162, 274 162"
    o = [f'<text x="14" y="52" font-size="12" fill="{TEXT}"><tspan fill="{AMBER}">model</tspan>.fit(X, y)</text>',
         f'<text x="14" y="70" font-size="10.5" fill="{MUTED}">'
         f'# ok but what is that line actually doing.</text>',
         f'<rect x="14.5" y="82.5" width="271" height="92" rx="6" fill="{DESK}" stroke="#1e2229"/>',
         f'<line x1="26" y1="162" x2="274" y2="162" stroke="#1e2229"/>',
         f'<text x="22" y="95" font-size="8.5" fill="{DIM}">loss</text>',
         f'<path d="{curve}" fill="none" stroke="{AMBER}" stroke-width="1.6" stroke-linecap="round"/>',
         f'<g><circle class="ball" r="4" fill="{TEXT}" style="offset-path:path(\'{curve}\')"/></g>',
         f'<text x="14" y="194" font-size="9.5" fill="{MUTED}">gradient descent: rolling downhill, carefully.</text>',
         f'<text x="14" y="212" font-size="11" fill="{TEAL}">w ← w − η·∇L</text>',
         f'<text x="14" y="226" font-size="9" fill="{DIM}">next: RAG · LangChain · LangGraph · agents</text>']
    return window("ml", "rabbit_hole.ipynb", "".join(o))


def nuclear():
    o = []
    for i, (lvl, place, year) in enumerate(INCIDENTS):
        y = 54 + 22 * i
        c = INES_COLOR[lvl]
        o.append(f'<rect x="14.5" y="{y - 12.5}" width="52" height="17" rx="8.5" fill="{c}" fill-opacity=".14" stroke="{c}" stroke-opacity=".6"/>')
        o.append(f'<text x="40.5" y="{y}" font-size="9" font-weight="700" fill="{c}" text-anchor="middle">INES {lvl}</text>')
        o.append(f'<text x="80" y="{y}" font-size="11" fill="{TEXT}">{esc(place)}</text>')
        o.append(f'<text x="276" y="{y}" font-size="10.5" fill="{MUTED}" text-anchor="end">{year}</text>')
    o.append(f'<line x1="14" y1="198.5" x2="276" y2="198.5" stroke="#1e2229"/>')
    o.append(f'<text x="14" y="216" font-size="9.5" font-style="italic" fill="{MUTED}">researching. purely academically.</text>')
    return window("nuclear", "less ines_incidents.log", "".join(o))


def decisions():
    o = []
    for i, (done, text) in enumerate(DILEMMAS):
        y = 54 + 24 * i
        o.append(f'<rect x="15" y="{y - 9}" width="11" height="11" rx="2.5" fill="{AMBER if done else "none"}" '
                 f'fill-opacity=".18" stroke="{AMBER if done else DIM}"/>')
        if done:
            o.append(f'<path d="M17.5 {y - 3.5} l2.5 2.5 l4 -5.5" fill="none" stroke="{AMBER}" stroke-width="1.5" '
                     f'stroke-linecap="round" stroke-linejoin="round"/>')
        o.append(f'<text x="34" y="{y}" font-size="10.5" fill="{TEXT if done else MUTED}">{esc(text)}</text>')
    o.append(f'<line x1="14" y1="196.5" x2="200" y2="196.5" stroke="#1e2229"/>')
    o.append(f'<text x="14" y="212" font-size="9.5" font-style="italic" fill="{MUTED}">decisions: questionable.</text>')
    o.append(f'<text x="14" y="226" font-size="9.5" font-style="italic" fill="{MUTED}">regrets: pending.</text>')
    return window("decisions", "dilemmas.txt", "".join(o))


def tabs():
    o = [f'<g transform="translate(24 536) rotate(.4 298 22)"><rect width="596" height="44" rx="10" fill="{CARD}" '
         f'stroke="{EDGE}" filter="url(#sh)"/>']
    for i in range(17):
        x = 12 + i * 33.5
        cls = "tab lit" if i in LIT_TABS else "tab"
        st = f' style="animation-delay:{LIT_TABS[i]}s"' if i in LIT_TABS else ""
        o.append(f'<rect class="{cls}" x="{x}" y="10" width="30" height="24" rx="6"{st}/>')
        o.append(f'<circle cx="{x + 15}" cy="22" r="2.6" fill="{DIM}" fill-opacity=".8"/>')
    o.append("</g>")
    o.append(f'<g transform="translate(642 528) rotate(-2.5 110 28)"><rect width="214" height="56" rx="3" fill="{AMBER}" filter="url(#sh)"/>'
             f'<text x="14" y="25" font-size="11" font-weight="700" fill="#2a1d05">4 of 17 tabs are important.</text>'
             f'<text x="14" y="43" font-size="11" fill="#2a1d05">I don\'t know which 4.</text></g>')
    return "".join(o)


def css():
    return f"""<style>
  text {{ font-family: {MONO}; }}
  .in {{ animation: appear .6s ease-out both; }}
  @keyframes appear {{ from {{ opacity: 0; }} }}
  .w {{ animation: pick 24s ease infinite backwards; }}
  @keyframes pick {{ 0% {{ transform: translateY(0); }} 1.5% {{ transform: translateY(-6px); }} 15.6% {{ transform: translateY(-6px); }}
                    16.6%, 100% {{ transform: translateY(0); }} }}
  .frame {{ animation: lit 24s ease infinite backwards; }}
  @keyframes lit {{ 0% {{ stroke: {EDGE}; }} 1.5% {{ stroke: {AMBER}; stroke-opacity: 1; }} 15.6% {{ stroke: {AMBER}; stroke-opacity: 1; }}
                   16.6%, 100% {{ stroke: {EDGE}; }} }}
  .tab {{ fill: #161a20; stroke: {EDGE}; }}
  .tab.lit {{ animation: tab 24s ease infinite backwards; }}
  @keyframes tab {{ 0% {{ fill: #161a20; stroke: {EDGE}; }} 1% {{ fill: {AMBER}; stroke: {AMBER}; }} 32% {{ fill: {AMBER}; stroke: {AMBER}; }}
                   33.3%, 100% {{ fill: #161a20; stroke: {EDGE}; }} }}
  .cursor {{ animation: roam 24s ease-in-out 2.4s infinite backwards; }}
  @keyframes roam {{
    0%, 12% {{ transform: translate({CURSOR[0][0]}px, {CURSOR[0][1]}px); }}
    16.6%, 29% {{ transform: translate({CURSOR[1][0]}px, {CURSOR[1][1]}px); }}
    33.3%, 45.5% {{ transform: translate({CURSOR[2][0]}px, {CURSOR[2][1]}px); }}
    50%, 62% {{ transform: translate({CURSOR[3][0]}px, {CURSOR[3][1]}px); }}
    66.6%, 79% {{ transform: translate({CURSOR[4][0]}px, {CURSOR[4][1]}px); }}
    83.3%, 95.5% {{ transform: translate({CURSOR[5][0]}px, {CURSOR[5][1]}px); }}
    100% {{ transform: translate({CURSOR[0][0]}px, {CURSOR[0][1]}px); }} }}
  .steam {{ animation: rise 2.6s ease-in-out infinite; }}
  .steam.b {{ animation-delay: 1.3s; }}
  @keyframes rise {{ 0% {{ opacity: 0; transform: translateY(3px); }} 40% {{ opacity: 1; }} 100% {{ opacity: 0; transform: translateY(-4px); }} }}
  .blink {{ animation: blink 1.1s steps(1) infinite; }}
  @keyframes blink {{ 50% {{ opacity: 0; }} }}
  .pulse {{ animation: pulse 1.8s ease-in-out infinite; }}
  @keyframes pulse {{ 50% {{ opacity: .3; }} }}
  .ball {{ offset-rotate: 0deg; animation: roll 6s ease-in infinite; }}
  @keyframes roll {{ 0% {{ offset-distance: 0%; opacity: 0; }} 6% {{ opacity: 1; }} 88% {{ opacity: 1; }}
                    100% {{ offset-distance: 100%; opacity: 0; }} }}
  @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} .cursor {{ display: none; }} }}
</style>"""


def main():
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="Ayesha\'s messy desktop. A code editor with a dev server open. A bookshelf: read and loved As Long As the Lemon Trees Grow by Zoulfa Katouh, war fiction set in Syria, and Mornings in Jenin by Susan Abulhawa, historical fiction about Palestine from before the Nakba to the 2000s. '
         f'A recipe for lebu-cha: 1 cup water, 1 and a half spoons sugar or honey, 1 cardamom, a pinch of cinnamon, a handful of mint, some squeezed lime. '
         f'A machine learning notebook with a loss curve. A log of nuclear accidents: Chernobyl, Fukushima, Kyshtym, Three Mile Island, Windscale, Goiania, Tokaimura. '
         f'A to-do list of questionable decisions. 17 browser tabs open, 4 important, she doesn\'t know which 4.">',
         css(),
         f'<defs><filter id="sh" color-interpolation-filters="sRGB" x="-10%" y="-10%" width="120%" height="130%">'
         f'<feDropShadow dx="0" dy="8" stdDeviation="8" flood-color="#000" flood-opacity=".5"/></filter>'
         f'<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="11" cy="11" r=".9" fill="#171b20"/></pattern>'
         f'<clipPath id="frame"><rect width="{W}" height="{H}" rx="14"/></clipPath></defs>',
         '<g clip-path="url(#frame)">',
         f'<rect width="{W}" height="{H}" fill="{DESK}"/><rect width="{W}" height="{H}" fill="url(#dots)"/>',
         # menubar
         f'<rect width="{W}" height="32" fill="{CARD}"/><line x1="0" y1="32.5" x2="{W}" y2="32.5" stroke="#1e2229"/>',
         f'<circle cx="26" cy="16" r="3.5" fill="{AMBER}"/>'
         f'<text x="40" y="20" font-size="11.5" font-weight="700" fill="#ffffff">ayesha</text>'
         f'<text x="98" y="20" font-size="11" fill="{DIM}" xml:space="preserve">file   edit   view   tabs</text>',
         f'<text x="{W - 24}" y="20" font-size="11" fill="{MUTED}" text-anchor="end">it\'s 2:07 a.m.</text>',
         # a coffee ring, because of course
         f'<circle cx="842" cy="276" r="26" fill="none" stroke="{AMBER}" stroke-opacity=".10" stroke-width="3"/>',
         coding(), reading(), cha(), ml(), nuclear(), decisions(), tabs(),
         f'<text x="{W / 2}" y="618" font-size="9.5" fill="{DIM}" text-anchor="middle" letter-spacing="2">'
         f'CLICK FOR THE ONE THAT ACTUALLY OPENS ↗</text>',
         f'<g class="cursor"><path d="M0 0 L0 15 L4 11.5 L7 18 L9.5 17 L6.5 10.5 L11.5 10.5 Z" fill="#ffffff" '
         f'stroke="#000" stroke-width="1" stroke-linejoin="round"/></g>',
         '</g>',
         f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="{EDGE}"/>',
         '</svg>']
    with open("assets/desktop.svg", "w", encoding="utf-8") as f:
        f.write("\n".join(o))
    print("wrote assets/desktop.svg")


if __name__ == "__main__":
    main()
