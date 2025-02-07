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
    """
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    pages = parse_ranges(ranges, total_pages)
    
    writer = PdfWriter()
    for p in pages:
        if 0 <= p < total_pages:
            writer.add_page(reader.pages[p])  # Add valid pages to the output PDF
        else:
            print(f"Skipping invalid page number: {p+1}")
    
    # Extract the filename stem from the input PDF file
    stem = os.path.splitext(os.path.basename(pdf_path))[0]
    output_path = os.path.join(os.path.dirname(pdf_path), f"{stem}_extracted_{ranges.replace(',', '_')}.pdf")
    
    with open(output_path, "wb") as out_file:
        writer.write(out_file)
    
    print(f"Extracted pages saved to {output_path}")
    
    # Remove the downloaded file after extraction
    os.remove(pdf_path)
    print(f"Deleted downloaded file: {pdf_path}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python pdf_processor.py <url> <download_dir> <ranges>")
        sys.exit(1)
    
    url = sys.argv[1]  # URL of the PDF file
    download_dir = sys.argv[2]  # Directory to save the downloaded PDF
    ranges = sys.argv[3]  # Page ranges specified as a string
    
    pdf_path = download_pdf(url, download_dir)
    extract_pages(pdf_path, ranges)
