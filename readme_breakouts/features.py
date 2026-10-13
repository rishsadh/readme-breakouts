"""Static feature detectors for a README. Pure functions, no network.

Every detector is a plain rule over the markdown text. The rules and what they miss are
written down in METHOD.md. Line numbers are 1-based and count every line of the file.
"""
import re

TOP_LINES = 40          # "above the fold" in lines
TOP_CHARS = 4000        # "above the fold" in characters
PITCH_LINES = 15        # the window the launch gate uses for the one-line pitch

FENCE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
ATX_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
SETEXT_RE = re.compile(r"^\s{0,3}(=+|-{2,})\s*$")
HTML_HEADING_RE = re.compile(r"<h([1-6])\b[^>]*>(.*?)</h\1>", re.I | re.S)
MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(\s*<?([^)\s>]+)>?(?:[^)]*\))?")  # the closing paren may be on the next line
MD_REF_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\[([^\]]*)\]")
REF_DEF_RE = re.compile(r"^\s{0,3}\[([^\]]+)\]:\s*<?(\S+?)>?(?:\s|$)", re.M)
HTML_IMG_RE = re.compile(r"<img\b[^>]*?\bsrc\s*=\s*[\"']([^\"']+)[\"'][^>]*>", re.I)
HTML_VIDEO_RE = re.compile(r"<video\b", re.I)
LINK_RE = re.compile(r"(?<!!)\[([^\]]*)\]\(\s*<?([^)\s>]+)>?[^)]*\)")
TAG_RE = re.compile(r"<[^>]+>")
INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
EMOJI_RE = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐⬆✅❌‼⁉ℹ⌚-⏿]|:[a-z0-9_+\\-]{2,}:")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
ANCHOR_LINK_RE = re.compile(r"\]\(#[^)]+\)")
WORD_RE = re.compile(r"[A-Za-z0-9À-ɏЀ-ӿ][\w'’\-]*")
CJK_RE = re.compile(r"[一-鿿぀-ヿ가-힯]")

BADGE_URL_RE = re.compile(
    r"shields\.io|badgen\.net|badge\.fury\.io|/badge(\.svg|\.png|/|\?)|codecov\.io|coveralls\.io|"
    r"travis-ci\.|circleci\.com|codacy\.com|sonarcloud\.io|bestpractices|visitor-badge|"
    r"hits\.seeyoufarm|hits\.dwyl|vercel\.com/button|deploy\.workers\.cloudflare|railway\.app/button|"
    r"render\.com/images/deploy|colab-badge|forthebadge|pepy\.tech|dcbadge|img\.shields|"
    r"github\.com/[^/]+/[^/]+/(actions/)?workflows?/.*badge|api\.netlify\.com/api/v1/badges|"
    r"opencollective\.com/.*/(badge|contributors\.svg)|contrib\.rocks|badges\.gitter|"
    r"discordapp\.com/api/guilds|discord\.com/api/guilds|readthedocs\.org/projects/.*/badge|"
    r"img\.shields|flat-square|for-the-badge|/badges?/|svg-badge|buymeacoffee\.com/button|skills\.sh/b/|"
    r"badge\.php|hits\.sh|komarev\.com|profile-views|moe-counter|trendshift\.io", re.I)
LOGO_RE = re.compile(r"logo|icon|favicon|wordmark|avatar|brand|[-_/]mark\b|emoji", re.I)

VIDEO_URL_RE = re.compile(
    r"youtube\.com/(watch|embed|shorts)|youtu\.be/|vimeo\.com/|loom\.com/share|bilibili\.com/video|"
    r"\.(mp4|webm|mov)(\?|$|\))|asciinema\.org/a/|streamable\.com/", re.I)
ATTACHMENT_RE = re.compile(r"^\s*https://github\.com/(user-attachments/assets|[^/\s]+/[^/\s]+/assets)/[\w-]+\s*$")

# (kind, regex) applied to a code line or an inline code span, after stripping a prompt.
INSTALL_RULES = [
    ("npm", re.compile(r"^(?:sudo\s+)?(?:npx|bunx|pnpx)\s+\S|^(?:npm|pnpm|yarn|bun|deno)\s+(?:i|install|add|create|init|exec|dlx|x|global\s+add)\b", re.I)),
    ("pip", re.compile(r"^(?:python3?\s+-m\s+)?(?:pip3?|pipx|conda|mamba)\s+(?:install|run)\b|^(?:poetry|rye|uv)\s+(?:add|tool\s+install|tool\s+run|pip\s+install|run|sync)\b|^uvx\s+\S", re.I)),
    ("brew", re.compile(r"^brew\s+(?:install|tap)\b", re.I)),
    ("cargo", re.compile(r"^cargo\s+(?:install|add|binstall)\b", re.I)),
    ("go", re.compile(r"^go\s+(?:install|get)\b", re.I)),
    ("docker", re.compile(r"^(?:sudo\s+)?(?:docker|podman)\s+(?:run|pull|compose\s+up|-\S+\s+run)\b|^docker-compose\s+up\b", re.I)),
    ("script", re.compile(r"\b(?:curl|wget)\b[^|]*\|\s*(?:sudo\s+)?(?:ba|z|da)?sh\b|\b(?:iwr|irm|Invoke-WebRequest|Invoke-RestMethod)\b.*\|\s*iex", re.I)),
    ("os-package", re.compile(r"^(?:sudo\s+)?(?:apt(?:-get)?|dnf|yum|pacman|choco|winget|scoop|snap|nix(?:-env|\s+profile)?|flatpak|zypper|apk)\s+(?:install|add|-S|-i|-Sy)\b", re.I)),
    ("script-file", re.compile(r"^(?:bash|sh|zsh)\s+\S*(?:install|setup)\S*|^\.?/\S*(?:install|setup)\S*\.sh\b", re.I)),
    ("other", re.compile(r"^(?:gem\s+install|dotnet\s+(?:add|tool\s+install)|composer\s+require|gh\s+extension\s+install|code\s+--install-extension|claude\s+mcp\s+add|claude\s+plugin|/plugin\s+(?:install|marketplace)|mvn\s+install|gradle\s+install|flutter\s+pub\s+add|swift\s+package|helm\s+install|kubectl\s+apply)\b", re.I)),
]
GIT_CLONE_RE = re.compile(r"^git\s+clone\b", re.I)
# Commands that set up a checkout for development rather than install the tool.
SETUP_RE = re.compile(
    r"^(?:npm|pnpm|yarn|bun)\s+(?:i|install|ci)\s*$|^(?:python3?\s+-m\s+)?pip3?\s+install\s+(?:-r|-e|\.)|"
    r"^uv\s+sync|^poetry\s+install|^make\s+(?:install|setup|build)\b", re.I)
PROMPT_RE = re.compile(r"^\s*(?:\$|>|%|PS>|PS [A-Z]:\\[^>]*>|#)\s*")

# Section heading rules: key -> regex on the normalised heading text.
SECTION_RULES = {
    "install": r"\b(install\w*|getting started|quick ?start|setup|set up|get started)\b",
    "usage": r"\b(usage|examples?|how to use|using|basic use|quick use)\b",
    "features": r"\b(features?|highlights?|what it does|key features|capabilities|what you get|why .{0,30}(is|are) (great|awesome|different))\b",
    "why": r"\b(why|motivation|background|rationale|philosophy|overview|about|introduction|what is|what s)\b",
    "comparison": r"\b(compar\w*|vs|versus|alternatives?|differences?|similar (tools|projects)|how (it|this) differs)\b",
    "limits": r"\b(limitations?|caveats?|non goals?|what it does not|not supported|known issues?|known limitations?|out of scope)\b",
    "demo": r"\b(demo|screenshots?|preview|showcase|gallery|see it in action|in action|videos?)\b",
    "roadmap": r"\b(roadmap|todo|to do|plans?|planned|future work|what s next|coming soon)\b",
    "contributing": r"\b(contribut\w*|development|developing|building|build from source|hacking)\b",
    "license": r"\b(licen[sc]e\w*|copyright)\b",
    "faq": r"\b(faq|frequently asked|troubleshooting|questions)\b",
    "citation": r"\b(cit(e|ation|ing)|bibtex)\b",
    "sponsors": r"\b(sponsors?|backers?|funding|support (me|us|the project)|donate|donations?)\b",
    "community": r"\b(community|discord|slack|join us|chat|get in touch)\b",
    "star_history": r"\b(star history|stargazers)\b",
    "toc": r"\b(table of contents|contents|toc)\b",
}
SECTION_RES = {k: re.compile(v, re.I) for k, v in SECTION_RULES.items()}

COMPARISON_CTX_RE = re.compile(
    r"\b(compar\w*|vs\.?|versus|alternatives?|differen\w*|differs?|similar (tools|projects)|"
    r"related (tools|projects|work)|why not|not another|unlike|instead of|rather than|why .{0,25}(over|instead of)|"
    r"how .{0,30}(stacks up|differs))\b", re.I)
COMPARISON_LEAD_RE = re.compile(r"\b(compar\w*|vs\.?|versus|alternatives?|compared (to|with))\b", re.I)
COMPARISON_HEADER_RE = re.compile(r"\b(compar\w*|alternatives?|differences?)\b", re.I)
RESULTS_CTX_RE = re.compile(
    r"\b(benchmarks?|scores?|accuracy|latency|speed|perf\w*|throughput|results?|leaderboard|metrics?|"
    r"eval\w*|pass@\d+|tokens?/s|fps|win rate|elo|mmlu|humaneval|swe-bench|ms)\b", re.I)
REFERENCE_CTX_RE = re.compile(
    r"\b(options?|flags?|parameters?|params?|variables?|env|environment|arguments?|args?|default|keys?|"
    r"settings?|fields?|propert(y|ies)|props?|commands?|endpoints?|routes?|methods?|attributes?|type|"
    r"config\w*|name|description|tools?|skills?|agents?|platforms?|model|version|file)\b", re.I)
MARK_RE = re.compile(r"✅|❌|✓|✔|✗|✘|✖|☑|☒|🟢|🔴|🟡|:white_check_mark:|:x:|:heavy_check_mark:|^\s*(yes|no|partial|supported|n/a)\s*$", re.I)

TRANSLATION_NAMES = re.compile(
    r"English|简体中文|繁體中文|中文|日本語|한국어|Español|Français|Deutsch|Português|Русский|العربية|हिन्दी|Türkçe|Tiếng Việt|Italiano|Polski|Nederlands|Bahasa|Indonesia", re.I)
TRANSLATION_FILE_RE = re.compile(r"README[._-][A-Za-z]{2}([_-][A-Za-z]{2,4})?\.md|/(?:docs?|i18n|translations?|locales?)/[A-Za-z]{2}([_-][A-Za-z]{2,4})?/README", re.I)
STAR_CTA_RE = re.compile(r"(give (it|us|this) a (⭐|star)|star (this|the|our) (repo|repository|project)|leave a (⭐|star)|⭐ (if|on)|if you (like|find|enjoy).{0,40}(⭐|star))", re.I)
COMMUNITY_URL_RE = re.compile(r"discord\.(gg|com/invite)|slack\.com|join\.slack|t\.me/|gitter\.im|matrix\.to|reddit\.com/r/", re.I)
SPONSOR_URL_RE = re.compile(r"github\.com/sponsors|ko-fi\.com|buymeacoffee\.com|patreon\.com|opencollective\.com|paypal\.me", re.I)
STAR_HISTORY_RE = re.compile(r"star-history\.com|starchart\.cc|api\.star-history", re.I)


def normalise_text(text):
    """Strip a BOM, unify newlines, blank out HTML comments but keep line numbers."""
    text = text.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)


def split_lines(text):
    """Return [(line_no, raw, in_code, char_offset)]. Fence lines count as code."""
    out, fence, offset = [], None, 0
    for i, raw in enumerate(text.split("\n"), 1):
        m = FENCE_RE.match(raw)
        in_code = False
        if fence:
            in_code = True
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not raw.strip().strip(fence[0]):
                fence = None
        elif m:
            in_code = True
            fence = m.group(1)
        out.append((i, raw, in_code, offset))
        offset += len(raw) + 1
    return out


def _norm_heading(s):
    s = TAG_RE.sub(" ", s)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"[^\w\s]|_", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def find_headings(lines):
    """[(line_no, level, raw_text)] for ATX, setext and HTML headings outside code."""
    heads = []
    prev = None
    for no, raw, in_code, _ in lines:
        if in_code:
            prev = None
            continue
        m = ATX_RE.match(raw)
        if m:
            heads.append((no, len(m.group(1)), m.group(2)))
            prev = None
            continue
        if prev and SETEXT_RE.match(raw) and prev[1].strip() and not prev[1].lstrip().startswith(("|", "-", "*", ">", "<", "!")):
            heads.append((prev[0], 1 if raw.strip()[0] == "=" else 2, prev[1].strip()))
        for hm in HTML_HEADING_RE.finditer(raw):
            heads.append((no, int(hm.group(1)), hm.group(2)))
        prev = (no, raw) if raw.strip() else None
    return heads


def is_badge(url, alt="", line=""):
    return bool(BADGE_URL_RE.search(url or ""))


def _html_alt(tag):
    m = re.search(r"\balt\s*=\s*[\"']([^\"']*)[\"']", tag, re.I)
    return m.group(1) if m else ""


def find_images(text, lines):
    """[(line_no, char_offset, url, is_badge)] for markdown, reference and HTML images outside code."""
    refs = {k.lower(): v for k, v in REF_DEF_RE.findall(text)}
    imgs = []
    for no, raw, in_code, off in lines:
        if in_code:
            continue
        for m in MD_IMAGE_RE.finditer(raw):
            imgs.append((no, off + m.start(), m.group(2), is_badge(m.group(2), m.group(1)), m.group(1)))
        for m in MD_REF_IMAGE_RE.finditer(raw):
            key = (m.group(2) or m.group(1)).lower()
            url = refs.get(key, "")
            imgs.append((no, off + m.start(), url, is_badge(url, m.group(1)), m.group(1)))
        for m in HTML_IMG_RE.finditer(raw):
            imgs.append((no, off + m.start(), m.group(1), is_badge(m.group(1)), _html_alt(raw[m.start():m.end()])))
    return imgs


def _plain(raw):
    s = MD_IMAGE_RE.sub(" ", raw)
    s = MD_REF_IMAGE_RE.sub(" ", s)
    s = HTML_IMG_RE.sub(" ", s)
    s = LINK_RE.sub(lambda m: m.group(1), s)
    s = TAG_RE.sub(" ", s)
    s = re.sub(r"<[^>]*$", " ", s)  # a tag that wraps onto the next line
    s = re.sub(r"[*_`~]|&nbsp;|&[a-z]+;", " ", s)
    return re.sub(r"\s+", " ", s).strip(" >|")


def _word_count(s):
    return len(WORD_RE.findall(s)) + len(CJK_RE.findall(s)) // 2


def _is_nav_line(raw, plain):
    links = LINK_RE.findall(raw)
    if len(links) >= 2 and re.search(r"[|·•]", raw):
        linked = sum(len(t) for t, _ in links)
        return linked >= 0.6 * max(len(plain), 1)
    return False


def _tagline_heading(raw):
    """Text of a sub-heading (level 2 to 6, ATX or HTML) that reads like a tagline, else None.

    Many READMEs put the pitch in an h3 under the title. Section headings such as Installation
    or Table of Contents do not count."""
    text = None
    m = ATX_RE.match(raw)
    if m and len(m.group(1)) >= 2:
        text = m.group(2)
    else:
        hm = HTML_HEADING_RE.search(raw)
        if hm and int(hm.group(1)) >= 2:
            text = hm.group(2)
    if text is None:
        return None
    plain = _plain(text)
    norm = _norm_heading(plain)
    if len(norm.split()) <= 5 and any(rx.search(norm) for key, rx in SECTION_RES.items() if key != "why"):
        return None
    if _word_count(plain) < 4 or len(plain) < 20:
        return None
    return plain


def find_pitch(lines, limit):
    """First pitch-like line inside the first `limit` lines: prose, bold text or a tagline sub-heading.

    Skips the title, badges, navigation links, tables, lists and code. Returns (line_no, words) or (None, 0)."""
    for no, raw, in_code, _ in lines[:limit]:
        if in_code or not raw.strip():
            continue
        s = raw.strip()
        if s.startswith(("[![", "![", ")")):
            continue  # an image or badge link, even when its URL wraps
        if re.match(r"""^[\w:-]+\s*=\s*["']""", s) or s.startswith("/>"):
            continue  # the tail of an HTML tag that wraps over several lines
        tag = _tagline_heading(raw)
        if tag:
            return no, _word_count(tag)
        if s.startswith(("#", "|", "- ", "* ", "+ ", "---", "===")) or re.match(r"^\d+[.)]\s", s) or ATX_RE.match(raw):
            continue
        if HTML_HEADING_RE.search(raw) or TRANSLATION_NAMES.findall(s) and len(TRANSLATION_NAMES.findall(s)) >= 2:
            continue
        plain = _plain(raw)
        if not plain or _is_nav_line(raw, plain):
            continue
        words = _word_count(plain)
        if words >= 4 and len(plain) >= 20:
            return no, words
    return None, 0


def _split_row(row):
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|") and not row.endswith("\\|"):
        row = row[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", row)]


def find_tables(lines, headings):
    """Parse pipe tables outside code. Returns [{line, header, rows, context, kind}]."""
    tables = []
    i = 0
    prose = [(no, raw, in_code) for no, raw, in_code, _ in lines]
    head_by_line = sorted(headings)
    while i < len(prose) - 1:
        no, raw, in_code = prose[i]
        nxt = prose[i + 1]
        if (not in_code and "|" in raw and not nxt[2] and "|" in nxt[1] and TABLE_SEP_RE.match(nxt[1])
                and not TABLE_SEP_RE.match(raw)):
            header = _split_row(raw)
            rows = []
            j = i + 2
            while j < len(prose) and not prose[j][2] and prose[j][1].strip() and "|" in prose[j][1]:
                rows.append(_split_row(prose[j][1]))
                j += 1
            heading = ""
            for hn, _, ht in head_by_line:
                if hn < no:
                    heading = ht
                else:
                    break
            lead = ""
            for k in range(i - 1, max(i - 4, -1), -1):
                if prose[k][1].strip() and not prose[k][2]:
                    lead = prose[k][1]
                    break
            ctx = " ".join([_plain(heading), _plain(lead)])
            tables.append({"line": no, "header": header, "rows": rows, "context": ctx,
                           "heading": _plain(heading), "lead": _plain(lead)})
            i = j
        else:
            i += 1
    for t in tables:
        t["kind"] = classify_table(t)
    return tables


def classify_table(t):
    header_text = " ".join(t["header"])
    ctx_all = t["context"] + " " + header_text
    # "vs" in a column header usually means "versus a baseline" in a results table, so header cells
    # only count with the words compare, alternative or difference. Heading and lead-in line count in full.
    if (COMPARISON_CTX_RE.search(t.get("heading", t["context"])) or COMPARISON_LEAD_RE.search(t.get("lead", ""))
            or COMPARISON_HEADER_RE.search(header_text)):
        return "comparison"
    if RESULTS_CTX_RE.search(ctx_all):
        return "results"
    cols = len(t["header"])
    rows = t["rows"]
    marked_cols = 0
    for c in range(cols):
        cells = [r[c] for r in rows if c < len(r)]
        if cells and sum(1 for x in cells if MARK_RE.search(x)) >= max(1, len(cells) // 2):
            marked_cols += 1
    if marked_cols >= 2:
        return "support_matrix"
    if REFERENCE_CTX_RE.search(header_text):
        return "reference"
    return "other"


def find_install(lines):
    """First install-style command.

    Returns (line_no, char_offset, kind, git_clone_seen, setup_seen). Dev-setup commands
    (bare npm install, pip install -r, uv sync) and git clone are tracked but do not count as an install."""
    hit, clone, setup = None, False, False
    for no, raw, in_code, off in lines:
        candidates = []
        if in_code:
            if FENCE_RE.match(raw):
                continue
            candidates.append(raw.strip())
        else:
            candidates += [m.group(1).strip() for m in INLINE_CODE_RE.finditer(raw)]
        for c in candidates:
            c = PROMPT_RE.sub("", c).strip()
            if not c:
                continue
            if GIT_CLONE_RE.match(c):
                clone = True
                continue
            if SETUP_RE.match(c):
                setup = True
                continue
            for kind, rx in INSTALL_RULES:
                if rx.search(c):
                    if hit is None:
                        hit = (no, off, kind)
                    break
    if hit:
        return hit[0], hit[1], hit[2], clone, setup
    return None, None, "", clone, setup


def describe(text):
    """Return a flat dict of features for one README text."""
    text = normalise_text(text)
    lines = split_lines(text)
    total_lines = len(lines)
    headings = find_headings(lines)
    imgs = find_images(text, lines)
    content_imgs = [i for i in imgs if not i[3]]
    badge_imgs = [i for i in imgs if i[3]]

    f = {"length_chars": len(text), "length_lines": total_lines}

    pno, pwords = find_pitch(lines, PITCH_LINES)
    pno40, pwords40 = find_pitch(lines, TOP_LINES)
    f["pitch_in_first_15"] = pno is not None
    f["pitch_in_first_40"] = pno40 is not None
    f["pitch_line_no"] = pno40 or ""
    f["pitch_words"] = pwords40 or ""

    first_img = content_imgs[0] if content_imgs else None
    f["image_count"] = len(content_imgs)
    f["first_image_line"] = first_img[0] if first_img else ""
    f["image_in_first_40"] = bool(first_img and first_img[0] <= TOP_LINES)
    f["image_in_first_4000"] = bool(first_img and first_img[1] < TOP_CHARS)
    shots = [i for i in content_imgs if not LOGO_RE.search(i[2]) and not LOGO_RE.search(i[4])]
    f["screenshot_in_first_40"] = any(i[0] <= TOP_LINES for i in shots)
    f["has_gif"] = any(re.search(r"\.gif(\?|$)", i[2], re.I) for i in content_imgs)
    f["gif_in_first_4000"] = any(re.search(r"\.gif(\?|$)", i[2], re.I) and i[1] < TOP_CHARS for i in content_imgs)

    video = bool(HTML_VIDEO_RE.search(text))
    if not video:
        for no, raw, in_code, _ in lines:
            if in_code:
                continue
            if VIDEO_URL_RE.search(raw) or ATTACHMENT_RE.match(raw):
                video = True
                break
    f["has_video"] = video

    f["badge_count"] = len(badge_imgs)
    f["has_badges"] = bool(badge_imgs)
    f["badges_in_first_15"] = any(b[0] <= PITCH_LINES for b in badge_imgs)

    ino, ioff, ikind, clone, setup = find_install(lines)
    f["install_oneliner"] = ino is not None
    f["install_kind"] = ikind
    f["install_line_no"] = ino or ""
    f["install_in_first_40"] = bool(ino and ino <= TOP_LINES)
    f["install_in_first_4000"] = bool(ioff is not None and ioff < TOP_CHARS)
    f["git_clone_seen"] = clone
    f["setup_command_seen"] = setup

    f["all_three_top40"] = f["pitch_in_first_40"] and f["image_in_first_40"] and f["install_in_first_40"]

    tables = find_tables(lines, headings)
    kinds = [t["kind"] for t in tables]
    f["table_count"] = len(tables)
    f["has_table"] = bool(tables)
    for k in ("comparison", "results", "support_matrix", "reference", "other"):
        f[f"tables_{k}"] = kinds.count(k)
    f["has_comparison_table"] = "comparison" in kinds
    f["html_table_count"] = len(re.findall(r"<table\b", text, re.I))

    norm = [_norm_heading(h[2]) for h in headings]
    f["heading_count"] = len(headings)
    f["h2_count"] = sum(1 for h in headings if h[1] == 2)
    for key, rx in SECTION_RES.items():
        f[f"sec_{key}"] = any(rx.search(n) for n in norm)
    f["sec_star_history"] = f["sec_star_history"] or bool(STAR_HISTORY_RE.search(text))
    f["sec_sponsors"] = f["sec_sponsors"] or bool(SPONSOR_URL_RE.search(text))
    f["sec_community"] = f["sec_community"] or bool(COMMUNITY_URL_RE.search(text))
    f["toc"] = f["sec_toc"] or len(ANCHOR_LINK_RE.findall(text)) >= 5
    f["sec_citation"] = f["sec_citation"] or bool(re.search(r"^@(article|misc|inproceedings|software)\{", text, re.M))
    del f["sec_toc"]

    head_lines = "\n".join(raw for _, raw, _, _ in lines[:30])
    f["translations"] = bool(TRANSLATION_FILE_RE.search(text)) or len(set(TRANSLATION_NAMES.findall(head_lines))) >= 2
    f["centered_header"] = bool(re.search(r"align\s*=\s*[\"']?center|<center>", "\n".join(raw for _, raw, _, _ in lines[:PITCH_LINES]), re.I))
    f["emoji_headings"] = sum(1 for h in headings if EMOJI_RE.search(h[2]))
    f["has_emoji_headings"] = f["emoji_headings"] > 0

    code_blocks = sum(1 for no, raw, in_code, _ in lines if in_code and FENCE_RE.match(raw))
    f["code_blocks"] = code_blocks // 2 + code_blocks % 2
    prose_text = "\n".join(raw for _, raw, in_code, _ in lines if not in_code)
    f["asks_for_star"] = bool(STAR_CTA_RE.search(prose_text))
    links = LINK_RE.findall(prose_text)
    f["has_demo_link"] = any(re.search(r"\b(live demo|demo|try it|playground|try (it )?online)\b", t, re.I) for t, _ in links)
    f["has_docs_link"] = any(re.search(r"\b(docs|documentation)\b", t, re.I) or re.search(r"docs?\.", u, re.I) for t, u in links)
    f["em_dash_count"] = prose_text.count("—")
    f["has_em_dash"] = f["em_dash_count"] > 0
    f["prose_words"] = _word_count(_plain(prose_text))
    return f


# Columns in the order they are written to features.csv and shown in reports.
BOOL_FEATURES = [
    ("pitch_in_first_15", "One-line pitch in the first 15 lines"),
    ("pitch_in_first_40", "One-line pitch in the first 40 lines"),
    ("image_in_first_40", "Image (not a badge) in the first 40 lines"),
    ("image_in_first_4000", "Image (not a badge) in the first 4,000 characters"),
    ("screenshot_in_first_40", "Image that is not a logo or icon in the first 40 lines"),
    ("has_gif", "A GIF anywhere"),
    ("has_video", "A video or video link anywhere"),
    ("has_badges", "Badges"),
    ("badges_in_first_15", "Badges in the first 15 lines"),
    ("install_oneliner", "An install or run command anywhere"),
    ("install_in_first_40", "Install or run command in the first 40 lines"),
    ("install_in_first_4000", "Install or run command in the first 4,000 characters"),
    ("git_clone_seen", "git clone shown"),
    ("setup_command_seen", "Dev setup command shown (bare npm install, pip install -r, uv sync)"),
    ("all_three_top40", "Pitch, image and install all in the first 40 lines"),
    ("has_table", "Any pipe table"),
    ("has_comparison_table", "A table framed as a comparison"),
    ("sec_install", "Install or quick start heading"),
    ("sec_usage", "Usage or examples heading"),
    ("sec_features", "Features heading"),
    ("sec_why", "Why, about or overview heading"),
    ("sec_comparison", "Comparison or alternatives heading"),
    ("sec_limits", "Limitations heading"),
    ("sec_demo", "Demo or screenshots heading"),
    ("sec_roadmap", "Roadmap heading"),
    ("sec_contributing", "Contributing heading"),
    ("sec_license", "License heading"),
    ("sec_faq", "FAQ or troubleshooting heading"),
    ("sec_citation", "Citation or BibTeX"),
    ("sec_sponsors", "Sponsor or funding link"),
    ("sec_community", "Community link (Discord, Slack, Telegram)"),
    ("sec_star_history", "Star history chart or heading"),
    ("toc", "Table of contents"),
    ("translations", "Translated READMEs linked"),
    ("centered_header", "Centered HTML header block"),
    ("has_emoji_headings", "Emoji in headings"),
    ("asks_for_star", "Asks the reader for a star"),
    ("has_demo_link", "Link to a demo or playground"),
    ("has_docs_link", "Link to docs"),
    ("has_em_dash", "Em dash in prose"),
]
NUMERIC_FEATURES = [
    "length_chars", "length_lines", "pitch_words", "image_count", "badge_count", "table_count",
    "heading_count", "h2_count", "code_blocks", "emoji_headings", "em_dash_count", "prose_words",
]
FEATURE_COLUMNS = (
    ["length_chars", "length_lines", "pitch_in_first_15", "pitch_in_first_40", "pitch_line_no", "pitch_words",
     "image_count", "first_image_line", "image_in_first_40", "image_in_first_4000", "screenshot_in_first_40", "has_gif", "gif_in_first_4000",
     "has_video", "badge_count", "has_badges", "badges_in_first_15", "install_oneliner", "install_kind",
     "install_line_no", "install_in_first_40", "install_in_first_4000", "git_clone_seen", "setup_command_seen", "all_three_top40",
     "table_count", "has_table", "tables_comparison", "tables_results", "tables_support_matrix", "tables_reference",
     "tables_other", "has_comparison_table", "html_table_count", "heading_count", "h2_count"]
    + [k for k in ("sec_install", "sec_usage", "sec_features", "sec_why", "sec_comparison", "sec_limits", "sec_demo",
                   "sec_roadmap", "sec_contributing", "sec_license", "sec_faq", "sec_citation", "sec_sponsors",
                   "sec_community", "sec_star_history", "toc")]
    + ["translations", "centered_header", "emoji_headings", "has_emoji_headings", "code_blocks", "asks_for_star",
       "has_demo_link", "has_docs_link", "em_dash_count", "has_em_dash", "prose_words"]
)
