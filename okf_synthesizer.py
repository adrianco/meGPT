"""
okf_synthesizer.py — OKF topic page synthesizer

Reads all OKF documents in okf/<author>/ and uses Claude to:
1. Identify recurring themes and topic clusters across all documents
2. Write a synthesized topic page for each cluster (saved to okf/<author>/topics/)
3. Update okf/<author>/index.md to include topics

Topic pages are the "wiki layer" — they cross-reference source docs, synthesize the
author's evolving positions on a topic, and include citations.

Usage:
    python okf_synthesizer.py <author> [options]

Options:
    --anthropic-key KEY     API key (or set ANTHROPIC_API_KEY)
    --model MODEL           Claude model (default: claude-sonnet-4-6)
    --max-docs N            Max source docs to send in one call (default: 30)
    --topics-only           Skip clustering, regenerate all topic pages
    --topic SLUG            Regenerate a single topic page
    --verbose
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime


def read_okf_doc(path: Path) -> dict:
    """Parse an OKF markdown file into frontmatter + body."""
    text = path.read_text(encoding="utf-8")
    doc = {"path": str(path), "raw": text, "frontmatter": {}, "body": ""}

    # Extract YAML frontmatter
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if m:
        fm_text, body = m.group(1), m.group(2)
        doc["body"] = body.strip()
        for line in fm_text.splitlines():
            kv = re.match(r"^(\w[\w-]*):\s*(.+)$", line)
            if kv:
                doc["frontmatter"][kv.group(1)] = kv.group(2).strip().strip('"\'')
    else:
        doc["body"] = text

    doc["title"] = doc["frontmatter"].get("title", path.stem)
    doc["type"] = doc["frontmatter"].get("type", "Unknown")
    doc["resource"] = doc["frontmatter"].get("resource", "")
    doc["tags"] = doc["frontmatter"].get("tags", "")
    return doc


def collect_docs(okf_dir: Path, exclude_dirs: set = None) -> list[dict]:
    """Collect all OKF docs, excluding index/log/topics."""
    if exclude_dirs is None:
        exclude_dirs = {"topics"}
    docs = []
    for md in sorted(okf_dir.rglob("*.md")):
        if md.name in ("index.md", "log.md"):
            continue
        if any(part in exclude_dirs for part in md.parts):
            continue
        try:
            docs.append(read_okf_doc(md))
        except Exception:
            pass
    return docs


def build_doc_digest(doc: dict, max_body: int = 600, compact: bool = False) -> str:
    """Build a compact representation of a doc for the clustering prompt.

    compact=True emits title+type+tags only (no body excerpt), allowing all docs
    to be sent in a single clustering call without exceeding token budgets.
    """
    if compact:
        return f"[{doc['type']}] {doc['title']}  tags: {doc['tags']}"
    body_excerpt = doc["body"][:max_body].replace("\n", " ")
    return (
        f"[{doc['type']}] {doc['title']}\n"
        f"  tags: {doc['tags']}\n"
        f"  excerpt: {body_excerpt}"
    )


CLUSTER_SYSTEM = """You are analyzing an author's complete body of work to identify recurring themes.
Output a JSON array of topic clusters. Each cluster:
{
  "slug": "kebab-case-slug",
  "title": "Human-Readable Topic Title",
  "description": "One sentence describing this topic area",
  "doc_titles": ["exact titles of docs that belong to this cluster"]
}

Rules:
- Create 5-15 clusters, each covering a coherent theme
- Each doc can appear in multiple clusters
- Cluster titles should reflect the author's perspective/angle
- Slugs must be unique, lowercase, hyphen-separated
- Respond with JSON array only, no other text"""


TOPIC_PAGE_SYSTEM = """You are writing a knowledge synthesis page for an author's OKF knowledge bundle.
Write a rich, detailed topic page in markdown (no frontmatter — that's added separately).

The page must include:
## Overview
2-3 paragraphs synthesizing the author's overall perspective on this topic across all their work.

## Evolution
How the author's thinking on this topic has changed over time (if evident from sources).

## Key Positions
Bullet list of specific, quotable positions the author has expressed. Use close paraphrases or direct quotes where possible.

## Related Work
Which talks, posts, books, or interviews are most relevant to this topic? Brief annotation for each.

## Cross-references
Links to related topics in this bundle (use markdown link syntax to other topic slugs).

Write from the author's perspective but in third person. Be specific — cite specific episodes, dates, arguments. Avoid generic statements."""


def call_claude(client, model: str, system: str, user: str, max_tokens: int = 4096) -> str:
    msg = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text.strip()


def generate_topic_frontmatter(slug: str, title: str, description: str, related_docs: list[dict]) -> str:
    tags = set()
    for doc in related_docs:
        for tag in re.findall(r"\w[\w-]+", doc.get("tags", "")):
            tags.add(tag.lower())

    tag_lines = "\n".join(f"  - {t}" for t in sorted(tags)[:12])
    return (
        "---\n"
        f'type: Topic\n'
        f'title: "{title}"\n'
        f'description: "{description}"\n'
        f"tags:\n{tag_lines}\n"
        f'timestamp: "{datetime.now().strftime("%Y-%m-%d")}"\n'
        "---\n"
    )


def synthesize(author: str, opts: argparse.Namespace) -> None:
    import anthropic

    api_key = opts.anthropic_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set. Topic synthesis requires Claude.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    model = opts.model

    okf_dir = Path(f"okf/{author}")
    topics_dir = okf_dir / "topics"
    topics_dir.mkdir(exist_ok=True)

    print(f"Collecting OKF docs from {okf_dir} ...")
    docs = collect_docs(okf_dir)
    print(f"Found {len(docs)} source documents")

    if not docs:
        print("No documents found. Run build_okf.py first.")
        sys.exit(1)

    # === Step 1: Identify topic clusters ===
    clusters_cache = okf_dir / ".topic_clusters.json"

    if clusters_cache.exists() and not opts.topics_only:
        clusters = json.loads(clusters_cache.read_text())
        print(f"Loaded {len(clusters)} clusters from cache")
    else:
        print("Clustering documents into topics ...")

        # Send ALL docs with compact digests (title+type+tags only, no body excerpt).
        # This keeps the prompt within ~15K tokens even for 500+ doc bundles while
        # ensuring the clustering sees the full breadth of the author's work.
        digest = "\n".join(build_doc_digest(d, compact=True) for d in docs)

        user_prompt = (
            f"Author: {author}\n"
            f"Document count: {len(docs)}\n\n"
            f"DOCUMENTS:\n{digest}"
        )

        raw = call_claude(client, model, CLUSTER_SYSTEM, user_prompt, max_tokens=2048)
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        clusters = json.loads(raw)
        clusters_cache.write_text(json.dumps(clusters, indent=2))
        print(f"Identified {len(clusters)} topic clusters")

    # Filter to single topic if requested
    if opts.topic:
        clusters = [c for c in clusters if c["slug"] == opts.topic]
        if not clusters:
            print(f"Topic '{opts.topic}' not found in clusters")
            sys.exit(1)

    # Build a title→doc lookup
    doc_by_title = {d["title"]: d for d in docs}

    # === Step 2: Generate topic pages ===
    all_slugs = [c["slug"] for c in clusters]

    for i, cluster in enumerate(clusters, 1):
        slug = cluster["slug"]
        title = cluster["title"]
        description = cluster.get("description", "")
        doc_titles = cluster.get("doc_titles", [])

        print(f"[{i}/{len(clusters)}] Writing topic: {title} ({len(doc_titles)} source docs)")

        # Gather relevant docs
        related_docs = [doc_by_title[t] for t in doc_titles if t in doc_by_title]
        if not related_docs:
            # Fallback: use any docs whose tags overlap
            related_docs = [d for d in docs if slug.replace("-", " ") in d.get("tags", "").lower()][:10]

        if not related_docs:
            print(f"  ⚠ No source docs found for {slug}, skipping")
            continue

        # Build source context for Claude
        source_context = []
        for doc in related_docs[:15]:
            excerpt = doc["body"][:1500]
            source_context.append(
                f"### {doc['title']} ({doc['type']})\n"
                f"Resource: {doc['resource']}\n\n{excerpt}"
            )

        other_topics = [s for s in all_slugs if s != slug]
        cross_ref_note = "Other topics in this bundle: " + ", ".join(other_topics[:10])

        user_prompt = (
            f"Author: {author}\n"
            f"Topic: {title}\n"
            f"Description: {description}\n\n"
            f"{cross_ref_note}\n\n"
            f"SOURCE DOCUMENTS:\n" + "\n\n---\n\n".join(source_context)
        )

        body = call_claude(client, model, TOPIC_PAGE_SYSTEM, user_prompt, max_tokens=3000)

        fm = generate_topic_frontmatter(slug, title, description, related_docs)
        full_doc = fm + "\n" + f"# {title}\n\n" + body + "\n\n## Sources\n"
        for doc in related_docs:
            rel_path = Path(doc["path"]).relative_to(okf_dir)
            full_doc += f"- [{doc['title']}]({rel_path})\n"

        out_path = topics_dir / f"{slug}.md"
        out_path.write_text(full_doc)
        print(f"  ✓ Written: topics/{slug}.md")

    print(f"\nTopic synthesis complete: {len(clusters)} topics in {topics_dir}")
    print("Run: python build_okf.py to regenerate index.md with topics included")


def main() -> None:
    parser = argparse.ArgumentParser(description="OKF topic synthesizer")
    parser.add_argument("author", help="Author name (matches okf/<author>/ directory)")
    parser.add_argument("--anthropic-key", default=None)
    parser.add_argument("--model", default="claude-sonnet-4-6")
    parser.add_argument("--max-docs", type=int, default=15,
                        help="Max source docs to include per topic page (default: 15)")
    parser.add_argument("--topics-only", action="store_true",
                        help="Skip re-clustering, just regenerate topic pages")
    parser.add_argument("--topic", default=None, help="Regenerate only this topic slug")
    parser.add_argument("--verbose", "-v", action="store_true")
    opts = parser.parse_args()

    synthesize(opts.author, opts)


if __name__ == "__main__":
    main()
