#!/usr/bin/env python3
"""
Draws assets/desktop.svg: a deliberately messy desktop with six windows, one per folder.
A few seconds after the page loads, everything minimizes into the dock (you showed up, so
you get her attention), then comes back. After that a spotlight (and a cursor) visits each
window in turn, forever.

  python scripts/desktop.py

Edit the data blocks below (recipe, incidents, todos, books) and re-run.
Standard library only.
"""
import html

W, H = 880, 640
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"
SANS = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
SERIF = "Georgia, 'Times New Roman', serif"
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

TODOS = [  # (done, text)
    (False, "sleep"),
    (True, "one more chapter (2 a.m.)"),
    (True, "rewrite it from scratch"),
    (True, "push --force, friday 6pm"),
    (False, "close a tab. which one?"),
    (True, '"works on my machine"'),
]

SPINES = [(16, 74, TEAL), (13, 58, AMBER), (20, 82, DIM), (14, 64, "#c9605a"), (18, 78, "#5d8a72"),
          (12, 54, AMBER), (17, 70, TEAL), (15, 60, MUTED), (13, 76, DIM)]

LIT_TABS = {1: 8.8, 2: 0.8, 3: 16.8, 5: 8.8, 7: 0.8, 8: 16.8, 9: 0.8, 11: 8.8, 12: 16.8, 13: 16.8, 14: 0.8, 16: 8.8}

# window: key -> (x, y, w, h, rotation)
LAYOUT = {
    "coding": (24, 50, 330, 214, -1.0),
    "reading": (368, 42, 236, 250, 1.3),
    "cha": (618, 46, 238, 218, 2.2),
    "ml": (24, 284, 300, 232, -0.8),
    "nuclear": (338, 298, 290, 232, 0.9),
    "decisions": (642, 278, 214, 232, -1.8),
}
ORDER = ["coding", "reading", "cha", "ml", "nuclear", "decisions"]
SPOT = {k: 0.8 + 4 * i for i, k in enumerate(ORDER)}  # seconds, one 4s turn each in a 24s loop
CURSOR = [(322, 206), (590, 196), (824, 214), (262, 466), (598, 500), (822, 404)]

T = 24                                 # the tour loop
# the one-time "oh, you're here" minimize, in seconds after the page loads
MINIMIZE, RESTORE = 4.5, 8.8           # windows start leaving / start coming back
GONE = 1.0                             # how long a window takes to fly in or out
ONCE = RESTORE + GONE + 0.6            # length of that one-time timeline

# the dock: one slot per window, plus the tab bar
DOCK = ORDER + ["tabs"]
DOCK_X, DOCK_Y = 339, 598              # first slot's left edge, the dock's top
DOCK_COLOR = {"coding": AMBER, "reading": TEAL, "cha": AMBER, "ml": TEAL, "nuclear": "#e06c5f",
              "decisions": AMBER, "tabs": MUTED}
BOUNDS = {k: (x, y, w, h) for k, (x, y, w, h, _) in LAYOUT.items()} | {"tabs": (24, 536, 596, 44)}


def pct(sec, total=T):
    return f"{100 * sec / total:.2f}%"


def once(sec):
    return pct(sec, ONCE)


def esc(s):
    return html.escape(s, quote=False)


# ------------------------------------------------------------------ pieces
def window(key, title, body, extra=""):
    x, y, w, h, rot = LAYOUT[key]
    bar = f"M0 10 a10 10 0 0 1 10 -10 h{w - 20} a10 10 0 0 1 10 10 v18 h-{w} z"
    return (
        f'<g class="mz mz-{key}"><g transform="translate({x} {y}) rotate({rot} {w / 2} {h / 2})">'
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
        f'</g></g></g></g>{extra}'
    )


# VS Code's Dark+ theme
VS_BG, VS_SIDE, VS_TABS, VS_LINE = "#1e1e1e", "#333333", "#252526", "#2a2d2e"
VS_KEY, VS_CTRL, VS_FN, VS_VAR, VS_TYPE, VS_CONST = "#569cd6", "#c586c0", "#dcdcaa", "#9cdcfe", "#4ec9b0", "#4fc1ff"
VS_STR, VS_COMMENT, VS_NUM, VS_BLUE = "#ce9178", "#6a9955", "#858585", "#007acc"


def coding():
    """VS Code: activity bar, tabs, Dark+ syntax colors, a terminal, the blue status bar."""
    _, _, w, h, _ = LAYOUT["coding"]
    t = lambda c, s: f'<tspan fill="{c}">{esc(s)}</tspan>'
    code = [
        t(VS_FN, "@app.post") + "(" + t(VS_STR, '"/check"') + ")",
        t(VS_KEY, "async def ") + t(VS_FN, "check") + "(" + t(VS_VAR, "skill") + ": " + t(VS_TYPE, "Skill") + "):",
        "    " + t(VS_VAR, "path") + " = " + t(VS_VAR, "graph") + "." + t(VS_FN, "hops") + "(" + t(VS_VAR, "skill")
        + ", " + t(VS_CONST, "MALWARE") + ")",
        "    " + t(VS_CTRL, "return ") + t(VS_FN, "decide") + "(" + t(VS_VAR, "path") + ")  " + t(VS_COMMENT, "# ALLOW/ASK/BLOCK"),
    ]
    bar = h - 15  # status bar top
    o = [f'<rect y="29" width="{w}" height="{bar - 29}" fill="{VS_BG}"/>',
         # activity bar: explorer (active), search, source control, extensions
         f'<rect y="29" width="26" height="{bar - 29}" fill="{VS_SIDE}"/>',
         f'<rect y="36" width="2" height="18" fill="#ffffff"/>',
         f'<path d="M8 39 h6 l3 3 v9 h-9 z" fill="none" stroke="#ffffff" stroke-width="1.2"/>',
         f'<circle cx="12.5" cy="66" r="3.6" fill="none" stroke="{VS_NUM}" stroke-width="1.2"/>'
         f'<line x1="15.2" y1="68.7" x2="18" y2="71.5" stroke="{VS_NUM}" stroke-width="1.2"/>',
         f'<circle cx="10" cy="83" r="1.6" fill="none" stroke="{VS_NUM}" stroke-width="1.1"/>'
         f'<circle cx="10" cy="95" r="1.6" fill="none" stroke="{VS_NUM}" stroke-width="1.1"/>'
         f'<circle cx="17" cy="87" r="1.6" fill="none" stroke="{VS_NUM}" stroke-width="1.1"/>'
         f'<path d="M10 84.6 v8.8 M17 88.6 q0 4 -6 5" fill="none" stroke="{VS_NUM}" stroke-width="1.1"/>',
         f'<rect x="8" y="104" width="4.5" height="4.5" fill="none" stroke="{VS_NUM}" stroke-width="1.1"/>'
         f'<rect x="13.5" y="104" width="4.5" height="4.5" fill="none" stroke="{VS_NUM}" stroke-width="1.1"/>'
         f'<rect x="8" y="109.5" width="4.5" height="4.5" fill="none" stroke="{VS_NUM}" stroke-width="1.1"/>'
         f'<rect x="14.5" y="108.5" width="4.5" height="4.5" fill="none" stroke="{VS_NUM}" stroke-width="1.1" transform="rotate(20 16.7 110.7)"/>',
         # tabs
         f'<rect x="26" y="29" width="{w - 26}" height="19" fill="{VS_TABS}"/>',
         f'<rect x="26" y="29" width="74" height="19" fill="{VS_BG}"/><rect x="26" y="29" width="74" height="1.5" fill="{VS_BLUE}"/>',
         f'<text x="34" y="42" font-size="9" fill="{VS_KEY}">py</text><text x="48" y="42" font-size="9" fill="#ffffff">main.py</text>'
         f'<text x="91" y="42" font-size="8" fill="{VS_NUM}">×</text>',
         f'<text x="108" y="42" font-size="9" fill="{VS_KEY}" fill-opacity=".6">py</text>'
         f'<text x="122" y="42" font-size="9" fill="{VS_NUM}">graph.py</text>',
         f'<rect x="26" y="{50 + 15 * 3}" width="{w - 26}" height="14" fill="{VS_LINE}"/>']  # current line
    for i, ln in enumerate(code):
        y = 59 + 15 * i
        o.append(f'<text x="44" y="{y}" font-size="9.5" fill="{VS_NUM if i < 3 else "#c6c6c6"}" text-anchor="end">{i + 1}</text>')
        o.append(f'<text x="52" y="{y}" font-size="9.5" fill="#d4d4d4" xml:space="preserve">{ln}</text>')
    o.append(f'<rect class="blink" x="{52 + 5.72 * 23}" y="{59 + 15 * 3 - 9}" width="1.4" height="11" fill="#aeafad"/>')
    # terminal panel
    o.append(f'<line x1="26" y1="117.5" x2="{w}" y2="117.5" stroke="#3c3c3c"/>')
    o.append(f'<text x="34" y="130" font-size="8" fill="{VS_NUM}" letter-spacing=".6">PROBLEMS</text>'
             f'<text x="90" y="130" font-size="8" fill="#e7e7e7" letter-spacing=".6">TERMINAL</text>'
             f'<rect x="90" y="133" width="41" height="1" fill="#e7e7e7"/>')
    o.append(f'<text x="34" y="147" font-size="8.5" fill="#cccccc" xml:space="preserve">'
             f'<tspan fill="{VS_TYPE}">bouncer</tspan> $ uvicorn main:app --reload</text>')
    o.append(f'<text x="34" y="160" font-size="8.5" fill="#cccccc" xml:space="preserve">'
             f'<tspan fill="#23d18b">INFO</tspan>:  Uvicorn running on <tspan fill="{VS_CONST}">http://127.0.0.1:8000</tspan></text>')
    o.append(f'<text x="34" y="173" font-size="8.5" fill="#cccccc" xml:space="preserve">'
             f'<tspan fill="#23d18b">INFO</tspan>:  Application startup complete.</text>')
    o.append(f'<text x="34" y="186" font-size="8.5" fill="{VS_TYPE}">bouncer <tspan fill="#cccccc">$</tspan></text>'
             f'<rect class="blink" x="85" y="178" width="5" height="10" fill="#cccccc"/>')
    # status bar, rounded at the bottom like the window
    o.append(f'<path d="M0 {bar} h{w} v5 a10 10 0 0 1 -10 10 h-{w - 20} a10 10 0 0 1 -10 -10 z" fill="{VS_BLUE}"/>')
    o.append(f'<text x="10" y="{bar + 10.5}" font-size="8" fill="#ffffff">⎇ main*  ⊗ 0 ⚠ 0</text>'
             f'<text x="{w - 10}" y="{bar + 10.5}" font-size="8" fill="#ffffff" text-anchor="end">'
             f'Ln 4, Col 24   UTF-8   Python 3.12</text>')
    return window("coding", "main.py — bouncer", "".join(o))


BOOKS = [  # (title, author and genre, the review: first line sits after the stars)
    ("As Long As the Lemon Trees Grow", "Zoulfa Katouh · war fiction, Syria", ["incredible."]),
    ("Mornings in Jenin", "Susan Abulhawa · historical fiction", ["heart-wrenching.", "Palestine, pre-Nakba to the 2000s."]),
    ("Poisoner in Chief", "Stephen Kinzer · nonfiction", ["a glimpse into", "the CIA's shady world."]),
]
# the Goodreads page: cream paper, brown ink, orange stars
GR_PAGE, GR_BROWN, GR_INK, GR_MUTED, GR_STAR, GR_LINE = "#f4f1ea", "#382110", "#333333", "#767676", "#e87400", "#dcd6cc"


def reading():
    """A browser with Goodreads open on the read shelf."""
    _, _, w, h, _ = LAYOUT["reading"]
    o = [f'<rect x="8" y="34" width="{w - 16}" height="15" rx="7.5" fill="#161a20" stroke="{EDGE}"/>',
         f'<path d="M17 39.5 v-1.5 a2.5 2.5 0 0 1 5 0 v1.5 M15.8 39.5 h7.4 v5 h-7.4 z" fill="none" stroke="{MUTED}" stroke-width=".9"/>',
         f'<text x="28" y="44.5" font-size="8.5" fill="{MUTED}">goodreads.com/review/list?shelf=<tspan fill="{TEXT}">read</tspan></text>',
         f'<rect x="6" y="55" width="{w - 12}" height="{h - 61}" rx="4" fill="{GR_PAGE}"/>',
         f'<text x="16" y="72" font-size="13" style="font-family:{SERIF}" fill="{GR_BROWN}">good<tspan font-weight="700">reads</tspan></text>',
         f'<text x="{w - 16}" y="71" font-size="8" style="font-family:{SANS}" fill="{GR_MUTED}" text-anchor="end">My Books</text>',
         f'<line x1="6" y1="79.5" x2="{w - 6}" y2="79.5" stroke="{GR_LINE}"/>',
         f'<text x="16" y="93" font-size="8.5" font-weight="700" style="font-family:{SANS}" fill="{GR_BROWN}">'
         f'Read <tspan font-weight="400" fill="{GR_MUTED}">({len(BOOKS)})</tspan></text>']
    y = 101
    for i, (title, by, take) in enumerate(BOOKS):
        col = SPINES[i * 3][2]
        rows = 3 + len(take) - 1
        o.append(f'<rect x="16" y="{y}" width="20" height="30" rx="1.5" fill="{col}" fill-opacity=".9"/>'
                 f'<rect x="16" y="{y}" width="3" height="30" fill="#000" fill-opacity=".18"/>')
        o.append(f'<text x="44" y="{y + 8}" font-size="9.5" font-weight="700" style="font-family:{SERIF}" fill="{GR_INK}">{esc(title)}</text>')
        o.append(f'<text x="44" y="{y + 19}" font-size="7.5" style="font-family:{SANS}" fill="{GR_MUTED}">by {esc(by)}</text>')
        o.append(f'<text x="44" y="{y + 30}" font-size="8" style="font-family:{SANS}" fill="{GR_STAR}">★★★★★</text>')
        for j, line in enumerate(take):
            o.append(f'<text x="{44 + (40 if j == 0 else 0)}" y="{y + 30 + 10 * j}" font-size="8" font-style="italic" '
                     f'style="font-family:{SANS}" fill="{GR_INK}">{esc(line)}</text>')
        y += 10 * rows + 12
        if i < len(BOOKS) - 1:
            o.append(f'<line x1="16" y1="{y - 5.5}" x2="{w - 16}" y2="{y - 5.5}" stroke="{GR_LINE}"/>')
    return window("reading", "Goodreads | My Books", "".join(o))


def cha():
    x, y, w, h, rot = LAYOUT["cha"]
    o = [f'<rect width="{w}" height="{h}" rx="4" fill="{PAPER}" filter="url(#sh)"/>',
         f'<rect x="{w / 2 - 36}" y="-8" width="72" height="18" fill="#ffffff" fill-opacity=".22" transform="rotate(-3 {w / 2} 0)"/>',
         f'<text x="20" y="44" font-size="22" font-weight="800" font-family="{SANS}" fill="{INK}">lebu-cha</text>']
    for i, ln in enumerate(RECIPE):
        yy = 76 + 22 * i
        o.append(f'<text x="20" y="{yy}" font-size="12" fill="{INK}" xml:space="preserve">'
                 f'<tspan fill="{INK}" fill-opacity=".45">–  </tspan>{esc(ln)}</text>')
    mug = (f'<g transform="translate({w - 44} 22)" fill="none" stroke="{INK}" stroke-width="1.6" '
           f'stroke-linecap="round" stroke-linejoin="round">'
           f'<path d="M0 8 H20 V18 a8 8 0 0 1 -8 8 H8 a8 8 0 0 1 -8 -8 Z"/><path d="M20 11 h3 a4 4 0 0 1 0 8 h-3"/>'
           f'<path class="steam" d="M6 4 q-3 -3 0 -7"/><path class="steam b" d="M13 4 q-3 -3 0 -7"/></g>')
    o.append(mug)
    return (f'<g class="mz mz-cha"><g transform="translate({x} {y}) rotate({rot} {w / 2} {h / 2})">'
            f'<g class="in" style="animation-delay:{0.15 * ORDER.index("cha"):.2f}s">'
            f'<g class="w" style="animation-delay:{SPOT["cha"]}s">{"".join(o)}'
            f'<rect class="frame" width="{w}" height="{h}" rx="4" fill="none" stroke="{PAPER}" stroke-opacity="0" '
            f'style="animation-delay:{SPOT["cha"]}s"/></g></g></g></g>')


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
    """A to-do app. Done ones get struck through, like in every to-do app."""
    _, _, w, h, _ = LAYOUT["decisions"]
    n_done = sum(d for d, _ in TODOS)
    o = [f'<text x="16" y="54" font-size="14" font-weight="700" fill="#ffffff" style="font-family:{SANS}">Tonight</text>',
         f'<text x="{w - 16}" y="54" font-size="9" fill="{MUTED}" text-anchor="end">{n_done} of {len(TODOS)} done</text>',
         f'<text x="16" y="68" font-size="8.5" fill="{DIM}">due: 2:00 a.m. · overdue</text>']
    for i, (done, text) in enumerate(TODOS):
        y = 89 + 21 * i
        if done:
            o.append(f'<circle cx="22" cy="{y - 3.5}" r="5.5" fill="{AMBER}"/>'
                     f'<path d="M19.4 {y - 3.6} l1.8 1.9 l3.4 -3.9" fill="none" stroke="#2a1d05" stroke-width="1.4" '
                     f'stroke-linecap="round" stroke-linejoin="round"/>')
            o.append(f'<text x="35" y="{y}" font-size="10" fill="{MUTED}" text-decoration="line-through">{esc(text)}</text>')
        else:
            o.append(f'<circle cx="22" cy="{y - 3.5}" r="5.5" fill="none" stroke="{MUTED}" stroke-width="1.2"/>')
            o.append(f'<text x="35" y="{y}" font-size="10" fill="{TEXT}">{esc(text)}</text>')
    o.append(f'<line x1="14" y1="{h - 26.5}" x2="{w - 14}" y2="{h - 26.5}" stroke="#1e2229"/>')
    o.append(f'<text x="16" y="{h - 11}" font-size="10" fill="{AMBER}">+ <tspan fill="{MUTED}">add a task</tspan></text>')
    return window("decisions", "To Do", "".join(o))


def tabs():
    o = [f'<g class="mz mz-tabs"><g transform="translate(24 536) rotate(.4 298 22)"><rect width="596" height="44" rx="10" fill="{CARD}" '
         f'stroke="{EDGE}" filter="url(#sh)"/>']
    for i in range(17):
        x = 12 + i * 33.5
        cls = "tab lit" if i in LIT_TABS else "tab"
        st = f' style="animation-delay:{LIT_TABS[i]}s"' if i in LIT_TABS else ""
        o.append(f'<rect class="{cls}" x="{x}" y="10" width="30" height="24" rx="6"{st}/>')
        o.append(f'<circle cx="{x + 15}" cy="22" r="2.6" fill="{DIM}" fill-opacity=".8"/>')
    o.append("</g></g>")
    return "".join(o)


def dock():
    w = 30 * len(DOCK) - 8 + 20
    o = [f'<rect x="{DOCK_X - 10}" y="{DOCK_Y}" width="{w}" height="30" rx="9" fill="{CARD}" stroke="{EDGE}"/>']
    for i, k in enumerate(DOCK):
        x = DOCK_X + 30 * i
        o.append(f'<rect x="{x}" y="{DOCK_Y + 5}" width="22" height="16" rx="3" fill="#161a20" stroke="{EDGE}"/>'
                 f'<rect x="{x + 4}" y="{DOCK_Y + 9}" width="9" height="2.5" rx="1" fill="{DOCK_COLOR[k]}" fill-opacity=".8"/>'
                 f'<rect x="{x + 4}" y="{DOCK_Y + 14}" width="14" height="2" rx="1" fill="{DIM}"/>'
                 f'<circle class="docked" cx="{x + 11}" cy="{DOCK_Y + 25.5}" r="1.3" fill="{AMBER}" '
                 f'style="animation-delay:{0.08 * i:.2f}s"/>')
    return "".join(o)


def away_css():
    """Minimize into the dock, hold, come back. Once. Each window flies to its own dock slot."""
    out = []
    for i, k in enumerate(DOCK):
        x, y, w, h = BOUNDS[k]
        dx = DOCK_X + 30 * i + 11 - (x + w / 2)
        dy = DOCK_Y + 21 - (y + h)
        go, back = MINIMIZE + 0.08 * i, RESTORE + 0.08 * i
        away = f"transform: translate({dx:.1f}px, {dy:.1f}px) scale(.03); opacity: 0;"
        out.append(f"  .mz-{k} {{ animation: mz-{k} {ONCE}s ease-in-out both; }}\n"
                   f"  @keyframes mz-{k} {{ 0%, {once(go)} {{ transform: none; opacity: 1; }} "
                   f"{once(go + GONE)}, {once(back)} {{ {away} }} {once(back + GONE)}, 100% {{ transform: none; opacity: 1; }} }}")
    return "\n".join(out)


def cursor_css():
    """Visits each window on the tour; steps aside while everything is minimized."""
    steps = [f"0% {{ transform: translate({CURSOR[0][0]}px, {CURSOR[0][1]}px); }}"]
    for i, k in enumerate(ORDER):
        t = SPOT[k]
        steps.append(f"{pct(t)}, {pct(t + 2.9)} {{ transform: translate({CURSOR[i][0]}px, {CURSOR[i][1]}px); }}")
    steps.append(f"100% {{ transform: translate({CURSOR[0][0]}px, {CURSOR[0][1]}px); }}")
    return ("  .cursor { animation: roam %ss ease-in-out infinite; }\n  @keyframes roam {\n    %s }\n"
            "  .aside { animation: aside %ss ease both; }\n"
            "  @keyframes aside { 0%%, %s { opacity: 1; } %s, %s { opacity: 0; } %s, 100%% { opacity: 1; } }"
            % (T, "\n    ".join(steps), ONCE, once(MINIMIZE), once(MINIMIZE + .3), once(RESTORE + GONE), once(RESTORE + GONE + .4)))


def css():
    return f"""<style>
  text {{ font-family: {MONO}; }}
  .in {{ animation: appear .6s ease-out both; }}
  @keyframes appear {{ from {{ opacity: 0; }} }}
  .w {{ animation: pick {T}s ease infinite backwards; }}
  @keyframes pick {{ 0% {{ transform: translateY(0); }} {pct(.36)} {{ transform: translateY(-6px); }} {pct(3.74)} {{ transform: translateY(-6px); }}
                    {pct(4)}, 100% {{ transform: translateY(0); }} }}
  .frame {{ animation: lit {T}s ease infinite backwards; }}
  @keyframes lit {{ 0% {{ stroke: {EDGE}; }} {pct(.36)} {{ stroke: {AMBER}; stroke-opacity: 1; }} {pct(3.74)} {{ stroke: {AMBER}; stroke-opacity: 1; }}
                   {pct(4)}, 100% {{ stroke: {EDGE}; }} }}
  .tab {{ fill: #161a20; stroke: {EDGE}; }}
  .tab.lit {{ animation: tab {T}s ease infinite backwards; }}
  @keyframes tab {{ 0% {{ fill: #161a20; stroke: {EDGE}; }} {pct(.24)} {{ fill: {AMBER}; stroke: {AMBER}; }} {pct(7.68)} {{ fill: {AMBER}; stroke: {AMBER}; }}
                   {pct(8)}, 100% {{ fill: #161a20; stroke: {EDGE}; }} }}
{cursor_css()}
  .mz {{ transform-box: fill-box; transform-origin: 50% 100%; }}
{away_css()}
  .docked {{ opacity: 0; animation: docked {ONCE}s ease both; }}
  @keyframes docked {{ 0%, {once(MINIMIZE + GONE - .2)} {{ opacity: 0; }} {once(MINIMIZE + GONE)}, {once(RESTORE)} {{ opacity: 1; }}
                      {once(RESTORE + .3)}, 100% {{ opacity: 0; }} }}
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
         f'aria-label="Ayesha\'s messy desktop. VS Code with the Bouncer API open and a dev server running in the terminal. Goodreads open on her read shelf, five stars each: As Long As the Lemon Trees Grow by Zoulfa Katouh, war fiction set in Syria, Mornings in Jenin by Susan Abulhawa, historical fiction about Palestine from before the Nakba to the 2000s, and Poisoner in Chief by Stephen Kinzer, nonfiction about the CIA. '
         f'A recipe for lebu-cha: 1 cup water, 1 and a half spoons sugar or honey, 1 cardamom, a pinch of cinnamon, a handful of mint, some squeezed lime. '
         f'A machine learning notebook with a loss curve. A log of nuclear accidents: Chernobyl, Fukushima, Kyshtym, Three Mile Island, Windscale, Goiania, Tokaimura. '
         f'A to-do app: tonight, 4 of 6 done; sleep is not one of them. A row of browser tabs. '
         f'A few seconds in, she notices you and minimizes everything into the dock, leaving a clean desktop, then opens it all again.">',
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
         dock(),
         coding(), reading(), cha(), ml(), nuclear(), decisions(), tabs(),
         f'<g class="aside"><g class="cursor"><path d="M0 0 L0 15 L4 11.5 L7 18 L9.5 17 L6.5 10.5 L11.5 10.5 Z" fill="#ffffff" '
         f'stroke="#000" stroke-width="1" stroke-linejoin="round"/></g></g>',
         '</g>',
         f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="{EDGE}"/>',
         '</svg>']
    with open("assets/desktop.svg", "w", encoding="utf-8") as f:
        f.write("\n".join(o))
    print("wrote assets/desktop.svg")


if __name__ == "__main__":
    main()
