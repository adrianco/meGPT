import sys
import subprocess
from pathlib import Path

def process_content(author, kind, subkind, url):
    """
    Process content based on author, kind, subkind, and URL.
    
    :param author: The author name
    :param kind: The kind of content
    :param subkind: The subkind of content
    :param url: The URL of the content
    """
    download_dir = Path(f"downloads/{author}")
    processor_script = Path(f"processors/{kind}_processor.py")

    if not processor_script.exists():
        print(f"No processor found for kind {kind}.")
        return

    # Ensure download directory exists
    download_dir.mkdir(parents=True, exist_ok=True)

    try:
        print(f"Processing {url} with kind {kind} and subkind {subkind} for author {author}...")
        subprocess.run(
            [sys.executable, str(processor_script), url, str(download_dir), subkind],
            check=True
        )
        print(f"Successfully processed {url} for author {author}.")
    except subprocess.CalledProcessError as e:
        print(f"Error processing {url} with kind {kind} for author {author}: {e}")

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
