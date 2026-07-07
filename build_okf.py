"""
build_okf.py — OKF bundle builder for megpt

Reads published_content.csv (or published_content_v2.csv for the enhanced format),
runs each item through the appropriate v2 processor, and builds an OKF bundle
in okf/<author>/.

Usage:
    python build_okf.py <author> [kind] [options]

Options:
    --force         Reprocess items even if already done
    --no-llm        Skip LLM enrichment in all processors
    --anthropic-key KEY   Anthropic API key (or set ANTHROPIC_API_KEY)
    --assemblyai-key KEY  AssemblyAI key for podcast diarization
    --whisper-model SIZE  Whisper model: tiny|base|small|medium (default: base)
    --workers N     Parallel workers for independent items (default: 2)
    --verbose       Verbose output

Enhanced CSV format (published_content_v2.csv):
    Kind, SubKind, What, Where, Published, URL, SlidesURL, Tags
    - SlidesURL: optional PDF/PPT URL to pair with a talk/video
    - Tags: comma-separated seed tags (LLM enrichment will add more)

Backward compatible with original published_content.csv format.

Output structure:
    okf/<author>/
        index.md              ← bundle root index
        log.md                ← change log
        podcasts/
            episode-title.md
        talks/
            talk-title.md
        books/
            book-title.md
        posts/
            post-title.md
        topics/               ← synthesized by okf_synthesizer.py
            topic-name.md
"""

import argparse
import asyncio
import csv
import json
import logging
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Map content Kind → processor script + output subfolder
PROCESSOR_MAP = {
    "podcast": ("processors/podcast_processor_v2.py", "podcasts"),
    "youtube": ("processors/youtube_processor_v2.py", "talks"),
    "book":    ("processors/book_processor_v2.py",    "books"),
    "story":   ("processors/story_processor_v2.py",   "posts"),
    "blog":    ("processors/story_processor_v2.py",   "posts"),
    "medium":  ("processors/story_processor_v2.py",   "posts"),
    "textfile":("processors/story_processor_v2.py",   "posts"),
    "file":    ("processors/story_processor_v2.py",   "posts"),
}

STATE_FILE_NAME = ".okf_state.json"


def load_state(author_dir: Path) -> dict:
    state_file = author_dir / STATE_FILE_NAME
    if state_file.exists():
        return json.loads(state_file.read_text())
    return {}


def save_state(author_dir: Path, state: dict) -> None:
    state_file = author_dir / STATE_FILE_NAME
    state_file.write_text(json.dumps(state, indent=2))


def sanitize_filename(name: str) -> str:
    clean = re.sub(r"[^\w\s-]", "", name)
    clean = re.sub(r"[\s_]+", "-", clean).strip("-")
    return clean[:100].lower()


def load_csv(author: str) -> list[dict]:
    """Load published_content_v2.csv or fall back to published_content.csv."""
    base = Path(f"authors/{author}")
    for fname in ("published_content_v2.csv", "published_content.csv"):
        csv_path = base / fname
        if csv_path.exists():
            with open(csv_path, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            logger.info("Loaded %d rows from %s", len(rows), fname)
            return rows
    raise FileNotFoundError(f"No published_content CSV found for author: {author}")


def build_processor_args(row: dict, okf_subdir: Path, script: str, opts: argparse.Namespace) -> list[str]:
    """Build the subprocess argv for a processor."""
    python = str(Path(sys.executable))
    url = row.get("URL", "").strip()
    subkind = row.get("SubKind", "").strip()
    slides_url = row.get("SlidesURL", "").strip()

    argv = [python, script, url, str(okf_subdir)]

    # Processor-specific args
    if "podcast" in script:
        if opts.whisper_model:
            argv += ["--whisper-model", opts.whisper_model]
        if opts.assemblyai_key:
            argv += ["--assemblyai-key", opts.assemblyai_key]
            argv += ["--transcriber", "assemblyai"]
        if opts.anthropic_key:
            argv += ["--anthropic-key", opts.anthropic_key]
        if opts.no_llm:
            argv.append("--no-llm")
        argv += ["--author", opts.author_display or "unknown"]

    elif "youtube" in script:
        if slides_url:
            argv += ["--slides-url", slides_url]
        if opts.anthropic_key:
            argv += ["--anthropic-key", opts.anthropic_key]
        if opts.no_llm:
            argv.append("--no-llm")
        argv += ["--author", opts.author_display or "unknown"]

    elif "book" in script:
        if subkind:  # subkind = page ranges for books
            argv.append(subkind)
        else:
            argv.append("1-")  # default: all pages
        title = row.get("What", "").strip()
        if title:
            argv += ["--title", title]
        if opts.anthropic_key:
            argv += ["--anthropic-key", opts.anthropic_key]
        if opts.no_llm:
            argv.append("--no-llm")

    elif "story" in script:
        if subkind:
            argv.append(subkind)
        if opts.anthropic_key:
            argv += ["--anthropic-key", opts.anthropic_key]
        if opts.no_llm:
            argv.append("--no-llm")

    if opts.verbose:
        argv.append("--verbose")

    return argv


def process_row(row: dict, okf_dir: Path, state: dict, opts: argparse.Namespace) -> dict:
    """Process a single CSV row. Returns a result dict."""
    url = row.get("URL", "").strip()
    kind = row.get("Kind", "").strip().lower()
    what = row.get("What", url)
    state_key = f"{kind}::{url}"

    if not url:
        return {"key": state_key, "status": "skipped", "reason": "empty URL"}

    if not opts.force and state.get(state_key, {}).get("status") == "done":
        return {"key": state_key, "status": "skipped", "reason": "already processed"}

    processor_info = PROCESSOR_MAP.get(kind)
    if not processor_info:
        return {"key": state_key, "status": "skipped", "reason": f"no processor for kind={kind}"}

    script, subfolder = processor_info
    if not Path(script).exists():
        return {"key": state_key, "status": "error", "reason": f"processor not found: {script}"}

    okf_subdir = okf_dir / subfolder
    okf_subdir.mkdir(parents=True, exist_ok=True)

    argv = build_processor_args(row, okf_subdir, script, opts)

    print(f"  → [{kind}] {what[:60]}")
    try:
        result = subprocess.run(argv, capture_output=not opts.verbose, text=True, timeout=600)
        if result.returncode == 0:
            return {"key": state_key, "status": "done", "ts": datetime.now().isoformat()}
        else:
            err = (result.stderr or "")[-300:]
            return {"key": state_key, "status": "error", "reason": err}
    except subprocess.TimeoutExpired:
        return {"key": state_key, "status": "error", "reason": "timeout after 600s"}
    except Exception as e:
        return {"key": state_key, "status": "error", "reason": str(e)}


def generate_bundle_index(author: str, okf_dir: Path) -> None:
    """Generate okf/<author>/index.md listing all content."""
    sections = {}
    for md_file in sorted(okf_dir.rglob("*.md")):
        if md_file.name in ("index.md", "log.md") or "/topics/" in str(md_file):
            continue
        subfolder = md_file.parent.name
        sections.setdefault(subfolder, []).append(md_file)

    lines = [
        "---",
        f'name: "{author}"',
        f'type: OKF Bundle',
        f'okf_version: "0.1"',
        "---",
        "",
        f"# {author} Knowledge Bundle",
        "",
        f"Auto-generated OKF bundle for {author}. "
        f"Contains {sum(len(v) for v in sections.values())} knowledge documents.",
        "",
    ]

    for section, files in sorted(sections.items()):
        lines.append(f"## {section.title()}")
        lines.append("")
        for f in files:
            rel = f.relative_to(okf_dir)
            # Try to extract title from frontmatter
            try:
                content = f.read_text()
                title_m = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', content, re.M)
                title = title_m.group(1) if title_m else f.stem
            except Exception:
                title = f.stem
            lines.append(f"- [{title}]({rel})")
        lines.append("")

    (okf_dir / "index.md").write_text("\n".join(lines))
    print(f"✓ Generated index.md ({sum(len(v) for v in sections.values())} docs)")


def append_log_entry(okf_dir: Path, author: str, n_processed: int, n_errors: int) -> None:
    """Append a run entry to log.md."""
    log_path = okf_dir / "log.md"
    date_str = datetime.now().strftime("%Y-%m-%d")
    entry = (
        f"\n## {date_str}\n\n"
        f"Build run: {n_processed} items processed, {n_errors} errors.\n"
    )
    if log_path.exists():
        log_path.write_text(log_path.read_text() + entry)
    else:
        log_path.write_text(f"# Change Log — {author}\n\n" + entry)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build OKF bundle for a megpt author")
    parser.add_argument("author", help="Author name (matches authors/<name>/ directory)")
    parser.add_argument("kind", nargs="?", help="Process only this content kind")
    parser.add_argument("--force", action="store_true", help="Reprocess already-done items")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM enrichment")
    parser.add_argument("--anthropic-key", default=os.environ.get("ANTHROPIC_API_KEY"))
    parser.add_argument("--assemblyai-key", default=os.environ.get("ASSEMBLYAI_API_KEY"))
    parser.add_argument("--whisper-model", default="base")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--author-display", default=None,
                        help="Display name for the author (e.g. 'Adrian Cockcroft')")
    parser.add_argument("--verbose", "-v", action="store_true")
    opts = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if opts.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s"
    )

    if not opts.author_display:
        opts.author_display = opts.author.replace("_", " ").replace("-", " ").title()

    okf_dir = Path(f"okf/{opts.author}")
    okf_dir.mkdir(parents=True, exist_ok=True)

    state = load_state(okf_dir)

    try:
        rows = load_csv(opts.author)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Filter by kind if specified
    if opts.kind:
        rows = [r for r in rows if r.get("Kind", "").lower() == opts.kind.lower()]
        print(f"Filtered to {len(rows)} rows of kind={opts.kind}")

    print(f"Processing {len(rows)} items for {opts.author} → okf/{opts.author}/")
    if not opts.anthropic_key:
        print("⚠  ANTHROPIC_API_KEY not set — LLM enrichment will be skipped")
    print()

    results = []
    n_done = n_error = n_skip = 0

    if opts.workers > 1:
        with ThreadPoolExecutor(max_workers=opts.workers) as pool:
            futures = {
                pool.submit(process_row, row, okf_dir, state, opts): row
                for row in rows
            }
            for future in as_completed(futures):
                res = future.result()
                results.append(res)
                state[res["key"]] = res
                if res["status"] == "done":
                    n_done += 1
                elif res["status"] == "error":
                    n_error += 1
                    print(f"  ✗ error: {res.get('reason', '')[:120]}")
                else:
                    n_skip += 1
                save_state(okf_dir, state)
    else:
        for row in rows:
            res = process_row(row, okf_dir, state, opts)
            results.append(res)
            state[res["key"]] = res
            if res["status"] == "done":
                n_done += 1
            elif res["status"] == "error":
                n_error += 1
                print(f"  ✗ error: {res.get('reason', '')[:120]}")
            else:
                n_skip += 1
            save_state(okf_dir, state)

    print(f"\nDone: {n_done} processed, {n_skip} skipped, {n_error} errors")

    generate_bundle_index(opts.author, okf_dir)
    append_log_entry(okf_dir, opts.author, n_done, n_error)

    print(f"\nOKF bundle: okf/{opts.author}/")
    print("Next: python okf_synthesizer.py to generate topic pages")


if __name__ == "__main__":
    main()
