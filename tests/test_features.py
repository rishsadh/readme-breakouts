import unittest

from readme_breakouts.features import describe, find_pitch, normalise_text, split_lines


FULL = """<p align="center"><img src="docs/logo.png" width="120"></p>

# Foo

[![CI](https://img.shields.io/github/actions/workflow/status/a/b/ci.yml)](https://ci)
[![npm](https://img.shields.io/npm/v/foo.svg)](https://npm)

Foo turns markdown notes into a fast static site for agents.

![demo](docs/demo.gif)

```sh
npx foo build
```

## Why
Because.

## Comparison with alternatives

| Tool | Fast | Typed |
|---|---|---|
| foo | ✅ | ✅ |
| bar | ❌ | ✅ |

## Options

| Flag | Default | Description |
|---|---|---|
| --out | dist | output folder |

## Limitations
Only markdown.

## License
MIT
"""


class Pitch(unittest.TestCase):
    def test_pitch_found_after_badges(self):
        f = describe(FULL)
        self.assertTrue(f["pitch_in_first_15"])
        self.assertEqual(f["pitch_line_no"], 8)
        self.assertGreaterEqual(f["pitch_words"], 8)

    def test_no_pitch_when_only_headings_and_badges(self):
        text = "# X\n\n[![a](https://img.shields.io/a.svg)](x)\n\n## Install\n\n- one\n- two\n"
        self.assertFalse(describe(text)["pitch_in_first_40"])

    def test_nav_links_are_not_a_pitch(self):
        text = "# X\n\n[Docs](a) | [Blog](b) | [Discord](c)\n\nA real sentence that explains the whole thing.\n"
        lines = split_lines(normalise_text(text))
        no, words = find_pitch(lines, 40)
        self.assertEqual(no, 5)

    def test_pitch_outside_window_does_not_count_for_15(self):
        text = "# X\n" + "\n".join(["<div>"] * 20) + "\n\nA real sentence that explains the whole thing.\n"
        f = describe(text)
        self.assertFalse(f["pitch_in_first_15"])
        self.assertTrue(f["pitch_in_first_40"])

    def test_html_wrapped_tagline(self):
        text = '<h1 align="center">Foo</h1>\n<p align="center">A fast thing for making other things faster.</p>\n'
        self.assertTrue(describe(text)["pitch_in_first_15"])

    def test_tagline_in_a_subheading_counts(self):
        text = '<div align="center">\n<h1>Foo</h1>\n<h3>The fast way to ship small sites for agents</h3>\n</div>\n'
        self.assertTrue(describe(text)["pitch_in_first_15"])
        self.assertTrue(describe("# Foo\n\n### Turn notes into a site that agents can read\n")["pitch_in_first_15"])

    def test_section_headings_are_not_taglines(self):
        text = "# Foo\n\n## Table of contents\n\n## Installation and quick start guide\n\n## Contributing to the project\n"
        self.assertFalse(describe(text)["pitch_in_first_40"])

    def test_cjk_pitch(self):
        text = "# 项目\n\n这是一个用于管理智能体工作流程的开源工具集合。\n"
        self.assertTrue(describe(text)["pitch_in_first_15"])


class Images(unittest.TestCase):
    def test_badges_are_not_images(self):
        f = describe("# X\n\n[![a](https://img.shields.io/a.svg)](x)\n")
        self.assertEqual(f["image_count"], 0)
        self.assertEqual(f["badge_count"], 1)
        self.assertTrue(f["has_badges"])
        self.assertFalse(f["image_in_first_40"])

    def test_image_and_gif(self):
        f = describe(FULL)
        self.assertEqual(f["image_count"], 2)
        self.assertEqual(f["first_image_line"], 1)
        self.assertTrue(f["has_gif"])
        self.assertTrue(f["image_in_first_40"])
        self.assertEqual(f["badge_count"], 2)

    def test_image_late_is_not_above_the_fold(self):
        text = "# X\n" + "word " * 1200 + "\n\n" + "\n".join(["line"] * 60) + "\n![late](a.png)\n"
        f = describe(text)
        self.assertEqual(f["image_count"], 1)
        self.assertFalse(f["image_in_first_40"])
        self.assertFalse(f["image_in_first_4000"])

    def test_reference_style_image(self):
        f = describe("# X\n\n![shot][s]\n\n[s]: docs/shot.png\n")
        self.assertEqual(f["image_count"], 1)

    def test_images_inside_code_fences_are_ignored(self):
        f = describe("# X\n\n```md\n![a](b.png)\n```\n")
        self.assertEqual(f["image_count"], 0)

    def test_html_comment_hides_image(self):
        f = describe("# X\n\n<!-- ![a](b.png) -->\ntext text text text text\n")
        self.assertEqual(f["image_count"], 0)

    def test_video_detection(self):
        self.assertTrue(describe("# X\n\n[watch](https://youtu.be/abc)\n")["has_video"])
        self.assertTrue(describe("# X\n\n<video src='a.mp4'></video>\n")["has_video"])
        self.assertTrue(describe("# X\n\nhttps://github.com/user-attachments/assets/abc-123\n")["has_video"])
        self.assertFalse(describe("# X\n\nno video here at all, only words\n")["has_video"])


class Install(unittest.TestCase):
    def cases(self):
        return [
            ("```sh\nnpx foo\n```", "npm"), ("```\n$ pip install foo\n```", "pip"),
            ("```\nuvx foo run\n```", "pip"), ("```\nbrew install foo\n```", "brew"),
            ("```\ncargo install foo\n```", "cargo"), ("```\ngo install x/y@latest\n```", "go"),
            ("```\ndocker run -p 80:80 foo\n```", "docker"),
            ("```\ncurl -fsSL https://x.sh | sh\n```", "script"),
            ("```\nclaude mcp add foo -- npx foo\n```", "other"),
            ("Run `npm install -g foo` first.", "npm"),
        ]

    def test_kinds(self):
        for md, kind in self.cases():
            with self.subTest(md=md):
                f = describe("# X\n\n" + md + "\n")
                self.assertTrue(f["install_oneliner"], md)
                self.assertEqual(f["install_kind"], kind)

    def test_git_clone_alone_is_not_an_install_one_liner(self):
        f = describe("# X\n\n```sh\ngit clone https://github.com/a/b\ncd b\n```\n")
        self.assertFalse(f["install_oneliner"])
        self.assertTrue(f["git_clone_seen"])

    def test_dev_setup_is_not_an_install(self):
        for cmd in ("npm install", "pnpm i", "npm ci", "pip install -r requirements.txt", "pip install -e .", "uv sync", "poetry install"):
            with self.subTest(cmd=cmd):
                f = describe("# X\n\n```sh\n" + cmd + "\n```\n")
                self.assertFalse(f["install_oneliner"], cmd)
                self.assertTrue(f["setup_command_seen"], cmd)

    def test_package_install_with_a_name_still_counts(self):
        self.assertTrue(describe("# X\n\n```sh\nnpm install foo\n```\n")["install_oneliner"])
        self.assertTrue(describe("# X\n\n```sh\npip install foo\n```\n")["install_oneliner"])

    def test_install_script_file(self):
        f = describe("# X\n\n```sh\n./install.sh\n```\n")
        self.assertEqual(f["install_kind"], "script-file")

    def test_badge_like_images_are_not_content(self):
        for url in ("https://skills.sh/b/a/b", "assets/badges/paper.svg", "https://hosted.weblate.org/widget/x/svg-badge.svg",
                    "https://olud.ai/badge.php?tool=x", "https://img.buymeacoffee.com/button-api/?slug=x"):
            with self.subTest(url=url):
                self.assertEqual(describe("# X\n\n![a](" + url + ")\n")["image_count"], 0)

    def test_logo_is_an_image_but_not_a_screenshot(self):
        f = describe("# X\n\n![Foo logo](docs/logo.png)\n")
        self.assertTrue(f["image_in_first_40"])
        self.assertFalse(f["screenshot_in_first_40"])
        f = describe("# X\n\n![editor](docs/editor.png)\n")
        self.assertTrue(f["screenshot_in_first_40"])

    def test_attribute_tail_is_not_a_pitch(self):
        text = '<picture>\n  <source media="(prefers-color-scheme: dark)"\n    srcset="https://example.com/some/long/banner-dark.png">\n</picture>\n'
        self.assertFalse(describe(text)["pitch_in_first_40"])

    def test_wrapped_badge_is_not_a_pitch(self):
        text = "# X\n[![dl](https://img.shields.io/badge/dynamic/json?label=Downloads%20(F-Droid)&color=gold&style=for-the-badge\n)](https://f-droid.org/packages/x/)\n"
        self.assertFalse(describe(text)["pitch_in_first_40"])

    def test_plain_pip_freeze_is_not_install(self):
        self.assertFalse(describe("# X\n\n```\npip freeze\nnpm run dev\n```\n")["install_oneliner"])

    def test_position(self):
        f = describe(FULL)
        self.assertEqual(f["install_line_no"], 13)
        self.assertTrue(f["install_in_first_40"])


class Tables(unittest.TestCase):
    def test_types(self):
        f = describe(FULL)
        self.assertEqual(f["table_count"], 2)
        self.assertEqual(f["tables_comparison"], 1)
        self.assertEqual(f["tables_reference"], 1)
        self.assertTrue(f["has_comparison_table"])

    def test_config_table_is_not_comparison(self):
        text = "# X\n\n## Configuration\n\n| Option | Default | Description |\n|---|---|---|\n| a | 1 | x |\n"
        f = describe(text)
        self.assertFalse(f["has_comparison_table"])
        self.assertEqual(f["tables_reference"], 1)

    def test_support_matrix_without_comparison_words(self):
        text = "# X\n\n## Platforms\n\n| OS | CLI | GUI |\n|---|---|---|\n| mac | ✅ | ✅ |\n| win | ✅ | ❌ |\n"
        f = describe(text)
        self.assertEqual(f["tables_support_matrix"], 1)
        self.assertFalse(f["has_comparison_table"])

    def test_results_table(self):
        text = "# X\n\n## Benchmarks\n\n| Model | Score |\n|---|---|\n| a | 1 |\n"
        self.assertEqual(describe(text)["tables_results"], 1)

    def test_vs_in_lead_in_line(self):
        text = "# X\n\nfoo vs the rest:\n\n| a | b |\n|---|---|\n| 1 | 2 |\n"
        self.assertTrue(describe(text)["has_comparison_table"])

    def test_table_in_code_fence_ignored(self):
        text = "# X\n\n```\n| a | b |\n|---|---|\n| 1 | 2 |\n```\n"
        self.assertEqual(describe(text)["table_count"], 0)

    def test_html_tables_counted_not_typed(self):
        f = describe("# X\n\n<table><tr><td>a</td></tr></table>\n")
        self.assertEqual(f["html_table_count"], 1)
        self.assertEqual(f["table_count"], 0)


class Sections(unittest.TestCase):
    def test_sections(self):
        f = describe(FULL)
        for k in ("sec_why", "sec_comparison", "sec_limits", "sec_license"):
            self.assertTrue(f[k], k)
        self.assertFalse(f["sec_roadmap"])

    def test_setext_headings(self):
        f = describe("Foo\n===\n\nIntro words go right here today.\n\nInstallation\n------------\n\nx\n")
        self.assertTrue(f["sec_install"])
        self.assertEqual(f["heading_count"], 2)

    def test_translations_and_toc(self):
        head = "# X\n\n[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)\n\n"
        f = describe(head + "\n".join(f"- [s{i}](#s{i})" for i in range(6)))
        self.assertTrue(f["translations"])
        self.assertTrue(f["toc"])

    def test_centered_header_and_emoji(self):
        f = describe('<div align="center">\n<h1>X</h1>\n</div>\n\n## 🚀 Quick start\n')
        self.assertTrue(f["centered_header"])
        self.assertTrue(f["has_emoji_headings"])

    def test_star_history_and_sponsors_by_url(self):
        f = describe("# X\n\n![s](https://api.star-history.com/svg?repos=a/b)\n\n[sponsor](https://github.com/sponsors/a)\n")
        self.assertTrue(f["sec_star_history"])
        self.assertTrue(f["sec_sponsors"])

    def test_em_dash_only_counts_prose(self):
        f = describe("# X\n\nA sentence — with a dash in it.\n\n```\nx — y\n```\n")
        self.assertEqual(f["em_dash_count"], 1)
        self.assertTrue(f["has_em_dash"])

    def test_asks_for_star(self):
        self.assertTrue(describe("# X\n\nIf you like it, give it a star!\n")["asks_for_star"])
        self.assertFalse(describe("# X\n\nThis repo stars nobody in particular.\n")["asks_for_star"])


class Shape(unittest.TestCase):
    def test_crlf_and_bom(self):
        f = describe("﻿# X\r\n\r\nA real sentence that explains the whole thing.\r\n")
        self.assertTrue(f["pitch_in_first_15"])
        self.assertEqual(f["length_lines"], 4)

    def test_empty(self):
        f = describe("")
        self.assertFalse(f["pitch_in_first_40"])
        self.assertEqual(f["table_count"], 0)

    def test_all_three_top40(self):
        self.assertTrue(describe(FULL)["all_three_top40"])


if __name__ == "__main__":
    unittest.main()
