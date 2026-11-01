#!/usr/bin/env python3
"""
Turns a GitHub contribution calendar into a night sky.

Every day you contributed is a star (brighter = busier).
Streaks of 3+ days in a row get joined into constellations,
and the longest ones get names they probably deserve.

Usage
  GITHUB_TOKEN=... python scripts/constellation.py ayeshamashiat
  python scripts/constellation.py --demo            # fake data, for previews

Writes assets/constellation.svg (change with --out). Standard library only.
"""
import argparse
import datetime as dt
import hashlib
import html
import json
import math
import os
import random
import urllib.request

W, H = 880, 330
SKY_X0, SKY_X1 = 36, 844
SKY_Y0, SKY_Y1 = 84, 262

NAMES = [
    "Ursa Deadline",
    "Orion's Merge Conflict",
    "The Great Refactor",
    "Cassiopeia.js",
    "The Big Dipper (into prod)",
    "Draco Debuggus",
    "Canis Major Bugfix",
    "The Hackathon Cluster",
    "Lyra, Lint Errors",
    "Gemini: Works On My Machine",
    "Pegasus Hotfix",
    "Scorpius Segfault",
    "Taurus 500",
    "Andromeda, Abandoned",
]

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}"""


# ---------------------------------------------------------------- data
def fetch(login, token):
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(f"GitHub said no: {data['errors']}")
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [
        (dt.date.fromisoformat(d["date"]), d["contributionCount"])
        for w in cal["weeks"]
        for d in w["contributionDays"]
    ]
    return days


def demo_days():
    rng = random.Random(7)
    end = dt.date.today()
    start = end - dt.timedelta(days=370)
    start -= dt.timedelta(days=(start.weekday() + 1) % 7)  # back to a Sunday
    bursts = [rng.randint(0, 360) for _ in range(6)]
    days, d = [], start
    while d <= end:
        i = (d - start).days
        near = any(abs(i - b) < rng.randint(4, 11) for b in bursts)
        p = 0.85 if near else 0.32
        n = 0
        if rng.random() < p:
            n = rng.randint(1, 4) + (rng.randint(3, 14) if near and rng.random() < 0.5 else 0)
        days.append((d, n))
        d += dt.timedelta(days=1)
    return days


# ---------------------------------------------------------------- helpers
def h01(*parts):
    """Stable pseudo-random number in [0, 1) from any inputs."""
    s = hashlib.md5("|".join(map(str, parts)).encode()).hexdigest()
    return int(s[:8], 16) / 0xFFFFFFFF


def levels(counts):
    nz = sorted(c for c in counts if c > 0)
    if not nz:
        return lambda c: 0
    q = [nz[int(len(nz) * f) - (1 if f == 1 else 0)] for f in (0.25, 0.5, 0.75)]
    return lambda c: 0 if c == 0 else 1 if c <= q[0] else 2 if c <= q[1] else 3 if c <= q[2] else 4


def streaks(days):
    out, cur = [], []
    for d, n in days:
        if n > 0:
            cur.append(d)
        else:
            if len(cur) >= 3:
                out.append(cur)
            cur = []
    if len(cur) >= 3:
        out.append(cur)
    return out


def spanning_tree(pts, max_edge):
    """Prim's minimum spanning tree over points; returns edges shorter than max_edge."""
    if len(pts) < 2:
        return []
    inside, edges = {0}, []
    best = {i: (math.dist(pts[0], pts[i]), 0) for i in range(1, len(pts))}
    while best:
        j = min(best, key=lambda i: best[i][0])
        d, i = best.pop(j)
        inside.add(j)
        if d <= max_edge:
            edges.append((pts[i], pts[j]))
        for k in best:
            dk = math.dist(pts[j], pts[k])
            if dk < best[k][0]:
                best[k] = (dk, j)
    return edges


def current_streak(days):
    n = 0
    seq = list(days)
    if seq and seq[-1][1] == 0:  # today not done yet doesn't break it
        seq = seq[:-1]
    for _, c in reversed(seq):
        if c == 0:
            break
        n += 1
    return n


def moon(today):
    """Phase in [0,1): 0 new, .5 full."""
    ref = dt.datetime(2000, 1, 6, 18, 14)
    age = (dt.datetime.combine(today, dt.time(12)) - ref).total_seconds() / 86400
    return (age % 29.530588) / 29.530588


def moon_name(p):
    names = ["new moon", "waxing crescent", "first quarter", "waxing gibbous",
             "full moon", "waning gibbous", "last quarter", "waning crescent"]
    return names[int((p * 8) + 0.5) % 8]


def moon_path(cx, cy, r, p):
    rx = r * abs(math.cos(2 * math.pi * p))
    if p < 0.5:
        outer, inner = 1, (0 if p < 0.25 else 1)
    else:
        outer, inner = 0, (1 if p > 0.75 else 0)
    return (f"M{cx:.1f} {cy - r:.1f} A{r} {r} 0 0 {outer} {cx:.1f} {cy + r:.1f} "
            f"A{rx:.2f} {r} 0 0 {inner} {cx:.1f} {cy - r:.1f} Z")


def sparkle(x, y, s):
    k = s * 0.22
    return (f"M{x:.1f} {y - s:.1f} Q{x + k:.1f} {y - k:.1f} {x + s:.1f} {y:.1f} "
            f"Q{x + k:.1f} {y + k:.1f} {x:.1f} {y + s:.1f} Q{x - k:.1f} {y + k:.1f} {x - s:.1f} {y:.1f} "
            f"Q{x - k:.1f} {y - k:.1f} {x:.1f} {y - s:.1f} Z")


# ---------------------------------------------------------------- render
def render(days, login):
    days = sorted(days)
    first = days[0][0]
    offset = (first.weekday() + 1) % 7  # GitHub weeks start on Sunday
    nweeks = (len(days) + offset + 6) // 7
    sx = (SKY_X1 - SKY_X0) / max(nweeks - 1, 1)
    sy = (SKY_Y1 - SKY_Y0) / 6
    lvl = levels([n for _, n in days])

    pos = {}
    for i, (d, _) in enumerate(days):
        col, row = divmod(i + offset, 7)
        jx = (h01(d, "x") - 0.5) * sx * 0.9
        jy = (h01(d, "y") - 0.5) * sy * 0.75
        pos[d] = (SKY_X0 + col * sx + jx, SKY_Y0 + row * sy + jy)

    total = sum(n for _, n in days)
    st = streaks(days)
    longest = max((len(s) for s in st), default=max((1 for _, n in days if n), default=0))
    bright_d, bright_n = max(days, key=lambda x: x[1])
    top3 = {d for d, n in sorted(days, key=lambda x: -x[1])[:3] if n > 0}
    today = days[-1][0]
    ph = moon(today)

    o = []
    a = o.append
    a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
      f'role="img" aria-label="{html.escape(login)}\'s contributions drawn as a night sky">')
    a("""<style>
  text { font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace; }
  .tw { animation: tw var(--d, 4s) ease-in-out var(--o, 0s) infinite; }
  @keyframes tw { 0%, 100% { opacity: 1; } 50% { opacity: .35; } }
  .ln { fill: none; stroke: #7aa7b8; stroke-opacity: .32; stroke-width: .8; stroke-linecap: round; stroke-linejoin: round;
        animation: draw 2.4s ease-out var(--o, 0s) both; }
  @keyframes draw { from { stroke-dashoffset: var(--l); } to { stroke-dashoffset: 0; } }
  .nm { font-size: 9px; letter-spacing: 1.6px; fill: #6f7680; text-transform: uppercase; animation: fade 1.2s ease-out var(--o, 0s) both; }
  @keyframes fade { from { opacity: 0; } }
  .shoot { animation: shoot 11s linear 3s infinite; opacity: 0; }
  @keyframes shoot {
    0% { transform: translate(0, 0); opacity: 0; }
    1% { opacity: 1; }
    6% { transform: translate(-260px, 96px); opacity: 0; }
    100% { transform: translate(-260px, 96px); opacity: 0; }
  }
  @media (prefers-reduced-motion: reduce) { * { animation: none !important; } }
</style>""")
    a("""<defs>
  <radialGradient id="ga" cx="120" cy="40" r="420" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#f0b44c" stop-opacity=".06"/><stop offset="1" stop-color="#f0b44c" stop-opacity="0"/></radialGradient>
  <radialGradient id="gb" cx="800" cy="320" r="380" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#7aa7b8" stop-opacity=".07"/><stop offset="1" stop-color="#7aa7b8" stop-opacity="0"/></radialGradient>
  <radialGradient id="halo"><stop offset="0" stop-color="#f0b44c" stop-opacity=".3"/><stop offset="1" stop-color="#f0b44c" stop-opacity="0"/></radialGradient>
  <linearGradient id="tail" x1="0" y1="1" x2="1" y2="0">
    <stop offset="0" stop-color="#e4e2dd"/><stop offset="1" stop-color="#e4e2dd" stop-opacity="0"/></linearGradient>
  <clipPath id="frame"><rect x="0" y="0" width="880" height="330" rx="14"/></clipPath>
</defs>""")
    a('<g clip-path="url(#frame)">')
    a(f'<rect width="{W}" height="{H}" fill="#08090b"/>')
    a(f'<rect width="{W}" height="{H}" fill="url(#ga)"/><rect width="{W}" height="{H}" fill="url(#gb)"/>')

    # background dust (decoration, not data)
    rng = random.Random(42)
    for _ in range(140):
        x, y = rng.uniform(8, W - 8), rng.uniform(64, H - 52)
        a(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rng.uniform(.3, .7):.2f}" fill="#e4e2dd" opacity="{rng.uniform(.05, .16):.2f}"/>')

    # header
    a('<text x="32" y="38" font-size="13" fill="#e4e2dd">'
      '<tspan fill="#f0b44c">✦ </tspan>ayesha\'s night sky</text>')
    a('<text x="32" y="56" font-size="10.5" fill="#6f7680">every star is a day I pushed something. '
      'the bright ones are days I should have been asleep.</text>')
    mx, my = 836, 40
    a(f'<circle cx="{mx}" cy="{my}" r="10" fill="#171a1f"/>')
    a(f'<path d="{moon_path(mx, my, 10, ph)}" fill="#e4e2dd" fill-opacity=".85"/>')
    a(f'<text x="{mx - 18}" y="{my + 3.5}" font-size="10" fill="#3b4048" text-anchor="end">{moon_name(ph)}</text>')

    # constellations: join each streak's stars by their nearest neighbours (a spanning tree),
    # skipping any link too long to look like it belongs
    max_edge = 2.6 * max(sx, sy * 0.8)
    for s in sorted(st, key=lambda s: s[0]):
        for (x1, y1), (x2, y2) in spanning_tree([pos[d] for d in s], max_edge):
            L = math.dist((x1, y1), (x2, y2))
            delay = 0.4 + 2.2 * (min(x1, x2) - SKY_X0) / (SKY_X1 - SKY_X0)
            a(f'<path class="ln" d="M{x1:.1f} {y1:.1f} L{x2:.1f} {y2:.1f}" stroke-dasharray="{L:.1f}" '
              f'style="--l:{L:.1f};--o:{delay:.2f}s"/>')

    # names for the 3 longest streaks
    used, placed = set(), []
    for s in sorted(st, key=lambda s: (-len(s), s[0]))[:3]:
        k = int(h01(s[0], "name") * len(NAMES))
        while k in used:
            k = (k + 1) % len(NAMES)
        used.add(k)
        label = f"{NAMES[k]} · {len(s)}d"
        half = len(label) * 3.6
        xs = [pos[d][0] for d in s]
        ys = [pos[d][1] for d in s]
        lx = min(max(sum(xs) / len(xs), 32 + half), W - 32 - half)
        ly = min(ys) - 12
        if ly < 76 or any(abs(px - lx) < half + 80 and abs(py - ly) < 14 for px, py in placed):
            ly = max(ys) + 18
        ly = min(max(ly, 76), H - 54)
        placed.append((lx, ly))
        delay = 1.4 + 2.0 * (lx - SKY_X0) / (SKY_X1 - SKY_X0)
        a(f'<text class="nm" x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" style="--o:{delay:.2f}s">'
          f'{html.escape(label)}</text>')

    # stars
    col = {1: "#7aa7b8", 2: "#c3d3d8", 3: "#f1e2c0", 4: "#f0b44c"}
    rad = {1: 1.2, 2: 1.7, 3: 2.2, 4: 2.8}
    for d, n in days:
        x, y = pos[d]
        L = lvl(n)
        if L == 0:
            a(f'<circle cx="{x:.1f}" cy="{y:.1f}" r=".6" fill="#3b4048" opacity=".55"/>')
            continue
        dur = 2.6 + h01(d, "d") * 3.2
        off = -h01(d, "o") * 5
        tip = f"<title>{d.strftime('%a %d %b %Y')}: {n} contribution{'s' if n != 1 else ''}</title>"
        if L == 4:
            a(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rad[L] * 3.4:.1f}" fill="url(#halo)"/>')
        if d in top3:
            a(f'<path class="tw" d="{sparkle(x, y, 6.5)}" fill="#f0b44c" style="--d:{dur:.1f}s;--o:{off:.1f}s">{tip}</path>')
        else:
            a(f'<circle class="tw" cx="{x:.1f}" cy="{y:.1f}" r="{rad[L]}" fill="{col[L]}" '
              f'style="--d:{dur:.1f}s;--o:{off:.1f}s">{tip}</circle>')

    # shooting star
    a('<g class="shoot"><line x1="760" y1="96" x2="800" y2="80" stroke="url(#tail)" stroke-width="1.2" stroke-linecap="round"/></g>')

    # footer
    a(f'<line x1="32" y1="{H - 44}" x2="{W - 32}" y2="{H - 44}" stroke="#1e2229"/>')
    cs = current_streak(days)
    stats = (f'<tspan fill="#e4e2dd">{total:,}</tspan> contributions  ·  '
             f'longest streak <tspan fill="#e4e2dd">{longest}</tspan> nights  ·  '
             f'brightest night <tspan fill="#f0b44c">{bright_d.strftime("%d %b")}</tspan> ({bright_n})')
    if cs:
        stats += f'  ·  current streak <tspan fill="#e4e2dd">{cs}</tspan>'
    a(f'<text x="32" y="{H - 20}" font-size="10.5" fill="#6f7680" xml:space="preserve">{stats}</text>')
    a(f'<text x="{W - 32}" y="{H - 20}" font-size="10" fill="#3b4048" text-anchor="end">'
      f'updated {today.strftime("%d %b %Y")}</text>')
    a('</g>')
    a(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="#1e2229"/>')
    a("</svg>")
    return "\n".join(o)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("login", nargs="?", default="ayeshamashiat")
    ap.add_argument("--demo", action="store_true", help="use fake data")
    ap.add_argument("--out", default="assets/constellation.svg")
    args = ap.parse_args()

    if args.demo:
        days = demo_days()
    else:
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not token:
            raise SystemExit("set GITHUB_TOKEN (or run with --demo)")
        days = fetch(args.login, token)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(render(days, args.login))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
