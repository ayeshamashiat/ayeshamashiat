"""Tests for scripts/activity.py, on fixture data only (no network).

  python -m unittest discover -s tests
"""
import datetime as dt
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


def release(when, tag="v1.0.0", name="Bouncer 1.0", draft=False, bot=False, target="main"):
    return {"tag_name": tag, "name": name, "draft": draft, "published_at": when, "created_at": when,
            "html_url": f"https://github.com/x/y/releases/tag/{tag}", "target_commitish": target,
            "author": {"login": "github-actions[bot]" if bot else LOGIN, "type": "Bot" if bot else "User"}}


class FakeGitHub:
    """Serves fixture pages by path; any path in `fail` raises like a real HTTP error."""

    def __init__(self, repos, releases=None, fail=(), calendar=None):
        self.repos, self.releases = repos, releases or {}
        self.fail, self.calls = set(fail), []
        self.cal = calendar if calendar is not None else year_calendar()

    def calendar(self, login):
        self.calls.append("calendar")
        if "calendar" in self.fail:
            raise A.DataError("GET https://github.com/users/x/contributions failed: HTTP 502 Bad Gateway")
        return self.cal

    def pages(self, path, params=None):
        self.calls.append(path)
        for f in self.fail:
            if f in path:
                raise A.DataError(f"GET {path} failed: HTTP 502 Bad Gateway")
        if path == f"/users/{LOGIN}/repos":
            yield self.repos
        elif path.endswith("/releases"):
            yield self.releases.get(path.split("/")[3], [])
        else:
            raise AssertionError(path)


def year_calendar(**counts):
    """A year of graph ending today (Nov 3), with year_calendar(**{"2026-11-01": 4}) style counts."""
    out = {dt.date(2026, 11, 3) - dt.timedelta(days=k): 0 for k in range(371)}
    out.update({dt.date.fromisoformat(d): n for d, n in counts.items()})
    return out


def ev(repo_name, when, text="Real work", kind="release", label="v1.0", sha=""):
    return A.Event(repo_name, A.parse_time(when), text, label, f"https://github.com/{LOGIN}/{repo_name}",
                   kind, sha)


def days(*spec):
    """days((offset_from_DAY, count), ...) -> per-day counts."""
    return {DAY - dt.timedelta(days=o): n for o, n in spec}


class DhakaDays(unittest.TestCase):
    def test_last_completed_day_flips_at_dhaka_midnight(self):
        self.assertEqual(A.last_completed_day(dt.datetime(2026, 11, 2, 17, 59, tzinfo=UTC)), dt.date(2026, 11, 1))
        self.assertEqual(A.last_completed_day(dt.datetime(2026, 11, 2, 18, 0, tzinfo=UTC)), dt.date(2026, 11, 2))

    def test_event_counts_on_its_dhaka_date(self):
        self.assertEqual(ev("R", "2026-11-01T18:30:00Z").day, dt.date(2026, 11, 2))  # 00:30 Dhaka
        self.assertEqual(ev("R", "2026-11-01T17:59:00Z").day, dt.date(2026, 11, 1))  # 23:59 Dhaka

    def test_activity_comes_from_the_contribution_calendar(self):
        cal = year_calendar(**{"2026-11-02": 3, "2026-10-05": 2})   # e.g. issues elsewhere, private work
        per_day, _ = A.collect(FakeGitHub([repo("Bouncer")], calendar=cal), LOGIN, NOW)
        self.assertEqual(per_day[DAY], 3)
        self.assertEqual(per_day[dt.date(2026, 10, 5)], 2)


# ---------------------------------------------------------------- releases
class Releases(unittest.TestCase):
    def test_private_fork_foreign_and_profile_excluded(self):
        repos = [repo("Bouncer"), repo("Secret", private=True), repo("Forked", fork=True),
                 repo("Shared", owner="someone"), repo(LOGIN)]
        rels = {r["name"]: [release("2026-11-01T09:00:00Z", name=f"{r['name']} 1.0")] for r in repos}
        gh = FakeGitHub(repos, rels)
        _, releases = A.collect(gh, LOGIN, NOW)
        self.assertEqual({e.repo for e in releases}, {"Bouncer"})
        touched = " ".join(gh.calls)
        for name in ("Secret", "Forked", "Shared"):
            self.assertNotIn(name, touched, "never even ask about it")
        self.assertNotIn(f"/repos/{LOGIN}/{LOGIN}/releases", gh.calls)

    def test_bot_and_draft_releases_ignored(self):
        gh = FakeGitHub([repo("Bouncer")], {"Bouncer": [
            release("2026-11-02T10:00:00Z", tag="v2", draft=True),
            release("2026-11-02T10:00:00Z", tag="v3", bot=True)]})
        _, releases = A.collect(gh, LOGIN, NOW)
        self.assertEqual(releases, [])


# ---------------------------------------------------------------- section
class Section(unittest.TestCase):
    def test_only_the_street(self):
        body = A.render("assets/street.svg?v=2026-11-02", 'say "hi" & <go>')
        self.assertIn('alt="say &quot;hi&quot; &amp; &lt;go&gt;"', body)
        self.assertNotIn("Mom", body)
        self.assertNotIn("<details>", body)
        self.assertTrue(body.rstrip().endswith("</p>"))

    def test_marker_replacement(self):
        readme = f"top\n{A.START}\nold stuff\n{A.END}\nbottom\n"
        self.assertEqual(A.replace_section(readme, "new"), f"top\n{A.START}\nnew\n{A.END}\nbottom\n")
        for broken in ["no markers", f"{A.END}\n{A.START}", f"{A.START}{A.START}{A.END}", f"{A.START} only"]:
            with self.assertRaises(A.DataError):
                A.replace_section(broken, "new")


class EndToEnd(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        d = Path(self.dir.name)
        self.readme, self.svg = d / "README.md", d / "street.svg"
        self.original = f"# hi\n\n{A.START}\nold\n{A.END}\n\nkeep me\n"
        self.readme.write_text(self.original)
        self.args = ["--readme", str(self.readme), "--svg", str(self.svg), "--now", NOW.isoformat()]

    def tearDown(self):
        self.dir.cleanup()

    def gh(self, **kw):
        return FakeGitHub([repo("Bouncer"), repo("Empty")],
                          {"Bouncer": [release("2026-11-02T10:00:00Z")]},
                          calendar=year_calendar(**{"2026-11-01": 1}), **kw)

    def test_writes_section_and_street(self):
        gh = self.gh()
        self.assertEqual(A.main(self.args, gh=gh), 0)
        text = self.readme.read_text()
        self.assertTrue(text.startswith("# hi\n\n" + A.START) and text.endswith(A.END + "\n\nkeep me\n"))
        self.assertIn("street.svg?v=2026-11-02", text)
        self.assertNotIn("Mom", text)
        self.assertNotIn("Ship log", text)
        self.assertIn("load shedding", self.svg.read_text())
        self.assertIn('class="burst"', self.svg.read_text())
        # second run, same day: identical output, nothing rewritten
        self.assertEqual(A.main(self.args, gh=gh), 0)
        self.assertEqual(self.readme.read_text(), text)

    def test_dry_run_writes_nothing(self):
        self.assertEqual(A.main(self.args + ["--dry-run"], gh=self.gh()), 0)
        self.assertEqual(self.readme.read_text(), self.original)
        self.assertFalse(self.svg.exists())

    def test_api_failure_leaves_readme_untouched(self):
        for fail in ("/users/", "Bouncer/releases", "calendar"):
            self.assertEqual(A.main(self.args, gh=self.gh(fail={fail})), 1, fail)
            self.assertEqual(self.readme.read_text(), self.original)
            self.assertFalse(self.svg.exists())

    def test_no_repos_is_treated_as_bad_data_not_inactivity(self):
        self.assertEqual(A.main(self.args, gh=FakeGitHub([])), 1)
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
        self.assertEqual(tips[-1], "Mon 02 Nov: 3 contributions")
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

    def test_street_has_only_a_cng_and_a_rickshaw(self):
        import street
        svg, alt, _ = self.draw()
        self.assertIn('fill="#2e8b57"', svg)        # the CNG
        self.assertIn('fill="#a8241c"', svg)        # the rickshaw hood
        self.assertNotIn("asleep", svg)
        self.assertIn("just a green CNG and a cycle rickshaw", alt)

    def test_no_mom_sign_in_the_picture(self):
        svg, alt, _ = self.draw()
        self.assertNotIn("AMMU SAYS", svg)
        self.assertNotIn("Ammu says", alt)
        self.assertIn("চা", svg)


class Calendar(unittest.TestCase):
    def html(self, n_days=371, tip="{n} contributions on {d}."):
        cells, tips = [], []
        for k in range(n_days):
            d = (dt.date(2026, 11, 3) - dt.timedelta(days=k)).isoformat()
            n = 23 if d == "2026-11-01" else 1 if d == "2026-11-02" else 0
            cells.append(f'<td tabindex="0" data-ix="{k}" data-date="{d}" id="contribution-day-component-{k}" data-level="1" class="ContributionCalendar-day"></td>')
            text = "No contributions on {d}." if n == 0 else ("1 contribution on {d}." if n == 1 else tip)
            tips.append(f'<tool-tip id="t{k}" for="contribution-day-component-{k}" popover="manual">{text.format(n=n, d=d)}</tool-tip>')
        return "<table>" + "".join(cells) + "</table>" + "".join(tips)

    def test_reads_the_public_graph(self):
        days = A.calendar_from_html(self.html())
        self.assertEqual(days[dt.date(2026, 11, 1)], 23)
        self.assertEqual(days[dt.date(2026, 11, 2)], 1)
        self.assertEqual(days[dt.date(2026, 10, 1)], 0)

    def test_thousands_separator(self):
        days = A.calendar_from_html(self.html(tip="1,204 contributions on {d}."))
        self.assertEqual(days[dt.date(2026, 11, 1)], 1204)

    def test_a_page_that_isnt_the_graph_fails(self):
        with self.assertRaises(A.DataError):
            A.calendar_from_html("<html>rate limited</html>")
        with self.assertRaises(A.DataError):
            A.calendar_from_html(self.html(n_days=40))
        with self.assertRaises(A.DataError):
            A.calendar_from_html(self.html().replace("contributions on", "commits on"))

    def test_graphql(self):
        weeks = [{"contributionDays": [{"date": (dt.date(2026, 11, 3) - dt.timedelta(days=w * 7 + k)).isoformat(),
                                         "contributionCount": 2} for k in range(7)]} for w in range(53)]
        data = {"data": {"user": {"contributionsCollection": {"contributionCalendar": {"weeks": weeks}}}}}
        self.assertEqual(A.calendar_from_graphql(data)[DAY], 2)
        for bad in ({"errors": [{"message": "nope"}]}, {"data": {"user": None}}):
            with self.assertRaises(A.DataError):
                A.calendar_from_graphql(bad)

    def test_stale_calendar_is_bad_data_not_inactivity(self):
        old = {d: n for d, n in year_calendar().items() if d < dt.date(2026, 10, 20)}
        with self.assertRaises(A.DataError):
            A.collect(FakeGitHub([repo("Bouncer")], calendar=old), LOGIN, NOW)


if __name__ == "__main__":
    unittest.main()
