import sys
import requests
from bs4 import BeautifulSoup
from pathlib import Path

def download_story(url, download_dir):
    """
    Download a story from the given URL and save the processed content.

    :param url: The URL of the story.
    :param download_dir: The directory to save the downloaded story.
    """
    print(f"Starting download from URL: {url}")

    # Fetch the story content
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to download the story: {e}")
        return

    # Parse the content with BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract the story text (customize the extraction logic as needed)
    story_title = soup.title.string if soup.title else "story"
    story_content = soup.get_text()

    # Create a text filename
    text_filename = f"{story_title}.txt".replace(" ", "_")
    story_filepath = Path(download_dir) / text_filename

    # Save the story text
    with open(story_filepath, "w", encoding="utf-8") as f:
        f.write(story_content)

    print(f"Story downloaded and saved to {story_filepath}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: story_processor.py <url> <download_dir>")
        sys.exit(1)

    story_url = sys.argv[1]
    download_directory = sys.argv[2]

    print(f"story_processor.py invoked with URL: {story_url} and Download Directory: {download_directory}")

    try:
        download_story(story_url, download_directory)
    except Exception as e:
        print(f"Error processing story from {story_url}: {e}")
