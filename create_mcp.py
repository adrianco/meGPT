"""
================================================================================
MCP RESOURCE CREATION SCRIPT - DEVELOPMENT CONTEXT
================================================================================

OVERVIEW:
This script creates Machine-Controlled Publishing (MCP) resources from an 
author's content by processing downloaded files and CSV metadata to generate
a comprehensive JSON resource with enhanced metadata, tags, and summaries.

DEVELOPMENT HISTORY:
1. Initial Request: User wanted to convert content into MCP resources and 
   requested guidance on the process and schema structure.

2. Schema Development: Created a detailed MCP JSON schema with metadata 
   properties including author info, content types, and processing statistics.

3. Basic Script Creation: Built initial create_mcp.py to process CSV content
   and convert to MCP format with basic functionality.

4. Enhancement Phase: Added comprehensive improvements including:
   - NLP-based tag extraction using NLTK (lemmatization, stopword removal)
   - Content summarization using BART model from Hugging Face Transformers
   - Enhanced metadata with content statistics and processing info
   - Improved error handling and logging throughout
   - Progress reporting with tqdm progress bars
   - ContentProcessor class for organized processing logic

5. File Processing Expansion: Extended script to walk through all downloaded
   content files, not just CSV-referenced content:
   - Added walk_all_downloaded_content() function
   - Processed both JSON and text files from downloads directory
   - Extracted URLs from first line of text files
   - Avoided duplicate processing by URL matching

6. Blog Archive Integration: Added special handling for blog archives:
   - medium_adrianco directory → 'medium' content type
   - blogger_perfcap_posts directory → 'blogger' content type
   - Each blog post becomes individual entry with proper metadata

7. File Directory Processing: Enhanced to handle the 'file' directory:
   - Categorized files by extension (pdf/pptx/ppt → presentation, txt → blog_post)
   - Processed each file as individual entry with proper subkind classification
   - Maintained file path references and metadata

8. Title Standardization: Ensured all file-based entries use filename as title:
   - File stem (name without extension) becomes title
   - Underscores replaced with spaces for readability
   - Consistent across all file types and directories

9. URL Extraction Improvements: Enhanced URL detection and processing:
   - Changed from startswith() to regex pattern matching
   - Finds URLs anywhere on first line (not just at start)
   - Properly removes URL lines from content text
   - Handles formats like "[URL] https://..." correctly

10. Code Generalization: Removed hardcoded author-specific references:
    - Eliminated "virtual_" prefix hardcoding
    - Made script work with any author name provided as argument
    - Dynamic processing based on actual directory structure

11. URL Standardization: Enhanced URL handling for proper resource linking:
    - Convert relative file paths to full GitHub repository URLs
    - For PDFs, use processed files from downloads directory as source
    - Ensure all URLs are absolute and accessible
    - Handle both local file references and web URLs consistently

12. PDF Processing Architecture: Moved PDF text extraction to preprocessing pipeline:
    - PDF text extraction now handled by book_processor.py during build phase
    - MCP script reads preprocessed text files created by book processor
    - Copy PDFs to mcp_resources directory for persistent storage
    - Reference copied PDFs in mcp_resources (downloads is ephemeral)
    - Simplified MCP script to focus on resource assembly rather than content extraction

13. MCP Resource Design Philosophy: Implemented hybrid approach for book content:
    - Books now include rich summaries instead of full text content
    - PDFs copied to mcp_resources/author/pdfs/ for persistent storage
    - URLs updated to point to copied PDFs rather than original GitHub files
    - Maintains compact MCP resource size while preserving access to full content
    - Balances self-contained metadata with external file references

14. Summary Generation Architecture: Moved summary generation to book processor:
    - Summary generation now handled by book_processor.py during preprocessing
    - Summaries cached in downloads/author/book/filename_summary.txt files
    - MCP script reads preprocessed summaries instead of generating them
    - Book processor has --force-summaries flag for cache control
    - Fixed PDF filename resolution for extracted page subsets
    - Significant performance improvement for MCP generation (summaries pre-generated)
    - Proper separation of concerns: preprocessing vs resource assembly
    - Removed --force-summaries option from MCP script (no longer needed)

CURRENT FUNCTIONALITY:
- Processes CSV metadata for published content
- Walks all downloaded content directories recursively
- Extracts and processes text files with URL detection
- Generates NLP-based tags from titles and content
- Creates summaries using BART transformer model with intelligent caching
- Handles multiple content types (youtube, podcast, story, book, etc.)
- Special processing for blog archives (medium, blogger)
- File categorization by extension and content type
- Converts relative paths to full GitHub repository URLs
- Reads preprocessed text content from book processor output
- Copies PDFs to mcp_resources directory for persistent storage
- Generates cached summaries from preprocessed text content for books/presentations
- Hybrid content approach: summaries + PDF references for optimal resource size
- Command line options for cache control (--force-summaries)
- Comprehensive error handling and logging
- JSON schema validation for output
- Deduplication by URL to avoid processing same content multiple times

DEPENDENCIES:
- nltk: Natural language processing (tokenization, stopwords, lemmatization)
- transformers: BART model for text summarization
- tqdm: Progress bar display
- jsonschema: MCP resource validation
- Standard libraries: json, csv, pathlib, datetime, re, logging, hashlib, shutil

USAGE:
    python create_mcp.py <author_name>
    
    Arguments:
        author_name: The author name to create MCP resources for
    
    Examples:
        python create_mcp.py virtual_adrianco
    
OUTPUTS:
- MCP resource JSON file at: mcp_resources/<author>/mcp_resource.json
- Copied PDF files at: mcp_resources/<author>/pdfs/
- Comprehensive logging of processing statistics
- Content type breakdown and processing metrics

SCHEMA COMPLIANCE:
Generates MCP resources following defined JSON schema with:
- Metadata section (author, version, timestamps, statistics)
- Content array with standardized entry format
- Proper validation and error handling
================================================================================
"""

"""
Create MCP Resources Script

Purpose:
This script creates Machine-Controlled Publishing (MCP) resources from an author's content.
It first ensures that all content is downloaded and processed by running build.py if needed,
then converts the processed content into MCP-compatible JSON format.

Usage:
    create_mcp.py <author>
      - author: The author name to create MCP resources for

Example:
    create_mcp.py virtual_adrianco
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime, UTC
import csv
import re
from typing import Dict, List, Any, Optional, Set
import jsonschema
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from transformers import pipeline
from tqdm import tqdm
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import shutil
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# GitHub repository base URL for converting relative paths
GITHUB_REPO_BASE = "https://raw.githubusercontent.com/adrianco/meGPT/main/"



def convert_to_full_url(url_or_path: str, author: str) -> str:
    """Convert relative file paths to full GitHub repository URLs."""
    if not url_or_path:
        return url_or_path
    
    # If it's already a full URL, return as-is
    if url_or_path.startswith(('http://', 'https://')):
        return url_or_path
    
    # If it's a relative path starting with ./authors/, convert to GitHub URL
    if url_or_path.startswith('./authors/'):
        return GITHUB_REPO_BASE + url_or_path[2:]  # Remove './' prefix
    
    # If it's a downloads path, convert to GitHub URL
    if url_or_path.startswith('downloads/'):
        return GITHUB_REPO_BASE + url_or_path
    
    # If it's an mcp_resources path, convert to GitHub URL
    if url_or_path.startswith('mcp_resources/'):
        return GITHUB_REPO_BASE + url_or_path
    
    # If it's just a filename or other relative path, assume it's in authors directory
    if not url_or_path.startswith('/'):
        return GITHUB_REPO_BASE + f"authors/{author}/" + url_or_path
    
    return url_or_path

def copy_pdf_to_mcp_resources(author: str, original_pdf_filename: str) -> str:
    """Copy PDF from downloads to mcp_resources directory and return the new path."""
    # Find the actual extracted PDF filename
    actual_pdf_filename = find_extracted_pdf_filename(original_pdf_filename, author)
    if not actual_pdf_filename:
        logger.warning(f"No extracted PDF found for: {original_pdf_filename}")
        return None
    
    downloads_pdf_path = f"downloads/{author}/book/{actual_pdf_filename}"
    mcp_pdf_dir = f"mcp_resources/{author}/pdfs"
    
    # Create pdfs directory if it doesn't exist
    os.makedirs(mcp_pdf_dir, exist_ok=True)
    
    # Use the actual extracted filename to preserve page range information
    mcp_pdf_path = f"{mcp_pdf_dir}/{actual_pdf_filename}"
    
    if os.path.exists(downloads_pdf_path):
        try:
            shutil.copy2(downloads_pdf_path, mcp_pdf_path)
            logger.info(f"Copied extracted PDF {actual_pdf_filename} to MCP resources")
            return mcp_pdf_path
        except Exception as e:
            logger.error(f"Failed to copy PDF {actual_pdf_filename}: {e}")
            return None
    else:
        logger.warning(f"Extracted PDF not found in downloads: {actual_pdf_filename}")
        return None

def copy_story_pdf_to_mcp_resources(author: str, pdf_filename: str, source_path: str) -> Optional[str]:
    """Copy story PDF to mcp_resources directory and return the new path."""
    mcp_pdf_dir = f"mcp_resources/{author}/pdfs"
    
    # Create pdfs directory if it doesn't exist
    os.makedirs(mcp_pdf_dir, exist_ok=True)
    
    mcp_pdf_path = f"{mcp_pdf_dir}/{pdf_filename}"
    
    if os.path.exists(source_path):
        try:
            shutil.copy2(source_path, mcp_pdf_path)
            logger.info(f"Copied story PDF {pdf_filename} to MCP resources")
            return mcp_pdf_path
        except Exception as e:
            logger.error(f"Failed to copy story PDF {pdf_filename}: {e}")
            return None
    else:
        logger.warning(f"Story PDF not found: {source_path}")
        return None

def get_processed_file_url(file_path: str, author: str) -> str:
    """For PDF and other files, check if there's a processed version in downloads directory."""
    if not file_path:
        return file_path
    
    # Extract filename from path
    path_obj = Path(file_path)
    filename = path_obj.name
    
    # For PDFs, copy to mcp_resources and return that path
    if filename.endswith('.pdf'):
        # Check if PDF exists in original location
        if path_obj.exists():
            copied_path = copy_pdf_to_mcp_resources(author, filename)
            if copied_path:
                return convert_to_full_url(copied_path, author)
        
        # Check if PDF exists in downloads directory
        downloads_file_path = Path(f"downloads/{author}/file/{filename}")
        if downloads_file_path.exists():
            copied_path = copy_pdf_to_mcp_resources(author, filename)
            if copied_path:
                return convert_to_full_url(copied_path, author)
    
    # Check if there's a processed version in downloads
    downloads_file_path = Path(f"downloads/{author}/file/{filename}")
    if downloads_file_path.exists():
        return GITHUB_REPO_BASE + f"downloads/{author}/file/{filename}"
    
    # If no processed version, convert the original path
    return convert_to_full_url(file_path, author)

def get_pdf_text_content(file_path: str, author: str) -> Optional[str]:
    """Get PDF text content from preprocessed text files created by book processor."""
    if not file_path or not file_path.endswith('.pdf'):
        return None
    
    # Extract filename from path
    path_obj = Path(file_path)
    filename = path_obj.name
    base_name = filename.replace('.pdf', '')
    
    # Look for preprocessed text file in downloads/author/book/ directory
    text_file_path = Path(f"downloads/{author}/book/{base_name}.txt")
    if text_file_path.exists():
        try:
            with open(text_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                logger.info(f"Found preprocessed text content for PDF: {filename} ({len(content)} characters)")
                return content.strip()
        except Exception as e:
            logger.warning(f"Error reading preprocessed text file {text_file_path}: {e}")
    
    logger.info(f"No preprocessed text content found for PDF: {filename}")
    return None

def get_pdf_summary_content(file_path: str, author: str) -> Optional[str]:
    """Get PDF summary content from preprocessed summary files created by book processor."""
    if not file_path or not file_path.endswith('.pdf'):
        return None
    
    # Extract filename from path
    path_obj = Path(file_path)
    filename = path_obj.name
    base_name = filename.replace('.pdf', '')
    
    # Look for preprocessed summary file in downloads/author/book/ directory
    summary_file_path = Path(f"downloads/{author}/book/{base_name}_summary.txt")
    if summary_file_path.exists():
        try:
            with open(summary_file_path, 'r', encoding='utf-8') as f:
                summary = f.read()
                logger.info(f"Found preprocessed summary for PDF: {filename}")
                return summary.strip()
        except Exception as e:
            logger.warning(f"Error reading preprocessed summary file {summary_file_path}: {e}")
    
    logger.info(f"No preprocessed summary found for PDF: {filename}")
    return None

def find_extracted_pdf_filename(original_filename: str, author: str) -> Optional[str]:
    """Find the actual extracted PDF filename in downloads directory."""
    base_name = original_filename.replace('.pdf', '')
    downloads_dir = Path(f"downloads/{author}/book")
    
    if not downloads_dir.exists():
        return None
    
    # Look for files that start with the base name and contain "extracted"
    for file_path in downloads_dir.glob(f"{base_name}_extracted_*.pdf"):
        logger.info(f"Found extracted PDF: {file_path.name}")
        return file_path.name
    
    # Fallback: look for the original filename
    original_path = downloads_dir / original_filename
    if original_path.exists():
        return original_filename
    
    return None

def get_pdf_metadata(text_content: str) -> dict:
    """Extract metadata from PDF text content."""
    lines = text_content.split('\n')
    word_count = len(text_content.split())
    
    # Extract first few paragraphs as excerpt
    paragraphs = [line.strip() for line in lines if line.strip() and len(line.strip()) > 50]
    excerpt = '\n\n'.join(paragraphs[:3]) if paragraphs else ""
    
    return {
        "word_count": word_count,
        "character_count": len(text_content),
        "excerpt": excerpt[:500] + "..." if len(excerpt) > 500 else excerpt
    }

# Download required NLTK data
try:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')
    logger.info("Successfully downloaded NLTK data")
except Exception as e:
    logger.error(f"Failed to download NLTK data: {e}")
    sys.exit(1)

# Initialize NLTK components
try:
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('english'))
    logger.info("Successfully initialized NLTK components")
except Exception as e:
    logger.error(f"Failed to initialize NLTK components: {e}")
    sys.exit(1)

# Initialize summarization pipeline
try:
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    logger.info("Successfully initialized summarization pipeline")
except Exception as e:
    logger.warning(f"Failed to load summarization model: {e}")
    summarizer = None

# MCP Schema definition
MCP_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "metadata": {
            "type": "object",
            "properties": {
                "author": {"type": "string"},
                "version": {"type": "string"},
                "last_updated": {"type": "string", "format": "date-time"},
                "content_count": {"type": "integer"},
                "content_types": {
                    "type": "object",
                    "additionalProperties": {"type": "integer"}
                },
                "processing_stats": {
                    "type": "object",
                    "properties": {
                        "total_items": {"type": "integer"},
                        "processed_items": {"type": "integer"},
                        "failed_items": {"type": "integer"},
                        "processing_time": {"type": "number"}
                    }
                }
            },
            "required": ["author", "version", "last_updated"]
        },
        "content": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "kind": {"type": "string"},
                    "subkind": {"type": "string"},
                    "title": {"type": "string"},
                    "source": {"type": "string"},
                    "published_date": {"type": "string"},
                    "url": {"type": "string"},
                    "content": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "transcript": {"type": "string"},
                            "summary": {"type": "string"},
                            "chapters": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "content": {"type": "string"},
                                        "timestamp": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "word_count": {"type": "integer"},
                            "processing_status": {"type": "string"},
                            "processing_errors": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        }
                    }
                },
                "required": ["id", "kind", "title", "source", "url"]
            }
        }
    },
    "required": ["metadata", "content"]
}

class ContentProcessor:
    def __init__(self, author: str):
        self.author = author
        self.technical_terms = {
            'cloud', 'aws', 'azure', 'gcp', 'microservices', 'devops', 'kubernetes',
            'docker', 'containers', 'serverless', 'ai', 'ml', 'sustainability',
            'netflix', 'architecture', 'platform', 'engineering', 'monitoring',
            'performance', 'scaling', 'resilience', 'hpc', 'podcast', 'video',
            'machine learning', 'artificial intelligence', 'data science', 'big data',
            'distributed systems', 'cloud native', 'infrastructure', 'security',
            'automation', 'ci/cd', 'continuous integration', 'continuous deployment',
            'agile', 'scrum', 'lean', 'kanban', 'sre', 'site reliability',
            'observability', 'logging', 'metrics', 'tracing', 'apm'
        }
        # Create cache directory for summaries
        self.cache_dir = Path(f"downloads/{author}/summaries")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def extract_tags(self, title: str, content: Dict[str, Any]) -> List[str]:
        """Extract relevant tags using NLP techniques."""
        tags = set()
        
        try:
            # Process title - simple word splitting
            title_words = title.lower().split()
            title_words = [word.strip('.,!?()[]{}":;') for word in title_words]
            title_words = [word for word in title_words if word and word not in stop_words]
            tags.update(word for word in title_words if word in self.technical_terms)
            
            # Process content if available
            if content.get('text'):
                text_words = content['text'].lower().split()
                text_words = [word.strip('.,!?()[]{}":;') for word in text_words]
                text_words = [word for word in text_words if word and word not in stop_words]
                tags.update(word for word in text_words if word in self.technical_terms)
            
            # Add multi-word terms
            text = f"{title} {content.get('text', '')}"
            for term in self.technical_terms:
                if ' ' in term and term.lower() in text.lower():
                    tags.add(term)
            
            return sorted(list(tags))
        except Exception as e:
            logger.error(f"Error extracting tags: {e}")
            return []

    def get_cache_key(self, text: str) -> str:
        """Generate a cache key for the text content."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def load_cached_summary(self, cache_key: str) -> Optional[str]:
        """Load a cached summary if it exists."""
        cache_file = self.cache_dir / f"{cache_key}_summary.txt"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except Exception as e:
                logger.warning(f"Error reading cached summary {cache_file}: {e}")
        return None
    
    def save_cached_summary(self, cache_key: str, summary: str) -> None:
        """Save a summary to cache."""
        cache_file = self.cache_dir / f"{cache_key}_summary.txt"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(summary)
            logger.debug(f"Cached summary saved to {cache_file}")
        except Exception as e:
            logger.warning(f"Error saving cached summary {cache_file}: {e}")

    def generate_summary(self, text: str, max_length: int = 150, content_title: str = "Unknown") -> Optional[str]:
        """Generate a summary of the text using BART (for non-book content) with caching."""
        if not text or not summarizer:
            return None
        
        # Check cache first
        cache_key = self.get_cache_key(text)
        cached_summary = self.load_cached_summary(cache_key)
        if cached_summary:
            logger.info(f"Using cached summary for: {content_title}")
            return cached_summary
        
        try:
            logger.info(f"Generating summary for: {content_title} ({len(text)} characters)")
            # Split text into chunks if it's too long
            chunks = [text[i:i+1024] for i in range(0, len(text), 1024)]
            summaries = []
            
            for chunk in chunks:
                summary = summarizer(chunk, max_length=max_length, min_length=30, do_sample=False)
                summaries.append(summary[0]['summary_text'])
            
            final_summary = ' '.join(summaries)
            
            # Cache the summary
            self.save_cached_summary(cache_key, final_summary)
            logger.info(f"Generated and cached summary for: {content_title}")
            
            return final_summary
        except Exception as e:
            logger.error(f"Error generating summary for {content_title}: {e}")
            return None

    def process_content(self, kind: str, content: Dict[str, Any], title: str = "Unknown") -> Dict[str, Any]:
        """Process content based on its kind."""
        processed = {}
        errors = []
        
        try:
            if kind == 'podcast':
                if 'transcript' in content:
                    processed['transcript'] = content['transcript']
                    content_title = content.get('title', title or 'Unknown Podcast')
                    processed['summary'] = self.generate_summary(content['transcript'], content_title=content_title)
                if 'chapters' in content:
                    processed['chapters'] = content['chapters']
            
            elif kind in ['story', 'file']:
                if 'text' in content:
                    processed['text'] = content['text']
                    content_title = content.get('title', title or 'Unknown Story/File')
                    processed['summary'] = self.generate_summary(content['text'], content_title=content_title)
            
            elif kind == 'youtube':
                if 'transcript' in content:
                    processed['transcript'] = content['transcript']
                    content_title = content.get('title', title or 'Unknown YouTube Video')
                    processed['summary'] = self.generate_summary(content['transcript'], content_title=content_title)
                if 'chapters' in content:
                    processed['chapters'] = content['chapters']
            
            # Add word count
            text = processed.get('text', '') or processed.get('transcript', '')
            processed['metadata'] = {
                'word_count': len(text.split()),
                'processing_status': 'success',
                'processing_errors': errors
            }
            
        except Exception as e:
            errors.append(str(e))
            processed['metadata'] = {
                'word_count': 0,
                'processing_status': 'error',
                'processing_errors': errors
            }
        
        return processed

    def process_story_content(self, entry: dict) -> tuple[dict, str]:
        """Process story content with PDF copying for stories without subkind. Returns (content, updated_url)."""
        content = {
            "metadata": {
                "word_count": 0,
                "processing_status": "success",
                "processing_errors": []
            }
        }
        
        updated_url = entry.get('URL', '')
        
        # Check if there's a PDF file in the story downloads directory
        story_dir = Path(f"downloads/{self.author}/story")
        if story_dir.exists():
            # Look for PDF files that might correspond to this story
            story_title = entry.get('What', 'Unknown')
            sanitized_title = story_title.replace(" ", "_").replace("/", "-").replace("\\", "-").replace(":", "-")
            
            pdf_file = story_dir / f"{sanitized_title}.pdf"
            if pdf_file.exists():
                # Copy PDF to MCP resources
                copied_pdf_path = copy_story_pdf_to_mcp_resources(self.author, pdf_file.name, str(pdf_file))
                
                if copied_pdf_path:
                    # Return updated URL to point to copied PDF
                    updated_url = f"./mcp_resources/{self.author}/pdfs/{pdf_file.name}"
                    logger.info(f"Copied story PDF to MCP resources: {pdf_file.name}")
                    
                    # Set basic metadata for PDF
                    content["metadata"]["processing_status"] = "pdf_copied"
                else:
                    content["metadata"]["processing_errors"].append("Failed to copy PDF to MCP resources")
            else:
                # Check if there's text content with summary
                text_file = story_dir / f"{sanitized_title}.txt"
                if text_file.exists():
                    try:
                        with open(text_file, 'r', encoding='utf-8') as f:
                            text_content = f.read()
                        
                        content["text"] = text_content
                        content["metadata"]["word_count"] = len(text_content.split())
                        
                        # Look for cached summary
                        summary_file = story_dir / f"{sanitized_title}_summary.txt"
                        if summary_file.exists():
                            try:
                                with open(summary_file, 'r', encoding='utf-8') as f:
                                    content["summary"] = f.read().strip()
                                logger.info(f"Loaded story summary for: {story_title}")
                            except Exception as e:
                                logger.warning(f"Error reading story summary {summary_file}: {e}")
                        
                    except Exception as e:
                        content["metadata"]["processing_errors"].append(f"Error reading story text: {e}")
                        logger.warning(f"Error reading story text file {text_file}: {e}")
        
        return content, updated_url

    def process_book_content(self, entry: dict) -> tuple[dict, str]:
        """Process book content with PDF copying and rich metadata. Returns (content, updated_url)."""
        content = {
            "metadata": {
                "word_count": 0,
                "processing_status": "success",
                "processing_errors": []
            }
        }
        
        updated_url = entry.get('URL', '')
        
        # Check if there's a PDF URL
        pdf_url = entry.get('URL', '')
        if pdf_url and pdf_url.endswith('.pdf'):
            pdf_filename = os.path.basename(pdf_url)
            
            # Look for preprocessed text content
            text_content = get_pdf_text_content(pdf_filename, self.author)
            
            if text_content:
                # Copy PDF to MCP resources
                copied_pdf_path = copy_pdf_to_mcp_resources(self.author, pdf_filename)
                
                if copied_pdf_path:
                    # Return updated URL to point to copied PDF with extracted filename
                    extracted_filename = os.path.basename(copied_pdf_path)
                    updated_url = f"./mcp_resources/{self.author}/pdfs/{extracted_filename}"
                
                # Get PDF metadata
                pdf_metadata = get_pdf_metadata(text_content)
                content["metadata"].update(pdf_metadata)
                
                # Look for preprocessed summary instead of generating it
                summary = get_pdf_summary_content(pdf_filename, self.author)
                if summary:
                    content["summary"] = summary
                    logger.info(f"Loaded preprocessed summary for book: {entry.get('What', 'Unknown')}")
                else:
                    content["metadata"]["processing_errors"].append("No preprocessed summary found")
                    logger.warning(f"No preprocessed summary found for book: {entry.get('What', 'Unknown')}")
            else:
                content["metadata"]["processing_status"] = "no_pdf_content"
                content["metadata"]["processing_errors"].append("No preprocessed PDF content found")
        
        return content, updated_url

def ensure_downloads_exist(author: str) -> None:
    """Check if downloads exist and run build.py if they don't."""
    download_dir = Path(f"downloads/{author}")
    if not download_dir.exists() or not any(download_dir.iterdir()):
        logger.info(f"No downloads found for {author}. Running build.py...")
        subprocess.run([sys.executable, "build.py", author], check=True)
    else:
        logger.info(f"Downloads found for {author}. Skipping build.py.")

def load_csv_content(author: str) -> List[Dict[str, str]]:
    """Load the published_content.csv file."""
    csv_path = Path(f"authors/{author}/published_content.csv")
    if not csv_path.exists():
        raise FileNotFoundError(f"No published_content.csv found for {author}")
    
    content = []
    with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            content.append(row)
    return content

def extract_url_from_text_file(file_path: Path) -> Optional[str]:
    """Extract URL from the first line of a text file if it exists."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            # Look for URL anywhere on the first line
            url_match = re.search(r'https?://\S+', first_line)
            if url_match:
                return url_match.group(0)
    except Exception as e:
        logger.warning(f"Error reading text file {file_path}: {e}")
    return None

def load_processed_content(author: str, kind: str) -> List[Dict[str, Any]]:
    """Load processed content from the downloads directory."""
    kind_dir = Path(f"downloads/{author}/{kind}")
    if not kind_dir.exists():
        return []
    
    content = []
    # Handle JSON files
    for file in kind_dir.glob("*.json"):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content.append(json.load(f))
        except Exception as e:
            logger.warning(f"Error loading JSON file {file}: {e}")
    
    # Handle text files
    for file in kind_dir.glob("*.txt"):
        try:
            url = extract_url_from_text_file(file)
            with open(file, 'r', encoding='utf-8') as f:
                text = f.read()
                # Skip the first line if it's a URL
                if url:
                    text = '\n'.join(text.split('\n')[1:])
                content.append({
                    'text': text,
                    'URL': url or str(file),  # Use file path as fallback URL
                    'title': file.stem  # Use filename as title
                })
        except Exception as e:
            logger.warning(f"Error loading text file {file}: {e}")
    
    return content

def walk_all_downloaded_content(author: str) -> List[Dict]:
    """Walk through all downloaded content for an author and return a list of content items."""
    discovered = []
    downloads_dir = Path(f"downloads/{author}")
    
    # Special directories for blog archives
    blog_dirs = {
        'medium_adrianco': 'medium',
        'blogger_perfcap_posts': 'blogger'
    }
    
    # Process blog archive directories
    for dir_name, content_type in blog_dirs.items():
        blog_dir = downloads_dir / dir_name
        if blog_dir.exists():
            for file_path in blog_dir.glob("*.txt"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        url = None
                        content_lines = []
                        
                        # Check first line for URL using regex
                        if lines:
                            url_match = re.search(r'https?://\S+', lines[0])
                            if url_match:
                                url = url_match.group(0)
                                content_lines = lines[1:]
                            else:
                                content_lines = lines
                        
                        # Always use file name as title
                        title = file_path.stem.replace("_", " ")
                        
                        content = {
                            "id": f"{author}_{content_type}_{hash(str(file_path))}",
                            "kind": content_type,
                            "subkind": "blog_post",
                            "title": title,
                            "source": dir_name,
                            "published_date": "",
                            "url": url or str(file_path),
                            "content": {
                                "text": "".join(content_lines),
                                "metadata": {
                                    "word_count": len("".join(content_lines).split()),
                                    "processing_status": "success",
                                    "processing_errors": []
                                }
                            }
                        }
                        discovered.append(content)
                except Exception as e:
                    logging.error(f"Error loading blog file {file_path}: {str(e)}")
    
    # Process files in the file directory
    file_dir = downloads_dir / "file"
    if file_dir.exists():
        for file_path in file_dir.glob("*"):
            if file_path.is_file():
                try:
                    # Determine subkind based on file extension
                    subkind = "document"
                    if file_path.suffix.lower() in [".pdf", ".pptx", ".ppt"]:
                        subkind = "presentation"
                    elif file_path.suffix.lower() == ".txt":
                        subkind = "blog_post"
                    
                    # Always use file name as title
                    title = file_path.stem.replace("_", " ")
                    
                    # For text files, read content and extract URL
                    if file_path.suffix.lower() == ".txt":
                        with open(file_path, "r", encoding="utf-8") as f:
                            lines = f.readlines()
                            url = None
                            content_lines = []
                            
                            # Check first line for URL using regex
                            if lines:
                                url_match = re.search(r'https?://\S+', lines[0])
                                if url_match:
                                    url = url_match.group(0)
                                    content_lines = lines[1:]
                                else:
                                    content_lines = lines
                            
                            content = {
                                "id": f"{author}_file_{hash(str(file_path))}",
                                "kind": "file",
                                "subkind": subkind,
                                "title": title,
                                "source": "file",
                                "published_date": "",
                                "url": url or str(file_path),
                                "content": {
                                    "text": "".join(content_lines),
                                    "metadata": {
                                        "word_count": len("".join(content_lines).split()),
                                        "processing_status": "success",
                                        "processing_errors": []
                                    }
                                }
                            }
                            discovered.append(content)
                    else:
                        # For non-text files, just include metadata
                        content = {
                            "id": f"{author}_file_{hash(str(file_path))}",
                            "kind": "file",
                            "subkind": subkind,
                            "title": title,
                            "source": "file",
                            "published_date": "",
                            "url": str(file_path),
                            "content": {
                                "metadata": {
                                    "word_count": 0,
                                    "processing_status": "success",
                                    "processing_errors": []
                                }
                            }
                        }
                        discovered.append(content)
                except Exception as e:
                    logging.error(f"Error loading file {file_path}: {str(e)}")
    
    # Process other directories
    for kind_dir in downloads_dir.glob("*"):
        if kind_dir.is_dir() and kind_dir.name not in ["file"] + list(blog_dirs.keys()):  # Skip already processed directories
            for file_path in kind_dir.glob("*"):
                if file_path.is_file():
                    try:
                        if file_path.suffix.lower() == ".json":
                            with open(file_path, "r", encoding="utf-8") as f:
                                data = json.load(f)
                                
                                # Check if this is already an MCP-compatible entry (from youtube_playlist_processor)
                                if kind_dir.name == "youtube_playlist" and "id" in data and "kind" in data:
                                    # This is already MCP-compatible, use it directly
                                    discovered.append(data)
                                else:
                                    # Legacy format, convert to MCP format
                                    title = file_path.stem.replace("_", " ")
                                    content = {
                                        "id": f"{author}_{kind_dir.name}_{hash(str(file_path))}",
                                        "kind": kind_dir.name,
                                        "subkind": "",
                                        "title": title,
                                        "source": kind_dir.name,
                                        "published_date": "",
                                        "url": data.get("url", str(file_path)),
                                        "content": {
                                            "metadata": {
                                                "word_count": 0,
                                                "processing_status": "success",
                                                "processing_errors": []
                                            }
                                        }
                                    }
                                    discovered.append(content)
                        elif file_path.suffix.lower() == ".txt":
                            with open(file_path, "r", encoding="utf-8") as f:
                                lines = f.readlines()
                                url = None
                                content_lines = []
                                
                                # Check first line for URL using regex
                                if lines:
                                    url_match = re.search(r'https?://\S+', lines[0])
                                    if url_match:
                                        url = url_match.group(0)
                                        content_lines = lines[1:]
                                    else:
                                        content_lines = lines
                                
                                content = {
                                    "id": f"{author}_{kind_dir.name}_{hash(str(file_path))}",
                                    "kind": kind_dir.name,
                                    "subkind": "",
                                    "title": title,
                                    "source": kind_dir.name,
                                    "published_date": "",
                                    "url": url or str(file_path),
                                    "content": {
                                        "text": "".join(content_lines),
                                        "metadata": {
                                            "word_count": len("".join(content_lines).split()),
                                            "processing_status": "success",
                                            "processing_errors": []
                                        }
                                    }
                                }
                                discovered.append(content)
                    except Exception as e:
                        logging.error(f"Error loading file {file_path}: {str(e)}")
    
    return discovered

def create_mcp_resource(author: str, csv_content: List[Dict[str, str]], processed_content: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create MCP resource from the content, including all discovered files."""
    processor = ContentProcessor(author)
    start_time = datetime.now(UTC)
    content_types = {}
    mcp_resource = {
        "metadata": {
            "author": author,
            "version": "1.0",
            "last_updated": datetime.now(UTC).isoformat(),
            "content_count": 0,  # Will update later
            "content_types": content_types,
            "processing_stats": {
                "total_items": 0,  # Will update later
                "processed_items": 0,
                "failed_items": 0,
                "processing_time": 0
            }
        },
        "content": []
    }
    
    # Map URLs from CSV for deduplication
    csv_urls = set(item.get('URL', '').strip() for item in csv_content if item.get('URL'))
    # Map URLs from processed_content for deduplication
    processed_urls = set(item.get('URL', '').strip() for item in processed_content if item.get('URL'))
    # Walk all discovered files
    discovered = walk_all_downloaded_content(author)
    discovered_urls = set(item['url'] for item in discovered)
    # Merge all URLs for deduplication
    all_urls = csv_urls | processed_urls | discovered_urls
    # Build a lookup for discovered content
    discovered_map = {item['url']: item for item in discovered}
    
    # Build MCP entries from CSV (with processed content if available)
    for idx, item in enumerate(csv_content):
        try:
            url = item.get('URL', '').strip()
            kind = item.get('Kind', '').strip() or discovered_map.get(url, {}).get('kind', '')
            subkind = item.get('SubKind', '').strip()
            title = item.get('What', '').strip() or discovered_map.get(url, {}).get('title', '') or 'Untitled'
            source = item.get('Where', '').strip()
            published = item.get('Published', '').strip()
            
            # Skip file kind entries from CSV as we'll handle them separately
            if kind.lower() == 'file':
                continue
            
            # Convert URL to full URL if it's a relative path
            original_url = url
            if url:
                if kind.lower() in ['book'] and url.endswith('.pdf'):
                    # For PDFs, check for processed version in downloads
                    url = get_processed_file_url(url, author)
                else:
                    # For other content, convert relative paths to full URLs
                    url = convert_to_full_url(url, author)
                
            # Update content type counter
            content_types[kind] = content_types.get(kind, 0) + 1
            content_item = {
                "id": f"{author}_{kind}_{idx}",
                "kind": kind.lower(),
                "subkind": subkind,
                "title": title,
                "source": source,
                "published_date": published,
                "url": url,
                "content": {},
                "tags": []
            }
            
            # Add processed content if available
            if url in discovered_map:
                content_item['content'] = processor.process_content(kind.lower(), discovered_map[url]['content'], title)
            elif url in processed_urls:
                # fallback to processed_content
                match = next((pc for pc in processed_content if pc.get('URL', '').strip() == url), None)
                if match:
                    content_item['content'] = processor.process_content(kind.lower(), match, title)
            
            # For books with PDFs, use the enhanced book processing
            if kind.lower() in ['book'] and original_url and original_url.endswith('.pdf'):
                book_content, updated_url = processor.process_book_content({
                    'URL': original_url,
                    'What': title
                })
                content_item['content'].update(book_content)
                # Update URL to point to copied PDF if available
                if updated_url != original_url:
                    content_item['url'] = updated_url
            
            # For stories, use the enhanced story processing to handle PDFs and cached summaries
            if kind.lower() == 'story':
                story_content, updated_url = processor.process_story_content({
                    'URL': original_url,
                    'What': title
                })
                content_item['content'].update(story_content)
                # Update URL to point to copied PDF if available
                if updated_url != original_url:
                    content_item['url'] = updated_url
            
            # Generate tags
            content_item['tags'] = processor.extract_tags(title, content_item['content'])
            mcp_resource['content'].append(content_item)
            mcp_resource['metadata']['processing_stats']['processed_items'] += 1
            
        except Exception as e:
            logger.error(f"Error processing item {item.get('URL', '')}: {e}")
            mcp_resource['metadata']['processing_stats']['failed_items'] += 1
    
    # Add all discovered content not in CSV
    csv_and_processed = csv_urls | processed_urls
    for item in discovered:
        if item['url'] not in csv_and_processed:
            try:
                kind = item.get('kind', '')
                subkind = item.get('subkind', '')
                title = item.get('title', '') or 'Untitled'
                url = item.get('url', '')
                source = item.get('source', '')
                content = item.get('content', {})
                
                # Convert URL to full URL if it's a relative path
                if url and not url.startswith(('http://', 'https://')):
                    url = convert_to_full_url(url, author)
                
                # For presentations (PDFs), try to get PDF text content and summary
                if subkind == 'presentation' and kind == 'file':
                    # The URL might be a file path, extract filename for PDF text lookup
                    file_path = item.get('url', '')
                    if file_path.endswith('.pdf'):
                        pdf_filename = os.path.basename(file_path)
                        pdf_text = get_pdf_text_content(file_path, author)
                        if pdf_text:
                            content['text'] = pdf_text
                            # Try to get preprocessed summary first
                            summary = get_pdf_summary_content(pdf_filename, author)
                            if summary:
                                content['summary'] = summary
                            else:
                                # Fallback to generating summary for presentations
                                content['summary'] = processor.generate_summary(pdf_text, max_length=200, content_title=title)
                            
                            if 'metadata' not in content:
                                content['metadata'] = {}
                            content['metadata'].update({
                                'word_count': len(pdf_text.split()),
                                'processing_status': 'success',
                                'processing_errors': []
                            })
                            logger.info(f"Added PDF content and summary for presentation: {title}")
                
                # Update content type counter
                content_types[kind] = content_types.get(kind, 0) + 1
                
                # Use a hash of the URL for unique id
                url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
                content_item = {
                    "id": f"{author}_{kind}_{url_hash}",
                    "kind": kind.lower(),
                    "subkind": subkind,
                    "title": title,
                    "source": source,
                    "published_date": "",
                    "url": url,
                    "content": content,
                    "tags": processor.extract_tags(title, content)
                }
                mcp_resource['content'].append(content_item)
                mcp_resource['metadata']['processing_stats']['processed_items'] += 1
                
            except Exception as e:
                logger.error(f"Error processing discovered file {url}: {e}")
                mcp_resource['metadata']['processing_stats']['failed_items'] += 1
    
    # Update counts
    mcp_resource['metadata']['content_count'] = len(mcp_resource['content'])
    mcp_resource['metadata']['processing_stats']['total_items'] = len(mcp_resource['content'])
    mcp_resource['metadata']['processing_stats']['processing_time'] = (datetime.now(UTC) - start_time).total_seconds()
    return mcp_resource

def validate_mcp_resource(mcp_resource: Dict[str, Any]) -> bool:
    """Validate the MCP resource against the schema."""
    try:
        jsonschema.validate(instance=mcp_resource, schema=MCP_SCHEMA)
        return True
    except jsonschema.exceptions.ValidationError as e:
        logger.error(f"Validation error: {e}")
        return False

def save_mcp_resource(author: str, mcp_resource: Dict[str, Any]) -> None:
    """Save the MCP resource to a JSON file."""
    output_dir = Path(f"mcp_resources/{author}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "mcp_resource.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(mcp_resource, f, indent=2)
    
    logger.info(f"MCP resource saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Create MCP resources from author content')
    parser.add_argument('author', help='Author name to create MCP resources for')
    
    args = parser.parse_args()
    author = args.author
    
    try:
        # Ensure downloads exist
        ensure_downloads_exist(author)
        
        # Load content
        csv_content = load_csv_content(author)
        
        # Load processed content for each kind
        processed_content = []
        for kind in set(item['Kind'].lower() for item in csv_content):
            processed_content.extend(load_processed_content(author, kind))
        
        # Create MCP resource
        mcp_resource = create_mcp_resource(author, csv_content, processed_content)
        
        # Validate the resource
        if not validate_mcp_resource(mcp_resource):
            logger.error("MCP resource validation failed")
            sys.exit(1)
        
        # Save the resource
        save_mcp_resource(author, mcp_resource)
        
        # Print summary
        stats = mcp_resource['metadata']['processing_stats']
        logger.info(f"Successfully created MCP resource for {author}")
        logger.info(f"Processed {stats['processed_items']} items in {stats['processing_time']:.2f} seconds")
        logger.info(f"Failed items: {stats['failed_items']}")
        logger.info(f"Content types: {mcp_resource['metadata']['content_types']}")
        
    except Exception as e:
        logger.error(f"Error creating MCP resource: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 