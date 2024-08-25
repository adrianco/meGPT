import sys
import requests
from PyPDF2 import PdfReader, PdfWriter
from pathlib import Path
import re
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
import os

def download_pdf(url, download_dir):
    response = requests.get(url, stream=True)
    response.raise_for_status()

    filename = url.split("/")[-1]
    file_path = Path(download_dir) / filename

    with open(file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return file_path

def find_toc_and_chapters(pdf_path):
    reader = PdfReader(pdf_path)
    toc_found = False
    chapter_mapping = []
    toc_start_page = None
    toc_end_page = None

    toc_regex = re.compile(r'(contents?|table\s+of\s+contents?)', re.IGNORECASE)
    chapter_regex = re.compile(r'^\s*(chapter|CHAPTER)\s+\d+', re.IGNORECASE)
    toc_end_regex = re.compile(r'\b(Index|Glossary|Appendix|Figures?)\b', re.IGNORECASE)

    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if not text:
            continue
        
        if toc_regex.search(text) and not toc_found:
            toc_found = True
            toc_start_page = i
            print(f"Table of Contents starts on page {i + 1}")

        if toc_found:
            lines = text.split('\n')
            for line in lines:
                match = re.match(r'(Chapter\s+\d+|[\d\.]+|Appendix\s+[A-Z])\s+(\w.*)\s+(\d+)$', line.strip())
                if match:
                    section_name = match.group(1).strip()
                    section_title = match.group(2).strip()
                    logical_page_number = int(match.group(3).strip())
                    chapter_mapping.append((section_name, section_title, logical_page_number))
            
            if toc_end_regex.search(text):
                toc_end_page = i
                print(f"End of ToC identified as {toc_end_regex.search(text).group(0)} on page {i + 1}")
                break

    if toc_end_page is None:
        toc_end_page = toc_start_page  # If no end found, assume ToC is on a single page

    # Log TOC contents
    print("\nTOC Chapter and Appendix Mapping:")
    for section_name, section_title, logical_page_number in chapter_mapping:
        print(f"{section_name}: {section_title} (Logical Page: {logical_page_number})")

    return chapter_mapping, toc_start_page, toc_end_page

def perform_ocr_on_images(images):
    ocr_results = []
    for i, image in enumerate(images):
        text = pytesseract.image_to_string(image)
        ocr_results.append(text)
        print(f"OCR completed for page {i + 1}")
    return ocr_results

def detect_chapter_and_appendix_starts(ocr_results, chapter_mapping):
    section_start_pages = {}
    last_detected_section = None

    for i, text in enumerate(ocr_results):
        # Extract the last line for logical page number
        last_line = text.splitlines()[-1] if text.splitlines() else ""
        logical_page_number_match = re.search(r'\b\d+\b', last_line)

        if logical_page_number_match:
            logical_page_number = int(logical_page_number_match.group(0))

            for section_name, title, logical_page_in_toc in chapter_mapping:
                # Broaden the search to include variations and case insensitivity
                title_pattern = re.escape(title)
                full_title_pattern = re.compile(rf"({section_name}\s+{title_pattern}|{title_pattern})", re.IGNORECASE)

                # Check if this page has the correct chapter title and logical page number
                if full_title_pattern.search(text) and logical_page_number == logical_page_in_toc:
                    if title not in section_start_pages:
                        print(f"Found '{section_name}: {title}' on OCR page {i + 1} (corresponding logical page: {logical_page_number})")
                        section_start_pages[title] = (i, logical_page_number)
                        last_detected_section = title
                    break

            # Stop searching for the last detected section once the next section is found
            if last_detected_section and title == last_detected_section:
                last_detected_section = None

    # Log sections not found, including appendices
    for section_name, title, _ in chapter_mapping:
        if title not in section_start_pages:
            print(f"Warning: Section '{section_name}: {title}' not detected in OCR.")

    return section_start_pages

def save_toc(pdf_path, download_dir, toc_start_page, toc_end_page):
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    for page_num in range(toc_start_page, toc_end_page + 1):
        writer.add_page(reader.pages[page_num])

    book_name = Path(pdf_path).stem
    toc_pdf_path = Path(download_dir) / f"{book_name}_ToC.pdf"

    with open(toc_pdf_path, "wb") as f:
        writer.write(f)

    print(f"Saved Table of Contents to {toc_pdf_path}")

def extract_and_save_sections(pdf_path, download_dir, section_start_pages, toc_end_page):
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)

    book_name = Path(pdf_path).stem
    book_dir = Path(download_dir) / book_name
    book_dir.mkdir(parents=True, exist_ok=True)

    section_titles = list(section_start_pages.keys())
    for i, title in enumerate(section_titles):
        actual_start_page, _ = section_start_pages[title]

        # Determine the end page
        next_title = section_titles[i + 1] if i + 1 < len(section_titles) else None
        actual_end_page = section_start_pages[next_title][0] - 1 if next_title else total_pages - toc_end_page - 1

        writer = PdfWriter()
        for page_num in range(actual_start_page + toc_end_page, actual_end_page + toc_end_page):
            writer.add_page(reader.pages[page_num])

        sanitized_title = re.sub(r'[\\/*?:"<>|]', "_", title)
        output_pdf_path = book_dir / f"{i+1}_{sanitized_title}.pdf"
        
        with open(output_pdf_path, "wb") as f:
            writer.write(f)

        print(f"Saved section '{title}' (Pages {actual_start_page + 1} - {actual_end_page + 1}) to {output_pdf_path}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: book_processor.py <url> <download_dir> <subkind>")
        sys.exit(1)

    book_url = sys.argv[1]
    download_directory = sys.argv[2]
    subkind = sys.argv[3]

    print(f"book_processor.py invoked with URL: {book_url}, Download Directory: {download_directory}, SubKind: {subkind}")

    try:
        # Download the PDF
        pdf_file_path = download_pdf(book_url, download_directory)

        # Find TOC and Chapters
        chapter_mapping, toc_start_page, toc_end_page = find_toc_and_chapters(pdf_file_path)
        save_toc(pdf_file_path, download_directory, toc_start_page, toc_end_page)

        # Convert PDF to images and perform OCR
        images = convert_from_path(pdf_file_path, first_page=toc_end_page + 2)  # Start after the TOC
        ocr_results = perform_ocr_on_images(images)

        # Detect Chapters and Appendices Starts
        section_start_pages = detect_chapter_and_appendix_starts(ocr_results, chapter_mapping)

        # Extract and Save Chapters and Appendices
        extract_and_save_sections(pdf_file_path, download_directory, section_start_pages, toc_end_page)

    except Exception as e:
        print(f"Error processing book from {book_url} with subkind {subkind}: {e}")
