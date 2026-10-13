# What 100 breakout repos put in their READMEs

Run date 2026-09-30. Tool version 0.1.0. All numbers are shares of this one sample, not of all GitHub repos, and none of them show that a feature causes stars.

## Sample

- Breakout means: public non-fork repos created in the 365 days up to the run date with at least 1000 stars on the run date.
- Population found: 3806 repos. Sample: 100 READMEs, drawn with seed 20260930, stratified by a rule-based kind, alternating between the faster and slower half by stars per day.
- Median stars 2,166 (quartiles 1,322 to 3,862); median 12.1 stars per day since creation.

| Kind | In population | In sample |
|---|---:|---:|
| agent-or-skill | 1566 | 28 |
| other | 675 | 15 |
| ai-model-or-research | 488 | 12 |
| mcp-server | 331 | 10 |
| app | 292 | 9 |
| library-or-framework | 168 | 7 |
| awesome-list | 154 | 7 |
| cli-tool | 100 | 6 |
| learning | 32 | 6 |

## Features

Sample share is the plain share of the 100 READMEs, with a 95% Wilson interval. The population estimate reweights each kind by how many repos it has among all breakouts, because small kinds were sampled more heavily than large ones; its interval uses the stratified variance. Detector rules are in METHOD.md.

| Feature | Count | Sample share | 95% interval | Population estimate | 95% interval |
|---|---:|---:|---:|---:|---:|
| One-line pitch in the first 15 lines | 82/100 | 82% | 73 to 88% | 80% | 70 to 87% |
| One-line pitch in the first 40 lines | 99/100 | 99% | 95 to 100% | 99% | 92 to 100% |
| Image (not a badge) in the first 40 lines | 77/100 | 77% | 68 to 84% | 77% | 67 to 84% |
| Image (not a badge) in the first 4,000 characters | 77/100 | 77% | 68 to 84% | 77% | 67 to 84% |
| Image that is not a logo or icon in the first 40 lines | 68/100 | 68% | 58 to 76% | 69% | 59 to 77% |
| A GIF anywhere | 16/100 | 16% | 10 to 24% | 16% | 10 to 25% |
| A video or video link anywhere | 8/100 | 8% | 4 to 15% | 9% | 5 to 17% |
| Badges | 65/100 | 65% | 55 to 74% | 66% | 55 to 75% |
| Badges in the first 15 lines | 45/100 | 45% | 36 to 55% | 47% | 36 to 57% |
| An install or run command anywhere | 63/100 | 63% | 53 to 72% | 62% | 52 to 72% |
| Install or run command in the first 40 lines | 12/100 | 12% | 7 to 20% | 13% | 7 to 22% |
| Install or run command in the first 4,000 characters | 29/100 | 29% | 21 to 39% | 28% | 20 to 38% |
| git clone shown | 45/100 | 45% | 36 to 55% | 49% | 39 to 59% |
| Dev setup command shown (bare npm install, pip install -r, uv sync) | 38/100 | 38% | 29 to 48% | 39% | 30 to 50% |
| Pitch, image and install all in the first 40 lines | 5/100 | 5% | 2 to 11% | 5% | 2 to 13% |
| Any pipe table | 76/100 | 76% | 67 to 83% | 74% | 64 to 82% |
| A table framed as a comparison | 14/100 | 14% | 9 to 22% | 14% | 9 to 22% |
| Install or quick start heading | 64/100 | 64% | 54 to 73% | 66% | 57 to 75% |
| Usage or examples heading | 22/100 | 22% | 15 to 31% | 21% | 14 to 31% |
| Features heading | 39/100 | 39% | 30 to 49% | 41% | 31 to 52% |
| Why, about or overview heading | 42/100 | 42% | 33 to 52% | 38% | 29 to 48% |
| Comparison or alternatives heading | 17/100 | 17% | 11 to 26% | 18% | 12 to 28% |
| Limitations heading | 3/100 | 3% | 1 to 8% | 3% | 1 to 10% |
| Demo or screenshots heading | 26/100 | 26% | 18 to 35% | 28% | 20 to 39% |
| Roadmap heading | 15/100 | 15% | 9 to 23% | 15% | 9 to 24% |
| Contributing heading | 46/100 | 46% | 37 to 56% | 45% | 35 to 55% |
| License heading | 59/100 | 59% | 49 to 68% | 58% | 48 to 68% |
| FAQ or troubleshooting heading | 15/100 | 15% | 9 to 23% | 15% | 9 to 24% |
| Citation or BibTeX | 9/100 | 9% | 5 to 16% | 12% | 6 to 21% |
| Sponsor or funding link | 15/100 | 15% | 9 to 23% | 12% | 7 to 19% |
| Community link (Discord, Slack, Telegram) | 24/100 | 24% | 17 to 33% | 22% | 15 to 32% |
| Star history chart or heading | 21/100 | 21% | 14 to 30% | 23% | 15 to 33% |
| Table of contents | 15/100 | 15% | 9 to 23% | 13% | 7 to 21% |
| Translated READMEs linked | 32/100 | 32% | 24 to 42% | 33% | 24 to 44% |
| Centered HTML header block | 67/100 | 67% | 57 to 75% | 65% | 54 to 74% |
| Emoji in headings | 26/100 | 26% | 18 to 35% | 27% | 19 to 37% |
| Asks the reader for a star | 7/100 | 7% | 3 to 14% | 6% | 3 to 14% |
| Link to a demo or playground | 9/100 | 9% | 5 to 16% | 8% | 4 to 15% |
| Link to docs | 46/100 | 46% | 37 to 56% | 46% | 35 to 56% |
| Em dash in prose | 62/100 | 62% | 52 to 71% | 61% | 51 to 71% |

## Sizes

| Measure | Min | Q1 | Median | Q3 | Max |
|---|---:|---:|---:|---:|---:|
| README characters | 755 | 6,556 | 13,663 | 22,493 | 247,886 |
| README lines | 25 | 147 | 240 | 450 | 2,623 |
| Pitch line, words | 4 | 8 | 11 | 17 | 94 |
| Images (not badges) | 0 | 1 | 3 | 5 | 729 |
| Badges | 0 | 0 | 4 | 6 | 44 |
| Pipe tables | 0 | 1 | 2 | 4 | 31 |
| Headings | 1 | 11 | 18 | 27 | 118 |
| Code blocks | 0 | 2 | 6 | 12 | 74 |
| Em dashes | 0 | 0 | 2 | 12 | 124 |

## Tables

Pipe tables only. The detector cannot read intent, so each table is typed from its heading, the line above it and its header cells.

| Type | Tables | READMEs with one |
|---|---:|---:|
| comparison | 16 | 14 |
| results | 11 | 7 |
| support matrix | 5 | 5 |
| reference | 149 | 44 |
| other | 215 | 59 |

## Install commands

First install or run command found, by package manager.

| Kind | READMEs |
|---|---:|
| npm | 14 |
| docker | 13 |
| script | 8 |
| pip | 8 |
| brew | 7 |
| script-file | 6 |
| other | 5 |
| os-package | 2 |

## Faster and slower breakouts

The sample split at the median of 12.5 stars per day since creation (50 faster, 50 slower). Stars per day is a lifetime average, so a repo that spiked early and then stalled looks the same as a steady one. This is an association, not a cause.

Adjusted p-values are Holm-corrected across all features, because 40 comparisons will throw up some small p-values by chance.

| Feature | Faster | Slower | p | Holm p |
|---|---:|---:|---:|---:|
| One-line pitch in the first 15 lines | 40/50 | 42/50 | 0.795 | 1.000 |
| One-line pitch in the first 40 lines | 49/50 | 50/50 | 1.000 | 1.000 |
| Image (not a badge) in the first 40 lines | 40/50 | 37/50 | 0.635 | 1.000 |
| Image (not a badge) in the first 4,000 characters | 39/50 | 38/50 | 1.000 | 1.000 |
| Image that is not a logo or icon in the first 40 lines | 33/50 | 35/50 | 0.830 | 1.000 |
| A GIF anywhere | 9/50 | 7/50 | 0.786 | 1.000 |
| A video or video link anywhere | 5/50 | 3/50 | 0.715 | 1.000 |
| Badges | 36/50 | 29/50 | 0.208 | 1.000 |
| Badges in the first 15 lines | 23/50 | 22/50 | 1.000 | 1.000 |
| An install or run command anywhere | 31/50 | 32/50 | 1.000 | 1.000 |
| Install or run command in the first 40 lines | 4/50 | 8/50 | 0.357 | 1.000 |
| Install or run command in the first 4,000 characters | 13/50 | 16/50 | 0.660 | 1.000 |
| git clone shown | 22/50 | 23/50 | 1.000 | 1.000 |
| Dev setup command shown (bare npm install, pip install -r, uv sync) | 18/50 | 20/50 | 0.837 | 1.000 |
| Pitch, image and install all in the first 40 lines | 1/50 | 4/50 | 0.362 | 1.000 |
| Any pipe table | 40/50 | 36/50 | 0.483 | 1.000 |
| A table framed as a comparison | 5/50 | 9/50 | 0.388 | 1.000 |
| Install or quick start heading | 32/50 | 32/50 | 1.000 | 1.000 |
| Usage or examples heading | 9/50 | 13/50 | 0.470 | 1.000 |
| Features heading | 15/50 | 24/50 | 0.100 | 1.000 |
| Why, about or overview heading | 18/50 | 24/50 | 0.311 | 1.000 |
| Comparison or alternatives heading | 7/50 | 10/50 | 0.595 | 1.000 |
| Limitations heading | 2/50 | 1/50 | 1.000 | 1.000 |
| Demo or screenshots heading | 9/50 | 17/50 | 0.110 | 1.000 |
| Roadmap heading | 8/50 | 7/50 | 1.000 | 1.000 |
| Contributing heading | 22/50 | 24/50 | 0.841 | 1.000 |
| License heading | 26/50 | 33/50 | 0.222 | 1.000 |
| FAQ or troubleshooting heading | 7/50 | 8/50 | 1.000 | 1.000 |
| Citation or BibTeX | 3/50 | 6/50 | 0.487 | 1.000 |
| Sponsor or funding link | 5/50 | 10/50 | 0.262 | 1.000 |
| Community link (Discord, Slack, Telegram) | 15/50 | 9/50 | 0.241 | 1.000 |
| Star history chart or heading | 12/50 | 9/50 | 0.624 | 1.000 |
| Table of contents | 7/50 | 8/50 | 1.000 | 1.000 |
| Translated READMEs linked | 18/50 | 14/50 | 0.521 | 1.000 |
| Centered HTML header block | 39/50 | 28/50 | 0.033 | 1.000 |
| Emoji in headings | 12/50 | 14/50 | 0.820 | 1.000 |
| Asks the reader for a star | 3/50 | 4/50 | 1.000 | 1.000 |
| Link to a demo or playground | 7/50 | 2/50 | 0.160 | 1.000 |
| Link to docs | 27/50 | 19/50 | 0.160 | 1.000 |
| Em dash in prose | 33/50 | 29/50 | 0.537 | 1.000 |

## Sensitivity to inflated stars

Fake stars were not tested: the stargazer lists that such tests need are no longer public. As a crude check, the 10 repos with the most stars per fork were dropped and every share was recomputed on the remaining 90. The largest change in any feature share was 3.9 percentage points. Stars per fork is a weak signal, not a fake-star test.


## By kind

Counts inside each kind, for five headline features. Kinds are small, so read these as a description of this sample only.

| Kind | n | Pitch in 15 lines | Image in 40 lines | Install in 40 lines | Badges | Comparison table |
|---|---:|---:|---:|---:|---:|---:|
| agent-or-skill | 28 | 21 | 22 | 5 | 19 | 3 |
| ai-model-or-research | 12 | 10 | 11 | 1 | 7 | 3 |
| app | 9 | 7 | 8 | 0 | 6 | 0 |
| awesome-list | 7 | 6 | 5 | 1 | 4 | 1 |
| cli-tool | 6 | 6 | 5 | 2 | 4 | 1 |
| learning | 6 | 5 | 4 | 0 | 2 | 0 |
| library-or-framework | 7 | 7 | 7 | 0 | 7 | 0 |
| mcp-server | 10 | 8 | 7 | 2 | 7 | 5 |
| other | 15 | 12 | 8 | 1 | 9 | 1 |
