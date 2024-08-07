import sys
import subprocess
from pathlib import Path

def process_content(author, kind, url):
    """
    Process content using the appropriate processor script.

    :param author: The author's name.
    :param kind: The type of content.
    :param url: The URL of the content.
    """
    # Construct the path to the processor script
    processor_script = Path("processors") / f"{kind}_processor.py"
    
    # Check if the processor script exists
    if not processor_script.exists():
        print(f"Processor script for '{kind}' not found at {processor_script}.")
        return

    # Construct the author's download directory
    author_download_dir = Path("downloads") / author
    author_download_dir.mkdir(parents=True, exist_ok=True)

    # Execute the processor script
    command = ["python", str(processor_script), url, str(author_download_dir)]
    print(f"Executing command: {' '.join(command)}")  # Debug statement

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Successfully processed {kind} from {url}")
        print(f"Output:\n{result.stdout}")
        if result.stderr:
            print(f"Warnings:\n{result.stderr}")
    except subprocess.CalledProcessError as e:
        print(f"Error processing {kind} from {url}: {e}")
        print(f"Output:\n{e.output}")
        print(f"Error Message:\n{e.stderr}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: process.py <author> <Kind> <URL>")
        sys.exit(1)

    author = sys.argv[1]
    kind = sys.argv[2].lower()  # Ensure kind is in lowercase
    url = sys.argv[3]

    process_content(author, kind, url)
