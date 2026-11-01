#!/usr/bin/env python3
"""
Draws the README's section headers, the status report and the "currently open" list
as SVG cards, so they all share one look. Standard library only.

  python scripts/sections.py
"""
import html

MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"
SANS = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
W = 880
CARD, EDGE, AMBER, TEXT, MUTED = "#0f1216", "#232830", "#f0b44c", "#e4e2dd", "#6f7680"

HEADERS = [
    ("built", "Things I've built"),
    ("rabbit-hole", "The current rabbit hole"),
    ("toolbox", "My toolbox"),
    ("contributions", "My contributions"),
    ("status", "Status report"),
    ("open", "Currently open"),
    ("still-here", "You're still here"),
]


def svg(w, h, body, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{html.escape(label)}">'
            f'<style>.m{{font-family:{MONO}}}.s{{font-family:{SANS}}}</style>{body}</svg>')


def card(x, y, w, h, r=12):
    return f'<rect x="{x + .5}" y="{y + .5}" width="{w - 1}" height="{h - 1}" rx="{r}" fill="{CARD}" stroke="{EDGE}"/>'


def header(i, title):
    h = 84
    body = (
        '<defs><linearGradient id="glow" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{AMBER}" stop-opacity=".16"/><stop offset=".55" stop-color="{AMBER}" stop-opacity="0"/>'
        '</linearGradient></defs>'
        + card(0, 0, W, h, 14)
        + f'<rect x="1" y="1" width="{W - 2}" height="{h - 2}" rx="13" fill="url(#glow)"/>'
        + f'<rect x="0" y="22" width="5" height="{h - 44}" rx="2.5" fill="{AMBER}"/>'
        + f'<text class="m" x="{W - 28}" y="{h - 16}" font-size="64" font-weight="700" fill="{TEXT}" fill-opacity=".07" '
          f'text-anchor="end">{i:02d}</text>'
        + f'<text class="m" x="36" y="30" font-size="11" letter-spacing="2.4" font-weight="700" fill="{AMBER}">{i:02d}</text>'
        + f'<text class="s" x="36" y="64" font-size="34" font-weight="800" letter-spacing="-.6" fill="#ffffff">{html.escape(title)}</text>'
    )
    return svg(W, h, body, title)


def rows(items, y0, row_h, label=None):
    """A list card: optional small label, then one row per item with a divider between."""
    top = 30 if label else 10
    h = top + len(items) * row_h + 6
    o = [card(0, y0, W, h)]
    if label:
        o.append(f'<text class="m" x="24" y="{y0 + 21}" font-size="10" letter-spacing="1.6" fill="{MUTED}">{label}</text>')
    for k, (tag, text, accent, *extra) in enumerate(items):
        cy = y0 + top + k * row_h + row_h / 2
        if k:
            o.append(f'<line x1="24" y1="{cy - row_h / 2:.0f}" x2="{W - 24}" y2="{cy - row_h / 2:.0f}" stroke="{EDGE}"/>')
        if accent:
            o.append(f'<rect x="24" y="{cy - 11:.0f}" width="84" height="22" rx="11" fill="{AMBER}" fill-opacity=".14" stroke="{AMBER}" stroke-opacity=".6"/>')
            o.append(f'<text class="m" x="66" y="{cy + 4:.0f}" font-size="10.5" font-weight="700" fill="{AMBER}" text-anchor="middle">{tag}</text>')
        else:
            o.append(f'<rect x="24" y="{cy - 11:.0f}" width="84" height="22" rx="11" fill="none" stroke="{EDGE}"/>')
            o.append(f'<text class="m" x="66" y="{cy + 4:.0f}" font-size="10.5" font-weight="700" fill="{MUTED}" text-anchor="middle">{tag}</text>')
        if extra:
            o.append(f'<text class="m" x="{W - 24}" y="{cy + 4:.0f}" font-size="12" fill="{AMBER}" text-anchor="end">{html.escape(extra[0])}</text>')
        o.append(f'<text class="s" x="132" y="{cy + 5:.0f}" font-size="15" fill="{TEXT}">{html.escape(text)}</text>')
    return "".join(o), h


def status():
    stats = [("17+", "REPOSITORIES"), ("3×", "HACKATHON FINALS"), ("1×", "TOP 100")]
    tw = (W - 2 * 16) / 3
    o = []
    for k, (n, lab) in enumerate(stats):
        x = k * (tw + 16)
        o.append(card(x, 0, tw, 92))
        o.append(f'<text class="s" x="{x + 24:.0f}" y="52" font-size="36" font-weight="700" fill="{TEXT}">{n}</text>')
        o.append(f'<text class="m" x="{x + 24:.0f}" y="76" font-size="10" letter-spacing="1.6" fill="{MUTED}">{lab}</text>')
    items = [("TOP 100", "Solvio AI Hackathon 2025", True),
             ("FINALIST", "CodeSprint — Inter-IUT Hackathon", False, "top 14 among top 50"),
             ("FINALIST", "SUST CSE Carnival Hackathon", False, "top 50 among 450+ submissions"),
             ("FINALIST", "IUT 12th ICT Fest — Agentic AI Hackathon", False, "top 20 among 700+ submissions")]
    body, h = rows(items, 108, 40, "ACHIEVEMENTS.LOG")
    return svg(W, 108 + h + 2, "".join(o) + body, "Status report: 17+ repositories, 3 hackathon finals, 1 top 100")


def current():
    items = [("01", "Machine learning fundamentals", False),
             ("02", "RAG / LLM rabbit holes", False),
             ("03", "One extremely fast-paced thriller", False)]
    body, h = rows(items, 0, 44, None)
    return svg(W, h + 2, body, "Currently open: machine learning fundamentals, RAG / LLM rabbit holes, one extremely fast-paced thriller")


def main():
    for i, (slug, title) in enumerate(HEADERS, 1):
        with open(f"assets/h-{slug}.svg", "w", encoding="utf-8") as f:
            f.write(header(i, title))
    with open("assets/status.svg", "w", encoding="utf-8") as f:
        f.write(status())
    with open("assets/open.svg", "w", encoding="utf-8") as f:
        f.write(current())
    print("wrote section assets")


if __name__ == "__main__":
    main()
