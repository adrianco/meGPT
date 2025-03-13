import sys
import os
import requests
from pathlib import Path

def get_github_file_list(api_url):
    """Fetch the list of text files from a GitHub directory using the API."""
    response = requests.get(api_url)
    response.raise_for_status()

    files = response.json()
    text_files = []

    for file in files:
        if isinstance(file, dict) and "download_url" in file and file["download_url"]:
            if file["name"].endswith(".txt"):
                text_files.append(file["download_url"])
        else:
            print(f"Skipping non-file entry: {file}")

    return text_files

def download_files(file_urls, download_dir):
    """Download each text file from GitHub and save it locally."""
    os.makedirs(download_dir, exist_ok=True)

    for file_url in file_urls:
        file_name = file_url.split("/")[-1]
        file_path = Path(download_dir) / file_name
        
        response = requests.get(file_url)
        response.raise_for_status()

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(response.text)
        
        print(f"Downloaded: {file_name}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: text_processor.py <github_api_url> <download_dir> <subkind>")
        sys.exit(1)

    github_api_url = sys.argv[1].replace("https://github.com/", "https://api.github.com/repos/").replace("/tree/main/", "/contents/")
    download_directory = sys.argv[2]
    subkind = sys.argv[3]

    print(f"text_processor.py invoked with API URL: {github_api_url}, Download Directory: {download_directory}, SubKind: {subkind}")

    try:
        file_urls = get_github_file_list(github_api_url)
        if not file_urls:
            print("No text files found in the specified directory.")
        else:
            download_files(file_urls, download_directory)
            print(f"All text files copied to {download_directory}/")
    except Exception as e:
        print(f"Error processing files from {github_api_url} with subkind {subkind}: {e}")
