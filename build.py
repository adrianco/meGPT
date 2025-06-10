"""
Build Script

Purpose:
This script automates the process of building and processing various types of content files. 
It ensures that different content sources (such as text files, PDFs, and other structured data) 
are correctly processed and saved in the appropriate output format.

Key Design Choices:
- Supports multiple content types and processing workflows.
- Uses a common calling convention to integrate with other processor scripts.
- Fetches and processes content from specified URLs or local directories.
- Handles text, PDFs, and potentially other formats in a modular way.
- Implements error handling for missing files, inaccessible URLs, and unexpected data formats.
- Allows debugging mode for deeper inspection of intermediate processing steps.
- Maintains state.json in the download directory to track processed content.
- Creates JSON files for content types without dedicated processors for later processing.
- Sanitizes filenames by replacing all non-alphanumeric characters with underscores.
- Organizes output into subdirectories named after each kind of data.

Important Considerations:
- The script must correctly determine which processor to use based on file type or user input.
- Network failures or missing resources should not halt the entire process.
- Processing logic may need to be extended to support new content types in the future.
- The script should maintain compatibility with the overall system's workflow and expected outputs.
- When no processor exists for a content type, data is preserved in JSON format using the 'What' field for naming.
- The published_content.csv file must have the header: Kind,SubKind,What,Where,Published,URL
- Output is organized in subdirectories by content kind (e.g., downloads/author/blog/, downloads/author/tweet/).

Usage:
    build.py <author> [kind]
      - author: The author name to process content for
      - kind (optional): Process only content of this specific kind
                         When provided, the script will process all content of this kind,
                         ignoring whether it was previously processed

Examples:
    build.py virtual_adrianco         # Process all unprocessed content for the author
    build.py virtual_adrianco podcast # Process all podcast content for the author

Process Flow:
1. The script reads from the author's published_content.csv file
2. For each content item, it checks if it's already been processed (via state.json)
   (This check is skipped when processing a specific kind)
3. If a local file/directory is found, it copies the files to the kind-specific subdirectory
4. For other content types, it attempts to find and use a matching processor script
5. If no processor exists, it creates a JSON file with all the CSV row fields in the kind-specific subdirectory
6. The state.json file is always updated after successful processing

Instruction:
This comment provides essential context for the script. If this script is used in a new chat session, 
this comment should be retained to preserve understanding without needing prior conversation.
"""

import os
import sys
import csv
import shutil
import json
import subprocess
import re  # Added for regex pattern matching
from pathlib import Path

def load_state(state_file):
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            return json.load(f)
    return {}

def save_state(state_file, state):
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=4)

def sanitize_filename(filename):
    """
    Replace all punctuation, spaces, and special characters with underscores.
    This ensures filenames are valid across all operating systems and contain no problematic characters.
    """
    if not filename:
        return "unknown"
    
    # First replace common problematic characters with underscores
    cleaned = re.sub(r'[:\?\*"<>|/\\@]', '_', filename)
    
    # Replace any remaining non-alphanumeric characters (including spaces) with underscores
    cleaned = re.sub(r'[^\w\.]', '_', cleaned)
    
    # Replace multiple consecutive underscores with a single underscore
    cleaned = re.sub(r'_+', '_', cleaned)
    
    # Remove leading/trailing underscores
    cleaned = cleaned.strip('_')
    
    # Ensure the filename isn't empty
    if not cleaned:
        return "unknown"
    
    # Truncate if too long (most filesystems have limits around 255 bytes)
    if len(cleaned) > 200:
        cleaned = cleaned[:200]
    
    return cleaned

def process_author(author, specific_kind=None):
    # Define paths
    author_dir = Path(f"authors/{author}")
    download_dir = Path(f"downloads/{author}")
    state_file = download_dir / "state.json"
    content_csv = author_dir / "published_content.csv"

    # Ensure directories exist
    download_dir.mkdir(parents=True, exist_ok=True)

    # Load previous state - always load it for updates
    state = load_state(state_file)
    
    # Initialize counters for summary
    summary = {
        "total": 0,
        "successful": 0,
        "failed": 0,
        "skipped": 0,
        "failed_urls": []
    }

    # Read CSV
    if not content_csv.exists():
        print(f"No published_content.csv found for author {author}.")
        return

    with open(content_csv, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            url = row['URL'].strip()
            kind = row['Kind'].strip()
            subkind = row.get('SubKind', '').strip()  # Read SubKind
            what = row.get('What', '').strip()  # Get the 'What' field for filename

            # Skip if processing specific kind and this row doesn't match
            if specific_kind and kind.lower() != specific_kind.lower():
                continue
            
            # If we're processing podcasts, count this item for our summary
            if specific_kind and specific_kind.lower() == "podcast" or kind.lower() == "podcast":
                summary["total"] += 1

            # Create kind-specific subdirectory
            kind_dir = download_dir / sanitize_filename(kind.lower())
            kind_dir.mkdir(parents=True, exist_ok=True)

            # If 'What' field is empty, use a fallback naming strategy
            if not what:
                what = f"{kind}_{sanitize_filename(url)}"

            if not url:  # Skip empty URL
                print(f"Skipping empty URL for kind {kind}.")
                continue

            # Check if already processed - only if not processing a specific kind
            state_key = f"{url}_{kind}_{subkind}"  # Include SubKind in state key
            if not specific_kind and state.get(state_key):
                print(f"Skipping {url} as it has already been processed.")
                if kind.lower() == "podcast":
                    summary["skipped"] += 1
                continue

            source_path = Path(url)

            if source_path.exists():
                try:
                    if source_path.is_file():
                        shutil.copy(source_path, kind_dir / source_path.name)
                        print(f"Copied file {source_path} to {kind_dir}")
                    elif source_path.is_dir():
                        for file in source_path.iterdir():
                            if file.is_file():
                                shutil.copy(file, kind_dir / file.name)
                        print(f"Copied all files from {source_path} to {kind_dir}")
                except Exception as e:
                    print(f"Error copying files from {source_path}: {e}")
                
                # Always update state regardless of specific_kind
                state[state_key] = {"url": url, "kind": kind, "subkind": subkind}
                save_state(state_file, state)
                continue

            if kind == "file":
                print(f"Skipping processing for kind 'file'. Only copying was performed.")
                continue

            processor_script = Path(f"processors/{kind}_processor.py")
            if processor_script.exists():
                try:
                    print(f"Processing {url} with kind {kind} and subkind {subkind}...")
                    
                    # Set default subkind for podcast processor if it's empty
                    effective_subkind = subkind
                    if kind.lower() == "podcast" and not subkind:
                        effective_subkind = "episode"
                        print(f"Using default subkind 'episode' for podcast URL: {url}")
                    
                    # Pass the kind_dir instead of download_dir to the processor
                    subprocess.run(
                        [sys.executable, str(processor_script), url, str(kind_dir), effective_subkind],
                        check=True
                    )
                    print(f"Successfully processed {url}.")
                    
                    # For podcasts, count successful processing
                    if kind.lower() == "podcast":
                        summary["successful"] += 1
                    
                    # Always update state regardless of specific_kind
                    state[state_key] = {"url": url, "kind": kind, "subkind": subkind}
                    save_state(state_file, state)
                except subprocess.CalledProcessError as e:
                    print(f"Error processing {url} with kind {kind}: {e}")
                    # For podcasts, track failures
                    if kind.lower() == "podcast":
                        summary["failed"] += 1
                        summary["failed_urls"].append(url)
            else:
                # Instead of just skipping, create a JSON file with all fields from the CSV
                print(f"No processor found for kind {kind}. Creating JSON file for later processing.")
                
                # Create a valid filename from the 'What' field (replace all punctuation)
                json_filename = f"{sanitize_filename(what)}.json"
                json_file_path = kind_dir / json_filename
                
                # Save all fields from the CSV row to the JSON file
                with open(json_file_path, 'w', encoding='utf-8') as f:
                    json.dump(row, f, indent=4)
                    
                print(f"Created JSON file: {json_file_path}")
                
                # Always update state regardless of specific_kind
                state[state_key] = {"url": url, "kind": kind, "subkind": subkind}
                save_state(state_file, state)
    
    # Display summary after processing if we were handling podcasts
    if specific_kind and specific_kind.lower() == "podcast" or summary["total"] > 0:
        print("\n" + "="*50)
        print("PODCAST PROCESSING SUMMARY")
        print("="*50)
        print(f"Total podcasts processed: {summary['total']}")
        print(f"Successfully processed:   {summary['successful']}")
        print(f"Failed to process:        {summary['failed']}")
        print(f"Skipped (already processed): {summary['skipped']}")
        
        if summary["failed"] > 0:
            print("\nFailed podcast URLs:")
            for url in summary["failed_urls"]:
                print(f"  • {url}")
        
        print("="*50)

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: build.py <author> [kind]")
        print("  - author: The author name to process content for")
        print("  - kind (optional): Process only content of this specific kind")
        sys.exit(1)

    author_name = sys.argv[1]
    specific_kind = sys.argv[2] if len(sys.argv) == 3 else None
    
    if specific_kind:
        print(f"Building {specific_kind} content for author: {author_name} (ignoring state checks for processing)")
    else:
        print(f"Building all content for author: {author_name}")

    try:
        process_author(author_name, specific_kind)
    except Exception as e:
        print(f"An error occurred while processing author {author_name}: {e}")
