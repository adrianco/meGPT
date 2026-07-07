"""
podcast_processor_v2.py — Modern OKF podcast processor

Pipeline:
  1. Resolve audio URL (direct HTTP scrape or RSS)
  2. Download audio (requests/yt-dlp)
  3. Transcribe with Whisper (local) or AssemblyAI (cloud, better diarization)
  4. Diarize speakers (pyannote or AssemblyAI speaker labels)
  5. LLM pass: identify host vs. guest, extract Q&A pairs, key positions
  6. Emit OKF-compliant markdown bundle document

Usage:
    python podcast_processor_v2.py <url> <output_dir> [options]

Options:
    --author NAME       Author name to identify in transcript (default: inferred)
    --transcriber       whisper | assemblyai  (default: whisper)
    --whisper-model     tiny | base | small | medium | large  (default: base)
    --assemblyai-key    AssemblyAI API key (or set ASSEMBLYAI_API_KEY env var)
    --anthropic-key     Anthropic API key (or set ANTHROPIC_API_KEY env var)
    --llm-model         Claude model for enrichment (default: claude-haiku-4-5-20251001)
    --no-llm            Skip LLM enrichment, output raw transcript only
    --verbose           Verbose logging
"""

import argparse
import json
import logging
import os
import re
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Audio URL resolution
# ---------------------------------------------------------------------------

def resolve_audio_url(page_url: str) -> tuple[str | None, dict]:
    """
    Try to find a direct audio URL from a podcast episode page.
    Returns (audio_url, metadata_dict).
    Tries in order: JSON-LD, <audio> tags, MP3 patterns in HTML, RSS link.
    """
    headers = {"User-Agent": "Mozilla/5.0 (compatible; meGPT/2.0; podcast processor)"}
    meta = {"title": None, "description": None, "published": None, "page_url": page_url}

    try:
        resp = requests.get(page_url, headers=headers, timeout=15)
        resp.raise_for_status()
        html = resp.text
        soup = BeautifulSoup(html, "html.parser")

        # Title
        og_title = soup.find("meta", property="og:title")
        meta["title"] = (og_title["content"] if og_title else None) or (
            soup.title.string.strip() if soup.title else None
        )

        # Description
        og_desc = soup.find("meta", property="og:description") or soup.find(
            "meta", attrs={"name": "description"}
        )
        meta["description"] = og_desc["content"] if og_desc else None

        # 1. JSON-LD
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                for item in (data if isinstance(data, list) else [data]):
                    url = item.get("contentUrl") or item.get("url", "")
                    if url and re.search(r"\.(mp3|m4a|ogg|wav|aac)", url, re.I):
                        logger.info("Audio URL from JSON-LD: %s", url)
                        return url, meta
            except (json.JSONDecodeError, TypeError):
                pass

        # 2. <audio> tags
        for audio in soup.find_all("audio"):
            src = audio.get("src") or (audio.find("source") or {}).get("src")
            if src:
                return urljoin(page_url, src), meta

        # 3. MP3/M4A patterns in raw HTML
        patterns = [
            r'(https?://[^\s"\'<>]+\.(?:mp3|m4a|ogg))(?:[^\w]|$)',
            r'audioUrl\s*[=:]\s*["\']([^"\']+)["\']',
            r'"audio_url"\s*:\s*"([^"]+)"',
        ]
        for pattern in patterns:
            m = re.search(pattern, html, re.I)
            if m:
                url = m.group(1)
                logger.info("Audio URL from pattern: %s", url)
                return url, meta

        # 4. RSS/feed link
        rss_link = soup.find("link", type="application/rss+xml")
        if rss_link and rss_link.get("href"):
            rss_audio = _first_audio_from_rss(rss_link["href"], page_url)
            if rss_audio:
                return rss_audio, meta

        # 5. Simplecast player embed → yt-dlp
        sc_matches = re.findall(
            r'player\.simplecast\.com/([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})',
            html,
        )
        if sc_matches:
            ep_uuid = sc_matches[0]
            player_url = f"https://player.simplecast.com/{ep_uuid}"
            try:
                import yt_dlp

                with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
                    info = ydl.extract_info(player_url, download=False)
                    # Simplecast returns direct URL in info["url"] with no formats list
                    if info.get("url"):
                        return info["url"], meta
                    formats = info.get("formats", [])
                    if formats:
                        return formats[-1]["url"], meta
            except Exception as exc:
                logger.debug("Simplecast yt-dlp failed for %s: %s", ep_uuid, exc)

        # 6. Libsyn embed → find enclosure in page's RSS feed with better matching
        libsyn_eps = re.findall(r'libsyn\.com/embed/episode/id/(\d+)', html)
        if libsyn_eps and not rss_link:
            # Try fetching Libsyn RSS from show homepage
            libsyn_feed_links = re.findall(r'(https?://feeds\.libsyn\.com/\d+/rss)', html)
            if libsyn_feed_links:
                rss_audio = _first_audio_from_rss(libsyn_feed_links[0], page_url)
                if rss_audio:
                    return rss_audio, meta

        # 7. SoundCloud iframe embed → yt-dlp
        sc_embeds = re.findall(
            r'soundcloud\.com/player/\?url=(https?://api\.soundcloud\.com/tracks/\d+)',
            html,
        )
        if sc_embeds:
            track_api_url = requests.utils.unquote(sc_embeds[0])
            try:
                import yt_dlp

                with yt_dlp.YoutubeDL({"format": "bestaudio", "quiet": True}) as ydl:
                    info = ydl.extract_info(track_api_url, download=False)
                    formats = info.get("formats", [])
                    if formats:
                        return formats[-1]["url"], meta
            except Exception as exc:
                logger.debug("SoundCloud yt-dlp failed: %s", exc)

    except requests.RequestException as e:
        logger.error("Failed to fetch page %s: %s", page_url, e)

    return None, meta


def _first_audio_from_rss(rss_url: str, episode_page_url: str) -> str | None:
    """Pull enclosure URL from an RSS feed matching the episode page URL."""
    import feedparser
    from urllib.parse import urlparse

    feed = feedparser.parse(rss_url)

    def _page_slug(url: str) -> str:
        """Extract last non-empty path segment for loose matching."""
        parts = [p for p in urlparse(url).path.strip("/").split("/") if p]
        return parts[-1] if parts else ""

    ep_slug = _page_slug(episode_page_url)

    def _first_audio_enc(entry) -> str | None:
        for enc in getattr(entry, "enclosures", []):
            href = enc.get("href") or enc.get("url", "")
            if href and (enc.get("type", "").startswith("audio") or
                         re.search(r"\.(mp3|m4a|ogg|aac)", href, re.I)):
                return href
        return None

    # Pass 1: exact URL match
    for entry in feed.entries:
        if episode_page_url and episode_page_url in getattr(entry, "link", ""):
            audio = _first_audio_enc(entry)
            if audio:
                return audio

    # Pass 2: slug-based match (handles URL scheme/www differences)
    if ep_slug:
        for entry in feed.entries:
            if ep_slug in getattr(entry, "link", ""):
                audio = _first_audio_enc(entry)
                if audio:
                    return audio

    return None


# ---------------------------------------------------------------------------
# Audio download
# ---------------------------------------------------------------------------

def download_audio(audio_url: str, output_path: str) -> bool:
    """Download audio to output_path. Uses yt-dlp for YouTube, requests otherwise."""
    if "youtube.com" in audio_url or "youtu.be" in audio_url:
        return _download_via_ytdlp(audio_url, output_path)
    return _download_via_requests(audio_url, output_path)


def _download_via_requests(url: str, output_path: str) -> bool:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; meGPT/2.0)"}
    try:
        with requests.get(url, headers=headers, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(output_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 20):
                    f.write(chunk)
        logger.info("Downloaded %s → %s", url, output_path)
        return True
    except requests.RequestException as e:
        logger.error("Download failed: %s", e)
        return False


def _download_via_ytdlp(url: str, output_path: str) -> bool:
    try:
        import yt_dlp
    except ImportError:
        logger.error("yt-dlp not installed; run: pip install yt-dlp")
        return False

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
        }],
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except yt_dlp.utils.DownloadError as e:
        logger.error("yt-dlp failed: %s", e)
        return False


# ---------------------------------------------------------------------------
# Transcription
# ---------------------------------------------------------------------------

def transcribe_whisper(audio_path: str, model_size: str = "base") -> dict:
    """
    Transcribe audio with local Whisper. Returns dict with 'text' and 'segments'.
    Each segment: {start, end, text}
    """
    import whisper
    logger.info("Loading Whisper model: %s", model_size)
    model = whisper.load_model(model_size)
    logger.info("Transcribing %s ...", audio_path)
    result = model.transcribe(audio_path, verbose=False)
    return {
        "text": result["text"],
        "segments": [
            {"start": s["start"], "end": s["end"], "text": s["text"].strip()}
            for s in result["segments"]
        ],
    }


def transcribe_assemblyai(audio_path: str, api_key: str) -> dict:
    """
    Transcribe with AssemblyAI speaker diarization. Returns dict with 'text',
    'segments', and 'utterances' (speaker-labeled).
    """
    import assemblyai as aai

    aai.settings.api_key = api_key
    config = aai.TranscriptionConfig(speaker_labels=True)
    transcriber = aai.Transcriber()

    logger.info("Uploading to AssemblyAI and transcribing...")
    transcript = transcriber.transcribe(audio_path, config=config)

    if transcript.status == aai.TranscriptStatus.error:
        raise RuntimeError(f"AssemblyAI error: {transcript.error}")

    utterances = [
        {"speaker": u.speaker, "start": u.start / 1000, "end": u.end / 1000, "text": u.text}
        for u in (transcript.utterances or [])
    ]

    return {
        "text": transcript.text,
        "segments": [
            {"start": u["start"], "end": u["end"], "text": u["text"]}
            for u in utterances
        ],
        "utterances": utterances,
    }


# ---------------------------------------------------------------------------
# Speaker identification and Q&A extraction (LLM)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are processing a podcast interview transcript to extract structured knowledge.
Your output must be valid JSON with exactly these keys:
{
  "host_speaker": "A" or "B" (or null if unknown),
  "guest_speaker": "A" or "B" (or null if unknown),
  "guest_name": "string or null",
  "host_name": "string or null",
  "topics": ["list of main topics discussed"],
  "key_positions": [
    {"topic": "string", "position": "Adrian's stated view/position as a direct quote or close paraphrase"}
  ],
  "qa_pairs": [
    {"q": "question text", "a": "answer text (guest's words)"}
  ],
  "summary": "2-3 sentence summary of the episode from the guest's perspective"
}

Guidelines:
- key_positions: extract statements of opinion, recommendation, or insight from the guest
- qa_pairs: select the 5-10 most substantive exchanges (skip small talk, intros, outros)
- If no speaker labels are available, still extract topics, positions, qa_pairs from the raw text
- Always respond with valid JSON only, no other text"""


def enrich_with_llm(
    transcript_data: dict,
    author_name: str,
    episode_meta: dict,
    api_key: str,
    model: str = "claude-haiku-4-5-20251001",
) -> dict:
    """
    Use Claude to identify speakers, extract Q&A pairs and key positions.
    Returns the parsed JSON enrichment dict.
    """
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    # Build transcript text for the prompt
    if "utterances" in transcript_data and transcript_data["utterances"]:
        # Speaker-labeled (from AssemblyAI)
        transcript_text = "\n".join(
            f"SPEAKER_{u['speaker']} [{u['start']:.0f}s]: {u['text']}"
            for u in transcript_data["utterances"][:200]  # cap at 200 turns
        )
        has_speakers = True
    else:
        # Raw transcript (from Whisper)
        transcript_text = transcript_data["text"][:8000]
        has_speakers = False

    user_prompt = f"""Episode: {episode_meta.get('title', 'Unknown')}
Author/Guest: {author_name}
Has speaker labels: {has_speakers}

TRANSCRIPT:
{transcript_text}

Extract the structured knowledge as JSON per the system prompt."""

    logger.info("Sending to Claude for enrichment (model=%s)...", model)
    msg = client.messages.create(
        model=model,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    response_text = msg.content[0].text.strip()
    # Strip markdown code fences if present
    response_text = re.sub(r"^```(?:json)?\n?", "", response_text)
    response_text = re.sub(r"\n?```$", "", response_text)

    return json.loads(response_text)


# ---------------------------------------------------------------------------
# OKF document generation
# ---------------------------------------------------------------------------

def sanitize_filename(name: str) -> str:
    clean = re.sub(r"[^\w\s-]", "", name)
    clean = re.sub(r"[\s_]+", "-", clean).strip("-")
    return clean[:120].lower()


def generate_okf_stub(episode_meta: dict, source_url: str) -> str:
    """
    Generate a minimal OKF doc from page metadata when audio is not available.
    Useful for indexing episodes whose audio player requires JS or authentication.
    """
    title = episode_meta.get("title") or "Unknown Episode"
    description = episode_meta.get("description") or ""
    published = episode_meta.get("published") or ""

    ts_line = f'timestamp: "{published}"\n' if published else ""
    safe_title = title.replace('"', "'")
    safe_desc = description[:200].replace('"', "'")
    frontmatter = (
        "---\n"
        "type: Podcast Interview\n"
        f'title: "{safe_title}"\n'
        f'description: "{safe_desc}"\n'
        f'resource: "{source_url}"\n'
        f"{ts_line}"
        "---\n"
    )

    body = (
        f"\n# {title}\n\n"
        f"{description}\n\n"
        "_Transcript not available — audio player could not be resolved automatically. "
        "Visit the source link to listen._\n\n"
        f"## Sources\n[1] Episode page: {source_url}\n"
    )

    return frontmatter + body


def generate_okf_document(
    episode_meta: dict,
    enrichment: dict,
    transcript_data: dict,
    source_url: str,
    audio_url: str | None = None,
) -> str:
    """
    Emit a single OKF-compliant markdown document for the podcast episode.
    """
    title = episode_meta.get("title") or enrichment.get("guest_name") or "Unknown Episode"
    guest = enrichment.get("guest_name") or "Unknown"
    tags = enrichment.get("topics", [])
    summary = enrichment.get("summary") or episode_meta.get("description") or ""
    published = episode_meta.get("published") or ""

    # Frontmatter
    tags_yaml = "\n".join(f"  - {t}" for t in tags)
    frontmatter = f"""---
type: Podcast Interview
title: "{title}"
description: "{summary[:200].replace('"', "'")}"
resource: "{source_url}"
tags:
{tags_yaml}
{f'timestamp: "{published}"' if published else ''}
---"""

    # Key positions block
    positions_md = ""
    if enrichment.get("key_positions"):
        positions_md = "\n## Key Positions\n"
        for pos in enrichment["key_positions"]:
            positions_md += f"\n**{pos['topic']}:** {pos['position']}\n"

    # Q&A block
    qa_md = ""
    if enrichment.get("qa_pairs"):
        qa_md = "\n## Q&A Excerpts\n"
        for pair in enrichment["qa_pairs"]:
            qa_md += f"\n**Q:** {pair['q']}\n\n**A:** {pair['a']}\n"

    # Topics block
    topics_md = ""
    if tags:
        topics_md = "\n## Topics\n" + ", ".join(tags) + "\n"

    # Raw transcript block — included when no LLM enrichment ran
    transcript_md = ""
    raw_text = (transcript_data or {}).get("text", "")
    if raw_text and not enrichment.get("qa_pairs") and not enrichment.get("key_positions"):
        # Cap at ~6000 chars; Whisper output is one long string (no speaker labels)
        excerpt = raw_text[:6000]
        if len(raw_text) > 6000:
            excerpt += "\n\n_[Transcript truncated — full text in _transcript.json]_"
        transcript_md = f"\n## Transcript\n\n{excerpt}\n"

    # Sources
    sources = [f"[1] Episode page: {source_url}"]
    if audio_url:
        sources.append(f"[2] Audio: {audio_url}")
    sources_md = "\n## Sources\n" + "\n".join(sources) + "\n"

    return "\n".join([
        frontmatter,
        f"\n# {title}\n",
        f"{summary}\n",
        topics_md,
        positions_md,
        qa_md,
        transcript_md,
        sources_md,
    ])


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def process_podcast(
    url: str,
    output_dir: str,
    author: str = "unknown",
    transcriber: str = "whisper",
    whisper_model: str = "base",
    assemblyai_key: str | None = None,
    anthropic_key: str | None = None,
    llm_model: str = "claude-haiku-4-5-20251001",
    no_llm: bool = False,
    verbose: bool = False,
) -> bool:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.WARNING,
                        format="%(levelname)s: %(message)s")

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 1. Resolve audio URL
    print(f"• Resolving audio URL from {url} ...")
    audio_url, meta = resolve_audio_url(url)
    if not audio_url:
        print("✗ Could not find audio URL on page")
        # Still proceed — we can note it manually
    else:
        print(f"✓ Audio URL: {audio_url}")

    # 2. Download audio
    audio_path = None
    if audio_url:
        slug = sanitize_filename(meta.get("title") or "episode")
        audio_path = str(Path(output_dir) / f"{slug}.mp3")
        print(f"• Downloading audio → {audio_path} ...")
        if not download_audio(audio_url, audio_path):
            print("✗ Download failed; proceeding without audio")
            audio_path = None
        else:
            print(f"✓ Downloaded ({Path(audio_path).stat().st_size // 1024}KB)")

    if not audio_path:
        # Save metadata stub
        stub = {**meta, "source_url": url, "audio_url": audio_url, "error": "no_audio"}
        # Use URL path as slug fallback to avoid collisions when title is None
        title_slug = meta.get("title") or ""
        if not title_slug:
            from urllib.parse import urlparse
            url_parts = [p for p in urlparse(url).path.strip("/").split("/") if p]
            title_slug = url_parts[-1] if url_parts else "episode"
        slug = sanitize_filename(title_slug)
        json_path = Path(output_dir) / f"{slug}.json"
        json_path.write_text(json.dumps(stub, indent=2))
        print(f"• Saved metadata stub → {json_path}")
        # Generate a minimal OKF doc from page metadata so the episode is indexed
        print("• Generating stub OKF doc (no transcript) ...")
        okf_doc = generate_okf_stub(meta, url)
        okf_path = Path(output_dir) / f"{slug}.md"
        okf_path.write_text(okf_doc)
        print(f"✓ Stub OKF document → {okf_path}")
        return True

    # 3. Transcribe
    print(f"• Transcribing ({transcriber}) ...")
    transcript_data: dict = {}
    try:
        if transcriber == "assemblyai" and assemblyai_key:
            transcript_data = transcribe_assemblyai(audio_path, assemblyai_key)
        else:
            transcript_data = transcribe_whisper(audio_path, whisper_model)
        print(f"✓ Transcript: {len(transcript_data['text'])} chars, "
              f"{len(transcript_data['segments'])} segments")
    except Exception as e:
        print(f"✗ Transcription failed: {e}")
        return False

    # Save raw transcript
    slug = sanitize_filename(meta.get("title") or "episode")
    transcript_path = Path(output_dir) / f"{slug}_transcript.json"
    transcript_path.write_text(json.dumps(transcript_data, indent=2))
    print(f"✓ Transcript saved → {transcript_path}")

    # 4. LLM enrichment
    enrichment: dict = {}
    if not no_llm:
        key = anthropic_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            print("⚠ No Anthropic API key found; skipping LLM enrichment (use --anthropic-key)")
        else:
            try:
                enrichment = enrich_with_llm(transcript_data, author, meta, key, llm_model)
                print(f"✓ Extracted {len(enrichment.get('qa_pairs', []))} Q&A pairs, "
                      f"{len(enrichment.get('key_positions', []))} key positions")
                enrich_path = Path(output_dir) / f"{slug}_enrichment.json"
                enrich_path.write_text(json.dumps(enrichment, indent=2))
            except Exception as e:
                print(f"✗ LLM enrichment failed: {e}")

    # 5. Generate OKF document
    okf_doc = generate_okf_document(meta, enrichment, transcript_data, url, audio_url)
    okf_path = Path(output_dir) / f"{slug}.md"
    okf_path.write_text(okf_doc)
    print(f"✓ OKF document → {okf_path}")

    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OKF podcast processor v2")
    parser.add_argument("url", help="Podcast episode page URL")
    parser.add_argument("output_dir", help="Directory for output files")
    parser.add_argument("--author", default="unknown", help="Author/guest name")
    parser.add_argument("--transcriber", choices=["whisper", "assemblyai"], default="whisper")
    parser.add_argument("--whisper-model", default="base",
                        choices=["tiny", "base", "small", "medium", "large"])
    parser.add_argument("--assemblyai-key", default=None)
    parser.add_argument("--anthropic-key", default=None)
    parser.add_argument("--llm-model", default="claude-haiku-4-5-20251001")
    parser.add_argument("--no-llm", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    success = process_podcast(
        url=args.url,
        output_dir=args.output_dir,
        author=args.author,
        transcriber=args.transcriber,
        whisper_model=args.whisper_model,
        assemblyai_key=args.assemblyai_key,
        anthropic_key=args.anthropic_key,
        llm_model=args.llm_model,
        no_llm=args.no_llm,
        verbose=args.verbose,
    )
    sys.exit(0 if success else 1)
