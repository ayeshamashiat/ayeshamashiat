"""Tests for scripts/activity.py, on fixture data only (no network).

  python -m unittest discover -s tests
"""
import datetime as dt
import json
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import activity as A  # noqa: E402

LOGIN = "ayeshamashiat"
UTC = dt.timezone.utc
NOW = dt.datetime(2026, 11, 3, 3, 0, tzinfo=UTC)          # 09:00 in Dhaka, Nov 3
DAY = dt.date(2026, 11, 2)                                 # last completed Dhaka day


# ---------------------------------------------------------------- fixtures
def repo(name, owner=LOGIN, private=False, fork=False):
    return {"name": name, "full_name": f"{owner}/{name}", "private": private, "fork": fork,
            "visibility": "private" if private else "public", "owner": {"login": owner}}


_n = [0]


def commit(when, msg="Add threat graph scoring", login=LOGIN, parents=1, bot=False, name=None):
    _n[0] += 1
    sha = f"{_n[0]:07d}" + "f" * 33
    author = {"login": login, "type": "Bot" if bot else "User"}
    return {"sha": sha, "html_url": f"https://github.com/x/y/commit/{sha}", "author": author,
            "parents": [{"sha": "p"}] * parents,
            "commit": {"message": msg, "author": {"date": when, "name": name or login}}}


def release(when, tag="v1.0.0", name="Bouncer 1.0", draft=False, bot=False, target="main"):
    return {"tag_name": tag, "name": name, "draft": draft, "published_at": when, "created_at": when,
            "html_url": f"https://github.com/x/y/releases/tag/{tag}", "target_commitish": target,
            "author": {"login": "github-actions[bot]" if bot else LOGIN, "type": "Bot" if bot else "User"}}


class FakeGitHub:
    """Serves fixture pages by path; any path in `fail` raises like a real HTTP error."""

    def __init__(self, repos, commits=None, releases=None, fail=()):
        self.repos, self.commits, self.releases = repos, commits or {}, releases or {}
        self.fail, self.calls = set(fail), []

    def pages(self, path, params=None):
        self.calls.append(path)
        for f in self.fail:
            if f in path:
                raise A.DataError(f"GET {path} failed: HTTP 502 Bad Gateway")
        if path == f"/users/{LOGIN}/repos":
            yield self.repos
        elif path.endswith("/commits"):
            yield self.commits.get(path.split("/")[3], [])
        elif path.endswith("/releases"):
            yield self.releases.get(path.split("/")[3], [])
        else:
            raise AssertionError(path)


def ev(repo_name, when, text="Real work", kind="commit", label="abc1234", sha=""):
    return A.Event(repo_name, A.parse_time(when), text, label, f"https://github.com/{LOGIN}/{repo_name}",
                   kind, sha)


def days(*spec):
    """days((offset_from_DAY, count), ...) -> per-day counts."""
    return {DAY - dt.timedelta(days=o): n for o, n in spec}


LINES = [{"id": f"{b}-p{i}", "bucket": b, "text": f"{b} line {i}", "source": "placeholder"}
         for b in A.BUCKETS for i in range(1, 6)]


# ---------------------------------------------------------------- buckets
class Buckets(unittest.TestCase):
    def test_each_bucket(self):
        self.assertEqual(A.bucket_for(days((1, 2)), [], DAY), "quiet_short")       # 1 quiet day
        self.assertEqual(A.bucket_for(days((3, 2)), [], DAY), "quiet_short")       # 3 quiet days
        self.assertEqual(A.bucket_for(days((4, 2)), [], DAY), "quiet_long")        # 4
        self.assertEqual(A.bucket_for(days((13, 2)), [], DAY), "quiet_long")       # 13
        self.assertEqual(A.bucket_for(days((14, 2)), [], DAY), "quiet_extreme")    # 14
        self.assertEqual(A.bucket_for({}, [], DAY), "quiet_extreme")               # nothing in 90 days
        self.assertEqual(A.bucket_for(days((0, 3)), [], DAY), "steady")
        self.assertEqual(A.bucket_for(days((0, 10)), [], DAY), "busy")
        self.assertEqual(A.bucket_for(days((0, 9)), [], DAY), "steady")
        self.assertEqual(A.bucket_for(days(*[(o, 1) for o in range(7)]), [], DAY), "streak")
        self.assertEqual(A.bucket_for(days(*[(o, 1) for o in range(6)]), [], DAY), "steady")
        shipped = [ev("Bouncer", "2026-11-02T10:00:00Z", kind="release")]
        self.assertEqual(A.bucket_for({}, shipped, DAY), "shipped")

    def test_priority(self):
        streak_busy = days((0, 12), *[(o, 1) for o in range(1, 9)])
        shipped = [ev("Bouncer", "2026-11-02T10:00:00Z", kind="release")]
        self.assertEqual(A.bucket_for(streak_busy, shipped, DAY), "shipped")
        self.assertEqual(A.bucket_for(streak_busy, [], DAY), "busy")
        self.assertEqual(A.bucket_for(days(*[(o, 2) for o in range(10)]), [], DAY), "streak")
        old_release = [ev("Bouncer", "2026-11-01T10:00:00Z", kind="release")]
        self.assertEqual(A.bucket_for(days((0, 1)), old_release, DAY), "steady")


class DhakaDays(unittest.TestCase):
    def test_last_completed_day_flips_at_dhaka_midnight(self):
        self.assertEqual(A.last_completed_day(dt.datetime(2026, 11, 2, 17, 59, tzinfo=UTC)), dt.date(2026, 11, 1))
        self.assertEqual(A.last_completed_day(dt.datetime(2026, 11, 2, 18, 0, tzinfo=UTC)), dt.date(2026, 11, 2))

    def test_commit_counts_on_its_dhaka_date(self):
        self.assertEqual(ev("R", "2026-11-01T18:30:00Z").day, dt.date(2026, 11, 2))  # 00:30 Dhaka
        self.assertEqual(ev("R", "2026-11-01T17:59:00Z").day, dt.date(2026, 11, 1))  # 23:59 Dhaka

    def test_late_utc_commit_is_not_quiet(self):
        gh = FakeGitHub([repo("Bouncer")], {"Bouncer": [commit("2026-11-01T19:00:00Z")]})
        per_day, _, _ = A.collect(gh, LOGIN, NOW)
        self.assertEqual(A.bucket_for(per_day, [], DAY), "steady")


# ---------------------------------------------------------------- rotation
class Rotation(unittest.TestCase):
    def test_deterministic(self):
        a = A.pick_line(LINES, "busy", DAY, [])
        self.assertEqual(a, A.pick_line(LINES, "busy", DAY, []))
        self.assertEqual(a["bucket"], "busy")

    def test_no_repeat_within_14_days_when_pool_allows(self):
        pool = [{"id": f"s{i:02d}", "bucket": "steady", "text": "x", "source": "model"} for i in range(15)]
        hist, seen = [], []
        for k in range(40):
            d = DAY + dt.timedelta(days=k)
            line = A.pick_line(pool, "steady", d, hist)
            hist = A.remember(hist, d, line["id"])
            seen.append(line["id"])
        for k in range(len(seen)):
            self.assertNotIn(seen[k], seen[max(0, k - 13):k], f"repeat within 14 days at day {k}")

    def test_small_pool_cycles_least_recently_used(self):
        hist, seen = [], []
        for k in range(10):
            d = DAY + dt.timedelta(days=k)
            line = A.pick_line(LINES, "quiet_long", d, hist)
            hist = A.remember(hist, d, line["id"])
            seen.append(line["id"])
        self.assertEqual(len(set(seen[:5])), 5)   # all five used before any repeat
        self.assertEqual(seen[5:], seen[:5])      # then oldest first

    def test_rerun_same_day_keeps_line(self):
        first = A.pick_line(LINES, "busy", DAY, [])
        hist = A.remember([], DAY, first["id"])
        self.assertEqual(A.pick_line(LINES, "busy", DAY, hist), first)


# ---------------------------------------------------------------- ship log
class Filtering(unittest.TestCase):
    def test_low_signal(self):
        for s in ["update", "Update", "updated", "Update README.md", "wip", "WIP.", "fix typo", "Fix typos",
                  "minor changes", "Minor fixes", "added minor change", "initial commit", "Initial commit", "first commit", "", "..."]:
            self.assertTrue(A.low_signal(s), s)
        for s in ["Update threat graph weights", "Add Bangla refusal path", "Fix typo in CLI flag parsing logic",
                  "wip: split llama.cpp loader"]:
            self.assertFalse(A.low_signal(s), s)

    def test_merges_bots_and_others_excluded(self):
        gh = FakeGitHub([repo("Bouncer")], {"Bouncer": [
            commit("2026-11-01T10:00:00Z", "Add MCP hook"),
            commit("2026-11-01T11:00:00Z", "Merge branch 'main' of github.com:x/y", parents=2),
            commit("2026-11-01T11:30:00Z", "Merge pull request #4 from x/y"),
            commit("2026-11-01T12:00:00Z", "Bump deps", login="dependabot[bot]", bot=True),
            commit("2026-11-01T12:30:00Z", "Bot with a user login", name="github-actions[bot]"),
            commit("2026-11-01T13:00:00Z", "Teammate change", login="teammate"),
            commit("2026-11-01T14:00:00Z", "update"),
        ]})
        per_day, commits, _ = A.collect(gh, LOGIN, NOW)
        self.assertEqual([c.text for c in commits], ["Add MCP hook", "update"])
        self.assertEqual(per_day, {dt.date(2026, 11, 1): 2})  # low-signal still counts as activity
        self.assertEqual([e.text for e in A.ship_log(commits, [], NOW)], ["Add MCP hook"])

    def test_private_fork_foreign_and_profile_excluded(self):
        repos = [repo("Bouncer"), repo("Secret", private=True), repo("Forked", fork=True),
                 repo("Shared", owner="someone"), repo(LOGIN)]
        each = {r["name"]: [commit("2026-11-01T10:00:00Z", f"Work in {r['name']}")] for r in repos}
        rels = {r["name"]: [release("2026-11-01T09:00:00Z", name=f"{r['name']} 1.0")] for r in repos}
        gh = FakeGitHub(repos, each, rels)
        per_day, commits, releases = A.collect(gh, LOGIN, NOW)
        log = A.ship_log(commits, releases, NOW)
        self.assertEqual({e.repo for e in log}, {"Bouncer"})
        touched = " ".join(gh.calls)
        for name in ("Secret", "Forked", "Shared"):
            self.assertNotIn(name, touched, "never even ask about it")
        self.assertEqual(per_day[dt.date(2026, 11, 1)], 2)  # profile repo commits are still activity
        self.assertNotIn(f"/repos/{LOGIN}/{LOGIN}/releases", gh.calls)

    def test_bot_and_draft_releases_ignored(self):
        gh = FakeGitHub([repo("Bouncer")], {}, {"Bouncer": [
            release("2026-11-02T10:00:00Z", tag="v2", draft=True),
            release("2026-11-02T10:00:00Z", tag="v3", bot=True)]})
        _, _, releases = A.collect(gh, LOGIN, NOW)
        self.assertEqual(releases, [])

    def test_per_repo_cap_newest_first_max_five(self):
        commits = [ev("Bouncer", f"2026-11-0{d}T10:00:00Z", f"Bouncer {d}") for d in range(1, 4)]
        commits += [ev(n, "2026-10-20T10:00:00Z", f"{n} work") for n in ("A", "B", "C", "D")]
        log = A.ship_log(commits, [], NOW)
        self.assertEqual(len(log), 5)
        self.assertEqual([e.text for e in log[:2]], ["Bouncer 3", "Bouncer 2"])
        self.assertEqual(sum(e.repo == "Bouncer" for e in log), 2)
        self.assertEqual(log, sorted(log, key=lambda e: e.when, reverse=True))

    def test_release_beats_same_day_commits(self):
        commits = [ev("Bouncer", "2026-11-01T08:00:00Z", "Cut 1.0", sha="aaa"),
                   ev("Bouncer", "2026-10-30T08:00:00Z", "Earlier work", sha="bbb"),
                   ev("Bouncer", "2026-10-29T08:00:00Z", "Tagged commit", sha="ccc")]
        rel = [ev("Bouncer", "2026-11-01T12:00:00Z", "Bouncer 1.0", "release", "v1.0", sha="ccc")]
        log = A.ship_log(commits, rel, NOW)
        self.assertEqual([e.text for e in log], ["Bouncer 1.0", "Earlier work"])

    def test_fewer_than_five_is_fine(self):
        log = A.ship_log([ev("Bouncer", "2026-10-30T08:00:00Z")], [], NOW)
        self.assertEqual(len(log), 1)

    def test_falls_back_to_older_work_with_real_dates(self):
        commits = [ev("Bouncer", "2025-01-05T08:00:00Z", "Old but real"),
                   ev("PetniHunter", "2025-03-01T08:00:00Z", "Older but real")]
        log = A.ship_log(commits, [], NOW)
        self.assertEqual([e.day.isoformat() for e in log], ["2025-03-01", "2025-01-05"])

    def test_window_wins_over_fallback(self):
        commits = [ev("Bouncer", "2026-10-30T08:00:00Z", "Recent"), ev("Bouncer", "2025-01-05T08:00:00Z", "Old")]
        self.assertEqual([e.text for e in A.ship_log(commits, [], NOW)], ["Recent"])


# ---------------------------------------------------------------- markdown
class Markdown(unittest.TestCase):
    def test_escaping(self):
        self.assertEqual(A.esc("<script>alert(1)</script> & *bold* _x_ [l](u) `c` a|b ~s~"),
                         r"&lt;script&gt;alert(1)&lt;/script&gt; &amp; \*bold\* \_x\_ \[l\](u) \`c\` a\|b \~s\~")

    def test_truncate_then_escape(self):
        e = ev("Bouncer", "2026-11-01T08:00:00Z", "x" * 79 + "*tail" + "y" * 20)
        line = A.entry_md(e)
        self.assertIn("x" * 79 + "…", line)
        self.assertNotIn("tail", line)
        self.assertLessEqual(len(A.truncate("a" * 200)), 80)
        self.assertEqual(A.truncate("short"), "short")

    def test_entry_format(self):
        e = ev("Petni_Hunter", "2026-11-01T20:00:00Z", "Add <Bangla> refusal", label="1a2b3c4")
        self.assertEqual(A.entry_md(e),
                         rf"- `2026-11-02` **Petni\_Hunter** — Add &lt;Bangla&gt; refusal "
                         rf"([1a2b3c4](https://github.com/{LOGIN}/Petni_Hunter))")

    def test_caption_only_when_every_line_is_model(self):
        line = {"text": "hi babu"}
        self.assertNotIn("on-device", A.render(line, False, [], "s.svg", "alt"))
        self.assertIn("on-device", A.render(line, True, [], "s.svg", "alt"))

    def test_image_then_mom_then_ship_log_in_details(self):
        body = A.render({"text": "Two days, babu."}, False, [ev("Bouncer", "2026-11-01T08:00:00Z")],
                        "assets/street.svg?v=2026-11-02", 'say "hi" & <go>')
        self.assertEqual(sum(ln.startswith(">") for ln in body.splitlines()), 1)
        self.assertIn('alt="say &quot;hi&quot; &amp; &lt;go&gt;"', body)
        self.assertLess(body.index("<img"), body.index("> **Mom:**"))
        self.assertLess(body.index("> **Mom:**"), body.index("<details>"))
        self.assertLess(body.index("<details>"), body.index("- `2026-11-01`"))
        self.assertLess(body.index("- `2026-11-01`"), body.index("</details>"))
        self.assertIn("</summary>\n\n", body)  # GitHub needs the blank line to render Markdown inside

    def test_marker_replacement(self):
        readme = f"top\n{A.START}\nold stuff\n{A.END}\nbottom\n"
        self.assertEqual(A.replace_section(readme, "new"), f"top\n{A.START}\nnew\n{A.END}\nbottom\n")
        for broken in ["no markers", f"{A.END}\n{A.START}", f"{A.START}{A.START}{A.END}", f"{A.START} only"]:
            with self.assertRaises(A.DataError):
                A.replace_section(broken, "new")


# ---------------------------------------------------------------- lines file
class LinesFile(unittest.TestCase):
    def _load(self, lines):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "l.json")
            p.write_text(json.dumps({"lines": lines}))
            return A.load_lines(p)

    def test_real_file_is_valid_with_five_placeholders_per_bucket(self):
        lines = A.load_lines(Path(__file__).resolve().parent.parent / "data/mom-lines.json")
        for b in A.BUCKETS:
            mine = [ln for ln in lines if ln["bucket"] == b]
            self.assertGreaterEqual(len(mine), 5, b)
        for ln in lines:
            self.assertLess(len(ln["text"]), 140)
            if ln["source"] == "placeholder":
                self.assertIn("-p", ln["id"])

    def test_rejects_bad_lines(self):
        ok = [dict(ln) for ln in LINES]
        self.assertEqual(len(self._load(ok)), len(ok))
        for bad in [{"source": "made-up"}, {"bucket": "sleepy"}, {"text": "x" * 141}, {"text": "a\nb"}]:
            with self.assertRaises(A.DataError):
                self._load([{**ok[0], **bad}] + ok[1:])
        with self.assertRaises(A.DataError):
            self._load([ln for ln in ok if ln["bucket"] != "busy"])
        with self.assertRaises(A.DataError):
            self._load(ok + [ok[0]])


# ---------------------------------------------------------------- end to end
class EndToEnd(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        d = Path(self.dir.name)
        self.readme, self.lines, self.history = d / "README.md", d / "lines.json", d / "history.json"
        self.svg = d / "street.svg"
        self.original = f"# hi\n\n{A.START}\nold\n{A.END}\n\nkeep me\n"
        self.readme.write_text(self.original)
        self.lines.write_text(json.dumps({"lines": LINES}))
        self.args = ["--readme", str(self.readme), "--lines", str(self.lines), "--history", str(self.history),
                     "--svg", str(self.svg), "--now", NOW.isoformat()]

    def tearDown(self):
        self.dir.cleanup()

    def gh(self, **kw):
        return FakeGitHub([repo("Bouncer"), repo("Empty")],
                          {"Bouncer": [commit("2026-11-01T10:00:00Z", "Add MCP hook")]}, **kw)

    def test_writes_section_and_history(self):
        gh = self.gh()
        self.assertEqual(A.main(self.args, gh=gh), 0)
        text = self.readme.read_text()
        self.assertTrue(text.startswith("# hi\n\n" + A.START) and text.endswith(A.END + "\n\nkeep me\n"))
        self.assertIn(r"> **Mom:** quiet\_short line", text)
        self.assertIn("**Bouncer** — Add MCP hook", text)
        self.assertEqual(json.loads(self.history.read_text())[0]["date"], "2026-11-02")
        self.assertIn("street.svg?v=2026-11-02", text)
        self.assertIn("load shedding", self.svg.read_text())
        self.assertIn(r"> **Mom:** quiet\_short line", text)
        # second run, same day: identical output, nothing rewritten
        self.assertEqual(A.main(self.args, gh=gh), 0)
        self.assertEqual(self.readme.read_text(), text)

    def test_dry_run_writes_nothing(self):
        self.assertEqual(A.main(self.args + ["--dry-run"], gh=self.gh()), 0)
        self.assertEqual(self.readme.read_text(), self.original)
        self.assertFalse(self.history.exists())
        self.assertFalse(self.svg.exists())

    def test_api_failure_leaves_readme_untouched(self):
        for fail in ("/users/", "Bouncer/commits", "Bouncer/releases"):
            self.assertEqual(A.main(self.args, gh=self.gh(fail={fail})), 1, fail)
            self.assertEqual(self.readme.read_text(), self.original)
            self.assertFalse(self.history.exists())
            self.assertFalse(self.svg.exists())

    def test_no_repos_is_treated_as_bad_data_not_inactivity(self):
        self.assertEqual(A.main(self.args, gh=FakeGitHub([])), 1)
        self.assertEqual(self.readme.read_text(), self.original)

    def test_bad_lines_file_fails(self):
        self.lines.write_text(json.dumps({"lines": LINES[:5]}))
        self.assertEqual(A.main(self.args, gh=self.gh()), 1)
        self.assertEqual(self.readme.read_text(), self.original)


class Street(unittest.TestCase):
    def draw(self, per_day=None, releases=()):
        import street
        svg, alt = street.draw(per_day or {}, set(releases), DAY)
        return svg, alt, ET.fromstring(svg)

    def test_well_formed_with_one_building_per_night(self):
        import street
        svg, _, root = self.draw(days((0, 3), (5, 12)))
        tips = [t.text for t in root.iter("{http://www.w3.org/2000/svg}title")]
        self.assertEqual(len(tips), street.NIGHTS)
        self.assertEqual(tips[-1], "Mon 02 Nov: 3 commits")
        self.assertEqual(tips[0], "Tue 22 Sep: load shedding")

    def test_blackout_has_no_lit_windows(self):
        import street
        svg, alt, _ = self.draw({})
        for warm in street.WARM:
            self.assertNotIn(f'width="5" height="6" fill="{warm}"', svg)  # no lit windows (the legend may use it)
        self.assertIn("Lights on 0 of 42 nights", alt)

    def test_busier_nights_light_more_windows(self):
        import street
        lit = lambda n: sum(street.building(0, DAY, n, street.levels([1, 2, 5, 9])(n), False).count(w)
                            for w in street.WARM)
        self.assertLess(lit(1), lit(9))

    def test_release_night_gets_fireworks(self):
        self.assertNotIn('class="burst"', self.draw(days((0, 1)))[0])
        svg, alt, _ = self.draw(days((0, 1)), {DAY})
        self.assertIn('class="burst"', svg)
        self.assertIn("1 release night with fireworks", alt)

    def test_every_storefront_is_open_and_continuous(self):
        import street
        for kind in ("biryani", "pharmacy", "library", "garage", "store", "sweets", "cng", "tailor"):
            front = street.storefront(0, 77, kind)
            self.assertNotIn('fill="#2a2f37"', front, kind)               # no shutters
            self.assertIn('fill="#f4fbff"', front, kind)                  # tube lights on
            self.assertEqual(front.count("<clipPath"), 1, kind)           # one opening, the whole span
        self.assertIn('stroke="#9aa3ad"', street.storefront(0, 117, "library"))   # the glass door
        self.assertIn('stroke="#9aa3ad"', street.storefront(0, 77, "store"))

    def test_ground_floor_is_a_shop_not_flats(self):
        import street
        svg = street.building(0, DAY, 9, 4, False)
        ys = [float(r.split('y="')[1].split('"')[0]) for r in svg.split("<rect") if 'width="5" height="6"' in r]
        self.assertTrue(ys and max(ys) < street.BASE - street.GF)

    def test_shop_row_covers_every_building_with_bangla_signs(self):
        import street
        self.assertEqual(sum(shop[2] for shop in street.SHOPS), street.NIGHTS)
        svg, alt, _ = self.draw(days((0, 2)))
        for bangla, english, *_ in street.SHOPS:
            self.assertIn(bangla, svg)
            self.assertIn(english, alt)

    def test_signboard_dims_when_every_shop_under_it_is_shut(self):
        import street
        self.assertIn('opacity="0.32"', street.signboard(0, 60, "মদিনা সুইটস", "#000", "#fff", lit=False))
        self.assertIn('opacity="1"', street.signboard(0, 60, "মদিনা সুইটস", "#000", "#fff", lit=True))

    def test_no_mom_sign_in_the_picture(self):
        svg, alt, _ = self.draw()
        self.assertNotIn("AMMU SAYS", svg)
        self.assertNotIn("Ammu says", alt)
        self.assertIn("চা", svg)


class EmptyRepo(unittest.TestCase):
    def test_409_means_no_commits(self):
        class G(FakeGitHub):
            def pages(self, path, params=None):
                if path.endswith("Empty/commits"):
                    raise A.DataError(f"GET {path} failed: HTTP 409 Conflict")
                yield from super().pages(path, params)
        per_day, commits, _ = A.collect(G([repo("Empty")]), LOGIN, NOW)
        self.assertEqual((per_day, commits), ({}, []))


if __name__ == "__main__":
    unittest.main()
