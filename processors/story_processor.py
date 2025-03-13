import sys
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from fpdf import FPDF

def sanitize_filename(title):
    """Sanitize the title to create a valid filename."""
    return title.replace(" ", "_").replace("/", "-").replace("\\", "-").replace(":", "-")

def download_story(url, download_dir, subkind=None):
    """
    Download a story from the given URL and save the processed content.
    
    If a subkind (div ID) is provided, extract content from that section.
    Otherwise, process the entire page into a PDF.
    """
    print(f"Starting download from URL: {url} with subkind: {subkind}")

    # Fetch the page content
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to download the story: {e}")
        return

    # Parse with BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Determine filename
    story_title = soup.title.string.strip() if soup.title else "story"
    filename_base = sanitize_filename(story_title)
    output_path = Path(download_dir) / filename_base

    if subkind:
        # Extract the specific div content
        story_div = soup.find('div', id=subkind)
        if not story_div:
            print(f"Could not find the story content in div with id: {subkind}.")
            return

        # Extract relevant text elements
        content_tags = story_div.find_all(['p', 'h1', 'h2', 'blockquote', 'li'])
        text_chunks = [f"[URL]: {url}\n"]

        for tag in content_tags:
            text = tag.get_text(separator=" ", strip=True)
            if text:
                text_chunks.append(text)

        # Save as a text file
        text_content = "\n\n".join(text_chunks)
        text_filepath = output_path.with_suffix(".txt")

        # Ensure UTF-8 encoding to prevent character errors
        with open(text_filepath, "w", encoding="utf-8") as f:
            f.write(text_content)

        print(f"Story saved to {text_filepath}")

    else:
        # No subkind provided, process the entire webpage into a PDF
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Extract text from body
        body_text = soup.get_text(separator="\n", strip=True)
        body_text = body_text.encode("utf-8", "ignore").decode("utf-8")  # Ensures safe encoding

        for line in body_text.split("\n"):
            if line.strip():
                pdf.cell(200, 10, txt=line.encode("latin-1", "ignore").decode("latin-1"), ln=True)

        pdf_filepath = output_path.with_suffix(".pdf")
        pdf.output(str(pdf_filepath))

        print(f"Entire webpage saved as PDF to {pdf_filepath}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: story_processor.py <url> <download_dir> [subkind]")
        sys.exit(1)

    story_url = sys.argv[1]
    download_directory = sys.argv[2]
    story_subkind = sys.argv[3] if len(sys.argv) > 3 else None  # Make subkind optional

    print(f"story_processor.py invoked with URL: {story_url}, Download Directory: {download_directory}, SubKind: {story_subkind}")

    try:
        download_story(story_url, download_directory, story_subkind)
    except Exception as e:
        print(f"Error processing story from {story_url} with subkind {story_subkind}: {e}")
