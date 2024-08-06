import os
import requests

def process(url, author_downloads_dir):
    """
    Process a book PDF given its URL.
    
    :param url: The URL of the book PDF to process.
    :param author_downloads_dir: The directory to save processed content.
    """
    try:
        # Fetch the PDF from the URL
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Determine the filename from the URL
        filename = os.path.basename(url)
        
        # Save the PDF to a file
        save_path = os.path.join(author_downloads_dir, filename)
        
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        
        print(f"Book PDF downloaded and saved to {save_path}")
    
    except requests.exceptions.RequestException as e:
        print(f"Failed to download book PDF from {url}: {e}")
