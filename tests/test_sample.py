import datetime as dt
import pathlib
import tempfile
import unittest

from readme_breakouts.pipeline import SAMPLE_COLUMNS
from readme_breakouts.sample import (KINDS, POP_COLUMNS, allocate, classify_kind, draw, enumerate_population, to_row,
                                     write_csv)


def item(name, stars=2000, created="2026-03-01T10:00:00Z", topics=None, desc="", **kw):
    d = {"full_name": f"o/{name}", "name": name, "description": desc, "topics": topics or [],
         "stargazers_count": stars, "forks_count": 10, "open_issues_count": 1, "created_at": created,
         "pushed_at": created, "language": "Python", "owner": {"type": "User"}, "archived": False,
         "license": {"spdx_id": "MIT"}}
    d.update(kw)
    return d


class Kinds(unittest.TestCase):
    def test_rules(self):
        cases = [("awesome-foo", "a list", [], "awesome-list"), ("x", "", ["mcp", "server"], "mcp-server"),
                 ("x", "an agent harness", [], "agent-or-skill"), ("x", "a vision model", [], "ai-model-or-research"),
                 ("x", "", ["cli"], "cli-tool"), ("x", "a typed sdk", [], "library-or-framework"),
                 ("x", "desktop client", [], "app"), ("x", "a free course", [], "learning"),
                 ("x", "something", [], "other")]
        for name, desc, topics, kind in cases:
            with self.subTest(kind=kind):
                self.assertEqual(classify_kind(name, desc, topics), kind)

    def test_precedence_agent_before_model(self):
        self.assertEqual(classify_kind("x", "agent for model training", []), "agent-or-skill")

    def test_hyphenated_topic(self):
        self.assertEqual(classify_kind("x", "", ["command-line"], ), "cli-tool")
        self.assertIn(classify_kind("x", "", ["self-hosted"]), KINDS)


class Rows(unittest.TestCase):
    def test_to_row(self):
        r = to_row(item("a", stars=3650, created="2026-03-01T00:00:00Z"), dt.date(2026, 9, 30))
        self.assertEqual(r["full_name"], "o/a")
        self.assertEqual(r["created_at"], "2026-03-01")
        self.assertAlmostEqual(r["age_days"], 213.0, delta=1)
        self.assertAlmostEqual(r["stars_per_day"], 3650 / 214, delta=0.5)
        self.assertEqual(r["stars_per_fork"], 365.0)

    def test_noassertion_license_blank_and_new_repo_age_floor(self):
        r = to_row(item("a", license={"spdx_id": "NOASSERTION"}, created="2026-09-30T05:00:00Z"), dt.date(2026, 9, 30))
        self.assertEqual(r["license"], "")
        self.assertGreaterEqual(r["age_days"], 1.0)


class NoDescriptions(unittest.TestCase):
    """Repo descriptions are read to classify kind and must never reach a published file."""

    def test_row_and_columns_carry_no_description(self):
        r = to_row(item("a", desc="mail me at someone@example.com"), dt.date(2026, 9, 30))
        self.assertNotIn("description", r)
        self.assertNotIn("description", POP_COLUMNS)
        self.assertNotIn("description", SAMPLE_COLUMNS)
        self.assertNotIn("someone@example.com", " ".join(str(v) for v in r.values()))

    def test_description_still_drives_kind(self):
        r = to_row(item("a", desc="an agent harness"), dt.date(2026, 9, 30))
        self.assertEqual(r["kind"], "agent-or-skill")

    def test_write_csv_refuses_a_description_column(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                write_csv(pathlib.Path(d) / "x.csv", [{"description": "x"}], ["description"])

    def test_written_data_files_have_no_description_column(self):
        data = pathlib.Path(__file__).resolve().parent.parent / "data"
        for f in data.glob("*/*.csv"):
            header = f.read_text(encoding="utf-8").splitlines()[0].split(",")
            self.assertNotIn("description", header, f.name)


class Allocation(unittest.TestCase):
    def test_sums_to_total_and_respects_sizes(self):
        sizes = {"a": 1000, "b": 500, "c": 3, "d": 40}
        alloc = allocate(sizes, 50, min_each=5)
        self.assertEqual(sum(alloc.values()), 50)
        self.assertEqual(alloc["c"], 3)
        self.assertTrue(all(alloc[k] <= sizes[k] for k in sizes))
        self.assertGreater(alloc["a"], alloc["b"])

    def test_small_population_takes_all(self):
        self.assertEqual(allocate({"a": 4, "b": 3}, 100), {"a": 4, "b": 3})

    def test_floor_applies(self):
        alloc = allocate({"a": 5000, "b": 10}, 20, min_each=5)
        self.assertEqual(alloc["b"], 5)


class Drawing(unittest.TestCase):
    def pop(self):
        rows = []
        for i in range(120):
            rows.append(to_row(item(f"r{i}", stars=1000 + i * 37, desc="an agent thing" if i % 2 else "a cli",
                                    topics=[] if i % 2 else ["cli"], created=f"2026-0{1 + i % 8}-10T00:00:00Z"),
                               dt.date(2026, 9, 30)))
        return rows

    def test_deterministic(self):
        a, qa = draw(self.pop(), n=30, seed=1)
        b, qb = draw(self.pop(), n=30, seed=1)
        self.assertEqual([r["full_name"] for r in a], [r["full_name"] for r in b])
        self.assertEqual(qa, qb)

    def test_seed_changes_draw(self):
        a, _ = draw(self.pop(), n=30, seed=1)
        b, _ = draw(self.pop(), n=30, seed=2)
        self.assertNotEqual([r["full_name"] for r in a], [r["full_name"] for r in b])

    def test_counts_and_reserves(self):
        rows, quotas = draw(self.pop(), n=30, seed=3, reserve_each=2)
        sel = [r for r in rows if r["role"] == "selected"]
        self.assertEqual(len(sel), 30)
        for kind, q in quotas.items():
            self.assertEqual(sum(1 for r in sel if r["kind"] == kind), q)
            self.assertEqual(sum(1 for r in rows if r["kind"] == kind and r["role"] == "reserve"), 2)
        self.assertEqual(len({r["full_name"] for r in rows}), len(rows))

    def test_both_speed_halves_represented(self):
        rows, _ = draw(self.pop(), n=30, seed=3)
        sel = [r for r in rows if r["role"] == "selected" and r["kind"] == "cli-tool"]
        speeds = sorted(float(r["stars_per_day"]) for r in sel)
        allspeeds = sorted(float(r["stars_per_day"]) for r in self.pop() if r["kind"] == "cli-tool")
        median = allspeeds[len(allspeeds) // 2]
        self.assertTrue(speeds[0] < median < speeds[-1])


class FakeSearch:
    """Serves search pages from a list of repos, honouring created: windows and the 1000-result cap."""
    def __init__(self, repos):
        self.repos, self.calls, self.queries = repos, 0, []

    def get_json(self, path, params=None, accept=None):
        self.calls += 1
        q = params["q"]
        self.queries.append(q)
        rng = q.split("created:")[1].split(" ")[0]
        a, b = rng.split("..")
        hits = [r for r in self.repos if a <= r["created_at"][:10] <= b]
        hits.sort(key=lambda r: -r["stargazers_count"])
        page, per = params["page"], params["per_page"]
        window = hits[:1000]
        return {"total_count": len(hits), "items": window[(page - 1) * per: page * per]}


class Enumerate(unittest.TestCase):
    def test_splits_windows_over_1000(self):
        repos = [item(f"n{i}", stars=1000 + i, created="2026-09-01T00:00:00Z") for i in range(600)]
        repos += [item(f"m{i}", stars=1000 + i, created="2026-09-20T00:00:00Z") for i in range(600)]
        fake = FakeSearch(repos)
        rows = enumerate_population(fake, dt.date(2026, 9, 30), days=30, step=30, log=lambda m: None)
        self.assertEqual(len(rows), 1200)
        self.assertEqual(len({r["full_name"] for r in rows}), 1200)

    def test_window_bounds(self):
        fake = FakeSearch([item("old", created="2024-01-01T00:00:00Z"), item("new", created="2026-09-01T00:00:00Z")])
        rows = enumerate_population(fake, dt.date(2026, 9, 30), log=lambda m: None)
        self.assertEqual([r["full_name"] for r in rows], ["o/new"])
        self.assertTrue(all("stars:>=1000" in q for q in fake.queries))


if __name__ == "__main__":
    unittest.main()
