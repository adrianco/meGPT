"""
mcp_server_v2.py — OKF-native MCP server for megpt

Serves an OKF bundle (okf/<author>/) directly via the Model Context Protocol.
All responses include source citations so every answer points back to the
original resource.

Usage:
    python mcp_server_v2.py <author> [--okf-dir DIR]

Config for Claude Desktop (~/.claude/claude_desktop_config.json):
    {
      "mcpServers": {
        "megpt": {
          "command": "python",
          "args": ["/path/to/megpt/mcp_server_v2.py", "virtual_adrianco"]
        }
      }
    }
"""

import argparse
import os
import re
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# OKF document model
# ---------------------------------------------------------------------------

def parse_okf_doc(path: Path, root: Path) -> dict:
    """Parse an OKF markdown file into a structured dict."""
    text = path.read_text(encoding="utf-8", errors="replace")
    doc = {
        "id": str(path.relative_to(root)).replace(".md", ""),
        "path": str(path),
        "rel_path": str(path.relative_to(root)),
        "raw": text,
        "frontmatter": {},
        "body": "",
        "title": path.stem,
        "type": "Unknown",
        "resource": "",
        "tags": [],
        "timestamp": "",
        "description": "",
    }

    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if m:
        fm_text, doc["body"] = m.group(1), m.group(2).strip()
        # Parse frontmatter key-value pairs (handles multi-line lists)
        current_key = None
        for line in fm_text.splitlines():
            list_item = re.match(r"^  - (.+)$", line)
            kv = re.match(r"^(\w[\w-]*):\s*(.*)$", line)
            if list_item and current_key:
                # YAML list item: append to current key as list
                existing = doc["frontmatter"].get(current_key)
                if isinstance(existing, list):
                    existing.append(list_item.group(1).strip())
                else:
                    doc["frontmatter"][current_key] = [list_item.group(1).strip()]
            elif kv:
                current_key = kv.group(1)
                val = kv.group(2).strip().strip("\"'")
                if val:
                    doc["frontmatter"][current_key] = val
                # else: key with no value — next list items will populate it
    else:
        doc["body"] = text

    doc["title"] = doc["frontmatter"].get("title", path.stem).strip("\"'")
    doc["type"] = doc["frontmatter"].get("type", "Unknown")
    doc["resource"] = doc["frontmatter"].get("resource", "")
    doc["timestamp"] = doc["frontmatter"].get("timestamp", "")
    doc["description"] = doc["frontmatter"].get("description", "")
    tags_raw = doc["frontmatter"].get("tags", [])
    if isinstance(tags_raw, list):
        doc["tags"] = tags_raw
    elif isinstance(tags_raw, str):
        doc["tags"] = [t.strip() for t in tags_raw.split(",") if t.strip()]

    return doc


class OKFIndex:
    """In-memory index over all OKF documents in a bundle."""

    def __init__(self, okf_dir: Path) -> None:
        self.okf_dir = okf_dir
        self.docs: list[dict] = []
        self._load()

    def _load(self) -> None:
        """Load all OKF markdown files (excluding index.md, log.md, topics/)."""
        for md in sorted(self.okf_dir.rglob("*.md")):
            if md.name in ("index.md", "log.md"):
                continue
            if "topics" in md.parts:
                continue
            try:
                self.docs.append(parse_okf_doc(md, self.okf_dir))
            except Exception:
                pass

        # Also load topic pages
        topics_dir = self.okf_dir / "topics"
        if topics_dir.exists():
            for md in sorted(topics_dir.glob("*.md")):
                try:
                    doc = parse_okf_doc(md, self.okf_dir)
                    doc["type"] = "Topic"
                    self.docs.append(doc)
                except Exception:
                    pass

    def search(self, query: str, limit: int = 10, kind: str | None = None) -> list[dict]:
        """Keyword search over title, tags, body, and description."""
        terms = [t.lower() for t in query.split() if t]
        results = []

        for doc in self.docs:
            if kind and kind.lower() not in doc.get("type", "").lower():
                # Also allow subfolder-based filtering
                subfolder = Path(doc["rel_path"]).parts[0] if doc["rel_path"] else ""
                if kind.lower() not in subfolder.lower():
                    continue

            haystack = " ".join([
                doc["title"].lower(),
                doc["description"].lower(),
                " ".join(doc["tags"]).lower(),
                doc["body"][:2000].lower(),
            ])

            score = sum(haystack.count(t) for t in terms)
            if score > 0:
                results.append((score, doc))

        results.sort(key=lambda x: -x[0])
        return [d for _, d in results[:limit]]

    def get_by_type(self, doc_type: str) -> list[dict]:
        """Return all docs of a given type."""
        dt = doc_type.lower()
        return [d for d in self.docs if dt in d.get("type", "").lower()]

    def get_by_id(self, doc_id: str) -> dict | None:
        """Return doc by its path-based ID."""
        for doc in self.docs:
            if doc["id"] == doc_id or doc["rel_path"] == doc_id:
                return doc
        return None

    def stats(self) -> dict:
        from collections import Counter
        types = Counter(d["type"] for d in self.docs)
        return {
            "total": len(self.docs),
            "by_type": dict(types.most_common()),
            "okf_dir": str(self.okf_dir),
        }


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _format_doc_summary(doc: dict, include_body: bool = False) -> str:
    """Format a doc as a concise summary with citation."""
    lines = [
        f"**{doc['title']}**",
        f"Type: {doc['type']} | ID: `{doc['id']}`",
    ]
    if doc["timestamp"]:
        lines.append(f"Date: {doc['timestamp']}")
    if doc["tags"]:
        lines.append(f"Tags: {', '.join(doc['tags'][:8])}")
    if doc["description"]:
        lines.append(f"Description: {doc['description'][:200]}")
    if doc["resource"]:
        lines.append(f"Source: {doc['resource']}")
    if include_body and doc["body"]:
        lines.append(f"\n---\n{doc['body'][:3000]}")
    return "\n".join(lines)


def _format_results(docs: list[dict], query: str, include_body: bool = False) -> str:
    if not docs:
        return f"No documents found for query: '{query}'"
    parts = [f"Found {len(docs)} result(s) for '{query}':\n"]
    for i, doc in enumerate(docs, 1):
        parts.append(f"### [{i}] {_format_doc_summary(doc, include_body=include_body)}")
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

def create_server(okf_dir: Path, author: str) -> FastMCP:
    mcp = FastMCP(f"megpt-{author}")
    index = OKFIndex(okf_dir)

    print(f"Loaded {len(index.docs)} OKF documents from {okf_dir}", file=sys.stderr)

    @mcp.tool()
    def search(query: str, limit: int = 8) -> str:
        """
        Search across all knowledge documents. Returns ranked results with
        citations (source URLs) for every match.

        Args:
            query: Keywords or phrase to search for
            limit: Maximum number of results (default 8)
        """
        docs = index.search(query, limit=limit)
        return _format_results(docs, query)

    @mcp.tool()
    def search_by_type(query: str, content_type: str, limit: int = 8) -> str:
        """
        Search within a specific content type (Podcast, Talk, Post, Book, Topic).

        Args:
            query: Keywords to search for
            content_type: One of: Podcast, Talk, Post, Book, Topic
            limit: Maximum results
        """
        docs = index.search(query, limit=limit, kind=content_type)
        return _format_results(docs, f"{query} [{content_type}]")

    @mcp.tool()
    def get_document(doc_id: str) -> str:
        """
        Get the full content of an OKF document by its ID (path without .md).
        Use this to read the complete transcript, Q&A, or key positions.

        Args:
            doc_id: Document ID from search results (e.g. 'podcasts/schedulers-with-adrian-cockcroft')
        """
        doc = index.get_by_id(doc_id)
        if not doc:
            return f"Document not found: {doc_id}"
        return _format_doc_summary(doc, include_body=True)

    @mcp.tool()
    def list_by_type(content_type: str) -> str:
        """
        List all documents of a given type with their IDs and source URLs.

        Args:
            content_type: One of: Podcast Interview, Talk, Post, Book, Topic
        """
        docs = index.get_by_type(content_type)
        if not docs:
            return f"No documents of type '{content_type}' found."
        lines = [f"**{content_type}** — {len(docs)} document(s):\n"]
        for doc in sorted(docs, key=lambda d: d.get("timestamp", "") or ""):
            ts = f" ({doc['timestamp']})" if doc["timestamp"] else ""
            src = f" — {doc['resource']}" if doc["resource"] else ""
            lines.append(f"- `{doc['id']}`{ts}: {doc['title']}{src}")
        return "\n".join(lines)

    @mcp.tool()
    def get_bundle_stats() -> str:
        """Return statistics about the knowledge bundle (document counts by type)."""
        stats = index.stats()
        lines = [
            f"**{author} Knowledge Bundle**",
            f"Total documents: {stats['total']}",
            "",
            "**By type:**",
        ]
        for t, count in stats["by_type"].items():
            lines.append(f"  - {t}: {count}")
        return "\n".join(lines)

    @mcp.tool()
    def get_topics() -> str:
        """List all synthesized topic pages (cross-linked knowledge synthesis)."""
        docs = index.get_by_type("Topic")
        if not docs:
            return "No topic pages found. Run okf_synthesizer.py to generate them."
        lines = [f"**{len(docs)} topic pages:**\n"]
        for doc in docs:
            tags_str = ", ".join(doc["tags"][:5]) if doc["tags"] else ""
            lines.append(f"- `{doc['id']}`: **{doc['title']}**  \n  {doc['description']}  \n  Tags: {tags_str}")
        return "\n".join(lines)

    @mcp.resource("okf://index")
    def bundle_index() -> str:
        """The OKF bundle root index."""
        idx_path = okf_dir / "index.md"
        if idx_path.exists():
            return idx_path.read_text(encoding="utf-8")
        return f"Bundle: {author}\nDocuments: {len(index.docs)}"

    @mcp.resource("okf://log")
    def bundle_log() -> str:
        """The OKF bundle change log."""
        log_path = okf_dir / "log.md"
        if log_path.exists():
            return log_path.read_text(encoding="utf-8")
        return "No log file found."

    @mcp.prompt()
    def answer_question(question: str) -> str:
        """
        Answer a question about the author using the knowledge bundle.
        Every answer must cite specific source documents.
        """
        docs = index.search(question, limit=5)
        if not docs:
            return f"Search the knowledge bundle for: {question}\nProvide citations in your answer."
        context = "\n\n".join(_format_doc_summary(d, include_body=True) for d in docs)
        return (
            f"Using the following knowledge from the OKF bundle, answer this question: {question}\n\n"
            f"IMPORTANT: Your answer must cite specific sources (titles and URLs).\n\n"
            f"RELEVANT DOCUMENTS:\n{context}"
        )

    @mcp.prompt()
    def summarize_topic(topic: str) -> str:
        """Create a synthesis of the author's views on a given topic."""
        docs = index.search(topic, limit=8)
        context = "\n\n".join(_format_doc_summary(d, include_body=True) for d in docs[:5])
        return (
            f"Synthesize {author}'s views on '{topic}' across their body of work.\n\n"
            f"Structure your response as:\n"
            f"1. Overview (2-3 sentences)\n"
            f"2. Evolution over time (how their thinking changed)\n"
            f"3. Key positions (bullet list with quotes)\n"
            f"4. Sources consulted (list with URLs)\n\n"
            f"RELEVANT DOCUMENTS:\n{context}"
        )

    return mcp


def main() -> None:
    parser = argparse.ArgumentParser(description="OKF MCP server v2")
    parser.add_argument("author", help="Author name (matches okf/<author>/ directory)")
    parser.add_argument("--okf-dir", default=None,
                        help="Override OKF directory (default: okf/<author>/)")
    parser.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    parser.add_argument("--port", type=int, default=8080)
    opts = parser.parse_args()

    okf_dir = Path(opts.okf_dir) if opts.okf_dir else Path(f"okf/{opts.author}")
    if not okf_dir.exists():
        print(f"Error: OKF directory not found: {okf_dir}", file=sys.stderr)
        sys.exit(1)

    mcp = create_server(okf_dir, opts.author)

    if opts.transport == "http":
        import uvicorn
        uvicorn.run(mcp.get_app(), host="0.0.0.0", port=opts.port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
