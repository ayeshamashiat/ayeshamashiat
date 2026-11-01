#!/usr/bin/env python3
"""
Turns a GitHub contribution calendar into Pokéballs in tall grass.

Every day you contributed is a Pokéball; the busier the day, the fancier the ball.
Days with nothing are just grass.

Usage
  GITHUB_TOKEN=... python scripts/pokeballs.py ayeshamashiat
  python scripts/pokeballs.py --demo            # fake data, for previews

Writes assets/pokeballs.svg (change with --out). Standard library only.
"""
import argparse
import datetime as dt
import hashlib
import html
import json
import os
import random
import urllib.request

W, H = 880, 262
CELL, PITCH = 13, 15
GRID_Y0 = 92

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
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
    return [
        (dt.date.fromisoformat(d["date"]), d["contributionCount"])
        for w in cal["weeks"]
        for d in w["contributionDays"]
    ]


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
        n = 0
        if rng.random() < (0.85 if near else 0.32):
            n = rng.randint(1, 4) + (rng.randint(3, 14) if near and rng.random() < 0.5 else 0)
        days.append((d, n))
        d += dt.timedelta(days=1)
    return days


# ---------------------------------------------------------------- helpers
def h01(*parts):
    """Stable pseudo-random number in [0, 1) from any inputs."""
    s = hashlib.md5("|".join(map(str, parts)).encode()).hexdigest()
    return int(s[:8], 16) / 0xFFFFFFFF


def cuts(counts):
    """Upper bounds of the Poké, Great and Ultra tiers (quartiles of non-zero days)."""
    nz = sorted(c for c in counts if c > 0)
    if not nz:
        return [0, 0, 0]
    return [nz[int(len(nz) * f)] if f < 1 else nz[-1] for f in (0.25, 0.5, 0.75)]


def levels(counts):
    q = cuts(counts)
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


def current_streak(days):
    seq = list(days)
    if seq and seq[-1][1] == 0:  # today not done yet doesn't break it
        seq = seq[:-1]
    n = 0
    for _, c in reversed(seq):
        if c == 0:
            break
        n += 1
    return n


# ---------------------------------------------------------------- render
BALLS = {  # level -> (top, bottom, band, button)
    1: ("#e74c3c", "#f4f4f4", "#2b2b2b", "#f4f4f4"),
    2: ("#3b82d6", "#f4f4f4", "#2b2b2b", "#f4f4f4"),
    3: ("#f4c20d", "#2b2b2b", "#f4f4f4", "#f4c20d"),
    4: ("#9b59b6", "#9b59b6", "#f4f4f4", "#ff6fae"),
}


def ball_symbol(level):
    top, bot, band, btn = BALLS[level]
    r = CELL / 2
    return (
        f'<symbol id="b{level}" viewBox="0 0 {CELL} {CELL}" overflow="visible">'
        f'<circle cx="{r}" cy="{r}" r="{r}" fill="{bot}"/>'
        f'<path d="M0 {r} A{r} {r} 0 0 1 {CELL} {r} Z" fill="{top}"/>'
        f'<rect x="0" y="{r - 1}" width="{CELL}" height="2" fill="{band}"/>'
        f'<circle cx="{r}" cy="{r}" r="2.3" fill="{band}"/><circle cx="{r}" cy="{r}" r="1.2" fill="{btn}"/>'
        f'<circle cx="{r}" cy="{r}" r="{r - .3}" fill="none" stroke="#1a1a1a" stroke-width=".7"/>'
        f'</symbol>'
    )


def render(days, login):
    days = sorted(days)
    first = days[0][0]
    offset = (first.weekday() + 1) % 7  # GitHub weeks start on Sunday
    nweeks = (len(days) + offset + 6) // 7
    x0 = (W - nweeks * PITCH + (PITCH - CELL)) / 2
    gx1 = x0 + nweeks * PITCH - (PITCH - CELL)
    lvl = levels([n for _, n in days])

    total = sum(n for _, n in days)
    longest = max((len(s) for s in streaks(days)), default=max((1 for _, n in days if n), default=0))
    cs = current_streak(days)
    bright_d, bright_n = max(days, key=lambda x: x[1])

    o = []
    a = o.append
    a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
      f'role="img" aria-label="{html.escape(login)}\'s GitHub contributions: {total:,} in the last year, '
      f'longest streak {longest} days">')
    a("""<style>
  text { font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace; }
  .sway { animation: sway 4s ease-in-out var(--o, 0s) infinite; }
  @keyframes sway { 0%, 100% { opacity: .55; } 50% { opacity: .9; } }
  @media (prefers-reduced-motion: reduce) { * { animation: none !important; } }
</style>""")
    a("<defs>")
    a('<symbol id="g" viewBox="0 0 13 13" overflow="visible">'
      '<path d="M2 11 L3.2 5 L4.6 11 M5.8 11 L6.5 3.5 L7.4 11 M8.6 11 L9.8 5.5 L11 11" '
      'fill="none" stroke="#3f7d4e" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></symbol>')
    for k in BALLS:
        a(ball_symbol(k))
    a('<pattern id="tile" width="30" height="30" patternUnits="userSpaceOnUse">'
      '<rect width="30" height="30" fill="#1d3b2a"/><rect width="15" height="15" fill="#21432f"/>'
      '<rect x="15" y="15" width="15" height="15" fill="#21432f"/></pattern>')
    a(f'<clipPath id="frame"><rect width="{W}" height="{H}" rx="14"/></clipPath>')
    a("</defs>")
    a('<g clip-path="url(#frame)">')
    a(f'<rect width="{W}" height="{H}" fill="#14261c"/>')

    # header
    a(f'<rect width="{W}" height="64" fill="#101a14"/><rect y="64" width="{W}" height="2" fill="#2e5a3d"/>')
    a('<text x="32" y="30" font-size="14" font-weight="700" fill="#f4f4f4">'
      '<tspan fill="#e74c3c">●</tspan> my contributions</text>')
    a('<text x="32" y="50" font-size="10.5" fill="#7fa88c">one ball for every day I pushed something. '
      'empty grass is a day I didn\'t.</text>')

    # the grass field
    a(f'<rect x="{x0 - 10:.1f}" y="{GRID_Y0 - 10}" width="{gx1 - x0 + 20:.1f}" height="{7 * PITCH + 5}" '
      f'rx="6" fill="url(#tile)"/>')
    for i, (d, n) in enumerate(days):
        col, row = divmod(i + offset, 7)
        x, y = x0 + col * PITCH, GRID_Y0 + row * PITCH
        L = lvl(n)
        if L == 0:
            a(f'<use class="sway" href="#g" x="{x:.1f}" y="{y}" width="{CELL}" height="{CELL}" '
              f'style="--o:{-h01(d, "s") * 4:.1f}s"/>')
            continue
        tip = f"<title>{d.strftime('%a %d %b %Y')}: {n} contribution{'s' if n != 1 else ''}</title>"
        a(f'<use href="#b{L}" x="{x:.1f}" y="{y}" width="{CELL}" height="{CELL}">{tip}</use>')

    # legend: fewer -> more, with the actual counts
    q = cuts([n for _, n in days])
    lo = [1, q[0] + 1, q[1] + 1, q[2] + 1]
    hi = [q[0], q[1], q[2]]
    ranges = [f"{lo[i]}" if lo[i] >= hi[i] else f"{lo[i]}-{hi[i]}" for i in range(3)] + [f"{lo[3]}+"]
    ly = GRID_Y0 + 7 * PITCH + 16
    a(f'<text x="{x0 - 10:.1f}" y="{ly + 9}" font-size="9.5" fill="#7fa88c">contributions in a day:</text>')
    for k, rg in enumerate(ranges, 1):
        x = x0 + 150 + (k - 1) * 70
        a(f'<use href="#b{k}" x="{x:.0f}" y="{ly}" width="11" height="11"/>')
        a(f'<text x="{x + 16:.0f}" y="{ly + 9}" font-size="9.5" fill="#7fa88c">{rg}</text>')

    # footer
    fy = H - 20
    a(f'<line x1="32" y1="{fy - 24}" x2="{W - 32}" y2="{fy - 24}" stroke="#2e5a3d"/>')
    stats = (f'<tspan fill="#f4f4f4">{total:,}</tspan> contributions this year  ·  '
             f'longest streak <tspan fill="#f4f4f4">{longest}</tspan> days  ·  '
             f'busiest day <tspan fill="#f4f4f4">{bright_d.strftime("%d %b")}</tspan> ({bright_n})')
    if cs:
        stats += f'  ·  current streak <tspan fill="#f4f4f4">{cs}</tspan>'
    a(f'<text x="32" y="{fy}" font-size="11" fill="#7fa88c" xml:space="preserve">{stats}</text>')

    a("</g>")
    a(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="#2e5a3d"/>')
    a("</svg>")
    return "\n".join(o)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("login", nargs="?", default="ayeshamashiat")
    ap.add_argument("--demo", action="store_true", help="use fake data")
    ap.add_argument("--out", default="assets/pokeballs.svg")
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
