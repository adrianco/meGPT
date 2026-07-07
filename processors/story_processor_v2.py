"""
story_processor_v2.py — OKF web article / blog post / text file processor

Handles: Medium posts, blog posts, any web article URL, or local .txt/.md files.
Also subsumes textfiles_processor.py functionality.

Pipeline:
  1. Fetch content (URL or local file)
  2. Extract clean text via readability-style heuristics
  3. Enrich with Claude: summary, themes, key argument, quotes, tags
  4. Emit OKF-compliant .md document

Usage:
    python story_processor_v2.py <url_or_path> <output_dir> [subkind] [options]

    subkind: optional div ID or CSS class to target for extraction

Options:
    --author NAME         Author name (default: unknown)
    --anthropic-key KEY   Anthropic API key (or ANTHROPIC_API_KEY env var)
    --no-llm              Skip LLM enrichment
    --content-type TYPE   "Blog Post" | "Article" | "Essay" (default: auto-detected)
    --verbose             Verbose logging
"""

import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

ENRICH_SYSTEM = """You extract structured knowledge from article/blog post text.
Output valid JSON only with these keys:
{
  "summary": "2-4 sentence summary",
  "main_argument": "one sentence stating the author's core point or thesis",
  "themes": ["list", "of", "topic", "tags"],
  "notable_quotes": ["verbatim quote 1", "verbatim quote 2"],
  "content_type": "Blog Post" or "Article" or "Essay"
}
No markdown, no prose outside JSON."""


# ---------------------------------------------------------------------------
# Content fetching
# ---------------------------------------------------------------------------

def is_local_path(source: str) -> bool:
    return not source.startswith(("http://", "https://")) and Path(source).exists()


def fetch_local_file(path: str) -> tuple[str, dict]:
    """Read a local archive file, extracting embedded [URL] and title if present.

    Medium and Blogger archive files start with:
        [URL] https://...

        Title Line
        Optional subtitle / description
    """
    import re as _re
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    # Extract embedded URL (first line or within first 5 lines)
    embedded_url: str | None = None
    for line in lines[:5]:
        m = _re.match(r"^\[URL\]\s+(https?://\S+)", line.strip())
        if m:
            embedded_url = m.group(1)
            break

    # Extract title: first non-empty, non-URL, non-metadata line after the URL line
    title_fallback = Path(path).stem.replace("_", " ").replace("-", " ").title()
    extracted_title = title_fallback
    if embedded_url:
        past_url = False
        for line in lines:
            if embedded_url in line:
                past_url = True
                continue
            if past_url and line.strip() and not line.startswith("["):
                candidate = line.strip()
                if len(candidate) > 5 and len(candidate) < 200:
                    extracted_title = candidate
                break

    meta = {
        "title": extracted_title,
        "description": None,
        "published": None,
        "url": embedded_url or path,
    }
    return text, meta


WAYBACK_BASE = "https://web.archive.org/web/2024/"


def _wayback_url(url: str) -> str:
    return WAYBACK_BASE + url


def _fetch_raw(url: str, verify_ssl: bool = True) -> requests.Response:
    """Fetch a URL with a realistic browser User-Agent."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    return requests.get(url, headers=headers, timeout=20, verify=verify_ssl)


def fetch_url(url: str, subkind: str | None = None) -> tuple[str, dict]:
    """Fetch URL and extract main article text plus metadata.

    Fallback chain:
      1. Direct fetch with SSL verification
      2. Direct fetch without SSL verification (handles TLS handshake failures)
      3. Wayback Machine archive (handles 403 and 404)
    """
    resp = None
    last_err = None

    for attempt_url, verify in [
        (url, True),
        (url, False),
        (_wayback_url(url), True),
    ]:
        try:
            r = _fetch_raw(attempt_url, verify_ssl=verify)
            if r.status_code in (200, 203):
                resp = r
                if attempt_url != url:
                    logger.info("Fetched via fallback: %s", attempt_url)
                break
            last_err = f"HTTP {r.status_code}"
            logger.warning("Fetch attempt %s → %s", attempt_url, last_err)
        except requests.exceptions.SSLError as e:
            last_err = f"SSLError: {e}"
            logger.warning("SSL failure for %s, trying fallback", attempt_url)
        except requests.RequestException as e:
            last_err = str(e)
            logger.warning("Request error for %s: %s", attempt_url, e)

    if resp is None:
        raise RuntimeError(f"Failed to fetch {url} (all attempts): {last_err}")

    soup = BeautifulSoup(resp.text, "html.parser")

    # --- Metadata ---
    def meta_content(name=None, prop=None):
        tag = None
        if prop:
            tag = soup.find("meta", property=prop)
        if not tag and name:
            tag = soup.find("meta", attrs={"name": name})
        return tag["content"].strip() if tag and tag.get("content") else None

    title = (
        meta_content(prop="og:title")
        or (soup.title.string.strip() if soup.title else None)
        or "Untitled"
    )
    description = meta_content(prop="og:description") or meta_content(name="description")
    published = (
        meta_content(prop="article:published_time")
        or meta_content(name="date")
        or meta_content(prop="og:updated_time")
    )
    meta = {"title": title, "description": description, "published": published, "url": url}

    # --- Content extraction ---
    # Remove noise elements
    for tag in soup(["script", "style", "nav", "header", "footer",
                     "aside", "form", "noscript", "iframe"]):
        tag.decompose()

    text = None

    # 1. Explicit subkind: div ID or class
    if subkind:
        target = soup.find(id=subkind) or soup.find(class_=subkind)
        if target:
            text = _clean_text(target)
            logger.info("Extracted via subkind=%s (%d chars)", subkind, len(text))

    # 2. <article> tag
    if not text:
        article = soup.find("article")
        if article:
            text = _clean_text(article)
            logger.info("Extracted via <article> (%d chars)", len(text))

    # 3. Largest <div> by text length
    if not text:
        candidates = []
        for div in soup.find_all("div"):
            t = _clean_text(div)
            if len(t) > 200:
                candidates.append((len(t), t))
        if candidates:
            text = sorted(candidates, reverse=True)[0][1]
            logger.info("Extracted via largest div (%d chars)", len(text))

    # 4. Body fallback
    if not text:
        text = _clean_text(soup.body or soup)
        logger.info("Extracted via body fallback (%d chars)", len(text))

    return text or "", meta


def _clean_text(element) -> str:
    """Extract readable text from a BS4 element."""
    lines = []
    for elem in element.descendants:
        if elem.name in ("p", "h1", "h2", "h3", "h4", "li", "blockquote"):
            t = elem.get_text(" ", strip=True)
            if t:
                lines.append(t)
    if not lines:
        return element.get_text(" ", strip=True)
    return "\n\n".join(lines)


# ---------------------------------------------------------------------------
# LLM enrichment
# ---------------------------------------------------------------------------

def enrich_with_llm(text: str, title: str, api_key: str) -> dict:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    excerpt = text[:6000]
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=ENRICH_SYSTEM,
        messages=[{
            "role": "user",
            "content": f"Title: {title}\n\nCONTENT:\n{excerpt}"
        }],
    )
    raw = msg.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


# ---------------------------------------------------------------------------
# OKF document generation
# ---------------------------------------------------------------------------

def sanitize_filename(name: str) -> str:
    clean = re.sub(r"[^\w\s-]", "", name)
    clean = re.sub(r"[\s_]+", "-", clean).strip("-")
    return clean[:120].lower()


def detect_content_type(url: str, enrichment: dict, override: str | None) -> str:
    if override:
        return override
    if enrichment.get("content_type"):
        return enrichment["content_type"]
    if "medium.com" in url or "substack.com" in url or "blogger.com" in url:
        return "Blog Post"
    return "Article"


def generate_okf_doc(
    title: str,
    source: str,
    author: str,
    meta: dict,
    enrichment: dict,
    raw_text: str,
    content_type: str,
) -> str:
    summary = enrichment.get("summary") or meta.get("description") or ""
    main_arg = enrichment.get("main_argument", "")
    themes = enrichment.get("themes", [])
    quotes = enrichment.get("notable_quotes", [])
    published = meta.get("published", "")

    tags_yaml = "\n".join(f"  - {t}" for t in themes) if themes else "  - article"

    frontmatter_lines = [
        "---",
        f'type: {content_type}',
        f'title: "{title.replace(chr(34), chr(39))}"',
        f'description: "{summary[:200].replace(chr(34), chr(39))}"',
        f'resource: "{source}"',
        "tags:",
        tags_yaml,
    ]
    if published:
        frontmatter_lines.append(f'timestamp: "{published}"')
    frontmatter_lines.append("---")
    frontmatter = "\n".join(frontmatter_lines)

    summary_section = f"\n## Summary\n\n{summary}\n" if summary else ""

    argument_section = f"\n## Core Argument\n\n{main_arg}\n" if main_arg else ""

    themes_section = ""
    if themes:
        themes_section = "\n## Key Themes\n\n" + "\n".join(f"- {t}" for t in themes) + "\n"

    quotes_section = ""
    if quotes:
        quotes_section = "\n## Notable Quotes\n\n"
        for q in quotes:
            quotes_section += f"> {q}\n\n"

    excerpt = raw_text[:1200].strip()
    excerpt_section = f"\n## Excerpt\n\n{excerpt}\n...\n" if excerpt else ""

    is_url = source.startswith("http")
    sources_section = f"\n## Sources\n\n[1] {'Original article' if is_url else 'Source file'}: {source}\n"

    return "\n".join([
        frontmatter,
        f"\n# {title}\n",
        summary_section,
        argument_section,
        themes_section,
        quotes_section,
        excerpt_section,
        sources_section,
    ])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def process_story(
    source: str,
    output_dir: str,
    subkind: str | None = None,
    author: str = "unknown",
    anthropic_key: str | None = None,
    no_llm: bool = False,
    content_type_override: str | None = None,
    verbose: bool = False,
) -> bool:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Fetch content
    print(f"• Fetching content from {source} ...")
    try:
        if is_local_path(source):
            raw_text, meta = fetch_local_file(source)
        else:
            raw_text, meta = fetch_url(source, subkind)
    except Exception as e:
        print(f"✗ Fetch failed: {e}")
        return False

    title = meta.get("title") or "Untitled"
    print(f"✓ Fetched '{title}' ({len(raw_text)} chars)")

    # LLM enrichment
    enrichment: dict = {}
    if not no_llm and raw_text:
        key = anthropic_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            print("⚠ No Anthropic API key; skipping LLM enrichment")
        else:
            try:
                enrichment = enrich_with_llm(raw_text, title, key)
                print(f"✓ Enrichment: {len(enrichment.get('themes', []))} themes, "
                      f"{len(enrichment.get('notable_quotes', []))} quotes")
            except Exception as e:
                print(f"✗ LLM enrichment failed: {e}")

    # Determine content type
    content_type = detect_content_type(source, enrichment, content_type_override)

    # Generate OKF doc
    slug = sanitize_filename(title)
    okf_doc = generate_okf_doc(title, source, author, meta, enrichment, raw_text, content_type)
    md_path = Path(output_dir) / f"{slug}.md"
    md_path.write_text(okf_doc, encoding="utf-8")
    print(f"✓ OKF document → {md_path}")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OKF story/article processor v2")
    parser.add_argument("source", help="URL or local file path")
    parser.add_argument("output_dir", help="Output directory")
    parser.add_argument("subkind", nargs="?", default=None,
                        help="Optional div ID or class to target for extraction")
    parser.add_argument("--author", default="unknown")
    parser.add_argument("--anthropic-key", default=None)
    parser.add_argument("--no-llm", action="store_true")
    parser.add_argument("--content-type", dest="content_type_override", default=None,
                        choices=["Blog Post", "Article", "Essay"])
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    success = process_story(
        source=args.source,
        output_dir=args.output_dir,
        subkind=args.subkind,
        author=args.author,
        anthropic_key=args.anthropic_key,
        no_llm=args.no_llm,
        content_type_override=args.content_type_override,
        verbose=args.verbose,
    )
    sys.exit(0 if success else 1)
