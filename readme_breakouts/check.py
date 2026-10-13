"""Compare one README against the breakout benchmark shipped with this tool."""
import json
import pathlib

from .features import BOOL_FEATURES, describe
from .stats import pct

HERE = pathlib.Path(__file__).resolve().parent
BENCHMARK = HERE / "benchmark.json"

KEYS = [
    "pitch_in_first_15", "image_in_first_40", "install_in_first_40", "all_three_top40", "has_badges",
    "has_gif", "has_video", "has_table", "has_comparison_table", "sec_limits", "sec_usage", "sec_license",
    "toc", "translations", "asks_for_star", "has_em_dash",
]


def load_benchmark(path=None):
    p = pathlib.Path(path) if path else BENCHMARK
    return json.loads(p.read_text(encoding="utf-8"))


def compare(text, benchmark, keys=None):
    """Return (rows, extras). Each row: label, yours (bool), share (float) of the benchmark sample."""
    feats = describe(text)
    keys = keys or KEYS
    labels = dict(BOOL_FEATURES)
    rows = [{"key": k, "label": labels[k], "yours": bool(feats[k]), "share": benchmark["features"][k]["share"],
             "weighted": benchmark["features"][k].get("weighted_share"),
             "k": benchmark["features"][k]["k"], "n": benchmark["features"][k]["n"]} for k in keys]
    nq = benchmark["numeric"]
    extras = {
        "pitch_words": (feats["pitch_words"] or 0, nq["pitch_words"]["q"][2] if nq["pitch_words"]["q"] else None),
        "length_chars": (feats["length_chars"], nq["length_chars"]["q"][2]),
        "image_count": (feats["image_count"], nq["image_count"]["q"][2]),
        "first_image_line": feats["first_image_line"],
        "install_kind": feats["install_kind"],
    }
    return rows, extras, feats


def render(name, rows, extras, benchmark):
    width = max(len(r["label"]) for r in rows)
    out = [f"{name}  vs {benchmark['n']} breakout READMEs ({benchmark['run_date']})", "",
           f"{'feature':<{width}}  yours  sample of {benchmark['n']}   all breakouts (est.)"]
    for r in rows:
        est = pct(r["weighted"]) if r["weighted"] is not None else "n/a"
        out.append(f"{r['label']:<{width}}  {'yes' if r['yours'] else 'no':<5}  {r['k']}/{r['n']} ({pct(r['share'])})".ljust(width + 26) + f"  {est}")
    pw, pm = extras["pitch_words"]
    lc, lm = extras["length_chars"]
    out += ["", f"pitch length: {pw or 'none found'} words (median {pm:.0f})" if pm is not None else "",
            f"README length: {lc:,} characters (median {lm:,.0f})",
            f"first image: {'line ' + str(extras['first_image_line']) if extras['first_image_line'] else 'none'}",
            f"install command: {extras['install_kind'] or 'none found'}", "",
            "Shares describe one sample of breakout READMEs. They are not a target and do not show cause."]
    return "\n".join(x for x in out if x is not None)
