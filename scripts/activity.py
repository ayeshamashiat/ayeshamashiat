#!/usr/bin/env python3
"""
Writes the README's activity section: one line from Mom (the AI mom in Touch Grass, Babu),
picked by yesterday's public activity, then a short ship log of real commits and releases.

  GITHUB_TOKEN=... python scripts/activity.py ayeshamashiat
  GITHUB_TOKEN=... python scripts/activity.py --dry-run      # print it, write nothing

Only public, non-fork repos owned by the user are read. Days are counted in Asia/Dhaka.
Mom's lines live in data/mom-lines.json; nothing here ever runs a model.
If any request fails, nothing is written and the script exits non-zero, so a broken API
never turns into a "you did nothing" roast. Standard library only.
"""
import argparse
import datetime as dt
import hashlib
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

try:
    from zoneinfo import ZoneInfo
    DHAKA = ZoneInfo("Asia/Dhaka")
except Exception:  # no tz database: Dhaka is UTC+6 all year, no DST
    DHAKA = dt.timezone(dt.timedelta(hours=6), "Asia/Dhaka")

ROOT = Path(__file__).resolve().parent.parent
START, END = "<!-- ACTIVITY:START -->", "<!-- ACTIVITY:END -->"

LOOKBACK_DAYS = 90     # ship log window, and how far back activity is counted
MAX_ENTRIES = 5
PER_REPO = 2           # so one project can't take over the log
SUBJECT_MAX = 80
NO_REPEAT_DAYS = 14
LINE_MAX = 140

BUSY_COMMITS = 10
STREAK_DAYS = 7
QUIET_LONG, QUIET_EXTREME = 4, 14
BUCKETS = ["shipped", "busy", "streak", "quiet_short", "quiet_long", "quiet_extreme", "steady"]
SOURCES = {"model", "placeholder"}

# Commit subjects that say nothing. Matched against the whole subject, lowercased,
# with trailing punctuation dropped. Add a pattern here to hide more.
LOW_SIGNAL = [
    r"updates?d?",
    r"updated? (the )?readme(\.md)?",
    r"wip",
    r"fix(ed)? typos?",
    r"typos?",
    r"(added |made |some )?minor (changes?|fix(es)?|updates?|edits?)",
    r"small (changes?|fix(es)?)",
    r"changes?",
    r"initial commit",
    r"first commit",
    r"init",
    r"test(ing)?",
    r"\.+",
]
_LOW = re.compile("|".join(f"(?:{p})" for p in LOW_SIGNAL))

CAPTION = ("<sub>Mom's lines come from the on-device model in "
           "[Touch Grass, Babu](https://github.com/ayeshamashiat/Touch-Grass-Babu).</sub>")


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


@dataclass
class Event:
    repo: str
    when: dt.datetime      # aware
    text: str              # commit subject or release name, raw
    label: str             # short sha or tag
    url: str
    kind: str              # "commit" | "release"
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


def subject_of(message):
    return " ".join((message or "").splitlines()[0].split()) if message else ""


def is_merge(c):
    return len(c.get("parents") or []) > 1 or subject_of(c["commit"]["message"]).startswith("Merge ")


def low_signal(subject):
    s = subject.lower().strip().rstrip(".!:;, ")
    return not s or bool(_LOW.fullmatch(s))


def own_commit(c, login):
    """Written by `login` (by GitHub account, not just a name) and not a bot."""
    author = c.get("author") or {}
    return (author.get("login", "").lower() == login.lower()
            and not is_bot(author, c["commit"]["author"].get("name", "")))


def fetch_commits(gh, repo, login, since):
    """Commits on the default branch by `login`: everything since `since`, and at least
    the newest page, so the log can fall back to older work when the window is empty."""
    out = []
    try:
        for page in gh.pages(f"/repos/{repo['full_name']}/commits", {"author": login, "per_page": 100}):
            out += page
            if len(page) < 100 or parse_time(page[-1]["commit"]["author"]["date"]) < since:
                break
    except DataError as e:
        if "HTTP 409" in str(e):  # empty repository: no commits is the truth here
            return []
        raise
    return out


def collect(gh, login, now):
    """Everything the section needs, from public data only."""
    since = now - dt.timedelta(days=LOOKBACK_DAYS)
    repos = [r for page in gh.pages(f"/users/{login}/repos", {"type": "owner", "per_page": 100}) for r in page]
    repos = [r for r in repos if eligible_repo(r, login)]
    if not repos:
        raise DataError(f"no public repos found for {login}; refusing to call that inactivity")

    per_day, seen = {}, set()
    commits, releases = [], []
    for repo in repos:
        name, profile = repo["name"], repo["name"].lower() == login.lower()
        for c in fetch_commits(gh, repo, login, since):
            if not own_commit(c, login) or is_merge(c) or c["sha"] in seen:
                continue
            seen.add(c["sha"])
            ev = Event(name, parse_time(c["commit"]["author"]["date"]), subject_of(c["commit"]["message"]),
                       c["sha"][:7], c["html_url"], "commit", c["sha"])
            per_day[ev.day] = per_day.get(ev.day, 0) + 1  # every real commit is activity
            if not profile:
                commits.append(ev)
        if profile:
            continue
        for r in next(gh.pages(f"/repos/{repo['full_name']}/releases", {"per_page": 100}), []):
            if r.get("draft") or is_bot(r.get("author")):
                continue
            when = r.get("published_at") or r.get("created_at")
            text = " ".join((r.get("name") or r.get("tag_name") or "").split())
            releases.append(Event(name, parse_time(when), text, r["tag_name"], r["html_url"], "release",
                                  r.get("target_commitish", "")))
    return per_day, commits, releases


# ---------------------------------------------------------------- mom's bucket
def last_completed_day(now):
    return now.astimezone(DHAKA).date() - dt.timedelta(days=1)


def run_length(per_day, day, active):
    n = 0
    while n <= LOOKBACK_DAYS and (per_day.get(day - dt.timedelta(days=n), 0) > 0) == active:
        n += 1
    return n


def bucket_for(per_day, releases, day):
    """shipped > busy > streak > the rest."""
    if any(r.day == day for r in releases):
        return "shipped"
    if per_day.get(day, 0) >= BUSY_COMMITS:
        return "busy"
    if per_day.get(day, 0) == 0:
        quiet = run_length(per_day, day, False)
        return "quiet_extreme" if quiet >= QUIET_EXTREME else "quiet_long" if quiet >= QUIET_LONG else "quiet_short"
    if run_length(per_day, day, True) >= STREAK_DAYS:
        return "streak"
    return "steady"


def load_lines(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    lines = data["lines"] if isinstance(data, dict) else data
    ids = set()
    for ln in lines:
        missing = {"id", "bucket", "text", "source"} - ln.keys()
        if missing:
            raise DataError(f"line {ln.get('id', '?')} is missing {sorted(missing)}")
        if ln["id"] in ids:
            raise DataError(f"duplicate line id {ln['id']}")
        ids.add(ln["id"])
        if ln["bucket"] not in BUCKETS:
            raise DataError(f"line {ln['id']}: unknown bucket {ln['bucket']!r}")
        if ln["source"] not in SOURCES:
            raise DataError(f"line {ln['id']}: source must be model or placeholder, not {ln['source']!r}")
        if not ln["text"].strip() or len(ln["text"]) > LINE_MAX or "\n" in ln["text"]:
            raise DataError(f"line {ln['id']}: text must be one line of 1-{LINE_MAX} characters")
    empty = [b for b in BUCKETS if not any(ln["bucket"] == b for ln in lines)]
    if empty:
        raise DataError(f"no lines for bucket(s) {empty}")
    return lines


def _h(*parts):
    return int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:12], 16)


def pick_line(lines, bucket, day, history):
    """Same date and history in, same line out. Lines used in the last 14 days are skipped;
    if the bucket has run out, the one used longest ago wins."""
    pool = sorted((ln for ln in lines if ln["bucket"] == bucket), key=lambda ln: ln["id"])
    used = {}
    for h in history:
        d = dt.date.fromisoformat(h["date"])
        if d == day:
            again = next((ln for ln in pool if ln["id"] == h["id"]), None)
            if again:
                return again  # a rerun on the same day keeps the same line
        elif d < day:
            used[h["id"]] = max(used.get(h["id"], d), d)
    fresh = [ln for ln in pool if ln["id"] not in used or (day - used[ln["id"]]).days >= NO_REPEAT_DAYS]
    if fresh:
        return fresh[_h(day, bucket) % len(fresh)]
    return min(pool, key=lambda ln: (used[ln["id"]], _h(day, ln["id"])))


def remember(history, day, line_id, keep_days=30):
    out = [h for h in history if h["date"] != day.isoformat()
           and (day - dt.date.fromisoformat(h["date"])).days < keep_days]
    return sorted(out + [{"date": day.isoformat(), "id": line_id}], key=lambda h: h["date"])


# ---------------------------------------------------------------- ship log
def ship_log(commits, releases, now):
    """Up to 5 entries, newest first, at most 2 per repo. A release beats the commits from
    the same repo and day (and the commit it was cut from)."""
    released = {(r.repo, r.day) for r in releases} | {(r.repo, r.sha) for r in releases if r.sha}
    events = [r for r in releases if not low_signal(r.text)]
    events += [c for c in commits
               if (c.repo, c.day) not in released and (c.repo, c.sha) not in released and not low_signal(c.text)]
    events.sort(key=lambda e: e.when, reverse=True)

    def take(evs):
        out, per = [], {}
        for e in evs:
            if per.get(e.repo, 0) < PER_REPO:
                out.append(e)
                per[e.repo] = per.get(e.repo, 0) + 1
            if len(out) == MAX_ENTRIES:
                break
        return out

    recent = take([e for e in events if e.when >= now - dt.timedelta(days=LOOKBACK_DAYS)])
    return recent or take(events)  # nothing lately: show the latest real work, with its real dates


# ---------------------------------------------------------------- markdown
_MD = re.compile(r"([\\`*_\[\]|~])")


def esc(text):
    return _MD.sub(r"\\\1", html.escape(text, quote=False))


def truncate(text, n=SUBJECT_MAX):
    return text if len(text) <= n else text[:n - 1].rstrip() + "…"


def entry_md(e):
    url = e.url.replace("(", "%28").replace(")", "%29").replace(" ", "%20")
    return f"- `{e.day.isoformat()}` **{esc(e.repo)}** — {esc(truncate(e.text))} ([{esc(e.label)}]({url}))"


def render(line, all_model, entries):
    out = ["<!-- generated by scripts/activity.py every night; edits in here get overwritten -->", "",
           f"> **Mom:** {esc(line['text'])}", ""]
    if all_model:
        out += [CAPTION, ""]
    out += ["**Ship log**", ""]
    out += [entry_md(e) for e in entries] or ["_Nothing shipped yet._"]
    return "\n".join(out)


def replace_section(readme, body):
    if readme.count(START) != 1 or readme.count(END) != 1 or readme.index(START) > readme.index(END):
        raise DataError("README needs exactly one ACTIVITY:START marker followed by one ACTIVITY:END marker")
    head, rest = readme.split(START)
    _, tail = rest.split(END)
    return f"{head}{START}\n{body}\n{END}{tail}"


# ---------------------------------------------------------------- main
def build(gh, login, now, lines, history):
    per_day, commits, releases = collect(gh, login, now)
    day = last_completed_day(now)
    bucket = bucket_for(per_day, releases, day)
    line = pick_line(lines, bucket, day, history)
    body = render(line, all(ln["source"] == "model" for ln in lines), ship_log(commits, releases, now))
    return body, bucket, day, line


def main(argv=None, gh=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("login", nargs="?", default=os.environ.get("GITHUB_REPOSITORY_OWNER", "ayeshamashiat"))
    ap.add_argument("--dry-run", action="store_true", help="print the section, write nothing")
    ap.add_argument("--readme", type=Path, default=ROOT / "README.md")
    ap.add_argument("--lines", type=Path, default=ROOT / "data/mom-lines.json")
    ap.add_argument("--history", type=Path, default=ROOT / "data/mom-history.json")
    ap.add_argument("--now", help="pretend it's this ISO time (for checking a past day)")
    args = ap.parse_args(argv)

    now = parse_time(args.now) if args.now else dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=dt.timezone.utc)
    gh = gh or GitHub(os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"))
    try:
        lines = load_lines(args.lines)
        history = json.loads(args.history.read_text(encoding="utf-8")) if args.history.exists() else []
        readme = args.readme.read_text(encoding="utf-8")
        body, bucket, day, line = build(gh, args.login, now, lines, history)
        new = replace_section(readme, body)
    except DataError as e:
        print(f"activity: {e}. README left untouched.", file=sys.stderr)
        return 1

    print(f"activity: {day} (Asia/Dhaka) -> {bucket} -> {line['id']}", file=sys.stderr)
    if args.dry_run:
        print(body)
        return 0
    if new == readme:
        print("activity: README unchanged", file=sys.stderr)
        return 0
    args.readme.write_text(new, encoding="utf-8")
    args.history.parent.mkdir(parents=True, exist_ok=True)
    args.history.write_text(json.dumps(remember(history, day, line["id"]), indent=1) + "\n", encoding="utf-8")
    print(f"activity: wrote {args.readme.name}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
