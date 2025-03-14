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

Important Considerations:
- The script must correctly determine which processor to use based on file type or user input.
- Network failures or missing resources should not halt the entire process.
- Processing logic may need to be extended to support new content types in the future.
- The script should maintain compatibility with the overall system's workflow and expected outputs.

Usage:
    build.py <source_url_or_path> <output_dir> <subkind>
Example:
    build.py https://example.com/content/ ./output debug

Instruction:
This comment provides essential context for the script. If this script is used in a new chat session, 
this comment should be retained to preserve understanding without needing prior conversation.
"""

import os
import sys
import csv
import shutil
import json
import subprocess  # Added import
from pathlib import Path

def load_state(state_file):
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            return json.load(f)
    return {}

def save_state(state_file, state):
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=4)

def process_author(author):
    # Define paths
    author_dir = Path(f"authors/{author}")
    download_dir = Path(f"downloads/{author}")
    state_file = author_dir / "state.json"
    content_csv = author_dir / "published_content.csv"

    # Ensure directories exist
    download_dir.mkdir(parents=True, exist_ok=True)

    # Load previous state
    state = load_state(state_file)

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

            if not url:  # Skip empty URL
                print(f"Skipping empty URL for kind {kind}.")
                continue

            # Check if already processed
            state_key = f"{url}_{kind}_{subkind}"  # Include SubKind in state key
            if state.get(state_key):
                print(f"Skipping {url} as it has already been processed.")
                continue

            source_path = Path(url)

            if source_path.exists():
                try:
                    if source_path.is_file():
                        shutil.copy(source_path, download_dir / source_path.name)
                        print(f"Copied file {source_path} to {download_dir}")
                    elif source_path.is_dir():
                        for file in source_path.iterdir():
                            if file.is_file():
                                shutil.copy(file, download_dir / file.name)
                        print(f"Copied all files from {source_path} to {download_dir}")
                except Exception as e:
                    print(f"Error copying files from {source_path}: {e}")
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
                    subprocess.run(
                        [sys.executable, str(processor_script), url, str(download_dir), subkind],
                        check=True
                    )
                    print(f"Successfully processed {url}.")
                    state[state_key] = {"url": url, "kind": kind, "subkind": subkind}
                    save_state(state_file, state)
                except subprocess.CalledProcessError as e:
                    print(f"Error processing {url} with kind {kind}: {e}")
            else:
                print(f"No processor found for kind {kind}. Skipping.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: build.py <author>")
        sys.exit(1)

    author_name = sys.argv[1]
    print(f"Building content for author: {author_name}")

    try:
        process_author(author_name)
    except Exception as e:
        print(f"An error occurred while processing author {author_name}: {e}")
