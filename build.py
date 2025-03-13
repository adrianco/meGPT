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
