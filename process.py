import os
import sys
import importlib

# Constants for directories
DOWNLOADS_DIR = "downloads"
PROCESSORS_DIR = "processors"

def process_content(content_type, url, author_name):
    """
    Dynamically import and execute the appropriate processor script.
    
    :param content_type: The content type to process (e.g., 'article', 'image', 'video').
    :param url: The URL of the content to be processed.
    :param author_name: The author associated with the content.
    """
    try:
        # Dynamically import the processor module based on content type
        processor_module = importlib.import_module(f'{PROCESSORS_DIR}.{content_type}_processor')
        
        # Check if the processor module has a 'process' function
        if hasattr(processor_module, 'process'):
            # Call the process function from the module, passing the URL and author's downloads directory
            processor_module.process(url, os.path.join(DOWNLOADS_DIR, author_name))
            print(f"Processed URL {url} as {content_type} for author {author_name}")
        else:
            print(f"Processor for '{content_type}' does not have a 'process' function.")
    except ModuleNotFoundError:
        print(f"No processor found for content type: {content_type}")
    except Exception as e:
        print(f"Error processing URL {url}: {e}")

def main(author_name, content_type, url):
    """
    Main function to process a single URL for a specific author.
    
    :param author_name: The name of the author.
    :param content_type: The type of content to process (e.g., 'article', 'image').
    :param url: The URL to process.
    """
    # Ensure the author's downloads directory exists
    author_downloads_dir = os.path.join(DOWNLOADS_DIR, author_name)
    os.makedirs(author_downloads_dir, exist_ok=True)
    
    # Process the content using the appropriate processor
    process_content(content_type, url, author_downloads_dir)

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python process.py <author> <Kind> <URL>")
        sys.exit(1)

    author_name = sys.argv[1]
    content_type = sys.argv[2]
    url = sys.argv[3]

    main(author_name, content_type, url)
