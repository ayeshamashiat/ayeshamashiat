#!/usr/bin/env python3
"""
Writes the README's activity section: a load-shedding street (assets/street.svg, drawn by
street.py), one building per night, lit on the nights I contributed on GitHub.

  GITHUB_TOKEN=... python scripts/activity.py ayeshamashiat
  GITHUB_TOKEN=... python scripts/activity.py --dry-run      # print it, write nothing
  python scripts/activity.py --demo --preview /tmp/street.svg  # fake data, no network

How busy each day was comes from the user's GitHub contribution calendar, the same numbers as
the graph on their profile (private contributions only as anonymous counts, if they show them
there). Release nights (fireworks) come from public, non-fork repos owned by the user.
Days are judged in Asia/Dhaka; which date a contribution lands on is GitHub's call, as on the graph.
If any request fails, nothing is written and the script exits non-zero, so a broken API
never turns into a dark street. Standard library only.
"""
import argparse
import datetime as dt
import random
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import street  # noqa: E402

try:
    from zoneinfo import ZoneInfo
    DHAKA = ZoneInfo("Asia/Dhaka")
except Exception:  # no tz database: Dhaka is UTC+6 all year, no DST
    DHAKA = dt.timezone(dt.timedelta(hours=6), "Asia/Dhaka")

ROOT = Path(__file__).resolve().parent.parent
START, END = "<!-- ACTIVITY:START -->", "<!-- ACTIVITY:END -->"

LOOKBACK_DAYS = 90     # how much fake activity --demo makes up


class DataError(Exception):
    """The data can't be trusted, so the README stays as it is."""


# ---------------------------------------------------------------- github
class GitHub:
    API = "https://api.github.com"

    def __init__(self, token=None):
        self.token = token

    def pages(self, path, params=None):
        """Yields one list per page, following Link headers."""
        url = f"{self.API}{path}?{urllib.parse.urlencode(params or {})}"
        while url:
            req = urllib.request.Request(url, headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "ayeshamashiat-profile-activity",
                **({"Authorization": f"Bearer {self.token}"} if self.token else {}),
            })
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    data = json.load(r)
                    link = r.headers.get("Link", "")
            except urllib.error.HTTPError as e:
                raise DataError(f"GET {path} failed: HTTP {e.code} {e.reason}") from e
            except (urllib.error.URLError, TimeoutError, ValueError) as e:
                raise DataError(f"GET {path} failed: {e}") from e
            if not isinstance(data, list):
                raise DataError(f"GET {path} returned {type(data).__name__}, expected a list")
            yield data
            m = re.search(r'<([^>]+)>;\s*rel="next"', link)
            url = m.group(1) if m else None

    def calendar(self, login):
        """{date: contributions} for the last year, exactly as the profile graph shows it.
        With a token, from the GraphQL API; without one, from the public graph itself."""
        if self.token:
            return calendar_from_graphql(self._graphql(CALENDAR_QUERY, {"login": login}))
        url = f"https://github.com/users/{urllib.parse.quote(login)}/contributions"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (profile-activity)"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return calendar_from_html(r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            raise DataError(f"GET {url} failed: HTTP {e.code} {e.reason}") from e
        except (urllib.error.URLError, TimeoutError) as e:
            raise DataError(f"GET {url} failed: {e}") from e

    def _graphql(self, query, variables):
        req = urllib.request.Request(f"{self.API}/graphql", json.dumps({"query": query, "variables": variables}).encode(),
                                     {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json",
                                      "User-Agent": "ayeshamashiat-profile-activity"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            raise DataError(f"GraphQL failed: HTTP {e.code} {e.reason}") from e
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            raise DataError(f"GraphQL failed: {e}") from e


CALENDAR_QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection { contributionCalendar { weeks { contributionDays { date contributionCount } } } }
  }
}"""
MIN_CALENDAR_DAYS = 300  # a year's graph has ~365; fewer means GitHub sent something else


def calendar_from_graphql(data):
    if data.get("errors") or not (data.get("data") or {}).get("user"):
        raise DataError(f"GraphQL calendar failed: {data.get('errors') or 'no such user'}")
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = {dt.date.fromisoformat(d["date"]): int(d["contributionCount"]) for w in weeks for d in w["contributionDays"]}
    if len(days) < MIN_CALENDAR_DAYS:
        raise DataError(f"contribution calendar has only {len(days)} days")
    return days


def calendar_from_html(page):
    """The graph's cells carry their date and an id; a tooltip per id says the count."""
    ids = re.findall(r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*?\bid="([^"]+)"', page)
    tips = dict(re.findall(r'<tool-tip[^>]*?\bfor="([^"]+)"[^>]*>\s*([^<]*?)\s*</tool-tip>', page))
    days = {}
    for date, cell in ids:
        tip = tips.get(cell)
        if tip is None:
            raise DataError(f"contribution graph cell {date} has no count")
        m = re.match(r"([\d,]+) contributions?\b", tip)
        if not m and not tip.startswith("No contributions"):
            raise DataError(f"can't read contribution count {tip!r}")
        days[dt.date.fromisoformat(date)] = int(m.group(1).replace(",", "")) if m else 0
    if len(days) < MIN_CALENDAR_DAYS:
        raise DataError(f"contribution graph has only {len(days)} days; GitHub may have changed the page")
    return days


@dataclass
class Event:
    repo: str
    when: dt.datetime      # aware
    text: str              # release name, raw
    label: str             # tag
    url: str
    kind: str              # "release"
    sha: str = ""

    @property
    def day(self):
        return self.when.astimezone(DHAKA).date()


def parse_time(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def eligible_repo(repo, login):
    """Public, not a fork, owned by `login`. The profile repo is handled separately."""
    return (repo.get("private") is False
            and repo.get("visibility", "public") == "public"
            and repo.get("fork") is False
            and (repo.get("owner") or {}).get("login", "").lower() == login.lower())


def is_bot(user, name=""):
    user = user or {}
    return user.get("type") == "Bot" or user.get("login", "").endswith("[bot]") or name.endswith("[bot]")


def collect(gh, login, now):
    """Everything the street needs: how busy each day was (the contribution calendar), and
    releases for the fireworks (public repos only)."""
    per_day = gh.calendar(login)
    if max(per_day) < last_completed_day(now) - dt.timedelta(days=1):
        raise DataError(f"contribution calendar stops at {max(per_day)}; refusing to call that inactivity")
    repos = [r for page in gh.pages(f"/users/{login}/repos", {"type": "owner", "per_page": 100}) for r in page]
    repos = [r for r in repos if eligible_repo(r, login)]
    if not repos:
        raise DataError(f"no public repos found for {login}; refusing to call that inactivity")

    releases = []
    for repo in repos:
        name = repo["name"]
        if name.lower() == login.lower():  # the profile repo's releases don't count
            continue
        for r in next(gh.pages(f"/repos/{repo['full_name']}/releases", {"per_page": 100}), []):
            if r.get("draft") or is_bot(r.get("author")):
                continue
            when = r.get("published_at") or r.get("created_at")
            text = " ".join((r.get("name") or r.get("tag_name") or "").split())
            releases.append(Event(name, parse_time(when), text, r["tag_name"], r["html_url"], "release",
                                  r.get("target_commitish", "")))
    return per_day, releases


# ---------------------------------------------------------------- days
def last_completed_day(now):
    return now.astimezone(DHAKA).date() - dt.timedelta(days=1)


def render(img, alt):
    return "\n".join(["<!-- generated by scripts/activity.py every night; edits in here get overwritten -->", "",
                      '<p align="center">',
                      f'  <img src="{img}" width="100%" alt="{html.escape(alt)}">',
                      "</p>"])


def replace_section(readme, body):
    if readme.count(START) != 1 or readme.count(END) != 1 or readme.index(START) > readme.index(END):
        raise DataError("README needs exactly one ACTIVITY:START marker followed by one ACTIVITY:END marker")
    head, rest = readme.split(START)
    _, tail = rest.split(END)
    return f"{head}{START}\n{body}\n{END}{tail}"


# ---------------------------------------------------------------- main
def build(gh, login, now, data=None):
    per_day, releases = data or collect(gh, login, now)
    day = last_completed_day(now)
    svg, alt = street.draw(per_day, {r.day for r in releases}, day)
    img = f"assets/street.svg?v={day.isoformat()}"  # a new URL each day, so GitHub's image cache lets go
    return render(img, alt), svg, day


def demo_data(now):
    """Made-up but plausible activity, for previewing the street without the network."""
    rng = random.Random(7)
    today = now.astimezone(DHAKA).date()
    per_day, releases = {}, []
    for k in range(1, LOOKBACK_DAYS):
        d = today - dt.timedelta(days=k)
        burst = (k // 9) % 2 == 0
        if rng.random() < (0.8 if burst else 0.3):
            per_day[d] = rng.randint(1, 4) + (rng.randint(2, 12) if burst and rng.random() < 0.4 else 0)
    releases.append(Event("Touch-Grass-Babu", dt.datetime.combine(today - dt.timedelta(days=11), dt.time(20), DHAKA),
                          "Touch Grass, Babu 1.0", "v1.0", "https://github.com/ayeshamashiat/Touch-Grass-Babu", "release"))
    return per_day, releases


def main(argv=None, gh=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("login", nargs="?", default=os.environ.get("GITHUB_REPOSITORY_OWNER", "ayeshamashiat"))
    ap.add_argument("--dry-run", action="store_true", help="print the section, write nothing")
    ap.add_argument("--readme", type=Path, default=ROOT / "README.md")
    ap.add_argument("--svg", type=Path, default=ROOT / "assets/street.svg")
    ap.add_argument("--now", help="pretend it's this ISO time (for checking a past day)")
    ap.add_argument("--demo", action="store_true", help="fake activity, no network (implies --dry-run)")
    ap.add_argument("--preview", type=Path, help="with --dry-run or --demo: also write the SVG here")
    args = ap.parse_args(argv)

    now = parse_time(args.now) if args.now else dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=dt.timezone.utc)
    gh = gh or GitHub(os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"))
    try:
        readme = args.readme.read_text(encoding="utf-8")
        body, svg, day = build(gh, args.login, now, demo_data(now) if args.demo else None)
        new = replace_section(readme, body)
    except DataError as e:
        print(f"activity: {e}. README left untouched.", file=sys.stderr)
        return 1

    print(f"activity: {day} (Asia/Dhaka)", file=sys.stderr)
    if args.dry_run or args.demo:
        print(body)
        if args.preview:
            args.preview.write_text(svg, encoding="utf-8")
            print(f"activity: wrote preview {args.preview}", file=sys.stderr)
        return 0
    old_svg = args.svg.read_text(encoding="utf-8") if args.svg.exists() else None
    if new == readme and svg == old_svg:
        print("activity: README unchanged", file=sys.stderr)
        return 0
    args.svg.parent.mkdir(parents=True, exist_ok=True)
    args.svg.write_text(svg, encoding="utf-8")
    args.readme.write_text(new, encoding="utf-8")
    print(f"activity: wrote {args.readme.name}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
