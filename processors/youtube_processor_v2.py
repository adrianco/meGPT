"""
youtube_processor_v2.py — Modern OKF YouTube processor

Pipeline:
  1. Detect URL type: single video, playlist, or channel
  2. Extract video metadata + auto-captions via yt-dlp (no video download)
  3. Parse VTT/SRT captions into clean text transcript
  4. Optional LLM enrichment via Claude: key points, quotes, summary, tags
  5. Emit OKF-compliant markdown document per video
  6. Save .info.json alongside for downstream processing

Usage:
    python youtube_processor_v2.py <url> <output_dir> [options]

Options:
    --author NAME        Author name (used in metadata)
    --anthropic-key KEY  Anthropic API key (or set ANTHROPIC_API_KEY env var)
    --no-llm             Skip LLM enrichment, output raw transcript only
    --slides-url URL     URL of accompanying slides PDF (paired into OKF doc)
    --verbose            Verbose logging
"""

import argparse
import json
import logging
import os
import re
import sys
import tempfile
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Filename sanitization
# ---------------------------------------------------------------------------

def sanitize_filename(name: str) -> str:
    clean = re.sub(r"[^\w\s-]", "", name or "unknown")
    clean = re.sub(r"[\s_]+", "-", clean).strip("-")
    return clean[:120].lower() or "unknown"


# ---------------------------------------------------------------------------
# VTT / SRT caption parsing
# ---------------------------------------------------------------------------

def parse_vtt(text: str) -> str:
    """Parse WebVTT caption text into clean deduplicated transcript."""
    lines = text.splitlines()
    clean = []
    prev = ""
    for line in lines:
        # Skip WEBVTT header, cue identifiers, timing lines, and blank lines
        if (line.startswith("WEBVTT")
                or re.match(r"^\d\d:\d\d:\d\d\.\d{3}\s*-->\s*", line)
                or re.match(r"^\d+$", line.strip())
                or not line.strip()):
            continue
        # Strip inline timestamp tags like <00:00:01.000>
        line = re.sub(r"<\d\d:\d\d:\d\d\.\d{3}>", "", line)
        # Strip other VTT tags like <c>, </c>, <i>, etc.
        line = re.sub(r"<[^>]+>", "", line).strip()
        if not line:
            continue
        # Deduplicate adjacent identical lines (common in auto-captions)
        if line != prev:
            clean.append(line)
            prev = line
    return " ".join(clean)


def parse_srt(text: str) -> str:
    """Parse SRT caption text into clean transcript."""
    # Remove sequence numbers and timing lines
    text = re.sub(r"^\d+\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\d\d:\d\d:\d\d,\d{3}\s*-->\s*\d\d:\d\d:\d\d,\d{3}", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    # Deduplicate
    clean, prev = [], ""
    for line in lines:
        if line != prev:
            clean.append(line)
            prev = line
    return " ".join(clean)


def parse_caption_file(path: str) -> str:
    """Auto-detect VTT or SRT and parse to clean text."""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
        if path.endswith(".vtt"):
            return parse_vtt(text)
        elif path.endswith(".srt"):
            return parse_srt(text)
        else:
            # Try VTT first
            if "WEBVTT" in text[:20]:
                return parse_vtt(text)
            return parse_srt(text)
    except Exception as e:
        logger.error("Failed to parse caption file %s: %s", path, e)
        return ""


# ---------------------------------------------------------------------------
# yt-dlp metadata + caption extraction
# ---------------------------------------------------------------------------

def extract_video_info(video_url: str) -> tuple[dict, str]:
    """
    Use yt-dlp to extract video metadata and auto-captions.
    Returns (info_dict, transcript_text).
    No video is downloaded.
    """
    try:
        import yt_dlp
    except ImportError:
        logger.error("yt-dlp not installed; run: pip install yt-dlp")
        return {}, ""

    with tempfile.TemporaryDirectory() as tmpdir:
        ydl_opts = {
            "skip_download": True,
            "writeautomaticsub": True,
            "writesubtitles": True,
            "subtitlesformat": "vtt",
            "subtitleslangs": ["en", "en-US", "en-GB"],
            "outtmpl": os.path.join(tmpdir, "%(id)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
        }

        info = {}
        transcript = ""

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True) or {}
        except yt_dlp.utils.DownloadError as e:
            logger.warning("yt-dlp error for %s: %s", video_url, e)
            # Still try to get info without captions
            try:
                ydl_opts_meta = {**ydl_opts, "writeautomaticsub": False, "writesubtitles": False}
                with yt_dlp.YoutubeDL(ydl_opts_meta) as ydl:
                    info = ydl.extract_info(video_url, download=False) or {}
            except Exception:
                pass

        # Find downloaded caption file
        video_id = info.get("id", "")
        for fname in Path(tmpdir).iterdir():
            if fname.suffix in (".vtt", ".srt") and (not video_id or video_id in fname.name):
                transcript = parse_caption_file(str(fname))
                if transcript:
                    break

        return info, transcript


def flatten_playlist(url: str) -> list[str]:
    """Return list of individual video URLs from a playlist or channel URL."""
    try:
        import yt_dlp
    except ImportError:
        return []

    ydl_opts = {
        "extract_flat": True,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False) or {}
        entries = info.get("entries") or []
        urls = []
        for entry in entries:
            if not entry:
                continue
            vid_url = entry.get("url") or entry.get("webpage_url") or entry.get("id")
            if vid_url and not vid_url.startswith("http"):
                vid_url = f"https://www.youtube.com/watch?v={vid_url}"
            if vid_url:
                urls.append(vid_url)
        return urls
    except Exception as e:
        logger.error("Failed to flatten playlist/channel %s: %s", url, e)
        return []


def detect_url_type(url: str) -> str:
    """Return 'video', 'playlist', or 'channel'."""
    u = url.lower()
    if "/@" in u or "/c/" in u or "/channel/" in u or "/user/" in u:
        return "channel"
    if "playlist?list=" in u or ("list=" in u and "watch?" not in u):
        return "playlist"
    return "video"


# ---------------------------------------------------------------------------
# LLM enrichment
# ---------------------------------------------------------------------------

LLM_SYSTEM = """You process YouTube talk transcripts to extract structured knowledge for an author knowledge base.
Output valid JSON only, no other text:
{
  "summary": "2-3 sentence summary from the speaker's perspective",
  "key_points": ["list of 5-8 key insights or arguments made"],
  "notable_quotes": ["2-3 direct or near-direct quotes worth preserving"],
  "topics": ["list of topic tags, lowercase, hyphenated"],
  "audience": "who this talk is aimed at (optional)"
}"""


def enrich_with_llm(
    transcript: str,
    title: str,
    author: str,
    api_key: str,
    model: str = "claude-haiku-4-5-20251001",
) -> dict:
    """Send transcript to Claude for structured enrichment."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    # Use first 6000 chars of transcript — enough for a talk summary
    excerpt = transcript[:6000] if transcript else "(no transcript available)"

    prompt = f"""Talk title: {title}
Speaker: {author}

TRANSCRIPT EXCERPT:
{excerpt}

Extract the structured knowledge as JSON per the system prompt."""

    try:
        msg = client.messages.create(
            model=model,
            max_tokens=1500,
            system=LLM_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        return json.loads(raw)
    except Exception as e:
        logger.error("LLM enrichment failed: %s", e)
        return {}


# ---------------------------------------------------------------------------
# OKF document generation
# ---------------------------------------------------------------------------

def generate_okf_document(
    info: dict,
    enrichment: dict,
    transcript: str,
    video_url: str,
    author: str,
    slides_url: str | None = None,
) -> str:
    """Emit a single OKF-compliant markdown document for a YouTube talk."""

    title = info.get("title") or enrichment.get("title") or "Unknown Talk"
    description = enrichment.get("summary") or info.get("description") or ""
    if description and len(description) > 200:
        description = description[:197] + "..."

    upload_date = info.get("upload_date") or ""
    if upload_date and len(upload_date) == 8:
        # YYYYMMDD → YYYY-MM-DD
        upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"

    tags = enrichment.get("topics") or []
    channel = info.get("channel") or info.get("uploader") or ""

    # Build frontmatter
    tags_yaml = "\n".join(f"  - {t}" for t in tags) if tags else "  - talk"
    frontmatter_lines = [
        "---",
        'type: YouTube Talk',
        f'title: "{title.replace(chr(34), chr(39))}"',
        f'description: "{description.replace(chr(34), chr(39))}"',
        f'resource: "{video_url}"',
        "tags:",
        tags_yaml,
    ]
    if upload_date:
        frontmatter_lines.append(f'timestamp: "{upload_date}"')
    if author:
        frontmatter_lines.append(f'author: "{author}"')
    frontmatter_lines.append("---")
    frontmatter = "\n".join(frontmatter_lines)

    # Summary
    summary = enrichment.get("summary") or info.get("description") or ""

    # Key points
    key_points_md = ""
    if enrichment.get("key_points"):
        key_points_md = "\n## Key Points\n\n" + "\n".join(
            f"- {p}" for p in enrichment["key_points"]
        ) + "\n"

    # Notable quotes
    quotes_md = ""
    if enrichment.get("notable_quotes"):
        quotes_md = "\n## Notable Quotes\n\n" + "\n".join(
            f'> "{q}"' for q in enrichment["notable_quotes"]
        ) + "\n"

    # Transcript excerpt
    transcript_md = ""
    if transcript:
        excerpt = transcript[:2000]
        if len(transcript) > 2000:
            excerpt += " ..."
        transcript_md = f"\n## Transcript Excerpt\n\n{excerpt}\n"

    # Sources
    sources = [f"[1] Video: {video_url}"]
    if channel:
        sources.append(f"[2] Channel: {channel}")
    if slides_url:
        sources.append(f"[3] Slides: {slides_url}")
    sources_md = "\n## Sources\n\n" + "\n".join(sources) + "\n"

    parts = [
        frontmatter,
        f"\n# {title}\n",
        f"{summary}\n" if summary else "",
        key_points_md,
        quotes_md,
        transcript_md,
        sources_md,
    ]
    return "\n".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# Per-video processing
# ---------------------------------------------------------------------------

def process_video(
    video_url: str,
    output_dir: str,
    author: str,
    anthropic_key: str | None,
    no_llm: bool,
    slides_url: str | None,
    llm_model: str,
    index: int = 0,
) -> bool:
    """Process a single video URL → OKF .md + .info.json in output_dir."""
    print(f"  • [{index}] Fetching captions: {video_url}")

    info, transcript = extract_video_info(video_url)

    if not info:
        print(f"  ✗ Could not fetch info for {video_url}")
        return False

    title = info.get("title") or f"video-{info.get('id', index)}"
    print(f"  ✓ \"{title}\" — transcript: {len(transcript)} chars")

    # LLM enrichment
    enrichment: dict = {}
    if not no_llm:
        key = anthropic_key or os.environ.get("ANTHROPIC_API_KEY")
        if key and transcript:
            print(f"  • Enriching with Claude...")
            enrichment = enrich_with_llm(transcript, title, author, key, llm_model)
            if enrichment:
                print(f"  ✓ {len(enrichment.get('key_points', []))} key points, "
                      f"{len(enrichment.get('topics', []))} topics")
        elif not key:
            print("  ⚠ No ANTHROPIC_API_KEY — skipping enrichment")
        elif not transcript:
            print("  ⚠ No transcript available — skipping enrichment")

    # Generate OKF document
    okf_doc = generate_okf_document(info, enrichment, transcript, video_url, author, slides_url)

    slug = sanitize_filename(title)
    if index > 0:
        slug = f"{index:03d}-{slug}"

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    md_path = Path(output_dir) / f"{slug}.md"
    md_path.write_text(okf_doc, encoding="utf-8")
    print(f"  ✓ OKF doc → {md_path}")

    # Save info JSON
    info_out = {
        "video_url": video_url,
        "title": title,
        "author": author,
        "channel": info.get("channel") or info.get("uploader"),
        "upload_date": info.get("upload_date"),
        "duration": info.get("duration"),
        "transcript_chars": len(transcript),
        "slides_url": slides_url,
        "enrichment": enrichment,
        "okf_path": str(md_path),
    }
    json_path = Path(output_dir) / f"{slug}.info.json"
    json_path.write_text(json.dumps(info_out, indent=2), encoding="utf-8")

    return True


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def process_youtube(
    url: str,
    output_dir: str,
    author: str = "unknown",
    anthropic_key: str | None = None,
    no_llm: bool = False,
    slides_url: str | None = None,
    llm_model: str = "claude-haiku-4-5-20251001",
    verbose: bool = False,
) -> bool:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    url_type = detect_url_type(url)
    print(f"• Detected URL type: {url_type}")

    if url_type in ("playlist", "channel"):
        print(f"• Enumerating videos in {url_type}...")
        video_urls = flatten_playlist(url)
        if not video_urls:
            print("✗ No videos found")
            return False
        print(f"✓ Found {len(video_urls)} videos")

        success_count = 0
        for i, vurl in enumerate(video_urls, start=1):
            ok = process_video(vurl, output_dir, author, anthropic_key,
                               no_llm, slides_url, llm_model, index=i)
            if ok:
                success_count += 1

        print(f"\n✓ Processed {success_count}/{len(video_urls)} videos → {output_dir}")
        return success_count > 0

    else:
        # Single video
        return process_video(url, output_dir, author, anthropic_key,
                             no_llm, slides_url, llm_model, index=0)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OKF YouTube processor v2")
    parser.add_argument("url", help="YouTube video, playlist, or channel URL")
    parser.add_argument("output_dir", help="Directory for OKF output files")
    parser.add_argument("--author", default="unknown", help="Author/speaker name")
    parser.add_argument("--anthropic-key", default=None, help="Anthropic API key")
    parser.add_argument("--llm-model", default="claude-haiku-4-5-20251001")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM enrichment")
    parser.add_argument("--slides-url", default=None, help="URL of accompanying slides PDF")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    success = process_youtube(
        url=args.url,
        output_dir=args.output_dir,
        author=args.author,
        anthropic_key=args.anthropic_key,
        no_llm=args.no_llm,
        slides_url=args.slides_url,
        llm_model=args.llm_model,
        verbose=args.verbose,
    )
    sys.exit(0 if success else 1)
