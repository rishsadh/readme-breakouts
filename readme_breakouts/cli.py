"""Command line entry: python -m readme_breakouts <command>."""
import argparse
import json
import pathlib
import re
import shutil
import sys

from . import __version__, check as check_mod, pipeline, report
from .features import describe
from .github import ApiError, Client, decode_readme

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _client(args):
    return Client(delay=args.delay, transport=args.transport)


def _run_dir(args):
    return pathlib.Path(args.dir) if args.dir else ROOT / "data" / pipeline.today().isoformat()


def cmd_run(args):
    run_dir = _run_dir(args)
    client = _client(args)
    run_date = pipeline.dt.date.fromisoformat(args.date) if args.date else pipeline.today()
    pipeline.step_sample(client, run_dir, run_date, n=args.n, seed=args.seed, population_csv=args.population)
    pipeline.step_fetch(client, run_dir)
    pipeline.step_analyze(run_dir)
    summary = pipeline.summarize(run_dir)
    _bundle(summary, run_dir, args)
    print(report.terminal(summary))
    return 0


def cmd_sample(args):
    run_date = pipeline.dt.date.fromisoformat(args.date) if args.date else pipeline.today()
    pipeline.step_sample(_client(args), _run_dir(args), run_date, n=args.n, seed=args.seed, population_csv=args.population)
    return 0


def cmd_fetch(args):
    pipeline.step_fetch(_client(args), _run_dir(args))
    return 0


def cmd_analyze(args):
    run_dir = _run_dir(args)
    pipeline.step_analyze(run_dir)
    summary = pipeline.summarize(run_dir)
    _bundle(summary, run_dir, args)
    print(report.terminal(summary))
    return 0


def _bundle(summary, run_dir, args):
    """Copy the summary next to the code so `check` works from an installed package."""
    if not args.no_bundle:
        shutil.copyfile(pathlib.Path(run_dir) / "summary.json", check_mod.BENCHMARK)


def cmd_report(args):
    path = pathlib.Path(args.summary) if args.summary else (_run_dir(args) / "summary.json")
    summary = json.loads(path.read_text(encoding="utf-8")) if path.exists() else check_mod.load_benchmark()
    if args.markdown:
        out = report.markdown(summary)
        if args.write:
            pathlib.Path(args.write).write_text(out, encoding="utf-8")
            print(f"wrote {args.write}")
        else:
            print(out)
    else:
        print(report.terminal(summary))
    return 0


def _read_target(target, args):
    p = pathlib.Path(target)
    if p.is_file():
        return p.read_text(encoding="utf-8", errors="replace"), p.name
    if re.fullmatch(r"[\w.-]+/[\w.-]+", target):
        try:
            payload = _client(args).get_json(f"/repos/{target}/readme")
        except ApiError as e:
            sys.exit(f"could not fetch the README of {target}: {e}")
        return decode_readme(payload)[0], target
    sys.exit(f"{target}: not a file, and not an owner/repo")


def cmd_check(args):
    benchmark = check_mod.load_benchmark(args.benchmark)
    text, name = _read_target(args.target, args)
    rows, extras, feats = check_mod.compare(text, benchmark)
    if args.json:
        print(json.dumps({"target": name, "benchmark_date": benchmark["run_date"], "features": feats,
                          "compared": rows}, indent=2))
    else:
        print(check_mod.render(name, rows, extras, benchmark))
    return 0


def cmd_features(args):
    text, _ = _read_target(args.target, args)
    print(json.dumps(describe(text), indent=2))
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="readme-breakouts", description=__doc__)
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp, network=True):
        sp.add_argument("--dir", help="run folder (default data/<today>)")
        if network:
            sp.add_argument("--delay", type=float, default=3.0, help="seconds between GitHub API calls (default 3)")
            sp.add_argument("--transport", choices=["auto", "token", "gh", "anon"], default="auto")

    def sampling(sp):
        sp.add_argument("--n", type=int, default=100)
        sp.add_argument("--seed", type=int, default=20260930)
        sp.add_argument("--date", help="run date, YYYY-MM-DD (default today)")
        sp.add_argument("--population", help="reuse a population.csv instead of searching GitHub")

    sp = sub.add_parser("run", help="sample, fetch, analyze and report in one go")
    common(sp); sampling(sp); sp.add_argument("--no-bundle", action="store_true", help="do not update the bundled benchmark")
    sp.set_defaults(fn=cmd_run)
    sp = sub.add_parser("sample", help="enumerate the population and draw the sample")
    common(sp); sampling(sp); sp.set_defaults(fn=cmd_sample)
    sp = sub.add_parser("fetch", help="download the sampled READMEs into the run's cache")
    common(sp); sp.set_defaults(fn=cmd_fetch)
    sp = sub.add_parser("analyze", help="detect features in cached READMEs and write features.csv and summary.json")
    common(sp, network=False); sp.add_argument("--no-bundle", action="store_true"); sp.set_defaults(fn=cmd_analyze)
    sp = sub.add_parser("report", help="print the headline table, or the full markdown report")
    common(sp, network=False)
    sp.add_argument("--summary", help="a summary.json (default: the run folder's, else the bundled one)")
    sp.add_argument("--markdown", action="store_true"); sp.add_argument("--write", help="write markdown to this file")
    sp.set_defaults(fn=cmd_report)
    sp = sub.add_parser("check", help="compare a README file, or owner/repo, with the breakout benchmark")
    sp.add_argument("target"); sp.add_argument("--benchmark", help="a summary.json (default: the bundled one)")
    sp.add_argument("--json", action="store_true"); sp.add_argument("--delay", type=float, default=3.0)
    sp.add_argument("--transport", choices=["auto", "token", "gh", "anon"], default="auto"); sp.set_defaults(fn=cmd_check)
    sp = sub.add_parser("features", help="print every detected feature of one README as JSON")
    sp.add_argument("target"); sp.add_argument("--delay", type=float, default=3.0)
    sp.add_argument("--transport", choices=["auto", "token", "gh", "anon"], default="auto"); sp.set_defaults(fn=cmd_features)
    return p


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)
    try:
        return args.fn(args)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
