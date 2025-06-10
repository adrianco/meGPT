"""
story_processor.py

This script downloads and processes web articles, extracting content based on a specified 
<div> ID (subkind) or saving the entire webpage as a PDF if no subkind is provided.

Key Features:
- If a subkind (div ID) is provided, extracts the text from that section and saves it as a UTF-8 encoded .txt file.
- If no subkind is specified, saves the entire webpage as a PDF, preserving text structure.
- Handles Unicode characters safely, preventing encoding errors.
- Ensures filenames are sanitized to avoid OS-related issues.
- Uses BeautifulSoup for HTML parsing and FPDF for PDF generation.
- Implements summary caching for text extraction to speed up reruns.
- Copies PDFs to mcp_resources directory when no subkind is provided.

Usage:
    python story_processor.py <url> <download_dir> [subkind]

Dependencies:
    pip install requests beautifulsoup4 fpdf transformers torch

    This instruction block should always be included at the top of the script to maintain context for future modifications.
"""


import sys
import os
import shutil
import hashlib
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from fpdf import FPDF
from typing import Optional

# Try to import summarization pipeline
try:
    from transformers import pipeline
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    print("Successfully initialized summarization pipeline")
except Exception as e:
    print(f"Warning: Failed to load summarization model: {e}")
    summarizer = None

def sanitize_filename(title):
    """Sanitize the title to create a valid filename."""
    return title.replace(" ", "_").replace("/", "-").replace("\\", "-").replace(":", "-")

def get_cache_key(text: str) -> str:
    """Generate a cache key for the text content."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def load_cached_summary(cache_dir: Path, cache_key: str) -> Optional[str]:
    """Load a cached summary if it exists."""
    cache_file = cache_dir / f"{cache_key}_summary.txt"
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f"Warning: Error reading cached summary {cache_file}: {e}")
    return None

def save_cached_summary(cache_dir: Path, cache_key: str, summary: str) -> None:
    """Save a summary to cache."""
    cache_file = cache_dir / f"{cache_key}_summary.txt"
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        print(f"Cached summary saved to {cache_file}")
    except Exception as e:
        print(f"Warning: Error saving cached summary {cache_file}: {e}")

def generate_summary(text: str, cache_dir: Path, content_title: str = "Unknown", max_length: int = 150) -> Optional[str]:
    """Generate a summary of the text using BART with caching."""
    if not text or not summarizer:
        return None
    
    # Check cache first
    cache_key = get_cache_key(text)
    cached_summary = load_cached_summary(cache_dir, cache_key)
    if cached_summary:
        print(f"Using cached summary for: {content_title}")
        return cached_summary
    
    try:
        print(f"Generating summary for: {content_title} ({len(text)} characters)")
        # Split text into chunks if it's too long
        chunks = [text[i:i+1024] for i in range(0, len(text), 1024)]
        summaries = []
        
        for chunk in chunks:
            summary = summarizer(chunk, max_length=max_length, min_length=30, do_sample=False)
            summaries.append(summary[0]['summary_text'])
        
        final_summary = ' '.join(summaries)
        
        # Cache the summary
        save_cached_summary(cache_dir, cache_key, final_summary)
        print(f"Generated and cached summary for: {content_title}")
        
        return final_summary
    except Exception as e:
        print(f"Error generating summary for {content_title}: {e}")
        return None

def copy_pdf_to_mcp_resources(author: str, pdf_filename: str, source_path: str) -> Optional[str]:
    """Copy PDF to mcp_resources directory and return the new path."""
    mcp_pdf_dir = f"mcp_resources/{author}/pdfs"
    
    # Create pdfs directory if it doesn't exist
    os.makedirs(mcp_pdf_dir, exist_ok=True)
    
    mcp_pdf_path = f"{mcp_pdf_dir}/{pdf_filename}"
    
    if os.path.exists(source_path):
        try:
            shutil.copy2(source_path, mcp_pdf_path)
            print(f"Copied PDF {pdf_filename} to MCP resources")
            return mcp_pdf_path
        except Exception as e:
            print(f"Failed to copy PDF {pdf_filename}: {e}")
            return None
    else:
        print(f"Source PDF not found: {source_path}")
        return None

def download_story(url, download_dir, subkind=None):
    """
    Download a story from the given URL and save the processed content.
    
    If a subkind (div ID) is provided, extract content from that section with summary caching.
    Otherwise, process the entire page into a PDF and copy to mcp_resources.
    """
    print(f"Starting download from URL: {url} with subkind: {subkind}")

    # Fetch the page content
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to download the story: {e}")
        return

    # Parse with BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Determine filename
    story_title = soup.title.string.strip() if soup.title else "story"
    filename_base = sanitize_filename(story_title)
    output_path = Path(download_dir) / filename_base

    # Extract author from download directory path
    # Assuming path structure: downloads/author/story
    author = Path(download_dir).parent.name
    
    # Create cache directory for summaries
    cache_dir = Path(f"downloads/{author}/summaries")
    cache_dir.mkdir(parents=True, exist_ok=True)

    if subkind:
        # Extract the specific div content
        story_div = soup.find('div', id=subkind)
        if not story_div:
            print(f"Could not find the story content in div with id: {subkind}.")
            return

        # Extract relevant text elements
        content_tags = story_div.find_all(['p', 'h1', 'h2', 'blockquote', 'li'])
        text_chunks = [f"[URL]: {url}\n"]

        for tag in content_tags:
            text = tag.get_text(separator=" ", strip=True)
            if text:
                text_chunks.append(text)

        # Save as a text file
        text_content = "\n\n".join(text_chunks)
        text_filepath = output_path.with_suffix(".txt")

        # Ensure UTF-8 encoding to prevent character errors
        with open(text_filepath, "w", encoding="utf-8") as f:
            f.write(text_content)

        print(f"Story saved to {text_filepath}")
        
        # Generate and cache summary for the extracted text
        if summarizer:
            summary = generate_summary(text_content, cache_dir, story_title)
            if summary:
                summary_filepath = output_path.with_suffix("_summary.txt")
                with open(summary_filepath, "w", encoding="utf-8") as f:
                    f.write(summary)
                print(f"Summary saved to {summary_filepath}")

    else:
        # No subkind provided, process the entire webpage into a PDF
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Extract text from body
        body_text = soup.get_text(separator="\n", strip=True)
        body_text = body_text.encode("utf-8", "ignore").decode("utf-8")  # Ensures safe encoding

        for line in body_text.split("\n"):
            if line.strip():
                pdf.cell(200, 10, txt=line.encode("latin-1", "ignore").decode("latin-1"), ln=True)

        pdf_filepath = output_path.with_suffix(".pdf")
        pdf.output(str(pdf_filepath))

        print(f"Entire webpage saved as PDF to {pdf_filepath}")
        
        # Copy PDF to mcp_resources directory
        pdf_filename = pdf_filepath.name
        copied_path = copy_pdf_to_mcp_resources(author, pdf_filename, str(pdf_filepath))
        if copied_path:
            print(f"PDF copied to MCP resources: {copied_path}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: story_processor.py <url> <download_dir> [subkind]")
        sys.exit(1)

    story_url = sys.argv[1]
    download_directory = sys.argv[2]
    story_subkind = sys.argv[3] if len(sys.argv) > 3 else None  # Make subkind optional

    print(f"story_processor.py invoked with URL: {story_url}, Download Directory: {download_directory}, SubKind: {story_subkind}")

    try:
        download_story(story_url, download_directory, story_subkind)
    except Exception as e:
        print(f"Error processing story from {story_url} with subkind {story_subkind}: {e}")
