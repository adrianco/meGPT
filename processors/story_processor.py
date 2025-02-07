import sys
import requests
from bs4 import BeautifulSoup
from pathlib import Path

def download_story(url, download_dir, subkind):
    """
    Download a story from the given URL and save the processed content as paragraphs with proper spacing.

    :param url: The URL of the story.
    :param download_dir: The directory to save the downloaded story.
    :param subkind: The subkind (name of the div) to extract the content.
    """
    print(f"Starting download from URL: {url} with subkind: {subkind}")

    # Fetch the story content
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to download the story: {e}")
        return

    # Parse the content with BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract the story text from the specified div
    story_div = soup.find('div', id=subkind)
    if story_div is None:
        print(f"Could not find the story content in div with id: {subkind}.")
        return

    # Extract all elements that might contain relevant content
    content_tags = story_div.find_all(['p', 'h1', 'h2', 'blockquote', 'li'])

    # List to hold each piece of text separately
    text_chunks = [f"[URL]: {url}\n"]

    for tag in content_tags:
        # Extract text from each tag
        text = tag.get_text(separator=" ", strip=True)
        
        # Only add non-empty text to the list
        if text:
            text_chunks.append(text)

    # Join text chunks with two newlines between paragraphs
    story_content = "\n\n".join(text_chunks)

    # Use the title as a filename, sanitize it
    story_title = soup.title.string if soup.title else "story"
    text_filename = f"{story_title}.txt".replace(" ", "_").replace("/", "-")
    story_filepath = Path(download_dir) / text_filename

    # Save the story text
    with open(story_filepath, "w", encoding="utf-8") as f:
        f.write(story_content)

    print(f"Story downloaded and saved to {story_filepath}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: story_processor.py <url> <download_dir> <subkind>")
        sys.exit(1)

    story_url = sys.argv[1]
    download_directory = sys.argv[2]
    story_subkind = sys.argv[3]

    print(f"story_processor.py invoked with URL: {story_url}, Download Directory: {download_directory}, SubKind: {story_subkind}")

    try:
        download_story(story_url, download_directory, story_subkind)
    except Exception as e:
        print(f"Error processing story from {story_url} with subkind {story_subkind}: {e}")
