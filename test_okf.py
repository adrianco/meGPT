"""
OKF Content Test Suite — three layers:
  1. Schema validation  — every OKF doc has required frontmatter fields
  2. Coverage check     — every CSV manifest entry has a matching OKF doc
  3. Golden Q&A         — LLM answers known questions and cites expected sources

Usage:
    python test_okf.py                  # run all tests
    python test_okf.py --schema         # schema only (fast, no API key)
    python test_okf.py --coverage       # coverage only (fast, no API key)
    python test_okf.py --qa             # golden Q&A only (requires ANTHROPIC_API_KEY)
    python test_okf.py --author my_author  # target a different author bundle
"""

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────

AUTHOR = "virtual_adrianco"
OKF_DIR = Path(__file__).parent / "okf"
AUTHORS_DIR = Path(__file__).parent / "authors"
MCP_RESOURCE = Path(__file__).parent / "mcp_resources"

REQUIRED_FRONTMATTER = ["type", "title", "resource"]

# Golden Q&A set: (question, [substrings that must appear in the answer])
# Each "must-contain" string is checked case-insensitively.
GOLDEN_QA = [
    (
        "What did Adrian Cockcroft say about schedulers and distributed systems?",
        ["scheduler", "container", "availability"],
    ),
    (
        "What is Adrian Cockcroft's view on microservices at Netflix?",
        ["netflix", "microservice"],
    ),
    (
        "What has Adrian Cockcroft written or said about sustainability and cloud computing?",
        ["sustainability", "cloud"],
    ),
    (
        "What did Adrian say about chaos engineering or continuous resilience?",
        ["chaos", "resilience"],
    ),
    (
        "What are Adrian Cockcroft's views on HPC and supercomputing?",
        ["hpc", "supercomputing"],
    ),
]

# ── Helpers ──────────────────────────────────────────────────────────────────

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
WARN = "\033[33mWARN\033[0m"


def header(title: str):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


def result(label: str, ok: bool, detail: str = ""):
    mark = PASS if ok else FAIL
    line = f"  [{mark}] {label}"
    if detail:
        line += f"  — {detail}"
    print(line)
    return ok


# ── Layer 1: Schema Validation ───────────────────────────────────────────────

def test_schema(author: str) -> bool:
    header("Layer 1: Schema Validation")
    okf_author = OKF_DIR / author
    if not okf_author.exists():
        result("OKF directory exists", False, str(okf_author))
        return False

    md_files = [
        p for p in okf_author.rglob("*.md")
        if p.name not in ("index.md", "log.md")
    ]
    result("OKF docs found", bool(md_files), f"{len(md_files)} docs")

    missing_fm: list[tuple[str, str]] = []
    no_content: list[str] = []
    empty_description: list[str] = []
    missing_tags: list[str] = []

    for path in md_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = str(path.relative_to(okf_author))

        fm_match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        if fm_match:
            fm = fm_match.group(1)
            for field in REQUIRED_FRONTMATTER:
                if f"{field}:" not in fm:
                    missing_fm.append((rel, field))
            if 'description: ""' in fm or "description: ''" in fm:
                empty_description.append(rel)
            if "tags:" in fm:
                tag_block = fm.split("tags:")[1].strip()
                if not tag_block or tag_block.startswith("\n") and not tag_block.strip():
                    missing_tags.append(rel)
        else:
            missing_fm.append((rel, "frontmatter block"))

        body = text.split("---", 2)[-1].strip() if text.count("---") >= 2 else text
        if len(body) < 50:
            no_content.append(rel)

    result("All docs have required fields", not missing_fm,
           f"{len(missing_fm)} violations" if missing_fm else "")
    if missing_fm:
        for doc, field in missing_fm[:5]:
            print(f"       missing '{field}': {doc}")

    result("No docs with empty bodies", not no_content,
           f"{len(no_content)} thin docs" if no_content else "")
    if no_content:
        for doc in no_content[:5]:
            print(f"       {doc}")

    if empty_description:
        print(f"  [{WARN}] {len(empty_description)} docs have empty description (non-fatal)")

    passed = not missing_fm and not no_content
    print(f"\n  Schema: {'ALL PASS' if passed else 'FAILURES FOUND'}")
    return passed


# ── Layer 2: Coverage Check ──────────────────────────────────────────────────

def _slug(url: str) -> str:
    """Normalise a URL to a comparable slug."""
    return re.sub(r"[^a-z0-9]+", "-", url.lower().rstrip("/")).strip("-")


def test_coverage(author: str) -> bool:
    header("Layer 2: Coverage Check")
    csv_path = AUTHORS_DIR / author / "published_content_v2.csv"
    okf_author = OKF_DIR / author

    if not csv_path.exists():
        result("CSV manifest found", False, str(csv_path))
        return False
    if not okf_author.exists():
        result("OKF directory found", False, str(okf_author))
        return False

    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    result("CSV manifest readable", True, f"{len(rows)} entries")

    # Build set of resource URLs present in OKF docs
    okf_resources: set[str] = set()
    for path in okf_author.rglob("*.md"):
        if path.name in ("index.md", "log.md"):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        fm_match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        if fm_match:
            for line in fm_match.group(1).splitlines():
                if line.startswith("resource:"):
                    url = line.split("resource:", 1)[1].strip().strip('"\'')
                    okf_resources.add(url)

    # Count OKF docs by subdirectory (category)
    counts: dict[str, int] = {}
    for path in okf_author.rglob("*.md"):
        if path.name in ("index.md", "log.md"):
            continue
        cat = path.parent.name
        counts[cat] = counts.get(cat, 0) + 1

    total_okf = sum(counts.values())
    result("OKF bundle non-empty", total_okf > 0, f"{total_okf} docs total")
    for cat, n in sorted(counts.items()):
        print(f"       {cat}: {n}")

    # For each CSV entry, check if a matching OKF resource exists
    missing: list[str] = []
    for row in rows:
        url = row.get("URL", "").strip()
        if not url:
            continue
        if url not in okf_resources:
            # loose match: check slug similarity
            url_slug = _slug(url)
            if not any(url_slug[:40] in _slug(r) or _slug(r)[:40] in url_slug
                       for r in okf_resources):
                missing.append(f"{row.get('Kind','?')} / {row.get('What','?')} — {url}")

    result("All CSV entries have OKF docs", not missing,
           f"{len(missing)} unmatched" if missing else "")
    if missing:
        for m in missing:
            print(f"       {m}")

    passed = total_okf > 0 and not missing
    print(f"\n  Coverage: {'ALL PASS' if passed else 'GAPS FOUND'}")
    return passed


# ── Layer 3: Golden Q&A ──────────────────────────────────────────────────────

def _load_mcp_resource(author: str) -> list[dict]:
    path = MCP_RESOURCE / author / "mcp_resource.json"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        r = json.load(f)
    return r.get("content", r.get("items", []))


def _load_okf_items(author: str) -> list[dict]:
    """Load OKF markdown docs as item dicts for Q&A context."""
    okf_author = OKF_DIR / author
    items: list[dict] = []
    kind_map = {"podcasts": "podcast", "talks": "youtube", "posts": "story", "books": "book"}
    for path in okf_author.rglob("*.md"):
        if path.name in ("index.md", "log.md"):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        fm_match = re.match(r"^---\n(.*?)\n---\s*(.*)", text, re.DOTALL)
        if not fm_match:
            continue
        fm_text, body = fm_match.group(1), fm_match.group(2)

        def fm_val(key: str) -> str:
            m = re.search(rf'^{key}:\s*"?([^"\n]+)"?', fm_text, re.MULTILINE)
            return m.group(1).strip() if m else ""

        tags: list[str] = re.findall(r"^\s+-\s+(.+)", fm_text.split("tags:", 1)[-1], re.MULTILINE) if "tags:" in fm_text else []
        kind = kind_map.get(path.parent.name, "story")
        items.append({
            "kind": kind,
            "title": fm_val("title"),
            "url": fm_val("resource"),
            "tags": [t.strip() for t in tags],
            "content": {"text": body.strip()},
        })
    return items


def _build_context(items: list[dict], max_chars: int = 80_000, query: str = "") -> str:
    """Build a compact context string from mcp_resource items.

    When a query is provided, items whose title/tags/text match query keywords
    are ranked first, ensuring relevant content isn't crowded out by earlier items.
    """
    keywords = [w.lower() for w in query.split() if len(w) > 3] if query else []

    def relevance(item: dict) -> int:
        if not keywords:
            return 0
        title = item.get("title", "").lower()
        tags = " ".join(item.get("tags", [])).lower()
        c = item.get("content", {})
        text = (c.get("text", "") if isinstance(c, dict) else str(c))[:500].lower()
        # Title matches are worth 3x — they signal the item is directly about the topic
        title_hits = sum(3 for kw in keywords if kw in title)
        tag_hits = sum(2 for kw in keywords if kw in tags)
        text_hits = sum(1 for kw in keywords if kw in text)
        return title_hits + tag_hits + text_hits

    # High-value kinds first within each relevance tier
    kind_priority = {"podcast": 0, "youtube": 1, "book": 2, "story": 3, "file": 4}

    ranked = sorted(
        items,
        key=lambda i: (-relevance(i), kind_priority.get(i.get("kind", ""), 5)),
    )

    parts: list[str] = []
    total = 0
    for item in ranked:
        c = item.get("content", {})
        text = c.get("text", "") if isinstance(c, dict) else str(c)
        if not text:
            continue
        # Richer content types get more chars; short posts get less
        kind = item.get("kind", "")
        item_limit = 6000 if kind in ("podcast", "youtube", "book") else 1500
        chunk = (
            f"[{kind}] {item.get('title','')}\n"
            f"URL: {item.get('url','')}\n"
            f"Tags: {', '.join(item.get('tags', []))}\n"
            f"{text[:item_limit]}\n"
        )
        if total + len(chunk) > max_chars:
            break
        parts.append(chunk)
        total += len(chunk)
    return "\n---\n".join(parts)


def _claude_cli_path() -> str:
    """Find the claude CLI binary."""
    import json as _json
    try:
        cfg = _json.load(open(Path(__file__).parent.parent / "house-agent/.instar/config.json"))
        p = cfg.get("sessions", {}).get("claudePath", "")
        if p and os.path.exists(p):
            return p
    except Exception:
        pass
    for candidate in ("/Users/corfehill/homebrew/bin/claude", "/usr/local/bin/claude", "claude"):
        if os.path.exists(candidate):
            return candidate
    return "claude"


def _oauth_token() -> str:
    """Read the OAuth token from instar config."""
    import json as _json
    try:
        cfg = _json.load(open(Path(__file__).parent.parent / "house-agent/.instar/config.json"))
        return cfg.get("sessions", {}).get("anthropicApiKey", "")
    except Exception:
        return ""


def _ask_claude_cli(prompt: str, claude: str) -> str:
    """Run a one-shot claude -p query and return stdout."""
    import subprocess
    env = os.environ.copy()
    token = _oauth_token()
    if token:
        env["CLAUDE_CODE_OAUTH_TOKEN"] = token
    r = subprocess.run(
        [claude, "--dangerously-skip-permissions", "-p", prompt],
        capture_output=True, text=True, timeout=60, env=env,
    )
    return (r.stdout + r.stderr).strip()


def test_golden_qa(author: str) -> bool:
    header("Layer 3: Golden Q&A (LLM-based)")

    claude = _claude_cli_path()
    result("claude CLI found", os.path.exists(claude), claude)
    if not os.path.exists(claude):
        return False

    items = _load_okf_items(author)
    if not items:
        result("OKF docs loaded", False, f"no docs in okf/{author}/")
        return False
    result("OKF docs loaded", True, f"{len(items)} docs")

    system = (
        "You are a research assistant with access to Adrian Cockcroft's published content. "
        "Answer questions using ONLY the provided content. "
        "Always cite the source URL when you reference specific content."
    )

    all_pass = True
    for question, must_contain in GOLDEN_QA:
        try:
            context = _build_context(items, query=question)
            prompt = (
                f"{system}\n\n"
                f"Content:\n{context[:40000]}\n\n"
                f"Question: {question}"
            )
            answer = _ask_claude_cli(prompt, claude).lower()
            hits = [kw for kw in must_contain if kw.lower() in answer]
            ok = len(hits) == len(must_contain)
            result(
                f"Q: {question[:60]}...",
                ok,
                f"found {len(hits)}/{len(must_contain)} expected terms"
                if not ok
                else f"all {len(must_contain)} terms present",
            )
            if not ok:
                missing_kw = [kw for kw in must_contain if kw.lower() not in answer]
                print(f"       missing terms: {missing_kw}")
                print(f"       answer snippet: {answer[:200]}")
            all_pass = all_pass and ok
        except Exception as e:
            result(f"Q: {question[:60]}...", False, str(e))
            all_pass = False

    print(f"\n  Q&A: {'ALL PASS' if all_pass else 'FAILURES FOUND'}")
    return all_pass


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="OKF content test suite")
    parser.add_argument("--author", default=AUTHOR, help="Author bundle to test")
    parser.add_argument("--schema", action="store_true", help="Run schema validation only")
    parser.add_argument("--coverage", action="store_true", help="Run coverage check only")
    parser.add_argument("--qa", action="store_true", help="Run golden Q&A only")
    args = parser.parse_args()

    run_all = not (args.schema or args.coverage or args.qa)

    results: list[bool] = []

    if run_all or args.schema:
        results.append(test_schema(args.author))

    if run_all or args.coverage:
        results.append(test_coverage(args.author))

    if run_all or args.qa:
        results.append(test_golden_qa(args.author))

    print(f"\n{'═' * 60}")
    overall = all(results)
    print(f"  Overall: {'ALL TESTS PASSED' if overall else 'SOME TESTS FAILED'}")
    print(f"{'═' * 60}\n")
    sys.exit(0 if overall else 1)


if __name__ == "__main__":
    main()
