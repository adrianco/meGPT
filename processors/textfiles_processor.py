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
