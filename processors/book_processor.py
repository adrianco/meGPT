import sys
import requests
from pdf2image import convert_from_path
import pytesseract
from PyPDF2 import PdfReader, PdfWriter
from pathlib import Path
import re

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
    toc_end_regex = re.compile(r'\b(Index|Glossary|Appendix|Figures?)\b', re.IGNORECASE)
    
    # Recognize different sections
    sections = ["Foreword", "Preface", "Chapter", "Appendix"]
    section_regex = re.compile(r'({})'.format('|'.join(sections)), re.IGNORECASE)

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
                match = re.match(r'(Foreword|Preface|Chapter\s+\d+|Appendix\s+[A-Z]|[\d\.]+)\s+(\w.*)\s+(\d+)$', line.strip())
                if match:
                    section_name = match.group(1).strip()
                    chapter_title = match.group(2).strip()
                    logical_page_number = int(match.group(3).strip())
                    chapter_mapping.append((section_name, chapter_title, logical_page_number))
                    print(f"Detected in TOC: {section_name} titled '{chapter_title}' starting on logical page {logical_page_number}")
            
            if toc_end_regex.search(text):
                toc_end_page = i
                print(f"End of ToC identified as {toc_end_regex.search(text).group(0)} on page {i + 1}")
                break

    if toc_end_page is None:
        toc_end_page = toc_start_page  # If no end found, assume ToC is on a single page

    return chapter_mapping, toc_start_page, toc_end_page

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

def perform_ocr_on_images(images):
    ocr_results = []
    for i, image in enumerate(images):
        print(f"Performing OCR on page {i + 1}/{len(images)}...")
        try:
            text = pytesseract.image_to_string(image, lang='eng', timeout=30)
            ocr_results.append(text)
        except RuntimeError as timeout_error:
            print(f"Skipping page {i + 1} due to timeout: {timeout_error}")
            ocr_results.append("")
    return ocr_results

def detect_chapter_starts(ocr_results, chapter_mapping):
    chapter_start_pages = {}

    for i, text in enumerate(ocr_results):
        # Extract the last line for logical page number
        last_line = text.splitlines()[-1] if text.splitlines() else ""
        logical_page_number_match = re.search(r'\b\d+\b', last_line)

        if logical_page_number_match:
            logical_page_number = int(logical_page_number_match.group(0))

            for section_name, title, logical_page_in_toc in chapter_mapping:
                # Check if this page has the correct chapter title and logical page number
                if (title.lower() in text.lower() or f"{section_name} {title}".lower() in text.lower()) and logical_page_number == logical_page_in_toc:
                    print(f"Found '{section_name}: {title}' on OCR page {i + 1} (corresponding logical page: {logical_page_number})")
                    chapter_start_pages[title] = (i, logical_page_number)
                    break

    return chapter_start_pages

def extract_and_save_chapters(pdf_path, download_dir, chapter_mapping, chapter_start_pages, toc_end_page):
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)

    book_name = Path(pdf_path).stem
    book_dir = Path(download_dir) / book_name
    book_dir.mkdir(parents=True, exist_ok=True)

    sorted_chapters = sorted(chapter_start_pages.items(), key=lambda x: x[1][0])

    for i, (title, (start_ocr_page, logical_start_page)) in enumerate(sorted_chapters):
        start_actual_page = toc_end_page + start_ocr_page  # Adjust OCR page to actual page in PDF
        end_actual_page = toc_end_page + sorted_chapters[i + 1][1][0] if i + 1 < len(sorted_chapters) else total_pages

        writer = PdfWriter()
        for page_num in range(start_actual_page, end_actual_page):
            writer.add_page(reader.pages[page_num])

        chapter_number = next((cn for cn, t, _ in chapter_mapping if t == title), None)
        sanitized_title = re.sub(r'[\\/*?:"<>|]', "_", title)
        output_pdf_path = book_dir / f"{chapter_number}_{sanitized_title}.pdf"
        
        with open(output_pdf_path, "wb") as f:
            writer.write(f)

        print(f"Saved chapter '{title}' (Section {chapter_number}) from actual pages {start_actual_page + 1}-{end_actual_page} to {output_pdf_path}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: book_processor.py <url> <download_dir> <subkind>")
        sys.exit(1)

    book_url = sys.argv[1]
    download_directory = sys.argv[2]
    subkind = sys.argv[3]

    print(f"book_processor.py invoked with URL: {book_url}, Download Directory: {download_directory}, SubKind: {subkind}")

    try:
        pdf_file_path = download_pdf(book_url, download_directory)
        chapter_mapping, toc_start_page, toc_end_page = find_toc_and_chapters(pdf_file_path)
        
        print(f"Table of Contents found from page {toc_start_page + 1} to {toc_end_page + 1}")
        save_toc(pdf_file_path, download_directory, toc_start_page, toc_end_page)

        images = convert_from_path(pdf_file_path, dpi=150, first_page=toc_end_page + 1)
        ocr_results = perform_ocr_on_images(images)

        chapter_start_pages = detect_chapter_starts(ocr_results, chapter_mapping)
        if chapter_start_pages:
            extract_and_save_chapters(pdf_file_path, download_directory, chapter_mapping, chapter_start_pages, toc_end_page)
        else:
            print("No chapters found in OCR results.")
            
    except Exception as e:
        print(f"Error processing book from {book_url} with subkind {subkind}: {e}")
