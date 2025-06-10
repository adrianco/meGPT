import os
import zipfile
import sys
import re
from pathlib import Path
from bs4 import BeautifulSoup
import urllib.parse

def sanitize_filename(filename):
    """Sanitize filename to be compatible across operating systems."""
    # Remove the .html extension if present
    filename = filename.replace('.html', '')
    # Replace invalid characters with underscore
    # This includes: < > : " / \ | ? * and any control characters
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', filename)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    # Replace multiple consecutive underscores with a single one
    sanitized = re.sub(r'_+', '_', sanitized)
    # Ensure the filename isn't empty after sanitization
    if not sanitized:
        sanitized = 'untitled_post'
    return sanitized

def get_profile_url(archive_path):
    """Extract the base URL of the Medium profile from profile/profile.html."""
    profile_path = Path(archive_path) / 'profile' / 'profile.html'
    
    if not profile_path.exists():
        print(f"Error: {profile_path} not found.")
        sys.exit(1)

    with open(profile_path, 'r', encoding='utf-8') as profile_file:
        profile_content = profile_file.read()
        soup = BeautifulSoup(profile_content, 'html.parser')
        # Find the URL in the <a class="u-url" href="...">
        url_tag = soup.find('a', {'class': 'u-url'})
        if url_tag and 'href' in url_tag.attrs:
            base_url = url_tag['href']
            # Extract the username (after '@')
            username = base_url.split('@')[-1]
            return base_url, username
    return None, None

def extract_content_from_html(html_content, base_url, username, file_name):
    """Extract the text inside the <section data-field="body" class="e-content"> tag with proper spacing and append the URL."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Construct the full URL by appending the post's relative URL
    post_url = urllib.parse.urljoin(base_url, f"@{username}/{file_name.replace('.html', '')}")
    
    section = soup.find('section', {'data-field': 'body', 'class': 'e-content'})
    if section:
        # Add spaces between paragraphs and other block-level elements
        for tag in section.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']):
            tag.insert_before('\n')
            tag.insert_after('\n')
        # Prepend the URL to the content
        return f"[URL] {post_url}\n\n{section.get_text().strip()}"
    return None

def process_and_save_story(story_file, output_file_path, base_url, username):
    """Process a story file to extract content and save it."""
    with open(story_file, 'r', encoding='utf-8') as file:
        html_content = file.read()
        extracted_text = extract_content_from_html(html_content, base_url, username, story_file.name)
        if extracted_text:
            with open(output_file_path, 'w', encoding='utf-8') as output_file:
                output_file.write(extracted_text)
                print(f"Processed and saved: {output_file_path}")
        else:
            print(f"Warning: No content found in {story_file}")

def extract_stories_from_zip(zip_file_path, output_dir, base_url, username):
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
                    sanitized_name = sanitize_filename(story_filename)
                    output_file_path = output_path / f"{sanitized_name}.txt"

                    extracted_text = extract_content_from_html(story_content, base_url, username, file_info.filename)
                    if extracted_text:
                        with open(output_file_path, 'w', encoding='utf-8') as output_file:
                            output_file.write(extracted_text)
                            print(f"Extracted and saved: {output_file_path}")
                    else:
                        print(f"Warning: No content found in {story_filename}")

def copy_stories_from_directory(source_dir, output_dir, base_url, username):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    posts_dir = Path(source_dir) / 'posts'
    if not posts_dir.exists() or not posts_dir.is_dir():
        print(f"No 'posts' subdirectory found in {source_dir}.")
        return

    for story_file in posts_dir.glob('*.html'):
        if story_file.name.startswith('draft'):
            continue
        
        sanitized_name = sanitize_filename(story_file.name)
        output_file_path = output_path / f"{sanitized_name}.txt"
        process_and_save_story(story_file, output_file_path, base_url, username)

def process_medium_archive(input_path, output_dir):
    base_url, username = get_profile_url(input_path)
    if not base_url:
        print("Error: Could not extract the base URL from profile/profile.html.")
        sys.exit(1)

    if input_path.endswith('.zip'):
        extract_stories_from_zip(input_path, output_dir, base_url, username)
    else:
        copy_stories_from_directory(input_path, output_dir, base_url, username)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_medium_stories.py <path_to_zip_or_directory> <output_directory>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_dir = sys.argv[2]

    process_medium_archive(input_path, output_dir)
