import sys
import os
import requests
from pathlib import Path

def download_book(url, download_dir):
    """
    Download a book from the given URL and save it to the specified directory.

    :param url: The URL of the book.
    :param download_dir: The directory to save the downloaded book.
    """
    print(f"Starting download from URL: {url}")  # Debug statement

    # Make a request to get the book
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to download the book: {e}")
        return

    # Define a file name for the book
    book_filename = os.path.basename(url) or "book.pdf"
    if not book_filename.endswith(".pdf"):
        book_filename += ".pdf"
    
    # Ensure the download directory exists
    Path(download_dir).mkdir(parents=True, exist_ok=True)
    
    # Save the book to a file
    book_filepath = Path(download_dir) / book_filename
    with open(book_filepath, "wb") as f:
        f.write(response.content)
    
    print(f"Book downloaded and saved to {book_filepath}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: book_processor.py <url> <download_dir>")
        sys.exit(1)

    book_url = sys.argv[1]
    download_directory = sys.argv[2]

    print(f"book_processor.py invoked with URL: {book_url} and Download Directory: {download_directory}")  # Debug statement

    try:
        download_book(book_url, download_directory)
    except Exception as e:
        print(f"Error processing book from {book_url}: {e}")
