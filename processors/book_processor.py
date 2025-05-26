"""
PDF Processor Script

Purpose:
This script downloads a PDF from a specified URL, extracts selected page ranges, extracts text content
from the page subsets, and saves both the extracted PDF pages and text content to separate files.
After extraction, the original downloaded file is deleted to save space.

Development Context:
- Originally only extracted page ranges from PDFs
- Enhanced to also extract text content for MCP resource generation
- Text extraction works on the specified page ranges, not the entire PDF
- Text extraction supports the preprocessing pipeline for content analysis
- Maintains backward compatibility with existing page range functionality

Key Design Choices:
- Uses `requests` to download the PDF from a given URL.
- Extracts specified page ranges based on user input.
- Extracts text content only from the specified page ranges for content analysis.
- Saves the extracted content in both PDF and text formats.
- Automatically deletes the downloaded PDF file after extraction to prevent clutter.

Important Considerations:
- Page ranges must be provided in a valid format (e.g., "1-4,8-22,83-").
- A trailing '-' in the range means including pages until the end.
- Invalid page numbers are skipped with a warning.
- Text extraction handles encoding issues and empty pages gracefully.
- Text extraction works only on the specified page subset, not the entire PDF.
- Requires `PyPDF2` for handling PDFs.

This instruction block should always be included at the top of the script to maintain context for future modifications.
"""

import sys
import re
import requests
import os
from PyPDF2 import PdfReader, PdfWriter

def download_pdf(url, download_dir):
    """
    Downloads a PDF from the given URL and saves it to the specified directory.
    """
    response = requests.get(url)
    if response.status_code == 200:
        filename = os.path.join(download_dir, os.path.basename(url))
        with open(filename, 'wb') as f:
            f.write(response.content)
        return filename
    else:
        raise ValueError(f"Failed to download PDF: {response.status_code}")

def extract_text_from_pdf_pages(pdf_path, page_indices):
    """
    Extracts text content from specific pages of the PDF and returns it as a string.
    """
    try:
        reader = PdfReader(pdf_path)
        text_content = []
        
        for page_index in page_indices:
            if 0 <= page_index < len(reader.pages):
                page = reader.pages[page_index]
                page_text = page.extract_text()
                if page_text.strip():  # Only add non-empty pages
                    text_content.append(page_text)
        
        full_text = '\n\n'.join(text_content)
        return full_text.strip() if full_text.strip() else None
        
    except Exception as e:
        print(f"Error extracting text from PDF {pdf_path}: {e}")
        return None

def save_text_content(pdf_path, text_content, ranges):
    """
    Saves the extracted text content to a text file.
    """
    if not text_content:
        print("No text content to save.")
        return
    
    # Create text filename based on PDF filename
    stem = os.path.splitext(os.path.basename(pdf_path))[0]
    text_path = os.path.join(os.path.dirname(pdf_path), f"{stem}.txt")
    
    try:
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
        print(f"Text content from pages {ranges} saved to {text_path}")
        return text_path
    except Exception as e:
        print(f"Error saving text content: {e}")
        return None

def parse_ranges(ranges, total_pages):
    """
    Parses the given range string and returns a list of page indices.
    Supports individual pages, ranges (e.g., 1-4), and open-ended ranges (e.g., 83-).
    """
    pages = []
    for part in ranges.split(','):
        match = re.match(r'^(\d+)(?:-(\d*)?)?$', part)
        if not match:
            raise ValueError(f"Invalid range format: {part}")
        start = int(match.group(1)) - 1  # Convert to zero-based index
        end = match.group(2)
        if end is None:
            pages.append(start)
        elif end == "":
            pages.extend(range(start, total_pages))  # Include all remaining pages
        else:
            pages.extend(range(start, int(end)))
    return pages

def extract_pages(pdf_path, ranges):
    """
    Extracts the specified page ranges from the given PDF file and saves them to a new PDF.
    Returns the list of page indices that were extracted.
    """
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    pages = parse_ranges(ranges, total_pages)
    
    writer = PdfWriter()
    extracted_pages = []
    for p in pages:
        if 0 <= p < total_pages:
            writer.add_page(reader.pages[p])  # Add valid pages to the output PDF
            extracted_pages.append(p)
        else:
            print(f"Skipping invalid page number: {p+1}")
    
    # Extract the filename stem from the input PDF file
    stem = os.path.splitext(os.path.basename(pdf_path))[0]
    output_path = os.path.join(os.path.dirname(pdf_path), f"{stem}_extracted_{ranges.replace(',', '_')}.pdf")
    
    with open(output_path, "wb") as out_file:
        writer.write(out_file)
    
    print(f"Extracted pages saved to {output_path}")
    return extracted_pages

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python book_processor.py <url> <download_dir> <ranges>")
        sys.exit(1)
    
    url = sys.argv[1]  # URL of the PDF file
    download_dir = sys.argv[2]  # Directory to save the downloaded PDF
    ranges = sys.argv[3]  # Page ranges specified as a string
    
    try:
        # Download the PDF
        pdf_path = download_pdf(url, download_dir)
        print(f"Downloaded PDF to {pdf_path}")
        
        # Extract specified page ranges first
        print(f"Extracting page ranges: {ranges}")
        extracted_page_indices = extract_pages(pdf_path, ranges)
        
        # Extract text content from the specified page ranges only
        print(f"Extracting text content from pages {ranges}...")
        text_content = extract_text_from_pdf_pages(pdf_path, extracted_page_indices)
        if text_content:
            save_text_content(pdf_path, text_content, ranges)
            print(f"Successfully extracted {len(text_content)} characters of text from specified pages")
        else:
            print("No text content could be extracted from the specified pages")
        
        # Remove the downloaded file after extraction
        os.remove(pdf_path)
        print(f"Deleted downloaded file: {pdf_path}")
        
    except Exception as e:
        print(f"Error processing PDF: {e}")
        sys.exit(1)
