"""
book_processor_v2.py — OKF book/PDF processor

Pipeline:
  1. Download PDF from URL
  2. Parse page ranges (e.g. "1-4,8-22,83-")
  3. Extract text via PyMuPDF (falls back to PyPDF2)
  4. Enrich with Claude: summary, themes, quotes, audience
  5. Emit OKF-compliant .md document + raw .txt

Usage:
    python book_processor_v2.py <pdf_url> <output_dir> <page_ranges> [options]

Options:
    --author NAME         Author name (default: unknown)
    --title TITLE         Override title (default: inferred from filename)
    --anthropic-key KEY   Anthropic API key (or ANTHROPIC_API_KEY env var)
    --no-llm              Skip LLM enrichment
    --verbose             Verbose logging
"""

import argparse
import json
import logging
import os
import re
import sys
import tempfile
from pathlib import Path

import requests

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    try:
        from PyPDF2 import PdfReader
        HAS_PYMUPDF = False
    except ImportError:
        print("ERROR: Neither PyMuPDF nor PyPDF2 is installed. Run: pip install PyMuPDF")
        sys.exit(1)

logger = logging.getLogger(__name__)

ENRICH_SYSTEM = """You extract structured knowledge from book/PDF text excerpts.
Output valid JSON only with these keys:
{
  "summary": "3-5 sentence summary of the content",
  "themes": ["list", "of", "key", "themes"],
  "notable_quotes": ["verbatim quote 1", "verbatim quote 2"],
  "audience": "one sentence describing target audience",
  "title_guess": "inferred title if not obvious"
}
No markdown, no prose outside JSON."""


# ---------------------------------------------------------------------------
# Page range parsing
# ---------------------------------------------------------------------------

def parse_ranges(range_str: str, total_pages: int) -> list[int]:
    """Parse "1-4,8-22,83-" into zero-based page indices."""
    indices = []
    for part in range_str.split(","):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^(\d+)(?:-(\d*))?$", part)
        if not m:
            logger.warning("Skipping invalid range part: %s", part)
            continue
        start = int(m.group(1)) - 1  # zero-based
        end_str = m.group(2)
        if end_str is None:
            indices.append(start)
        elif end_str == "":
            indices.extend(range(start, total_pages))
        else:
            indices.extend(range(start, int(end_str)))  # "1-4" means pages 1,2,3,4
    return [i for i in sorted(set(indices)) if 0 <= i < total_pages]


# ---------------------------------------------------------------------------
# PDF download
# ---------------------------------------------------------------------------

def download_pdf(url: str, dest: str) -> bool:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; meGPT/2.0)"}
    try:
        with requests.get(url, headers=headers, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 20):
                    f.write(chunk)
        logger.info("Downloaded %s → %s (%dKB)", url, dest, Path(dest).stat().st_size // 1024)
        return True
    except requests.RequestException as e:
        logger.error("Download failed: %s", e)
        return False


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def extract_text_pymupdf(pdf_path: str, page_indices: list[int]) -> tuple[str, int]:
    doc = fitz.open(pdf_path)
    total = len(doc)
    chunks = []
    for i in page_indices:
        if 0 <= i < total:
            page = doc[i]
            text = page.get_text("text")
            if text.strip():
                chunks.append(text.strip())
    doc.close()
    return "\n\n".join(chunks), total


def extract_text_pypdf2(pdf_path: str, page_indices: list[int]) -> tuple[str, int]:
    reader = PdfReader(pdf_path)
    total = len(reader.pages)
    chunks = []
    for i in page_indices:
        if 0 <= i < total:
            try:
                text = reader.pages[i].extract_text() or ""
                if text.strip():
                    chunks.append(text.strip())
            except Exception as e:
                logger.warning("Page %d extraction error: %s", i + 1, e)
    return "\n\n".join(chunks), total


def extract_text(pdf_path: str, page_indices: list[int]) -> tuple[str, int]:
    if HAS_PYMUPDF:
        return extract_text_pymupdf(pdf_path, page_indices)
    return extract_text_pypdf2(pdf_path, page_indices)


# ---------------------------------------------------------------------------
# LLM enrichment
# ---------------------------------------------------------------------------

def enrich_with_llm(text: str, title_hint: str, api_key: str) -> dict:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    excerpt = text[:8000]
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=ENRICH_SYSTEM,
        messages=[{
            "role": "user",
            "content": f"Title hint: {title_hint}\n\nTEXT EXCERPT:\n{excerpt}"
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


def generate_okf_doc(
    title: str,
    source_url: str,
    author: str,
    enrichment: dict,
    raw_text: str,
    page_ranges: str,
) -> str:
    summary = enrichment.get("summary", "")
    themes = enrichment.get("themes", [])
    quotes = enrichment.get("notable_quotes", [])
    audience = enrichment.get("audience", "")

    tags_yaml = "\n".join(f"  - {t}" for t in themes) if themes else "  - book"

    frontmatter = f"""---
type: Book
title: "{title.replace('"', "'")}"
description: "{summary[:200].replace('"', "'")}"
resource: "{source_url}"
tags:
{tags_yaml}
---"""

    summary_section = f"\n## Summary\n\n{summary}\n" if summary else ""

    themes_section = ""
    if themes:
        themes_section = "\n## Key Themes\n\n" + "\n".join(f"- {t}" for t in themes) + "\n"

    quotes_section = ""
    if quotes:
        quotes_section = "\n## Notable Quotes\n\n"
        for q in quotes:
            quotes_section += f"> {q}\n\n"

    audience_section = f"\n## About\n\n**Target audience:** {audience}\n" if audience else ""

    excerpt = raw_text[:1500].strip() if raw_text else ""
    excerpt_section = f"\n## Text Excerpt (pages {page_ranges})\n\n```\n{excerpt}\n...\n```\n" if excerpt else ""

    sources_section = f"\n## Sources\n\n[1] PDF: {source_url}\n"

    return "\n".join([
        frontmatter,
        f"\n# {title}\n",
        summary_section,
        themes_section,
        quotes_section,
        audience_section,
        excerpt_section,
        sources_section,
    ])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def process_book(
    pdf_url: str,
    output_dir: str,
    page_ranges: str,
    author: str = "unknown",
    title_override: str | None = None,
    anthropic_key: str | None = None,
    no_llm: bool = False,
    verbose: bool = False,
) -> bool:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Derive title from URL filename
    url_filename = Path(pdf_url.split("?")[0]).stem
    title_hint = title_override or url_filename.replace("_", " ").replace("-", " ").title()
    slug = sanitize_filename(title_hint)

    # Download
    pdf_path = str(Path(output_dir) / f"{slug}.pdf")
    print(f"• Downloading {pdf_url} ...")
    if not download_pdf(pdf_url, pdf_path):
        return False
    print(f"✓ Downloaded ({Path(pdf_path).stat().st_size // 1024}KB)")

    # Extract text
    print(f"• Extracting text (pages: {page_ranges}, engine: {'PyMuPDF' if HAS_PYMUPDF else 'PyPDF2'}) ...")
    page_indices = parse_ranges(page_ranges, 10000)  # will be clamped inside extract_text
    # Re-parse with actual total
    _, total_pages = extract_text(pdf_path, [0])  # quick call to get total
    page_indices = parse_ranges(page_ranges, total_pages)
    raw_text, _ = extract_text(pdf_path, page_indices)

    if not raw_text:
        print("✗ No text extracted from PDF")
        raw_text = ""

    print(f"✓ Extracted {len(raw_text)} chars from {len(page_indices)} pages")

    # Save raw text
    txt_path = Path(output_dir) / f"{slug}.txt"
    txt_path.write_text(raw_text, encoding="utf-8")
    print(f"✓ Text saved → {txt_path}")

    # LLM enrichment
    enrichment: dict = {}
    if not no_llm and raw_text:
        key = anthropic_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            print("⚠ No Anthropic API key; skipping LLM enrichment")
        else:
            try:
                enrichment = enrich_with_llm(raw_text, title_hint, key)
                if enrichment.get("title_guess") and not title_override:
                    title_hint = enrichment["title_guess"]
                    slug = sanitize_filename(title_hint)
                print(f"✓ Enrichment: {len(enrichment.get('themes', []))} themes, "
                      f"{len(enrichment.get('notable_quotes', []))} quotes")
            except Exception as e:
                print(f"✗ LLM enrichment failed: {e}")

    # Generate OKF doc
    okf_doc = generate_okf_doc(title_hint, pdf_url, author, enrichment, raw_text, page_ranges)
    md_path = Path(output_dir) / f"{slug}.md"
    md_path.write_text(okf_doc, encoding="utf-8")
    print(f"✓ OKF document → {md_path}")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OKF book/PDF processor v2")
    parser.add_argument("pdf_url", help="URL of the PDF file")
    parser.add_argument("output_dir", help="Output directory")
    parser.add_argument("page_ranges", help='Page ranges, e.g. "1-4,8-22,83-"')
    parser.add_argument("--author", default="unknown")
    parser.add_argument("--title", dest="title_override", default=None)
    parser.add_argument("--anthropic-key", default=None)
    parser.add_argument("--no-llm", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    success = process_book(
        pdf_url=args.pdf_url,
        output_dir=args.output_dir,
        page_ranges=args.page_ranges,
        author=args.author,
        title_override=args.title_override,
        anthropic_key=args.anthropic_key,
        no_llm=args.no_llm,
        verbose=args.verbose,
    )
    sys.exit(0 if success else 1)
