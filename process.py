"""
process.py - Processes content for a given author by either copying files or invoking a processor script.

Key Features:
- Accepts an author name, content kind, subkind, and a URL or file path as input.
- If the URL is a local file, copies it to the author's "downloads" directory.
- If the URL is a local directory, copies all its files to the "downloads" directory.
- If the kind is "file", only copies the file(s) without further processing.
- If a processor script exists in "processors/" for the specified kind, executes it with the provided arguments.

Important Considerations:
- Ensure processor scripts exist in "processors/" for non-"file" kinds.
- Handles errors gracefully, logging issues instead of stopping execution.
- This script is designed to be invoked via the command line.
- Usage: `process.py <author> <kind> <subkind> <url>`

Instruction:
Keep this comment updated if modifying the script to reflect changes in behavior or functionality.
"""


import sys
import subprocess
import shutil
from pathlib import Path

def process_content(author, kind, subkind, url):
    """
    Process content based on author, kind, subkind, and URL.
    
    If the URL is a file path, copy it to the author's download directory.
    If the URL is a directory, copy all its files to the download directory.
    If the kind is "file", only copy the file(s) and do not process them.
    Otherwise, process it using the corresponding processor script.
    
    :param author: The author name
    :param kind: The kind of content
    :param subkind: The subkind of content
    :param url: The URL or file path of the content
    """
    download_dir = Path(f"downloads/{author}")
    processor_script = Path(f"processors/{kind}_processor.py")
    source_path = Path(url)

    # Ensure download directory exists
    download_dir.mkdir(parents=True, exist_ok=True)

    if source_path.exists():
        if source_path.is_file() or source_path.is_dir():
            # If URL is actually a local file path or directory, copy it
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
            return
    
    if kind == "file":
        print(f"Skipping processing for kind 'file'. Only copying was performed.")
        return
    
    if processor_script.exists():
        # Otherwise, process as usual
        try:
            print(f"Processing {url} with kind {kind} and subkind {subkind} for author {author}...")
            subprocess.run(
                [sys.executable, str(processor_script), url, str(download_dir), subkind],
                check=True
            )
            print(f"Successfully processed {url} for author {author}.")
        except subprocess.CalledProcessError as e:
            print(f"Error processing {url} with kind {kind} for author {author}: {e}")
    else:
        print(f"No processor found for kind {kind}.")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: process.py <author> <kind> <subkind> <url>")
        sys.exit(1)

    author_name = sys.argv[1]
    content_kind = sys.argv[2]
    content_subkind = sys.argv[3]
    content_url = sys.argv[4]

    print(f"process.py invoked with Author: {author_name}, Kind: {content_kind}, SubKind: {content_subkind}, URL: {content_url}")

    process_content(author_name, content_kind, content_subkind, content_url)
