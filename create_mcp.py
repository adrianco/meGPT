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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    def __init__(self):
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

    def generate_summary(self, text: str, max_length: int = 150) -> Optional[str]:
        """Generate a summary of the text using BART."""
        if not text or not summarizer:
            return None
        
        try:
            # Split text into chunks if it's too long
            chunks = [text[i:i+1024] for i in range(0, len(text), 1024)]
            summaries = []
            
            for chunk in chunks:
                summary = summarizer(chunk, max_length=max_length, min_length=30, do_sample=False)
                summaries.append(summary[0]['summary_text'])
            
            return ' '.join(summaries)
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return None

    def process_content(self, kind: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """Process content based on its kind."""
        processed = {}
        errors = []
        
        try:
            if kind == 'podcast':
                if 'transcript' in content:
                    processed['transcript'] = content['transcript']
                    processed['summary'] = self.generate_summary(content['transcript'])
                if 'chapters' in content:
                    processed['chapters'] = content['chapters']
            
            elif kind in ['story', 'file']:
                if 'text' in content:
                    processed['text'] = content['text']
                    processed['summary'] = self.generate_summary(content['text'])
            
            elif kind == 'youtube':
                if 'transcript' in content:
                    processed['transcript'] = content['transcript']
                    processed['summary'] = self.generate_summary(content['transcript'])
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
            # Check if the first line looks like a URL
            if first_line.startswith(('http://', 'https://')):
                return first_line
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
                        
                        # Check first line for URL
                        if lines and (lines[0].startswith("http://") or lines[0].startswith("https://")):
                            url = lines[0].strip()
                            content_lines = lines[1:]
                        else:
                            content_lines = lines
                        
                        # Always use file name as title
                        title = file_path.stem.replace("_", " ")
                        
                        content = {
                            "id": f"virtual_{author}_{content_type}_{hash(str(file_path))}",
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
                            
                            # Check first line for URL
                            if lines and (lines[0].startswith("http://") or lines[0].startswith("https://")):
                                url = lines[0].strip()
                                content_lines = lines[1:]
                            else:
                                content_lines = lines
                            
                            content = {
                                "id": f"virtual_{author}_file_{hash(str(file_path))}",
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
                            "id": f"virtual_{author}_file_{hash(str(file_path))}",
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
                        # Always use file name as title for these entries as well
                        title = file_path.stem.replace("_", " ")
                        if file_path.suffix.lower() == ".json":
                            with open(file_path, "r", encoding="utf-8") as f:
                                data = json.load(f)
                                content = {
                                    "id": f"virtual_{author}_{kind_dir.name}_{hash(str(file_path))}",
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
                                
                                # Check first line for URL
                                if lines and (lines[0].startswith("http://") or lines[0].startswith("https://")):
                                    url = lines[0].strip()
                                    content_lines = lines[1:]
                                else:
                                    content_lines = lines
                                
                                content = {
                                    "id": f"virtual_{author}_{kind_dir.name}_{hash(str(file_path))}",
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
    processor = ContentProcessor()
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
                content_item['content'] = processor.process_content(kind.lower(), discovered_map[url]['content'])
            elif url in processed_urls:
                # fallback to processed_content
                match = next((pc for pc in processed_content if pc.get('URL', '').strip() == url), None)
                if match:
                    content_item['content'] = processor.process_content(kind.lower(), match)
            
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
    if len(sys.argv) != 2:
        logger.error("Usage: create_mcp.py <author>")
        sys.exit(1)
    
    author = sys.argv[1]
    
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