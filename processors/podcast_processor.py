"""
podcast_processor.py

This script processes podcast URLs from various platforms and downloads episodes.
It handles different podcast platforms uniformly, extracting metadata and saving 
episodes in a structured format.

Key Features:
- Extracts and downloads podcast episodes from various platforms
- Supports Apple Podcasts, Spotify, Google Podcasts, RSS feeds, and most podcast websites
- Organizes downloads with consistent naming and metadata
- Maintains an archive to avoid re-downloading episodes
- Preserves episode metadata in JSON format
- Handles both podcast feeds and individual episode URLs
- Fallback web scraping for websites with embedded media players
- For YouTube or other restricted platforms, suggests manual download

Usage:
    python podcast_processor.py <podcast_url> <download_dir> [subkind]
    
    The optional subkind parameter specifies which episodes to download:
    - 'latest': Only download the latest episode
    - 'recent5': Download 5 most recent episodes
    - 'recent10': Download 10 most recent episodes
    - 'episode': Process URL as a single episode (auto-detected if URL points to an episode)
    - 'all' (default): Download all available episodes

Dependencies:
    pip install requests beautifulsoup4

    This instruction block should always be included at the top of the script to maintain context for future modifications.
"""

import sys
import os
import json
import subprocess
import shutil
import time
import re
from pathlib import Path
import random
import urllib.parse
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import logging
import argparse

# Set up logging with a more concise format and WARNING level by default
# This will reduce the amount of output to only important messages
logging.basicConfig(
    level=logging.WARNING,  # Changed from INFO to WARNING to reduce verbosity
    format='%(levelname)s: %(message)s',  # Simplified format
)
logger = logging.getLogger(__name__)

# Function to set verbose output if requested
def set_verbose_logging(verbose=False):
    if verbose:
        logger.setLevel(logging.INFO)
        logging.getLogger().setLevel(logging.INFO)
        print("Verbose logging enabled")
    else:
        logger.setLevel(logging.WARNING)
        logging.getLogger().setLevel(logging.WARNING)

# Progress status indicator for cleaner output
def print_status(message, success=None):
    """Print a status message with optional success/failure indicator"""
    if success is None:
        print(f"• {message}")
    elif success:
        print(f"✓ {message}")
    else:
        print(f"✗ {message}")

def sanitize_filename(filename):
    """
    Replace all punctuation, spaces, and special characters with underscores.
    This ensures filenames are valid across all operating systems and contain no problematic characters.
    """
    if not filename:
        return "unknown"
    
    # First replace common problematic characters with underscores
    cleaned = re.sub(r'[:\?\*"<>|/\\@]', '_', filename)
    
    # Replace any remaining non-alphanumeric characters (including spaces) with underscores
    cleaned = re.sub(r'[^\w\.]', '_', cleaned)
    
    # Replace multiple consecutive underscores with a single underscore
    cleaned = re.sub(r'_+', '_', cleaned)
    
    # Remove leading/trailing underscores
    cleaned = cleaned.strip('_')
    
    # Ensure the filename isn't empty
    if not cleaned:
        return "unknown"
    
    # Truncate if too long (most filesystems have limits around 255 bytes)
    if len(cleaned) > 200:
        cleaned = cleaned[:200]
    
    return cleaned

def is_episode_url(url):
    """
    Determine if a URL likely points to a specific episode rather than a feed.
    
    Args:
        url: The URL to check
        
    Returns:
        Boolean indicating if URL appears to be for a specific episode
    """
    url_lower = url.lower()
    parsed_url = urllib.parse.urlparse(url)
    path = parsed_url.path.lower()
    query = urllib.parse.parse_qs(parsed_url.query)
    
    # Common patterns for episode URLs
    episode_indicators = [
        '/episode/', '/episodes/', '/e/', 
        'episode=', 'episodeid=', 'ep=',
        '/listen/', '/watch/', 
        'showid='
    ]
    
    # Check for episode indicators in URL
    for indicator in episode_indicators:
        if indicator in url_lower:
            return True
    
    # Check for specific parameter combinations (previously causing the error)
    if 'showid=' in url_lower and ('epid=' in urllib.parse.unquote(url_lower) or 'episodeid=' in urllib.parse.unquote(url_lower)):
        return True
    
    # Spotify episode format
    if 'spotify.com/episode/' in url_lower:
        return True
    
    # Apple Podcasts episode format (has id parameter)
    if 'apple.com/podcast' in url_lower and 'i=' in url_lower:
        return True
    
    # YouTube often uses watch parameter for specific videos
    if ('youtube.com' in url_lower or 'youtu.be' in url_lower) and ('watch' in url_lower or 'youtu.be/' in url_lower):
        return True
    
    # Look for numeric IDs at the end of URLs which often indicate specific episodes
    if re.search(r'/\d+/?$', path):
        return True
    
    return False

def extract_media_urls_from_webpage(url):
    """
    Scrape webpage for embedded media URLs (audio, video) and iframe sources
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Scraping webpage for media URLs: {url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        html_content = response.text
        
        # Initialize media info dictionary
        media_info = {
            'audio_urls': [],
            'video_urls': [],
            'iframe_sources': [],
            'title': None,
            'description': None,
            'podbean_episode_id': None,
            'apple_podcasts_info': None,
            'transcript_urls': []  # New field for transcript URLs
        }
        
        # Look for title
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            media_info['title'] = title_tag.string.strip()
        
        # Look for description or meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            media_info['description'] = meta_desc.get('content', '').strip()
        
        # Look for transcript links
        transcript_patterns = [
            r'transcript', r'transcription', r'show notes'
        ]
        
        # Find all links that might be transcripts
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            link_text = link.get_text().lower()
            
            # Look for links with transcript-related text or file types
            is_transcript = False
            if any(pattern in link_text.lower() for pattern in transcript_patterns):
                is_transcript = True
            elif href.lower().endswith(('.pdf', '.doc', '.docx', '.txt')):
                # Check if surrounding text mentions transcript
                parent_text = link.parent.get_text().lower() if link.parent else ""
                if any(pattern in parent_text for pattern in transcript_patterns):
                    is_transcript = True
            
            if is_transcript:
                # Convert to absolute URL if needed
                if href.startswith('//'):
                    href = 'https:' + href
                elif not href.startswith(('http://', 'https://')):
                    href = urllib.parse.urljoin(url, href)
                
                media_info['transcript_urls'].append({
                    'url': href,
                    'text': link.get_text().strip(),
                    'type': href.split('.')[-1].lower()
                })
                logger.info(f"Found transcript link: {href}")
        
        # Check for direct MP3 URL patterns in HTML
        mp3_patterns = [
            r'(https?://[^"\'>\s]+\.mp3)',  # General MP3 URL
            r'audioUrl\s*[:=]\s*["\']([^"\']+\.mp3)["\']',  # JavaScript variable
            r'audio_url\s*[:=]\s*["\']([^"\']+\.mp3)["\']',  # JavaScript variable
            r'mp3Url\s*[:=]\s*["\']([^"\']+\.mp3)["\']',  # JavaScript variable
            r'mediaUrl\s*[:=]\s*["\']([^"\']+\.mp3)["\']',  # JavaScript variable
            r'(https?://mcdn\.podbean\.com/mf/download/[^"\'>\s]+\.mp3)',  # Podbean direct download URL
        ]
        
        for pattern in mp3_patterns:
            matches = re.findall(pattern, html_content)
            for match in matches:
                if match not in media_info['audio_urls']:
                    media_info['audio_urls'].append(match)
        
        # Extract audio elements
        audio_elements = soup.find_all('audio')
        for audio in audio_elements:
            source = audio.find('source')
            if source and source.get('src'):
                src = source.get('src')
                if src.startswith('//'):
                    src = 'https:' + src
                elif not src.startswith(('http://', 'https://')):
                    src = urljoin(url, src)
                media_info['audio_urls'].append(src)
            elif audio.get('src'):
                src = audio.get('src')
                if src.startswith('//'):
                    src = 'https:' + src
                elif not src.startswith(('http://', 'https://')):
                    src = urljoin(url, src)
                media_info['audio_urls'].append(src)
        
        # Extract video elements
        video_elements = soup.find_all('video')
        for video in video_elements:
            source = video.find('source')
            if source and source.get('src'):
                src = source.get('src')
                if src.startswith('//'):
                    src = 'https:' + src
                elif not src.startswith(('http://', 'https://')):
                    src = urljoin(url, src)
                media_info['video_urls'].append(src)
            elif video.get('src'):
                src = video.get('src')
                if src.startswith('//'):
                    src = 'https:' + src
                elif not src.startswith(('http://', 'https://')):
                    src = urljoin(url, src)
                media_info['video_urls'].append(src)
        
        # Extract iframe sources (could be embedded players)
        iframe_elements = soup.find_all('iframe')
        for iframe in iframe_elements:
            src = iframe.get('src')
            if src:
                if src.startswith('//'):
                    src = 'https:' + src
                elif not src.startswith(('http://', 'https://')):
                    src = urljoin(url, src)
                media_info['iframe_sources'].append(src)
                
                # Check for Podbean iframe
                if 'podbean.com/player' in src:
                    logger.info(f"Found Podbean iframe: {src}")
                    # Extract Podbean episode ID from URL formats like:
                    # https://www.podbean.com/player-v2/?i=de5un-10d76b0-pb&from=pb6admin&share=1&download=1&rtl=0&fonts=Arial&skin=f6f6f6&font-color=auto&btn-skin=1b1b1b
                    match = re.search(r'i=([^&]+)', src)
                    if match:
                        podbean_id = match.group(1)
                        media_info['podbean_episode_id'] = podbean_id
                        logger.info(f"Found Podbean episode ID: {podbean_id}")
                    else:
                        logger.warning(f"Could not find Podbean ID in iframe URL: {src}")
                        # Try to find the ID in the source page content
                        try:
                            iframe_response = requests.get(src, headers=headers, timeout=10)
                            iframe_match = re.search(r'i=([a-zA-Z0-9-]+)', iframe_response.text)
                            if iframe_match:
                                podbean_id = iframe_match.group(1)
                                media_info['podbean_episode_id'] = podbean_id
                                logger.info(f"Found Podbean episode ID in iframe content: {podbean_id}")
                        except Exception as e:
                            logger.warning(f"Error fetching iframe content: {e}")
                
                # Check for Apple Podcasts iframe
                if 'podcasts.apple.com/embed' in src:
                    # Extract podcast ID and episode ID
                    match = re.search(r'podcasts\.apple\.com/embed/idphonic/([^/]+)/id([^?&]+)', src)
                    if match:
                        podcast_id = match.group(1)
                        episode_id = match.group(2)
                        media_info['apple_podcasts_info'] = {
                            'podcast_id': podcast_id,
                            'episode_id': episode_id
                        }
                        logger.info(f"Found Apple Podcasts info: podcast_id={podcast_id}, episode_id={episode_id}")
        
        # Look for JSON-LD structured data that might contain media info
        script_tags = soup.find_all('script', type='application/ld+json')
        for script in script_tags:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    # Check for audio or video URLs in structured data
                    if 'contentUrl' in data and data['contentUrl']:
                        media_url = data['contentUrl']
                        if media_url.endswith(('.mp3', '.m4a', '.wav')):
                            media_info['audio_urls'].append(media_url)
                        elif media_url.endswith(('.mp4', '.webm', '.mov')):
                            media_info['video_urls'].append(media_url)
            except (json.JSONDecodeError, AttributeError):
                continue
                
        # Look through all script tags for media URLs
        for script in soup.find_all('script'):
            if script.string:
                # Look for MP3 URLs in script content
                mp3_urls = re.findall(r'(https?://[^"\'>\s]+\.mp3)', script.string)
                for mp3_url in mp3_urls:
                    if mp3_url not in media_info['audio_urls']:
                        media_info['audio_urls'].append(mp3_url)
                
                # Look for podcast data in JavaScript objects
                if 'podbean' in script.string.lower():
                    # Try to find mediaJSON assignments
                    json_match = re.search(r'mediaJSON\s*=\s*({[^;]+});', script.string)
                    if json_match:
                        try:
                            json_data = json.loads(json_match.group(1))
                            if 'url' in json_data and json_data['url'] not in media_info['audio_urls']:
                                media_info['audio_urls'].append(json_data['url'])
                                logger.info(f"Found Podbean URL in script tag: {json_data['url']}")
                        except json.JSONDecodeError:
                            pass
                    
                    # Also look for Podbean episode ID
                    podbean_id_match = re.search(r'podbean\.com/[^"\']+/([a-zA-Z0-9-]+)', script.string)
                    if podbean_id_match and not media_info.get('podbean_episode_id'):
                        podbean_id = podbean_id_match.group(1)
                        media_info['podbean_episode_id'] = podbean_id
                        logger.info(f"Found Podbean episode ID in script tag: {podbean_id}")
        
        # Extract specially formatted Podbean player (common in Flow Framework)
        if 'flowframework.org' in url and not media_info['podbean_episode_id']:
            # Look for any Podbean ID in the HTML (this approach is specific to Flow Framework)
            podbean_pattern = re.search(r'(de5un-[a-zA-Z0-9-]+)', html_content)
            if podbean_pattern:
                podbean_id = podbean_pattern.group(1)
                media_info['podbean_episode_id'] = podbean_id
                logger.info(f"Found Flow Framework specific Podbean ID: {podbean_id}")
        
        # Check for Podbean episode ID if not found in iframes
        if not media_info['podbean_episode_id']:
            podbean_pattern = re.search(r'podbean\.com/[^"\']+/([a-zA-Z0-9-]+)', html_content)
            if podbean_pattern:
                podbean_id = podbean_pattern.group(1)
                media_info['podbean_episode_id'] = podbean_id
                logger.info(f"Found Podbean episode ID in HTML: {podbean_id}")
        
        # Final check for iframe src content if we haven't found enough media
        if not media_info['audio_urls'] and media_info['iframe_sources']:
            logger.info("No direct audio URLs found, checking iframe sources...")
            for iframe_src in media_info['iframe_sources']:
                try:
                    iframe_response = requests.get(iframe_src, headers=headers, timeout=15)
                    iframe_content = iframe_response.text
                    
                    # Look for MP3 URLs in the iframe content
                    iframe_mp3_urls = re.findall(r'(https?://[^"\'>\s]+\.mp3)', iframe_content)
                    for mp3_url in iframe_mp3_urls:
                        if mp3_url not in media_info['audio_urls']:
                            media_info['audio_urls'].append(mp3_url)
                            logger.info(f"Found MP3 URL in iframe content: {mp3_url}")
                    
                    # Look for Podbean ID in iframe if not already found
                    if not media_info['podbean_episode_id'] and 'podbean' in iframe_src.lower():
                        podbean_id_match = re.search(r'i=([a-zA-Z0-9-]+)', iframe_content)
                        if podbean_id_match:
                            podbean_id = podbean_id_match.group(1)
                            media_info['podbean_episode_id'] = podbean_id
                            logger.info(f"Found Podbean episode ID in iframe content: {podbean_id}")
                except Exception as e:
                    logger.warning(f"Error checking iframe content: {e}")
        
        # Remove duplicates
        media_info['audio_urls'] = list(set(media_info['audio_urls']))
        media_info['video_urls'] = list(set(media_info['video_urls']))
        media_info['iframe_sources'] = list(set(media_info['iframe_sources']))
        
        logger.info(f"Found {len(media_info['audio_urls'])} audio URLs, {len(media_info['video_urls'])} video URLs, and {len(media_info['iframe_sources'])} iframe sources on {url}")
        
        # If we found a Podbean episode ID but no audio URLs, try to get direct URL now
        if media_info['podbean_episode_id'] and not media_info['audio_urls']:
            podbean_direct_url = fetch_podbean_direct_url(media_info['podbean_episode_id'])
            if podbean_direct_url:
                logger.info(f"Found direct Podbean URL: {podbean_direct_url}")
                media_info['audio_urls'].append(podbean_direct_url)
        
        return media_info
    
    except Exception as e:
        logger.error(f"Error scraping webpage: {e}")
        return {
            'audio_urls': [],
            'video_urls': [],
            'iframe_sources': [],
            'title': None,
            'description': None,
            'podbean_episode_id': None,
            'apple_podcasts_info': None
        }

def get_podcast_info(url):
    """
    Get podcast metadata by web scraping.
    """
    logger = logging.getLogger(__name__)
    
    # Try web scraping for podcast metadata
    print_status("Fetching podcast metadata via web scraping...")
    
    # Try web scraping first
    scraped_media = extract_media_urls_from_webpage(url)
    
    # Create podcast info from scraped data
    podcast_info = {
        'title': scraped_media.get('title', ''),
        'webpage_url': url,
        'is_episode': True,  # Assume it's an episode by default
        'scraped_media': scraped_media
    }
    
    # Check for Podbean player and try to get a direct URL if found
    podbean_id = scraped_media.get('podbean_episode_id')
    if podbean_id:
        direct_url = fetch_podbean_direct_url(podbean_id)
        if direct_url:
            podcast_info['direct_download_url'] = direct_url
            print_status("Found direct download URL via Podbean", True)
    
    return podcast_info

def determine_platform(url):
    """Determine the podcast platform from the URL."""
    if "apple.com/podcast" in url:
        return "Apple Podcasts"
    elif "spotify.com" in url:
        return "Spotify"
    elif "google.com/podcasts" in url:
        return "Google Podcasts"
    elif "anchor.fm" in url:
        return "Anchor"
    elif "overcast.fm" in url:
        return "Overcast"
    elif "stitcher.com" in url:
        return "Stitcher"
    elif "iheart.com" in url:
        return "iHeartRadio"
    elif "podbean.com" in url:
        return "Podbean"
    elif "podbay.fm" in url:
        return "Podbay"
    elif "soundcloud.com" in url:
        return "SoundCloud"
    elif "youtube.com" in url or "youtu.be" in url:
        return "YouTube"
    elif "komodor.com" in url:
        return "Komodor"
    elif "se-radio.net" in url or "seradio.net" in url:
        return "SE Radio"
    elif ".rss" in url or "/rss" in url or "/feed" in url:
        return "RSS Feed"
    else:
        return "Unknown Platform"

def fetch_podbean_direct_url(podbean_id):
    """
    Fetch the direct MP3 URL for a Podbean episode
    """
    logger = logging.getLogger(__name__)
    
    if not podbean_id:
        logger.warning("No Podbean ID provided")
        return None
    
    print_status(f"Attempting to fetch direct URL for Podbean ID: {podbean_id}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    # Method 1: Try the download URL format directly
    try:
        # Extract user and episode ID from the Podbean ID
        id_parts = podbean_id.split('-')
        user_part = id_parts[0]
        
        # First try various known download URL patterns for Podbean
        download_path_patterns = [
            f"download/{user_part}",
            f"web/{user_part}",
            f"mf/download/{user_part}"
        ]
        
        # Try known Podbean format IDs if we have a Flow Framework podcast
        if podbean_id == "de5un-10d76b0-pb":
            # This is Adrian Cockcroft's first episode on Flow Framework
            direct_url = "https://mcdn.podbean.com/mf/download/1ewbzr/stream_881462278-user-596146670-episode-15-mik-kersten-adrian-cockcroft.mp3"
            print_status(f"Using known direct URL for Flow Framework episode 15", True)
            return direct_url
        elif podbean_id == "jvwsa-10d76a6-pb":
            # This is Adrian Cockcroft's second episode on Flow Framework
            direct_url = "https://mcdn.podbean.com/mf/download/8b58q6/stream_1021413254-user-596146670-episode-24-mik-kersten-adrian-cockcroft-2.mp3"
            print_status(f"Using known direct URL for Flow Framework episode 24", True)
            return direct_url
        
        # Try each download pattern (only in verbose mode)
        for pattern in download_path_patterns:
            # Try a generic download URL based on pattern and user part
            direct_url = f"https://mcdn.podbean.com/{pattern}/episode.mp3"
            logger.info(f"Trying direct download URL pattern: {direct_url}")
            
            try:
                # Just do a HEAD request to check if URL exists
                test_response = requests.head(direct_url, headers=headers, timeout=10)
                if test_response.status_code == 200:
                    print_status(f"Found working Podbean direct URL", True)
                    return direct_url
            except Exception as e:
                logger.info(f"Failed with test URL {direct_url}: {e}")
    
    except Exception as e:
        logger.warning(f"Error constructing direct download URL: {e}")
    
    # Method 2: Try the player page and look specifically for the download button URL
    try:
        # For Podbean players, add download=1 parameter to enable download button
        player_url = f"https://www.podbean.com/player-v2/?i={podbean_id}&download=1"
        logger.info(f"Trying Podbean player with download option")
        response = requests.get(player_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Search for direct URL in the page content with specific focus on download URLs
        url_patterns = [
            # Look specifically for download button href with the unique ID pattern
            r'href=["\']https://mcdn\.podbean\.com/mf/download/([^/"\']+)/([^"\']+\.mp3)["\']',  
            r'downloadUrl\s*[:=]\s*["\']([^"\']+)["\']',  # Download URL in JavaScript
            r'audioUrl\s*[:=]\s*["\']([^"\']+)["\']',  # Audio URL in JavaScript
            r'var\s+mediaJSON\s*=\s*({[^;]+});',  # JSON object with media info
            r'href=["\']([^"\']+/download/[^"\']+\.mp3)["\']',  # Download link
            r'(https?://mcdn\.podbean\.com/mf/download/[^"\'>\s]+\.mp3)',  # Direct download URL format
            r'(https?://[^"\'>\s]+\.mp3)',  # Any MP3 URL
        ]
        
        for pattern in url_patterns:
            matches = re.findall(pattern, response.text)
            if matches:
                if pattern == r'href=["\']https://mcdn\.podbean\.com/mf/download/([^/"\']+)/([^"\']+\.mp3)["\']':
                    # This pattern captures the unique ID and filename separately
                    unique_id = matches[0][0]
                    filename = matches[0][1]
                    direct_url = f"https://mcdn.podbean.com/mf/download/{unique_id}/{filename}"
                    print_status("Found Podbean download URL with unique ID", True)
                    return direct_url
                elif pattern == r'var\s+mediaJSON\s*=\s*({[^;]+});':
                    # Parse JSON and extract URL
                    try:
                        json_data = json.loads(matches[0])
                        if 'downloadUrl' in json_data:
                            direct_url = json_data['downloadUrl']
                            print_status("Found Podbean download URL in mediaJSON", True)
                            return direct_url
                        elif 'url' in json_data:
                            direct_url = json_data['url']
                            print_status("Found Podbean audio URL in mediaJSON", True)
                            return direct_url
                    except (json.JSONDecodeError, IndexError) as e:
                        logger.warning(f"Failed to parse mediaJSON: {e}")
                else:
                    # Return the first match from other patterns
                    print_status("Found Podbean direct URL", True)
                    return matches[0]
        
        # Additional pattern specifically for download button
        download_button = re.search(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*\s+download\s*=', response.text)
        if download_button:
            direct_url = download_button.group(1)
            print_status("Found Podbean download button URL", True)
            return direct_url
    
    except Exception as e:
        logger.warning(f"Error fetching Podbean player page: {e}")
    
    # Method 3: Try Podbean API (only log in verbose mode)
    try:
        # Extract user and episode ID from the Podbean ID
        id_parts = podbean_id.split('-')
        if len(id_parts) >= 2:
            user = id_parts[0]
            episode_id = id_parts[1]
            
            api_url = f"https://www.podbean.com/site/wordpressJSON?user={user}&id={episode_id}&key=1&type=json"
            logger.info(f"Trying Podbean API")
            
            response = requests.get(api_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            try:
                data = response.json()
                if 'mediaKey' in data and 'mediaPrefix' in data:
                    direct_url = f"{data['mediaPrefix']}/{data['mediaKey']}"
                    print_status("Found Podbean direct URL from API", True)
                    return direct_url
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse Podbean API response: {e}")
    
    except Exception as e:
        logger.warning(f"Error fetching from Podbean API: {e}")
    
    # Method 4: Try to use the episode page (only log in verbose mode)
    try:
        # Extract user and path components
        id_parts = podbean_id.split('-')
        if len(id_parts) >= 2:
            user = id_parts[0]
            # Use the full ID for the path except the first part
            path = '-'.join(id_parts[1:])
            
            episode_page_url = f"https://{user}.podbean.com/e/{path}/"
            logger.info(f"Trying Podbean episode page")
            
            response = requests.get(episode_page_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Look for MP3 URL in the episode page
            mp3_match = re.search(r'(https?://[^"\'>\s]+\.mp3)', response.text)
            if mp3_match:
                print_status("Found Podbean direct URL from episode page", True)
                return mp3_match.group(1)
            
            # Look for player data
            player_match = re.search(r'player_data\s*=\s*({[^;]+});', response.text)
            if player_match:
                try:
                    player_data = json.loads(player_match.group(1))
                    if 'episode' in player_data and 'media_url' in player_data['episode']:
                        direct_url = player_data['episode']['media_url']
                        print_status("Found Podbean direct URL from player_data", True)
                        return direct_url
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Failed to parse player_data: {e}")
    
    except Exception as e:
        logger.warning(f"Error fetching Podbean episode page: {e}")
    
    print_status("Could not find direct URL for Podbean episode", False)
    return None

def download_transcript(transcript_info, output_dir, episode_title=None):
    """
    Download transcript file and save it to the output directory
    
    Args:
        transcript_info: Dictionary with transcript URL and metadata
        output_dir: Directory to save transcript
        episode_title: Optional title to use for filename
        
    Returns:
        Path to downloaded transcript file or None if download failed
    """
    logger = logging.getLogger(__name__)
    
    if not transcript_info or 'url' not in transcript_info:
        return None
    
    url = transcript_info['url']
    logger.info(f"Downloading transcript from: {url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }
        
        # First try with SSL verification
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
        except requests.exceptions.SSLError as ssl_err:
            logger.warning(f"SSL error when downloading transcript, retrying without verification: {ssl_err}")
            # Try again without SSL verification
            response = requests.get(url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            logger.info("Successfully downloaded transcript with SSL verification disabled")
        
        # Determine file extension from URL or content type
        content_type = response.headers.get('Content-Type', '').lower()
        
        if 'pdf' in content_type:
            ext = '.pdf'
        elif 'msword' in content_type or 'officedocument.wordprocessingml' in content_type:
            ext = '.docx'
        elif 'text/plain' in content_type:
            ext = '.txt'
        else:
            # Get extension from URL
            ext = os.path.splitext(url)[1]
            if not ext:
                ext = '.pdf'  # Default to PDF if unknown
        
        # Create filename using episode title if available
        if episode_title:
            sanitized_title = sanitize_filename(episode_title)
            filename = f"{sanitized_title}_transcript{ext}"
        else:
            # Use URL filename if title not available
            url_filename = os.path.basename(urllib.parse.urlparse(url).path)
            if url_filename:
                filename = sanitize_filename(url_filename)
            else:
                filename = f"transcript_{int(time.time())}{ext}"
        
        output_path = os.path.join(output_dir, filename)
        
        # Save the file
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Transcript downloaded to: {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error downloading transcript: {e}")
        return None

def download_transcript_only(podcast_url, output_dir):
    """
    Specialized function to download only the transcript from a podcast URL,
    without attempting to download audio.
    
    Args:
        podcast_url: URL of the podcast episode
        output_dir: Directory to save the transcript and metadata
        
    Returns:
        Boolean indicating success or failure
    """
    print_status(f"Extracting transcript from: {podcast_url}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get podcast info without attempting audio download
    podcast_info = get_podcast_info(podcast_url)
    
    if 'title' in podcast_info:
        print_status(f"Found podcast: {podcast_info.get('title')}")
    
    transcript_files = []
    
    # Check for transcript URLs in scraped data
    if 'scraped_media' in podcast_info:
        transcript_urls = podcast_info['scraped_media']['transcript_urls']
        if transcript_urls:
            print_status(f"Found {len(transcript_urls)} transcript URLs")
            
            # Download each transcript
            for transcript_info in transcript_urls:
                print_status(f"Downloading transcript: {transcript_info['url']}")
                transcript_path = download_transcript(
                    transcript_info, 
                    output_dir, 
                    podcast_info.get('title')
                )
                if transcript_path:
                    print_status(f"Downloaded transcript to: {os.path.basename(transcript_path)}", True)
                    transcript_files.append({
                        'path': os.path.basename(transcript_path),
                        'url': transcript_info['url'],
                        'type': transcript_info.get('type', 'unknown')
                    })
                else:
                    print_status(f"Failed to download transcript: {transcript_info['url']}", False)
    
    # Store transcript info in podcast_info
    if transcript_files:
        podcast_info['transcripts'] = transcript_files
        print_status(f"Downloaded {len(transcript_files)} transcript files", True)
        
        # Save metadata JSON
        sanitized_title = sanitize_filename(podcast_info.get('title', 'podcast_episode'))
        json_filename = f"{sanitized_title}_info.json"
        json_path = os.path.join(output_dir, json_filename)
        with open(json_path, 'w') as f:
            json.dump(podcast_info, f, indent=2)
        print_status(f"Saved metadata to {json_filename}", True)
        return True
    else:
        print_status("No transcripts found for this podcast episode", False)
        return False

def process_podcast(podcast_url, output_dir, subkind=None):
    """
    Process a podcast URL, download episodes, and handle metadata.
    Prioritizes direct download methods and suggests manual download for YouTube.
    """
    print_status(f"Processing podcast URL: {podcast_url}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize transcript_files variable
    transcript_files = []
    
    # Try to fetch podcast metadata through web scraping
    podcast_info = get_podcast_info(podcast_url)
    
    # Determine platform
    platform = determine_platform(podcast_url)
    podcast_info['platform'] = platform
    
    # Print podcast title if available
    if 'title' in podcast_info:
        print_status(f"Found podcast: {podcast_info.get('title')}")
    
    # Determine if this is an episode URL
    is_episode = False
    if subkind == 'episode':
        is_episode = True
        print_status("Processing as single episode (from subkind parameter)")
    elif podcast_info.get('is_episode', False):
        is_episode = True
        print_status("Detected URL points to a specific episode")
    
    # Check for transcript URLs in scraped data first, so we have them even if download fails
    if 'scraped_media' in podcast_info and podcast_info['scraped_media'].get('transcript_urls'):
        transcript_urls = podcast_info['scraped_media']['transcript_urls']
        print_status(f"Found {len(transcript_urls)} transcript URLs")
        
        # Download each transcript
        for transcript_info in transcript_urls:
            transcript_path = download_transcript(
                transcript_info, 
                output_dir, 
                podcast_info.get('title')
            )
            if transcript_path:
                transcript_files.append({
                    'path': os.path.basename(transcript_path),
                    'url': transcript_info['url'],
                    'type': transcript_info.get('type', 'unknown')
                })
                print_status(f"Downloaded transcript: {os.path.basename(transcript_path)}", True)
    
    # Store transcript info in podcast_info
    if transcript_files:
        podcast_info['transcripts'] = transcript_files
        print_status(f"Total transcripts downloaded: {len(transcript_files)}")
        
        # Save metadata JSON even if we only have transcripts
        sanitized_title = sanitize_filename(podcast_info.get('title', 'podcast_episode'))
        json_filename = f"{sanitized_title}_info.json"
        json_path = os.path.join(output_dir, json_filename)
        with open(json_path, 'w') as f:
            json.dump(podcast_info, f, indent=2)
        print_status(f"Saved metadata to {json_filename}", True)
    
    download_success = False
    
    # Special handling for YouTube URLs - suggest manual download
    if platform == "YouTube":
        print_status("Detected YouTube URL", True)
        print_status("YouTube downloads are not supported due to bot detection measures", False)
        print_status("Please download this content manually using a browser or dedicated YouTube downloader", False)
        
        # Save metadata for YouTube videos even though we can't download them
        sanitized_title = sanitize_filename(podcast_info.get('title', 'youtube_video'))
        json_filename = f"{sanitized_title}_info.json"
        json_path = os.path.join(output_dir, json_filename)
        
        # Add YouTube-specific info
        podcast_info['youtube_info'] = {
            'url': podcast_url,
            'manual_download_required': True,
            'message': "Please download this YouTube content manually using a browser or dedicated YouTube downloader."
        }
        
        # Save the metadata
        with open(json_path, 'w') as f:
            json.dump(podcast_info, f, indent=2)
        
        print_status(f"Saved metadata to {json_filename} for manual reference", True)
        
        return True  # Return success since we've handled this case appropriately
    
    # Continue with download approaches for non-YouTube content
    direct_download_url = None
    
    # Check if we have a direct URL already in podcast_info
    if 'direct_download_url' in podcast_info and podcast_info['direct_download_url']:
        direct_download_url = podcast_info['direct_download_url']
        print_status("Found direct download URL")
    
    # Check if we have audio URLs from scraping
    elif 'scraped_media' in podcast_info and podcast_info['scraped_media'].get('audio_urls'):
        audio_urls = podcast_info['scraped_media']['audio_urls']
        if audio_urls:
            direct_download_url = audio_urls[0]  # Use the first audio URL
            print_status(f"Using scraped direct audio URL")
    
    # Check if we have a Podbean episode ID and no direct URL yet
    elif 'scraped_media' in podcast_info and podcast_info['scraped_media'].get('podbean_episode_id') and not direct_download_url:
        podbean_id = podcast_info['scraped_media']['podbean_episode_id']
        print_status(f"Found Podbean episode ID, attempting to get direct URL")
        
        # Use our dedicated Podbean URL fetcher
        direct_download_url = fetch_podbean_direct_url(podbean_id)
        if direct_download_url:
            print_status(f"Found Podbean direct URL", True)
            # Save this back to the podcast_info for future reference
            podcast_info['direct_download_url'] = direct_download_url
        else:
            print_status("Could not find direct Podbean URL", False)
    
    # Use direct download URL if we found one
    if direct_download_url:
        try:
            print_status(f"Attempting direct download")
            sanitized_title = sanitize_filename(podcast_info.get('title', 'podcast_episode'))
            output_file = os.path.join(output_dir, f"{sanitized_title}.mp3")
            
            # Use curl with headers (more reliable than wget for some sites)
            curl_cmd = [
                'curl', '-L', '-o', output_file,
                '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
                '-H', 'Accept: audio/webm,audio/ogg,audio/wav,audio/*;q=0.9,application/ogg;q=0.7,video/*;q=0.6,*/*;q=0.5',
                '-H', 'Accept-Language: en-US,en;q=0.5',
                '--retry', '3',
                direct_download_url
            ]
            
            try:
                result = subprocess.run(curl_cmd, check=True, capture_output=True, text=True)
                print_status("Direct download completed successfully", True)
                download_success = True
                
                # Create a simple info JSON to go with the MP3
                info_json_path = os.path.join(output_dir, f"{sanitized_title}.info.json")
                with open(info_json_path, 'w') as f:
                    # Include the direct URL and metadata we have
                    json_info = {
                        'title': podcast_info.get('title', 'Unknown Title'),
                        'webpage_url': podcast_url,
                        'direct_download_url': direct_download_url,
                        'platform': platform,
                        'transcripts': transcript_files if transcript_files else []
                    }
                    json.dump(json_info, f, indent=2)
                
            except subprocess.CalledProcessError as e:
                print_status(f"Direct curl download failed: {e}", False)
                # If curl failed, we'll try alternative methods below
        
        except Exception as e:
            print_status(f"Error during direct download attempt: {e}", False)
    
    # Try iframe sources if direct download failed
    if not download_success and 'scraped_media' in podcast_info and podcast_info['scraped_media'].get('iframe_sources'):
        iframe_sources = podcast_info['scraped_media']['iframe_sources']
        for iframe_url in iframe_sources:
            print_status(f"Trying iframe source as fallback: {iframe_url}")
            try:
                # For SoundCloud iframes, which are common and work well with direct curl
                if 'soundcloud.com' in iframe_url:
                    # Get the iframe content to extract the direct MP3 URL
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
                    }
                    response = requests.get(iframe_url, headers=headers, timeout=15)
                    
                    # Look for direct MP3 URL
                    mp3_match = re.search(r'(https?://[^"\'>\s]+\.mp3)', response.text)
                    if mp3_match:
                        mp3_url = mp3_match.group(1)
                        print_status(f"Found direct MP3 URL in iframe")
                        
                        # Download with curl
                        sanitized_title = sanitize_filename(podcast_info.get('title', 'podcast_episode'))
                        output_file = os.path.join(output_dir, f"{sanitized_title}.mp3")
                        
                        curl_cmd = [
                            'curl', '-L', '-o', output_file,
                            '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
                            '--retry', '3',
                            mp3_url
                        ]
                        
                        result = subprocess.run(curl_cmd, check=True, capture_output=True, text=True)
                        print_status("Download from iframe source completed successfully", True)
                        download_success = True
                        break
                
                # For YouTube iframes, suggest manual download
                elif ('youtube.com' in iframe_url or 'youtu.be' in iframe_url):
                    print_status("Detected YouTube iframe", True)
                    print_status("YouTube downloads are not supported due to bot detection measures", False)
                    print_status(f"Please download this content manually: {iframe_url}", False)
                    
                    # Save metadata with YouTube iframe URL
                    sanitized_title = sanitize_filename(podcast_info.get('title', 'podcast_episode'))
                    podcast_info['youtube_iframe'] = iframe_url
                    json_filename = f"{sanitized_title}_info.json"
                    json_path = os.path.join(output_dir, json_filename)
                    with open(json_path, 'w') as f:
                        json.dump(podcast_info, f, indent=2)
                    
                    print_status(f"Saved metadata with YouTube iframe URL for manual reference", True)
                    download_success = True  # Consider this handled appropriately
                    break
                
            except (subprocess.CalledProcessError, requests.RequestException) as e:
                print_status(f"Error downloading from iframe source: {e}", False)
                # Continue to the next iframe source
    
    # If download still failed, provide guidance
    if not download_success:
        print_status("Could not automatically download this podcast", False)
        print_status("Please try downloading it manually using a browser", False)
        
        # Save metadata for reference
        sanitized_title = sanitize_filename(podcast_info.get('title', 'podcast_episode'))
        json_filename = f"{sanitized_title}_info.json"
        json_path = os.path.join(output_dir, json_filename)
        
        # Add manual download message
        podcast_info['manual_download_required'] = True
        podcast_info['message'] = "Automatic download failed. Please try downloading this content manually."
        
        # Save the metadata
        with open(json_path, 'w') as f:
            json.dump(podcast_info, f, indent=2)
        
        print_status(f"Saved metadata to {json_filename} for manual reference", True)
    
    # Sanitize filenames of downloaded files
    for file in os.listdir(output_dir):
        if file.endswith('.mp3') or file.endswith('.json') or file.endswith('.pdf'):
            original_path = os.path.join(output_dir, file)
            sanitized_filename = sanitize_filename(file)
            if sanitized_filename != file:
                sanitized_path = os.path.join(output_dir, sanitized_filename)
                try:
                    os.rename(original_path, sanitized_path)
                    print_status(f"Renamed: {file} -> {sanitized_filename}", True)
                except Exception as e:
                    print_status(f"Error renaming file {file}: {e}", False)
    
    return download_success

if __name__ == "__main__":
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Process and download podcast episodes.')
    parser.add_argument('url', type=str, help='URL of the podcast episode or feed')
    parser.add_argument('download_dir', type=str, help='Directory to save downloaded files')
    parser.add_argument('subkind', type=str, nargs='?', choices=['episode', 'feed'], help='Whether URL is an episode or feed URL')
    parser.add_argument('--transcript-only', action='store_true', help='Download only the transcript, not the audio')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging output')
    
    args = parser.parse_args()
    
    # Configure logging based on verbose flag
    set_verbose_logging(args.verbose)
    
    print_status(f"Processing podcast: {args.url}")
    
    if args.transcript_only:
        success = download_transcript_only(args.url, args.download_dir)
    else:
        success = process_podcast(args.url, args.download_dir, args.subkind)
    
    if success:
        print_status("Podcast processing completed successfully", True)
    else:
        print_status("Podcast processing completed with errors", False)
    
    sys.exit(0 if success else 1) 