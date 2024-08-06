import os
import csv
import json
import subprocess
from pathlib import Path

# Constants
DOWNLOADS_DIR = "downloads"
AUTHORS_DIR = "authors"
STATE_FILENAME = "state.json"

def load_state(author):
    """
    Load the state.json file for a given author.

    :param author: The author's name.
    :return: A dictionary representing the state.
    """
    state_path = Path(DOWNLOADS_DIR) / author / STATE_FILENAME
    if state_path.exists():
        with open(state_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"processed": []}

def save_state(author, state):
    """
    Save the state.json file for a given author.

    :param author: The author's name.
    :param state: A dictionary representing the state.
    """
    state_path = Path(DOWNLOADS_DIR) / author / STATE_FILENAME
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)

def process_content(author, kind, url):
    """
    Process content by calling the appropriate processor script.

    :param author: The author's name.
    :param kind: The type of content.
    :param url: The URL of the content.
    :return: Boolean indicating if processing was successful.
    """
    # Processor script based on content type
    processor_script = f"processors/{kind}_processor.py"
    
    # Check if the processor script exists
    if not Path(processor_script).exists():
        print(f"Processor for content type '{kind}' not found.")
        return False  # Indicate failure
    
    # Author's download directory
    author_download_dir = Path(DOWNLOADS_DIR) / author
    
    # Execute the processor script
    command = ["python", processor_script, url, str(author_download_dir)]
    result = subprocess.run(command)
    
    return result.returncode == 0

def main(author):
    """
    Main function to process published content for a given author.

    :param author: The author's name.
    """
    # Path to author's published content CSV
    csv_path = Path(AUTHORS_DIR) / author / "published_content.csv"
    
    # Load the current state
    state = load_state(author)
    
    # Ensure the downloads directory exists
    author_download_dir = Path(DOWNLOADS_DIR) / author
    author_download_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each row in the CSV
    with open(csv_path, "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            url = row.get("URL")
            kind = row.get("Kind")

            # Skip if URL is blank or already processed
            if not url:
                print(f"Skipping blank URL in CSV row.")
                continue

            if url in state["processed"]:
                print(f"Skipping already processed URL: {url}")
                continue
            
            print(f"Processing {kind} from {url}...")
            try:
                # Process the content
                success = process_content(author, kind, url)
                
                if success:
                    # Update the state only if processing was successful
                    state["processed"].append(url)
                    save_state(author, state)
                    print(f"Successfully processed {kind} from {url}")
                else:
                    print(f"Failed to process {kind} from {url}: Processor not found.")
            
            except Exception as e:
                print(f"Failed to process {kind} from {url}: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: build.py <author>")
        sys.exit(1)

    author = sys.argv[1]
    main(author)
