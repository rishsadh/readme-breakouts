"""Define "breakout", enumerate the whole population, and draw a stratified sample.

Breakout, as used here: a public, non-fork repository created in the 365 days before the run
date that has at least MIN_STARS stars on the run date. The population is enumerated in full
through the GitHub search API (created-date windows, split whenever a window holds more than
the 1,000 results search will return), so the sample is drawn from every qualifying repo, not
from a trending list.
"""
import csv
import datetime as dt
import math
import random
import re

MIN_STARS = 1000
WINDOW_DAYS = 365
KINDS = ["awesome-list", "mcp-server", "agent-or-skill", "ai-model-or-research", "cli-tool",
         "library-or-framework", "app", "learning", "other"]

POP_COLUMNS = ["full_name", "kind", "stars", "forks", "open_issues", "created_at", "pushed_at", "age_days",
               "stars_per_day", "stars_per_fork", "language", "owner_type", "archived", "license", "topics"]

# Repo descriptions are read while classifying kind and are never written to a published file.
# They belong to strangers and some carry contact details, so no CSV column may hold them.
NEVER_PUBLISHED = ("description",)

_TOKEN = re.compile(r"[a-z0-9]+")
_RULES = [
    ("awesome-list", {"awesome", "curated"}, ["awesome-", "curated list", "collection of"]),
    ("mcp-server", {"mcp"}, ["model context protocol"]),
    ("agent-or-skill", {"agent", "agents", "agentic", "skill", "skills", "claude", "codex", "cursor",
                        "copilot", "subagent", "subagents", "prompt", "prompts", "openclaw", "swarm"}, []),
    ("ai-model-or-research", {"model", "models", "llm", "llms", "paper", "benchmark", "dataset", "inference",
                              "training", "diffusion", "transformer", "transformers", "rag", "embedding",
                              "embeddings", "vision", "speech", "tts", "asr", "robotics", "neural", "ml", "ai"}, []),
    ("cli-tool", {"cli", "terminal", "tui", "commandline"}, ["command line", "command-line"]),
    ("library-or-framework", {"library", "framework", "sdk", "package", "component", "components", "toolkit",
                              "api", "runtime", "engine", "compiler", "parser"}, []),
    ("app", {"app", "apps", "desktop", "extension", "browser", "plugin", "dashboard", "editor", "client",
             "selfhosted", "ui", "gui", "ide", "game", "website", "platform"}, ["self-hosted"]),
    ("learning", {"tutorial", "tutorials", "course", "guide", "roadmap", "book", "interview", "cheatsheet",
                  "learn", "learning", "education", "notes", "handbook"}, []),
]


def classify_kind(name, description, topics):
    """Rule-based kind from name, description and topics. First matching rule wins."""
    topics = topics or []
    base = f"{name} {description or ''} {' '.join(topics)}".lower()
    tokens = set(_TOKEN.findall(base))
    tokens |= {t.replace("-", "") for t in topics}
    for kind, words, phrases in _RULES:
        if tokens & words or any(p in base for p in phrases):
            return kind
    return "other"


def to_row(item, run_date):
    created = dt.datetime.strptime(item["created_at"], "%Y-%m-%dT%H:%M:%SZ")
    age = max((dt.datetime.combine(run_date, dt.time.max) - created).total_seconds() / 86400, 1.0)
    stars, forks = item["stargazers_count"], item["forks_count"]
    lic = (item.get("license") or {}).get("spdx_id") or ""
    return {
        "full_name": item["full_name"],
        "kind": classify_kind(item["name"], item.get("description"), item.get("topics")),
        "stars": stars,
        "forks": forks,
        "open_issues": item.get("open_issues_count", 0),
        "created_at": item["created_at"][:10],
        "pushed_at": (item.get("pushed_at") or "")[:10],
        "age_days": round(age, 1),
        "stars_per_day": round(stars / age, 2),
        "stars_per_fork": round(stars / forks, 1) if forks else "",
        "language": item.get("language") or "",
        "owner_type": (item.get("owner") or {}).get("type", ""),
        "archived": bool(item.get("archived")),
        "license": lic if lic != "NOASSERTION" else "",
        "topics": " ".join(item.get("topics") or []),
    }


def _search(client, a, b, min_stars, log):
    q = f"created:{a.isoformat()}..{b.isoformat()} stars:>={min_stars}"
    params = {"q": q, "sort": "stars", "order": "desc", "per_page": 100, "page": 1}
    first = client.get_json("/search/repositories", params)
    total = first["total_count"]
    if total > 1000 and a < b:
        mid = a + (b - a) // 2
        log(f"  {a}..{b} holds {total}, splitting")
        return _search(client, a, mid, min_stars, log) + _search(client, mid + dt.timedelta(days=1), b, min_stars, log)
    items = list(first["items"])
    for page in range(2, math.ceil(min(total, 1000) / 100) + 1):
        params["page"] = page
        items += client.get_json("/search/repositories", params)["items"]
    log(f"  {a}..{b}: {len(items)} of {total}")
    return items


def enumerate_population(client, run_date, min_stars=MIN_STARS, days=WINDOW_DAYS, step=30, log=print):
    """Every repo created in (run_date - days, run_date] with >= min_stars. Returns a list of rows."""
    start = run_date - dt.timedelta(days=days - 1)
    seen, a = {}, start
    while a <= run_date:
        b = min(a + dt.timedelta(days=step - 1), run_date)
        for item in _search(client, a, b, min_stars, log):
            seen[item["full_name"]] = item
        a = b + dt.timedelta(days=1)
    return sorted((to_row(i, run_date) for i in seen.values()), key=lambda r: -r["stars"])


def allocate(sizes, total, min_each=5):
    """Split `total` picks across strata: a floor per stratum, then proportional by largest remainder."""
    kinds = [k for k, n in sizes.items() if n > 0]
    alloc = {k: min(sizes[k], min_each) for k in kinds}
    left = total - sum(alloc.values())
    if left <= 0:
        return alloc
    room = {k: sizes[k] - alloc[k] for k in kinds}
    pool = sum(room.values())
    if pool <= 0:
        return alloc
    quota = {k: left * room[k] / pool for k in kinds}
    for k in kinds:
        add = min(int(quota[k]), room[k])
        alloc[k] += add
    left = total - sum(alloc.values())
    for k in sorted(kinds, key=lambda k: quota[k] - int(quota[k]), reverse=True):
        if left <= 0:
            break
        if alloc[k] < sizes[k]:
            alloc[k] += 1
            left -= 1
    return alloc


def draw(population, n=100, seed=20260930, reserve_each=4, min_each=5):
    """Stratify by kind. Inside a stratum, alternate between the faster and slower half by stars per day.

    Returns rows with `role` set to selected or reserve, and `order` within the stratum."""
    rng = random.Random(seed)
    by_kind = {}
    for r in population:
        by_kind.setdefault(r["kind"], []).append(r)
    quotas = allocate({k: len(v) for k, v in by_kind.items()}, n, min_each)
    out = []
    for kind in sorted(by_kind):
        rows = sorted(by_kind[kind], key=lambda r: (-float(r["stars_per_day"]), r["full_name"]))
        half = (len(rows) + 1) // 2
        fast, slow = rows[:half], rows[half:]
        rng.shuffle(fast)
        rng.shuffle(slow)
        order = []
        while fast or slow:
            if fast:
                order.append(fast.pop())
            if slow:
                order.append(slow.pop())
        q = quotas.get(kind, 0)
        for i, r in enumerate(order[: q + reserve_each]):
            out.append({**r, "role": "selected" if i < q else "reserve", "order": i + 1})
    return out, quotas


def write_csv(path, rows, columns):
    banned = [c for c in columns if c in NEVER_PUBLISHED]
    if banned:
        raise ValueError(f"refusing to write a column that is never published: {', '.join(banned)}")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))
