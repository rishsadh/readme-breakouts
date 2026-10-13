"""The four steps of a run: sample, fetch, analyze, summarize. Each writes files into one run folder."""
import datetime as dt
import json
import os
import pathlib
import sys

from . import __version__
from .features import BOOL_FEATURES, FEATURE_COLUMNS, NUMERIC_FEATURES, describe
from .github import ApiError, decode_readme
from .sample import (MIN_STARS, POP_COLUMNS, WINDOW_DAYS, draw, enumerate_population, read_csv, write_csv)
from .stats import fisher_two_sided, holm, quantiles, stratified_share, wilson

SAMPLE_COLUMNS = POP_COLUMNS + ["role", "order", "status", "readme_name", "readme_sha", "readme_bytes"]
FEATURE_META = ["full_name", "kind", "stars", "forks", "stars_per_fork", "created_at", "stars_per_day", "language", "owner_type",
                "readme_name", "readme_sha"]


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def cache_dir(run_dir):
    return pathlib.Path(run_dir) / ".cache" / "readmes"


def cache_key(full_name):
    return full_name.replace("/", "__")


def step_sample(client, run_dir, run_date, n=100, seed=20260930, population_csv=None):
    run_dir = pathlib.Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    pop_path = run_dir / "population.csv"
    if population_csv:
        rows = read_csv(population_csv)
        for r in rows:
            r["stars_per_day"] = float(r["stars_per_day"])
        log(f"using population from {population_csv}: {len(rows)} repos")
    else:
        log(f"enumerating breakout repos (created in the last {WINDOW_DAYS} days, >= {MIN_STARS} stars) as of {run_date}")
        rows = enumerate_population(client, run_date, log=log)
    if not population_csv or pathlib.Path(population_csv).resolve() != pop_path.resolve():
        write_csv(pop_path, rows, POP_COLUMNS)
    picked, quotas = draw(rows, n=n, seed=seed)
    for r in picked:
        r.update({"status": "", "readme_name": "", "readme_sha": "", "readme_bytes": ""})
    write_csv(run_dir / "sample.csv", picked, SAMPLE_COLUMNS)
    meta = {"tool": "readme-breakouts", "version": __version__, "run_date": run_date.isoformat(),
            "definition": f"public non-fork repos created in the {WINDOW_DAYS} days up to the run date with at least {MIN_STARS} stars on the run date",
            "population": len(rows), "sample_size": n, "seed": seed, "quotas": quotas,
            "search_api_calls": getattr(client, "calls", 0), "transport": getattr(client, "transport", "file")}
    (run_dir / "run.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    log(f"population {len(rows)}, sample {n} across {len(quotas)} kinds")
    return picked


def step_fetch(client, run_dir):
    """Fetch each selected README (and reserves when one is missing). Resumable: cached files are kept."""
    run_dir = pathlib.Path(run_dir)
    rows = read_csv(run_dir / "sample.csv")
    cdir = cache_dir(run_dir)
    cdir.mkdir(parents=True, exist_ok=True)
    kinds = sorted({r["kind"] for r in rows})
    for kind in kinds:
        group = sorted((r for r in rows if r["kind"] == kind), key=lambda r: int(r["order"]))
        quota = sum(1 for r in group if r["role"] == "selected")
        got = 0
        for r in group:
            if got >= quota:
                r["status"] = "unused"
                continue
            path = cdir / (cache_key(r["full_name"]) + ".md")
            meta_path = cdir / (cache_key(r["full_name"]) + ".json")
            if path.exists() and meta_path.exists():
                m = json.loads(meta_path.read_text(encoding="utf-8"))
            else:
                log(f"  fetching {r['full_name']}")
                try:
                    payload = client.get_json(f"/repos/{r['full_name']}/readme")
                except ApiError as e:
                    r["status"] = f"no_readme_{e.status}"
                    continue
                text, name, sha = decode_readme(payload)
                if not text.strip():
                    r["status"] = "empty_readme"
                    continue
                path.write_text(text, encoding="utf-8")
                m = {"name": name, "sha": sha, "bytes": len(text.encode("utf-8"))}
                meta_path.write_text(json.dumps(m), encoding="utf-8")
            r.update({"status": "ok", "readme_name": m["name"], "readme_sha": m["sha"], "readme_bytes": m["bytes"]})
            got += 1
        write_csv(run_dir / "sample.csv", rows, SAMPLE_COLUMNS)
        log(f"{kind}: {got}/{quota} READMEs")
    return rows


def step_analyze(run_dir):
    run_dir = pathlib.Path(run_dir)
    rows = [r for r in read_csv(run_dir / "sample.csv") if r["status"] == "ok"]
    out = []
    for r in rows:
        text = (cache_dir(run_dir) / (cache_key(r["full_name"]) + ".md")).read_text(encoding="utf-8")
        feats = describe(text)
        rec = {k: r[k] for k in FEATURE_META}
        rec.update({k: feats[k] for k in FEATURE_COLUMNS})
        out.append(rec)
    write_csv(run_dir / "features.csv", out, FEATURE_META + FEATURE_COLUMNS)
    log(f"features for {len(out)} READMEs")
    return out


def _truthy(v):
    return v is True or str(v).lower() == "true"


def summarize(run_dir):
    run_dir = pathlib.Path(run_dir)
    rows = read_csv(run_dir / "features.csv")
    run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    pop = read_csv(run_dir / "population.csv")
    n = len(rows)

    by_kind_rows = {}
    for r in rows:
        by_kind_rows.setdefault(r["kind"], []).append(r)
    pop_sizes = _count(pop, "kind")
    sample_sizes = {k: len(v) for k, v in by_kind_rows.items()}
    feats = {}
    for key, label in BOOL_FEATURES:
        k = sum(1 for r in rows if _truthy(r[key]))
        lo, hi = wilson(k, n)
        feats[key] = {"label": label, "k": k, "n": n, "share": k / n if n else 0, "ci": [lo, hi]}
        hits = {kind: sum(1 for r in v if _truthy(r[key])) for kind, v in by_kind_rows.items()}
        ws, (wlo, whi) = stratified_share(pop_sizes, hits, sample_sizes)
        feats[key].update({"weighted_share": ws, "weighted_ci": [wlo, whi]})

    numeric = {}
    for key in NUMERIC_FEATURES:
        vals = [float(r[key]) for r in rows if r[key] != ""]
        numeric[key] = {"n": len(vals), "q": quantiles(vals)}

    kinds = {}
    for r in rows:
        kinds.setdefault(r["kind"], []).append(r)
    headline = ["pitch_in_first_15", "image_in_first_40", "install_in_first_40", "has_badges", "has_comparison_table"]
    by_kind = {k: {"n": len(v), **{h: sum(1 for r in v if _truthy(r[h])) for h in headline}} for k, v in sorted(kinds.items())}

    ranked = sorted(rows, key=lambda r: (-float(r["stars_per_day"]), r["full_name"]))
    half = n // 2
    fast, slow = ranked[:half], ranked[half:]
    speed = {"fast_n": len(fast), "slow_n": len(slow),
             "cut_stars_per_day": float(ranked[half - 1]["stars_per_day"]) if half else None, "features": {}}
    raw_p = []
    for key, _ in BOOL_FEATURES:
        a = sum(1 for r in fast if _truthy(r[key]))
        c = sum(1 for r in slow if _truthy(r[key]))
        p = fisher_two_sided(a, len(fast) - a, c, len(slow) - c) if fast and slow else 1.0
        speed["features"][key] = {"fast": a, "slow": c, "p": p}
        raw_p.append(p)
    for (key, _), adj in zip(BOOL_FEATURES, holm(raw_p)):
        speed["features"][key]["p_holm"] = adj

    by_spf = sorted(rows, key=lambda r: float(r["stars_per_fork"]) if r["stars_per_fork"] != "" else float("inf"))
    drop = n // 10
    kept = by_spf[: n - drop] if drop else by_spf
    sens = {"dropped": drop, "n": len(kept), "features": {}}
    for key, _ in BOOL_FEATURES:
        sens["features"][key] = sum(1 for r in kept if _truthy(r[key])) / len(kept) if kept else 0
    sens["max_shift"] = max(abs(sens["features"][k] - feats[k]["share"]) for k in feats)

    tables = {k: sum(int(r[f"tables_{k}"]) for r in rows) for k in ("comparison", "results", "support_matrix", "reference", "other")}
    install_kinds = {}
    for r in rows:
        if r["install_kind"]:
            install_kinds[r["install_kind"]] = install_kinds.get(r["install_kind"], 0) + 1
    summary = {
        "tool": "readme-breakouts", "version": __version__, "run_date": run["run_date"],
        "definition": run["definition"], "population": {"n": len(pop), "by_kind": _count(pop, "kind")},
        "n": n, "seed": run["seed"], "quotas": run["quotas"], "features": feats, "numeric": numeric,
        "by_kind": by_kind, "by_speed": speed, "sensitivity_stars_per_fork": sens, "tables_by_type": tables,
        "repos_with_table_type": {k: sum(1 for r in rows if int(r[f"tables_{k}"]) > 0) for k in tables},
        "install_kinds": dict(sorted(install_kinds.items(), key=lambda kv: -kv[1])),
        "stars_per_day": {"q": quantiles([float(r["stars_per_day"]) for r in rows])},
        "stars": {"q": quantiles([float(r["stars"]) for r in rows])},
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary


def _count(rows, key):
    out = {}
    for r in rows:
        out[r[key]] = out.get(r[key], 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def today():
    return dt.date.today()
