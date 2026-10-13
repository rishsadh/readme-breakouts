"""Text and markdown views of a summary.json."""
from .stats import pct

HEADLINE = [
    "pitch_in_first_15", "image_in_first_40", "install_in_first_40", "all_three_top40", "has_badges",
    "has_gif", "has_video", "has_table", "has_comparison_table", "sec_limits", "toc", "translations",
    "asks_for_star", "has_em_dash",
]


def _row(f):
    lo, hi = f["ci"]
    wlo, whi = f["weighted_ci"]
    return (f"{f['k']:>3}/{f['n']:<3} {pct(f['share']):>4} ({100 * lo:.0f}-{100 * hi:.0f})   "
            f"{pct(f['weighted_share']):>4} ({100 * wlo:.0f}-{100 * whi:.0f})")


def terminal(summary, keys=None):
    feats = summary["features"]
    keys = keys or HEADLINE
    width = max(len(feats[k]["label"]) for k in keys)
    pop = summary["population"]["n"]
    out = [f"readme-breakouts  {summary['run_date']}  n={summary['n']} of {pop} breakout repos",
           f"breakout: {summary['definition']}", ""]
    out.append(f"{'feature':<{width}}  {'sample (95% CI)':<21} {'all ' + format(pop, ',') + ' (weighted)'}")
    for k in keys:
        out.append(f"{feats[k]['label']:<{width}}  {_row(feats[k])}")
    nq = summary["numeric"]
    q = nq["pitch_words"]["q"]
    if q:
        out.append("")
        out.append(f"median pitch length {q[2]:.0f} words, median README {nq['length_chars']['q'][2]:,.0f} characters")
    return "\n".join(out)


def markdown(summary):
    f = summary["features"]
    s = summary
    lines = [f"# What {s['n']} breakout repos put in their READMEs", "",
             f"Run date {s['run_date']}. Tool version {s['version']}. All numbers are shares of this one sample, "
             "not of all GitHub repos, and none of them show that a feature causes stars.", "",
             "## Sample", "",
             f"- Breakout means: {s['definition']}.",
             f"- Population found: {s['population']['n']} repos. Sample: {s['n']} READMEs, drawn with seed {s['seed']}, "
             "stratified by a rule-based kind, alternating between the faster and slower half by stars per day.",
             f"- Median stars {s['stars']['q'][2]:,.0f} (quartiles {s['stars']['q'][1]:,.0f} to {s['stars']['q'][3]:,.0f}); "
             f"median {s['stars_per_day']['q'][2]:.1f} stars per day since creation.", "",
             "| Kind | In population | In sample |", "|---|---:|---:|"]
    for k, n in s["population"]["by_kind"].items():
        lines.append(f"| {k} | {n} | {s['by_kind'].get(k, {}).get('n', 0)} |")
    lines += ["", "## Features", "",
              f"Sample share is the plain share of the {s['n']} READMEs, with a 95% Wilson interval. The population estimate "
              "reweights each kind by how many repos it has among all breakouts, because small kinds were sampled more "
              "heavily than large ones; its interval uses the stratified variance. Detector rules are in METHOD.md.", "",
              "| Feature | Count | Sample share | 95% interval | Population estimate | 95% interval |", "|---|---:|---:|---:|---:|---:|"]
    for key, d in f.items():
        lines.append(f"| {d['label']} | {d['k']}/{d['n']} | {pct(d['share'])} | {100 * d['ci'][0]:.0f} to {100 * d['ci'][1]:.0f}% "
                     f"| {pct(d['weighted_share'])} | {100 * d['weighted_ci'][0]:.0f} to {100 * d['weighted_ci'][1]:.0f}% |")
    nq = s["numeric"]
    lines += ["", "## Sizes", "", "| Measure | Min | Q1 | Median | Q3 | Max |", "|---|---:|---:|---:|---:|---:|"]
    labels = {"length_chars": "README characters", "length_lines": "README lines", "pitch_words": "Pitch line, words",
              "image_count": "Images (not badges)", "badge_count": "Badges", "table_count": "Pipe tables",
              "heading_count": "Headings", "code_blocks": "Code blocks", "em_dash_count": "Em dashes"}
    for key, lab in labels.items():
        q = nq[key]["q"]
        if q:
            lines.append(f"| {lab} | " + " | ".join(f"{v:,.0f}" for v in q) + " |")
    t, tr = s["tables_by_type"], s["repos_with_table_type"]
    lines += ["", "## Tables", "",
              "Pipe tables only. The detector cannot read intent, so each table is typed from its heading, the line above it and its header cells.", "",
              "| Type | Tables | READMEs with one |", "|---|---:|---:|"]
    for k in t:
        lines.append(f"| {k.replace('_', ' ')} | {t[k]} | {tr[k]} |")
    lines += ["", "## Install commands", "", "First install or run command found, by package manager.", "",
              "| Kind | READMEs |", "|---|---:|"]
    for k, n in s["install_kinds"].items():
        lines.append(f"| {k} | {n} |")
    sp = s["by_speed"]
    lines += ["", "## Faster and slower breakouts", "",
              f"The sample split at the median of {sp['cut_stars_per_day']:.1f} stars per day since creation "
              f"({sp['fast_n']} faster, {sp['slow_n']} slower). Stars per day is a lifetime average, so a repo that spiked "
              "early and then stalled looks the same as a steady one. This is an association, not a cause.", "",
              f"Adjusted p-values are Holm-corrected across all features, because {len(sp['features'])} comparisons will throw up some "
              "small p-values by chance.", "",
              "| Feature | Faster | Slower | p | Holm p |", "|---|---:|---:|---:|---:|"]
    for key, d in sp["features"].items():
        lines.append(f"| {f[key]['label']} | {d['fast']}/{sp['fast_n']} | {d['slow']}/{sp['slow_n']} | {d['p']:.3f} | {d['p_holm']:.3f} |")
    se = s["sensitivity_stars_per_fork"]
    lines += ["", "## Sensitivity to inflated stars", "",
              "Fake stars were not tested: the stargazer lists that such tests need are no longer public. As a crude check, "
              f"the {se['dropped']} repos with the most stars per fork were dropped and every share was recomputed on the remaining {se['n']}. "
              f"The largest change in any feature share was {100 * se['max_shift']:.1f} percentage points. "
              "Stars per fork is a weak signal, not a fake-star test.", ""]
    lines += ["", "## By kind", "", "Counts inside each kind, for five headline features. Kinds are small, so read these as a description of this sample only.", "",
              "| Kind | n | Pitch in 15 lines | Image in 40 lines | Install in 40 lines | Badges | Comparison table |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for k, d in s["by_kind"].items():
        lines.append(f"| {k} | {d['n']} | {d['pitch_in_first_15']} | {d['image_in_first_40']} | {d['install_in_first_40']} | {d['has_badges']} | {d['has_comparison_table']} |")
    return "\n".join(lines) + "\n"
