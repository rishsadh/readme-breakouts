# Method

Run date 2026-09-30. Everything below describes the run stored in `data/2026-09-30/`. A later run writes a new dated folder and leaves this one alone.

## What "breakout" means here

A public, non-fork repository created in the 365 days up to the run date (2025-10-01 to 2026-09-30) that has at least 1,000 stars on the run date. Stars are read on the run date, so a repo that later gains or loses stars keeps its row.

The population is every repo the GitHub search API returns for that rule, not a trending list. The search was run in 30-day created windows, with a window split in half whenever it held more than the 1,000 results search will return. Every window returned as many repos as the API said it held. The run found 3,806 repos in 54 API calls, retries included. Archived repos are kept (43 of them).

Source: `GET /search/repositories`, query `created:A..B stars:>=1000`, read on 2026-09-30.

## Kinds

Each repo gets one kind from a fixed rule over its name, description and topics. The first rule that matches wins, in this order. Descriptions are read during this step and are not published: the CSVs in `data/` carry the kind that came out of the rule, never the description text.

1. awesome-list: name or topics contain "awesome", or the description says "curated list" or "collection of"
2. mcp-server: "mcp" or "model context protocol"
3. agent-or-skill: agent, skill, Claude, Codex, Cursor, Copilot, prompt and similar words
4. ai-model-or-research: model, LLM, paper, benchmark, dataset, inference, diffusion, RAG, AI and similar words
5. cli-tool: cli, terminal, tui, command line
6. library-or-framework: library, framework, sdk, package, toolkit, api, engine
7. app: app, desktop, extension, browser, plugin, dashboard, editor, game, platform and similar words
8. learning: tutorial, course, guide, roadmap, book, interview, cheatsheet
9. other

The rules are in `readme_breakouts/sample.py`. They are crude. A read of about 35 sampled rows found plenty of repos a person would file elsewhere, so the kinds exist to spread the sample out, not to say what a repo is.

| Kind | Repos | Sample |
|---|---:|---:|
| agent-or-skill | 1,566 | 28 |
| other | 675 | 15 |
| ai-model-or-research | 488 | 12 |
| mcp-server | 331 | 10 |
| app | 292 | 9 |
| library-or-framework | 168 | 7 |
| awesome-list | 154 | 7 |
| cli-tool | 100 | 6 |
| learning | 32 | 6 |

## The sample

- 100 repos. Each kind gets at least 5 (or all of it, if smaller), and the rest are shared out in proportion to kind size by largest remainder.
- Inside a kind, repos are ranked by lifetime stars per day (stars divided by days since creation). The ranking is cut into a faster half and a slower half, both are shuffled with seed 20260930, and picks alternate between them. So every kind holds both fast and slow climbers.
- Four reserves per kind are drawn the same way. A reserve is used only when a selected repo has no README. In this run no reserve was needed: all 100 selected repos had one.
- Because small kinds are sampled more heavily than large ones, the plain share of the 100 is not an estimate for all 3,806. The report therefore gives two numbers for every feature: the sample share, and a population estimate that reweights each kind by its share of the population (post-stratification). The interval on the estimate uses the stratified variance, turned into a Wilson interval on an effective sample size. In this run the two numbers are within five points of each other for every feature.

`python -m readme_breakouts sample --population data/2026-09-30/population.csv` redraws the same sample from the saved population.

## Reading the READMEs

`GET /repos/{owner}/{repo}/readme`, which returns the README of the default branch, read 2026-09-30. The git blob SHA of each README is in `sample.csv`, so a later reader can tell whether a README has changed. The README texts are not in this repo: they belong to their authors. Fetched copies sit in a git-ignored `.cache` folder, and `features.csv` holds only what the detectors found.

Calls were spaced 3 seconds apart, with a 65-second wait after any 403 or 429. Only read endpoints are used.

## Feature detectors

All detectors are plain rules in `readme_breakouts/features.py`, run on the README text. Line numbers count every line of the file. "First 40 lines" and "first 4,000 characters" are two ways of saying above the fold; both are reported because two different people would pick two different definitions. HTML comments are blanked out and fenced code blocks are ignored by every detector except the install one.

| Feature | Rule |
|---|---|
| Pitch | The first prose line, bold line or tagline sub-heading (level 2 to 6, at least 4 words) in the window. It skips the title, badges, image links, navigation links, translation links, tables, lists, code, wrapped HTML attributes and section headings like Installation |
| Image | A markdown, reference-style or HTML image that is not a badge. Badges are recognised by URL: shields.io, badge paths and files, codecov, trendshift, visitor counters, deploy buttons and similar |
| Not a logo | An image whose URL or alt text does not contain logo, icon, favicon, wordmark, avatar, brand or a trailing "mark" |
| GIF, video | A `.gif` image. A `<video>` tag, a YouTube, Vimeo, Loom or Bilibili link, a `.mp4`, `.webm` or `.mov` link, or a bare GitHub user-attachments link |
| Badges | The count of badge images |
| Install or run command | A line in a code block, or an inline code span, that starts with a package-manager, container or script command: npm, npx, pnpm, yarn, bun, pip, pipx, uv, conda, brew, cargo, go, docker, curl or wget piped to a shell, apt and similar, `bash install.sh`, `gh extension install`, `claude mcp add`, `/plugin install` |
| Dev setup | Bare `npm install`, `pip install -r`, `pip install -e .`, `uv sync`, `poetry install`, `make build`. Counted on its own, not as an install |
| git clone | A `git clone` line. Counted on its own, not as an install |
| Pipe table | A header row followed by a separator row. HTML tables are only counted, not typed |
| Table type | comparison when the heading says compare, vs, versus, alternative, different, why not, not another, unlike, instead of or rather than, or the line above says compare, vs or alternative, or a header cell says compare, alternative or difference. Otherwise results (benchmark, score, latency and similar), support matrix (two or more columns of check marks), reference (options, flags, variables, commands and similar) or other |
| Section headings | Regexes over the heading text for install, usage, features, why or about, comparison, limitations, demo, roadmap, contributing, license, FAQ, citation, sponsors, community and star history. Sponsor, community, star-history and BibTeX links also count without a heading |
| Table of contents | A contents heading, or five or more in-page anchor links |
| Translations | A link to a `README.xx.md` style file, or two or more language names in the first 30 lines |
| Centered header | `align="center"` or `<center>` in the first 15 lines |
| Asks for a star | Phrases like "give it a star", "star this repo", "leave a star" in prose |
| Em dash | The character U+2014 in prose outside code |

## How well the detectors work

I read the detector output against the READMEs by hand. The detail of the disagreements is in `data/2026-09-30/hand-checks.csv`.

- Pitch in the first 15 lines: 82 flagged. Six were not a pitch (an author list, a deprecation notice, three bylines, a website link line), so about 93% of flags are right. Of the 18 not flagged, 17 have a pitch between lines 16 and 34 and one has none. The 15-line window mostly penalises long centered HTML headers, which is why the first-40-lines number (99%) is reported beside it.
- Image: the first version counted five badge-like images as images (a skills.sh badge, a badge.php badge, a badge folder, a Weblate badge, a coffee button). The badge rules were extended and the run repeated. I then read the top of every README with no image found and found no missed image.
- Install or run command: 63 flagged. I judged 13 to be installs of a dependency or environment rather than the repo's own tool, so about 80% of flags are the repo's own install. Of the 12 in the first 40 lines, 10 are. The detector does not see installs that happen through a Releases download, an APK, a `make` target or a Gradle build.
- Comparison table: 14 READMEs flagged. By hand, 4 compare against tools outside the project. The other 10 compare the project's own editions, models or options, a concept, or a before and after. One README with an outside comparison was missed (its heading read "Why X?"). So treat the 14% as "a table framed as a comparison", and about 5% as a comparison against outside tools.
- Badges, GIF, video, translations, asks for a star, limitations: every flagged README was looked at. Translations (32), video (8) and asks for a star (7) were all real. The limitations rule was narrowed after "Disclaimer" and "Supported scope" headings turned out not to be limitations.

The rates for the other section and link features were not checked one by one.

## Limits

- One sample of 100, from one day. The 95% intervals are about 8 to 10 points wide for mid-sized shares.
- Stars are a selection, not a cause. The report splits the sample into faster and slower climbers and compares features. After correcting for the 40 comparisons, nothing differs; the smallest raw p-value was 0.033, for the centered header (39 of 50 faster repos against 28 of 50 slower). Stars per day is a lifetime average, so an early spike and a steady climb look alike.
- Fake stars were not tested. GitHub restricted the stargazer list to admins and collaborators (changelog dated 2026-06-30), and the endpoint answered 404 when tried on 2026-09-30. Such tests need that list. As a crude check the 10 repos with the most stars per fork were dropped: no share moved by more than 3.9 points. That is a weak signal and not a fake-star test. Some repos in a 1,000-star population will have bought stars.
- The detectors read one line at a time. A markdown image or link that wraps over lines can be missed, and the install detector only knows package-manager style commands.
- Kinds come from crude rules and weight the population estimate. A different set of rules would shift the estimates a little.
- READMEs change. The SHA in `sample.csv` tells you which version was read.
- The sample is weighted towards AI tooling because that is most of what broke out in these 12 months (1,566 of 3,806 repos match the agent-or-skill rules). It says little about other eras or other kinds of project.
- 20 of the 100 READMEs are mostly Chinese. The structural detectors (images, badges, tables, code, install commands) handle them, but the heading and comparison rules match English words and miss their Chinese equivalents, so those features are undercounted for them.

## Re-running

```sh
python -m readme_breakouts run            # sample, fetch, analyze and report, into data/<today>
python -m readme_breakouts sample --population data/2026-09-30/population.csv --dir data/redraw
python -m readme_breakouts analyze --dir data/2026-09-30
python -m readme_breakouts report --markdown --write REPORT.md
```

`run` reads the GitHub API through `GITHUB_TOKEN`, or through the `gh` command line when it is installed, and takes about half an hour at the polite pace, longer when a shared token hits the search limit. `analyze` and `report` work offline on cached READMEs.

## Files in a run folder

| File | Holds |
|---|---|
| `population.csv` | Every breakout repo: name, kind, stars, forks, dates, stars per day, stars per fork, language, owner type, licence, topics. No description text: descriptions belong to their authors, some contain contact details, so they are read to assign a kind and then dropped |
| `sample.csv` | The draw: role (selected or reserve), order, fetch status, README name, SHA and size |
| `features.csv` | One row per sampled README with every detector's output |
| `summary.json` | Shares, intervals, sizes, tables, install kinds, faster versus slower, sensitivity check. `readme_breakouts/benchmark.json` is a copy, used by `check` |
| `run.json` | Date, definition, seed, quotas, API calls |
| `hand-checks.csv` | The detector disagreements found by hand |
