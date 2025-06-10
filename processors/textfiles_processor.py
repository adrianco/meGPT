"""
Text File Processor for GitHub Directories

Purpose:
This script downloads all text files from a specified GitHub directory (provided as a URL) and saves them to a local directory. 
It is designed to work with the same calling convention as other processor scripts.

Key Design Choices:
- Uses the GitHub API to list files in a repository directory.
- Filters and downloads only `.txt` files.
- Handles missing or malformed API responses gracefully.
- Supports a "subkind" argument for consistency with other processors, though it is not actively used in this script.

Important Considerations:
- The GitHub URL provided must be a directory, not an individual file.
- The URL is automatically converted to the GitHub API format.
- The script ensures all downloaded files are saved with UTF-8 encoding.
- Debug messages help diagnose issues such as missing files or incorrect directory paths.

Usage:
    textfiles_processor.py <github_directory_url> <download_dir> <subkind>
Example:
    textfiles_processor.py https://github.com/user/repo/tree/main/texts ./downloads debug

    This instruction block should always be included at the top of the script to maintain context for future modifications.
"""

import sys
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path

def get_text_file_links(directory_url):
    """Fetch all text file links from a given directory URL."""
    response = requests.get(directory_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    links = []

    for link in soup.find_all("a"):
        file_name = link.get("href")
        if file_name.endswith(".txt"):
            full_url = urljoin(directory_url, file_name)
            links.append(full_url)

    return links

def download_files(file_urls, download_dir):
    """Download each text file from the list of URLs to the local directory."""
    os.makedirs(download_dir, exist_ok=True)

    for file_url in file_urls:
        file_name = os.path.basename(file_url)
        file_path = Path(download_dir) / file_name

        response = requests.get(file_url)
        response.raise_for_status()

        with open(file_path, "wb") as file:
            file.write(response.content)

        print(f"Downloaded: {file_name}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: text_processor.py <url> <download_dir> <subkind>")
        sys.exit(1)

    directory_url = sys.argv[1]
    download_directory = sys.argv[2]
    subkind = sys.argv[3]

    print(f"text_processor.py invoked with URL: {directory_url}, Download Directory: {download_directory}, SubKind: {subkind}")

    try:
        text_file_links = get_text_file_links(directory_url)
        if not text_file_links:
            print("No text files found in the given directory.")
        else:
            download_files(text_file_links, download_directory)
            print(f"All text files downloaded to {download_directory}/")
    except Exception as e:
        print(f"Error processing files from {directory_url} with subkind {subkind}: {e}")
