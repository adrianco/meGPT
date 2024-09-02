import os
import zipfile
import sys
from pathlib import Path
import shutil
from bs4 import BeautifulSoup

def extract_content_from_html(html_content):
    """Extract the text inside the <section data-field="body" class="e-content"> tag with proper spacing."""
    soup = BeautifulSoup(html_content, 'html.parser')
    section = soup.find('section', {'data-field': 'body', 'class': 'e-content'})
    if section:
        # Add spaces between paragraphs and other block-level elements
        for tag in section.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']):
            tag.insert_before('\n')
            tag.insert_after('\n')
        return section.get_text().strip()
    return None

def process_and_save_story(story_file, output_file_path):
    """Process a story file to extract content and save it."""
    with open(story_file, 'r', encoding='utf-8') as file:
        html_content = file.read()
        extracted_text = extract_content_from_html(html_content)
        if extracted_text:
            with open(output_file_path, 'w', encoding='utf-8') as output_file:
                output_file.write(extracted_text)
                print(f"Processed and saved: {output_file_path}")
        else:
            print(f"Warning: No content found in {story_file}")

def extract_stories_from_zip(zip_file_path, output_dir):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        for file_info in zip_ref.infolist():
            if file_info.filename.startswith('posts/') and file_info.filename.endswith('.html'):
                if Path(file_info.filename).name.startswith('draft'):
                    continue

                with zip_ref.open(file_info) as file:
                    story_content = file.read().decode('utf-8')
                    story_filename = Path(file_info.filename).name
                    output_file_path = output_path / story_filename.replace('.html', '.txt')

                    extracted_text = extract_content_from_html(story_content)
                    if extracted_text:
                        with open(output_file_path, 'w', encoding='utf-8') as output_file:
                            output_file.write(extracted_text)
                            print(f"Extracted and saved: {output_file_path}")
                    else:
                        print(f"Warning: No content found in {story_filename}")

def copy_stories_from_directory(source_dir, output_dir):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    posts_dir = Path(source_dir) / 'posts'
    if not posts_dir.exists() or not posts_dir.is_dir():
        print(f"No 'posts' subdirectory found in {source_dir}.")
        return

    for story_file in posts_dir.glob('*.html'):
        if story_file.name.startswith('draft'):
            continue
        
        output_file_path = output_path / story_file.name.replace('.html', '.txt')
        process_and_save_story(story_file, output_file_path)

def process_medium_archive(input_path, output_dir):
    if input_path.endswith('.zip'):
        extract_stories_from_zip(input_path, output_dir)
    else:
        copy_stories_from_directory(input_path, output_dir)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_medium_stories.py <path_to_zip_or_directory> <output_directory>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_dir = sys.argv[2]

    process_medium_archive(input_path, output_dir)
