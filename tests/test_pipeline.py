import base64
import contextlib
import datetime as dt
import io
import json
import pathlib
import tempfile
import unittest

from readme_breakouts import check, cli, pipeline, report
from readme_breakouts.github import ApiError
from readme_breakouts.sample import POP_COLUMNS, to_row, write_csv
from tests.test_sample import item

GOOD = "# {n}\n\n![s](docs/s.png)\n\n{n} turns markdown notes into a fast static site.\n\n```sh\nnpx {n}\n```\n\n## Usage\nx\n"
BARE = "# {n}\n\nx\n"


def readme_payload(text):
    return {"content": base64.b64encode(text.encode()).decode(), "encoding": "base64", "name": "README.md", "sha": "s" + str(len(text))}


class FakeClient:
    calls = 0
    transport = "fake"

    def __init__(self, missing=(), bare=()):
        self.missing, self.bare, self.asked = set(missing), set(bare), []

    def get_json(self, path, params=None, accept=None):
        repo = path.split("/repos/")[1].rsplit("/readme", 1)[0]
        self.asked.append(repo)
        if repo in self.missing:
            raise ApiError(404, "Not Found")
        name = repo.split("/")[1]
        return readme_payload((BARE if repo in self.bare else GOOD).format(n=name))


def population(n=60):
    rows = []
    for i in range(n):
        kind_bits = [("an agent tool", []), ("a cli", ["cli"]), ("a typed sdk", [])][i % 3]
        rows.append(to_row(item(f"r{i}", stars=1000 + 17 * i, desc=kind_bits[0], topics=kind_bits[1],
                                created=f"2026-0{1 + i % 8}-15T00:00:00Z"), dt.date(2026, 9, 30)))
    return rows


class EndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self.tmp.name) / "run"
        self.pop_csv = pathlib.Path(self.tmp.name) / "pop.csv"
        write_csv(self.pop_csv, population(), POP_COLUMNS)
        pipeline.log = lambda m: None

    def tearDown(self):
        self.tmp.cleanup()

    def run_all(self, client):
        pipeline.step_sample(client, self.dir, dt.date(2026, 9, 30), n=15, seed=7, population_csv=self.pop_csv)
        rows = pipeline.step_fetch(client, self.dir)
        pipeline.step_analyze(self.dir)
        return rows, pipeline.summarize(self.dir)

    def test_full_run(self):
        rows, summary = self.run_all(FakeClient())
        self.assertEqual(summary["n"], 15)
        self.assertEqual(summary["population"]["n"], 60)
        f = summary["features"]
        self.assertEqual(f["install_in_first_40"]["k"], 15)
        self.assertEqual(f["has_badges"]["k"], 0)
        self.assertAlmostEqual(f["image_in_first_40"]["share"], 1.0)
        self.assertEqual(summary["install_kinds"], {"npm": 15})
        self.assertEqual(summary["by_speed"]["fast_n"] + summary["by_speed"]["slow_n"], 15)
        for name in ("population.csv", "sample.csv", "features.csv", "summary.json", "run.json"):
            self.assertTrue((self.dir / name).exists(), name)
        self.assertEqual(sum(1 for r in rows if r["status"] == "ok"), 15)

    def test_missing_readme_is_replaced_from_the_same_kind(self):
        pipeline.step_sample(FakeClient(), self.dir, dt.date(2026, 9, 30), n=15, seed=7, population_csv=self.pop_csv)
        chosen = [r for r in pipeline.read_csv(self.dir / "sample.csv") if r["role"] == "selected"][0]
        rows = pipeline.step_fetch(FakeClient(missing={chosen["full_name"]}), self.dir)
        by = {r["full_name"]: r for r in rows}
        self.assertEqual(by[chosen["full_name"]]["status"], "no_readme_404")
        ok_in_kind = [r for r in rows if r["kind"] == chosen["kind"] and r["status"] == "ok"]
        quota = sum(1 for r in rows if r["kind"] == chosen["kind"] and r["role"] == "selected")
        self.assertEqual(len(ok_in_kind), quota)
        self.assertTrue(any(r["role"] == "reserve" and r["status"] == "ok" for r in ok_in_kind))

    def test_fetch_is_resumable(self):
        client = FakeClient()
        self.run_all(client)
        again = FakeClient()
        pipeline.step_fetch(again, self.dir)
        self.assertEqual(again.asked, [])

    def test_summary_is_reproducible_from_same_population_and_seed(self):
        _, a = self.run_all(FakeClient())
        first = (self.dir / "features.csv").read_text(encoding="utf-8")
        _, b = self.run_all(FakeClient())
        self.assertEqual(first, (self.dir / "features.csv").read_text(encoding="utf-8"))
        self.assertEqual(a["features"]["pitch_in_first_15"], b["features"]["pitch_in_first_15"])

    def test_report_renders(self):
        _, summary = self.run_all(FakeClient(bare={"o/r1"}))
        text = report.terminal(summary)
        self.assertIn("n=15 of 60", text)
        md = report.markdown(summary)
        self.assertIn("| Feature | Count | Sample share | 95% interval | Population estimate | 95% interval |", md)
        self.assertIn("Holm", md)
        self.assertNotIn("—", md)

    def test_check_against_benchmark(self):
        _, summary = self.run_all(FakeClient())
        bench = self.dir / "summary.json"
        readme = pathlib.Path(self.tmp.name) / "README.md"
        readme.write_text(BARE.format(n="thing"), encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            cli.main(["check", str(readme), "--benchmark", str(bench)])
        text = out.getvalue()
        self.assertIn("vs 15 breakout READMEs", text)
        self.assertIn("Image (not a badge) in the first 40 lines", text)
        self.assertIn("15/15 (100%)", text)
        self.assertIn("do not show cause", text)

    def test_check_json(self):
        self.run_all(FakeClient())
        readme = pathlib.Path(self.tmp.name) / "README.md"
        readme.write_text(GOOD.format(n="thing"), encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            cli.main(["check", str(readme), "--benchmark", str(self.dir / "summary.json"), "--json"])
        data = json.loads(out.getvalue())
        self.assertTrue(data["features"]["install_in_first_40"])
        self.assertEqual(data["benchmark_date"], "2026-09-30")

    def test_features_command(self):
        readme = pathlib.Path(self.tmp.name) / "R.md"
        readme.write_text(GOOD.format(n="thing"), encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            cli.main(["features", str(readme)])
        self.assertTrue(json.loads(out.getvalue())["pitch_in_first_15"])


class Bundled(unittest.TestCase):
    def test_bundled_benchmark_is_consistent(self):
        if not check.BENCHMARK.exists():
            self.skipTest("no bundled benchmark yet")
        b = check.load_benchmark()
        self.assertEqual(b["n"], 100)
        for key, d in b["features"].items():
            self.assertLessEqual(d["k"], d["n"], key)
            lo, hi = d["ci"]
            self.assertLessEqual(lo, d["share"] + 1e-9)
            self.assertGreaterEqual(hi, d["share"] - 1e-9)


if __name__ == "__main__":
    unittest.main()
