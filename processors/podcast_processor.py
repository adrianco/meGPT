"""
podcast_processor.py

This script processes podcast URLs from various platforms and downloads episodes
using yt-dlp (youtube-dl fork). It handles different podcast platforms uniformly,
extracting metadata and saving episodes in a structured format.

Key Features:
- Extracts and downloads podcast episodes from various platforms
- Supports Apple Podcasts, Spotify, Google Podcasts, RSS feeds, and most podcast websites
- Organizes downloads with consistent naming and metadata
- Allows downloading all episodes or just the most recent ones
- Maintains an archive to avoid re-downloading episodes
- Preserves episode metadata in JSON format
- Handles both podcast feeds and individual episode URLs
- Fallback web scraping for websites with embedded media players

Usage:
    python podcast_processor.py <podcast_url> <download_dir> [subkind]
    
    The optional subkind parameter specifies which episodes to download:
    - 'latest': Only download the latest episode
    - 'recent5': Download 5 most recent episodes
    - 'recent10': Download 10 most recent episodes
    - 'episode': Process URL as a single episode (auto-detected if URL points to an episode)
    - 'all' (default): Download all available episodes

Dependencies:
    pip install yt-dlp requests beautifulsoup4

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
import requests
from bs4 import BeautifulSoup
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def sanitize_filename(filename):
    """Replace all non-alphanumeric characters with underscores."""
    return re.sub(r'[^\w]', '_', filename)

def check_yt_dlp_installed():
    """Check if yt-dlp is installed and accessible."""
    if shutil.which("yt-dlp"):
        return True
    else:
        print("Error: yt-dlp is not installed. Please install it with: pip install yt-dlp")
        return False

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
    Scrape a webpage to find embedded media URLs.
    
    Args:
        url: The URL of the webpage to scrape
        
    Returns:
        Dictionary with media info including direct media URLs, title, and description
    """
    logger.info(f"Scraping webpage for media URLs: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract basic metadata
        title = soup.title.text.strip() if soup.title else None
        description = soup.find('meta', {'name': 'description'})
        description = description['content'] if description else None
        
        # Initialize results
        media_info = {
            'title': title,
            'description': description,
            'url': url,
            'audio_urls': [],
            'video_urls': [],
            'iframe_srcs': []
        }
        
        # Look for direct audio files (mp3, m4a, ogg, etc.)
        audio_extensions = ['.mp3', '.m4a', '.wav', '.ogg', '.aac', '.flac']
        for link in soup.find_all('a', href=True):
            href = link['href']
            if any(href.lower().endswith(ext) for ext in audio_extensions):
                media_info['audio_urls'].append(href)
        
        # Look for audio elements
        for audio in soup.find_all('audio', src=True):
            media_info['audio_urls'].append(audio['src'])
        
        for audio in soup.find_all('audio'):
            sources = audio.find_all('source', src=True)
            for source in sources:
                media_info['audio_urls'].append(source['src'])
        
        # Look for video elements (which might contain audio)
        for video in soup.find_all('video', src=True):
            media_info['video_urls'].append(video['src'])
        
        for video in soup.find_all('video'):
            sources = video.find_all('source', src=True)
            for source in sources:
                media_info['video_urls'].append(source['src'])
        
        # Look for iframes (could be embedded players like SoundCloud, Spotify, etc.)
        for iframe in soup.find_all('iframe', src=True):
            media_info['iframe_srcs'].append(iframe['src'])
        
        # Look for common podcast player patterns
        # Simplecast
        simplecast_match = re.search(r'https://player\.simplecast\.com/([a-zA-Z0-9-]+)', html)
        if simplecast_match:
            simplecast_id = simplecast_match.group(1)
            simplecast_url = f"https://player.simplecast.com/{simplecast_id}"
            media_info['iframe_srcs'].append(simplecast_url)
        
        # Anchor.fm
        anchor_match = re.search(r'https://anchor\.fm/[^/]+/embed/episodes/[^"\']+', html)
        if anchor_match:
            media_info['iframe_srcs'].append(anchor_match.group(0))
        
        # SoundCloud
        soundcloud_match = re.search(r'https://w\.soundcloud\.com/player/\?url=[^"\']+', html)
        if soundcloud_match:
            media_info['iframe_srcs'].append(soundcloud_match.group(0))
        
        # Look for data attributes that might contain media URLs
        data_sources = soup.find_all(attrs={"data-audio-source": True})
        for source in data_sources:
            media_info['audio_urls'].append(source["data-audio-source"])
        
        # Look for JSON-LD structured data which might contain media info
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                json_data = json.loads(script.string)
                if isinstance(json_data, dict):
                    # Check for AudioObject or PodcastEpisode schema
                    if json_data.get('@type') in ['AudioObject', 'PodcastEpisode'] and 'contentUrl' in json_data:
                        media_info['audio_urls'].append(json_data['contentUrl'])
            except (json.JSONDecodeError, AttributeError):
                pass
        
        # Komodor-specific: Look for specific patterns in Komodor podcast pages
        if 'komodor.com' in url:
            # Search for any media URLs that might be in JavaScript variables
            media_url_pattern = re.search(r'(https://[^"\']+\.(mp3|mp4|m4a|wav|ogg))', html)
            if media_url_pattern:
                media_info['audio_urls'].append(media_url_pattern.group(0))
                
            # Check for Spotify or Apple Podcasts widgets
            spotify_iframe = soup.find('iframe', {'src': lambda src: src and 'spotify.com/embed' in src})
            if spotify_iframe and spotify_iframe.get('src'):
                media_info['iframe_srcs'].append(spotify_iframe['src'])
                
            apple_iframe = soup.find('iframe', {'src': lambda src: src and 'podcasts.apple.com' in src})
            if apple_iframe and apple_iframe.get('src'):
                media_info['iframe_srcs'].append(apple_iframe['src'])
        
        # Remove duplicates and convert relative URLs to absolute
        for key in ['audio_urls', 'video_urls', 'iframe_srcs']:
            media_info[key] = list(set(media_info[key]))
            media_info[key] = [urllib.parse.urljoin(url, media_url) for media_url in media_info[key]]
        
        logger.info(f"Found {len(media_info['audio_urls'])} audio URLs, {len(media_info['video_urls'])} video URLs, "
                   f"and {len(media_info['iframe_srcs'])} iframe sources on {url}")
        
        return media_info
    
    except Exception as e:
        logger.error(f"Error scraping webpage: {e}")
        return {
            'title': None,
            'description': None,
            'url': url,
            'audio_urls': [],
            'video_urls': [],
            'iframe_srcs': [],
            'error': str(e)
        }

def get_podcast_info(podcast_url):
    """
    Retrieve basic information about the podcast.
    
    Args:
        podcast_url: URL of the podcast
        
    Returns:
        Dictionary containing podcast metadata or None if failed
    """
    # Determine if this is a YouTube URL
    is_youtube = "youtube.com" in podcast_url or "youtu.be" in podcast_url
    is_single_video = is_episode_url(podcast_url) or "watch?v=" in podcast_url or "youtu.be/" in podcast_url
    
    try:
        # Build command based on URL type
        cmd = ["yt-dlp", "--dump-json"]
        
        # For YouTube videos, we need different parameters than for playlists/channels
        if is_youtube and is_single_video:
            # For single YouTube videos, don't use playlist options
            print("Detected YouTube single video, fetching metadata...")
        else:
            # For playlists or feeds, limit to first item for metadata
            cmd.extend(["--flat-playlist", "--playlist-items", "1"])
        
        cmd.append(podcast_url)
        print(f"Executing metadata fetch: {' '.join(cmd)}")
        
        # First attempt - standard metadata fetch
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            output = result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"First metadata fetch attempt failed: {e}")
            if is_youtube:
                # Fallback for YouTube - try without --dump-json, just get info
                print("Trying alternative YouTube metadata fetch...")
                fallback_cmd = ["yt-dlp", "--skip-download", "--print", "title,channel", podcast_url]
                try:
                    fallback_result = subprocess.run(fallback_cmd, check=True, capture_output=True, text=True)
                    # Parse basic info from output
                    lines = fallback_result.stdout.strip().split('\n')
                    title = lines[0] if lines else "Unknown Video"
                    channel = lines[1] if len(lines) > 1 else "Unknown Channel"
                    
                    return {
                        "title": title,
                        "channel": channel,
                        "url": podcast_url,
                        "platform": "YouTube",
                        "is_episode": True
                    }
                except subprocess.CalledProcessError:
                    # If all else fails, return basic info
                    print("All metadata fetch attempts failed, using basic info")
                    return {
                        "title": f"YouTube_{sanitize_filename(podcast_url.split('?v=')[-1])}",
                        "url": podcast_url,
                        "platform": "YouTube",
                        "is_episode": True
                    }
            else:
                # For non-YouTube URLs, try web scraping to get media info
                print(f"Trying web scraping fallback for: {podcast_url}")
                media_info = extract_media_urls_from_webpage(podcast_url)
                
                if media_info.get('title'):
                    return {
                        "title": media_info.get('title', f"Podcast_{sanitize_filename(podcast_url)}"),
                        "description": media_info.get('description', ''),
                        "url": podcast_url,
                        "platform": determine_platform(podcast_url),
                        "is_episode": is_episode_url(podcast_url),
                        "scraped_media": {
                            "audio_urls": media_info.get('audio_urls', []),
                            "video_urls": media_info.get('video_urls', []),
                            "iframe_srcs": media_info.get('iframe_srcs', [])
                        }
                    }
                else:
                    # If web scraping also failed, return basic info
                    print(f"Web scraping fallback failed, using basic info")
                    return {
                        "title": f"Podcast_{sanitize_filename(podcast_url)}",
                        "url": podcast_url,
                        "platform": determine_platform(podcast_url),
                        "is_episode": is_episode_url(podcast_url),
                        "error": str(e)
                    }
        
        if output:
            try:
                # Try parsing as JSON
                info = json.loads(output)
                return {
                    "title": info.get("series", info.get("channel", info.get("title", "Unknown Podcast"))),
                    "channel": info.get("channel", ""),
                    "channel_url": info.get("channel_url", ""),
                    "description": info.get("description", ""),
                    "url": podcast_url,
                    "platform": determine_platform(podcast_url),
                    "is_episode": is_episode_url(podcast_url) or bool(info.get("_type") == "video")
                }
            except json.JSONDecodeError:
                # If not JSON, try extracting from stdout
                title = re.search(r'"([^"]+)"', output)
                if title:
                    return {
                        "title": title.group(1),
                        "url": podcast_url,
                        "platform": determine_platform(podcast_url),
                        "is_episode": is_episode_url(podcast_url)
                    }
        
        # Fallback if we couldn't get info from yt-dlp
        return {
            "title": f"Podcast_{sanitize_filename(podcast_url)}",
            "url": podcast_url,
            "platform": determine_platform(podcast_url),
            "is_episode": is_episode_url(podcast_url)
        }
    except Exception as e:
        print(f"Warning: Could not fetch podcast info: {e}")
        return {
            "title": f"Podcast_{sanitize_filename(podcast_url)}",
            "url": podcast_url,
            "platform": determine_platform(podcast_url),
            "is_episode": is_episode_url(podcast_url),
            "error": str(e)
        }

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
    elif ".rss" in url or "/rss" in url or "/feed" in url:
        return "RSS Feed"
    else:
        return "Unknown Platform"

def process_podcast(podcast_url, download_dir, subkind=None):
    """
    Process a podcast URL, extracting and downloading episodes.
    
    Args:
        podcast_url: URL of the podcast page or feed
        download_dir: Directory to save the downloaded files
        subkind: Optional parameter to specify download behavior
                 'latest': Only download the latest episode
                 'recent5': Download 5 most recent episodes
                 'recent10': Download 10 most recent episodes
                 'episode': Process URL as a single episode
                 'all': Download all episodes (default)
    
    Returns:
        Boolean indicating success or failure
    """
    # Ensure yt-dlp is installed
    if not check_yt_dlp_installed():
        return False
    
    # Clean up the URL if needed
    podcast_url = podcast_url.strip()
    
    print(f"Processing podcast URL: {podcast_url}")
    
    # Create output directory
    output_dir = Path(download_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create archive file to track downloaded episodes
    archive_file = output_dir / "downloaded.txt"
    
    # Get podcast information
    podcast_info = get_podcast_info(podcast_url)
    print(f"Podcast title: {podcast_info.get('title', 'Unknown Title')}")
    
    # Determine if this is a single episode URL
    is_single_episode = podcast_info.get("is_episode", False) or subkind == 'episode'
    
    if is_single_episode:
        print("Detected URL points to a specific episode.")
        
    # Save basic podcast info
    with open(output_dir / "podcast_info.json", "w", encoding="utf-8") as f:
        json.dump(podcast_info, f, indent=4, ensure_ascii=False)
    
    # Check if we need to use the scraping fallback
    if 'scraped_media' in podcast_info and (
            podcast_info['scraped_media'].get('audio_urls') or 
            podcast_info['scraped_media'].get('video_urls') or
            podcast_info['scraped_media'].get('iframe_srcs')):
        print("Using scraped media URLs as yt-dlp couldn't process the original URL")
        
        # Try audio URLs first
        if podcast_info['scraped_media'].get('audio_urls'):
            print(f"Found {len(podcast_info['scraped_media']['audio_urls'])} direct audio links")
            download_url = podcast_info['scraped_media']['audio_urls'][0]
            print(f"Using first audio URL: {download_url}")
        # Then try video URLs
        elif podcast_info['scraped_media'].get('video_urls'):
            print(f"Found {len(podcast_info['scraped_media']['video_urls'])} video links")
            download_url = podcast_info['scraped_media']['video_urls'][0]
            print(f"Using first video URL: {download_url}")
        # Then try iframes, which might contain playable content
        elif podcast_info['scraped_media'].get('iframe_srcs'):
            print(f"Found {len(podcast_info['scraped_media']['iframe_srcs'])} iframe sources")
            # For iframes, we need to check if they're from known platforms that yt-dlp can handle
            iframe_url = podcast_info['scraped_media']['iframe_srcs'][0]
            
            # These are platforms we know yt-dlp can handle
            supported_iframe_domains = [
                'spotify.com', 'youtube.com', 'soundcloud.com', 'apple.com/podcasts', 
                'simplecast.com', 'anchor.fm', 'podbean.com'
            ]
            
            if any(domain in iframe_url for domain in supported_iframe_domains):
                print(f"Using iframe from supported platform: {iframe_url}")
                download_url = iframe_url
            else:
                print(f"No supported media found in iframe sources")
                download_url = podcast_url  # Fallback to original URL
        else:
            # No useful media found, try the original URL
            print("No media URLs found in scraping, falling back to original URL")
            download_url = podcast_url
    else:
        # No scraping results or scraping wasn't needed, use the original URL
        download_url = podcast_url
    
    # Determine how many episodes to download
    playlist_option = ""
    if is_single_episode:
        print("Processing as a single episode.")
        # No playlist option needed - will download just this episode
    elif subkind == 'latest':
        print("Downloading only the latest episode.")
        playlist_option = "--playlist-items 1"
    elif subkind == 'recent5':
        print("Downloading 5 most recent episodes.")
        playlist_option = "--playlist-items 1-5"
    elif subkind == 'recent10':
        print("Downloading 10 most recent episodes.")
        playlist_option = "--playlist-items 1-10"
    else:
        print("Downloading all available episodes.")
    
    # Add random delay to avoid rate limiting
    time.sleep(random.uniform(1, 3))
    
    # Construct the yt-dlp command
    cmd = [
        "yt-dlp",
        "-x",  # Extract audio
        "--audio-format", "mp3",  # Convert to mp3
        "--audio-quality", "0",  # Best quality
        "--add-metadata",  # Add metadata to the file
        "--write-info-json",  # Write episode metadata to JSON
        "--download-archive", str(archive_file),  # Track downloaded episodes
        "--embed-thumbnail",  # Embed thumbnail if available
        "--embed-chapters",  # Embed chapters if available
        "--no-overwrites",  # Don't overwrite existing files
        "--retries", "3",  # Retry 3 times if download fails
    ]
    
    # Single episode URLs should not be treated as playlists
    if is_single_episode:
        cmd.append("--no-playlist")
    
    # For non-episode URLs (feed/show URLs), we may need to handle playlist differently
    if not is_single_episode:
        cmd.append("--verbose")  # More detailed output for multi-episode downloads
        cmd.append("--ignore-errors")  # Continue on errors with individual episodes
    
    # Platform-specific optimizations
    platform = podcast_info.get("platform", "")
    if platform == "Apple Podcasts":
        cmd.extend(["--add-header", "User-Agent:Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"])
    elif platform == "Spotify":
        cmd.append("--cookies-from-browser")
        cmd.append("chrome")  # You can change this to your preferred browser
    elif platform == "YouTube":
        print("Applying YouTube-specific optimizations")
        # Add browser cookies to authenticate with YouTube
        cmd.append("--cookies-from-browser")
        cmd.append("chrome")  # Change to 'firefox', 'safari', etc. based on your preferred browser
        
        # Add user agent to appear more like a browser
        cmd.extend(["--add-header", 
                    "User-Agent:Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"])
        
        # Add options to help bypass YouTube restrictions
        cmd.append("--extractor-args")
        cmd.append("youtube:player_client=web")
        
        # Bypass geo-restrictions and rate limiting
        cmd.append("--geo-bypass")
        
        # Add sleep before each download to avoid rate limiting
        cmd.append("--sleep-requests")
        cmd.append("1")
        
        # Try to bypass age gates
        cmd.append("--age-limit")
        cmd.append("21")
        
        # Allow download options fallback
        cmd.append("--format-sort")
        cmd.append("res,ext:mp4:m4a")
    elif platform == "Komodor":
        print("Applying Komodor-specific optimizations")
        # Add user agent for browser-like requests
        cmd.extend(["--add-header", 
                    "User-Agent:Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"])
        
        # Add sleep before each download to avoid rate limiting
        cmd.append("--sleep-requests")
        cmd.append("1")
        
        # Use cookies from browser to handle potential auth
        cmd.append("--cookies-from-browser")
        cmd.append("chrome")
    
    # Set output path and format
    # For single episodes, prioritize title in the filename
    if is_single_episode:
        cmd.extend([
            "--paths", str(output_dir),
            "--output", "%(title)s.%(ext)s"
        ])
    else:
        cmd.extend([
            "--paths", str(output_dir),
            "--output", "%(upload_date)s-%(title)s.%(ext)s"
        ])
    
    # Add playlist option if specified and not a single episode
    if playlist_option and not is_single_episode:
        cmd.append(playlist_option)
    
    # Use the download URL which might be different from original URL if we found media through scraping
    cmd.append(download_url)
    
    # Execute the command
    try:
        print(f"Executing: {' '.join(cmd)}")
        
        # Run the command
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        # Process output to extract important information
        output_lines = []
        for line in result.stdout.split('\n'):
            if any(x in line for x in ["Destination", "download", "Extracting URL", "Writing metadata"]):
                output_lines.append(line)
        
        # Update podcast info with results
        podcast_info["status"] = "success"
        podcast_info["download_date"] = time.strftime("%Y-%m-%d %H:%M:%S")
        podcast_info["download_command"] = " ".join(cmd)
        
        # Count downloaded episodes
        mp3_files = list(output_dir.glob("*.mp3"))
        podcast_info["episodes_count"] = len(mp3_files)
        podcast_info["episodes"] = [f.name for f in mp3_files]
        
        # Save updated podcast info
        with open(output_dir / "podcast_info.json", "w", encoding="utf-8") as f:
            json.dump(podcast_info, f, indent=4, ensure_ascii=False)
        
        print(f"Successfully processed podcast. Downloaded {len(mp3_files)} episodes.")
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"Error downloading podcast: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        
        # If download failed, and we haven't tried direct download yet, attempt to manually download audio
        if 'scraped_media' in podcast_info and podcast_info['scraped_media'].get('audio_urls'):
            print("Attempting direct download of audio file as fallback")
            try:
                audio_url = podcast_info['scraped_media']['audio_urls'][0]
                output_file = output_dir / f"{sanitize_filename(podcast_info.get('title', 'podcast'))}.mp3"
                
                print(f"Downloading {audio_url} to {output_file}")
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
                }
                
                with requests.get(audio_url, headers=headers, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    with open(output_file, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                
                # Update podcast info with results
                podcast_info["status"] = "success (direct download)"
                podcast_info["download_date"] = time.strftime("%Y-%m-%d %H:%M:%S")
                podcast_info["download_method"] = "direct_download"
                podcast_info["direct_url"] = audio_url
                
                # Count downloaded episodes
                mp3_files = list(output_dir.glob("*.mp3"))
                podcast_info["episodes_count"] = len(mp3_files)
                podcast_info["episodes"] = [f.name for f in mp3_files]
                
                # Save updated podcast info
                with open(output_dir / "podcast_info.json", "w", encoding="utf-8") as f:
                    json.dump(podcast_info, f, indent=4, ensure_ascii=False)
                
                print(f"Successfully downloaded audio file directly.")
                return True
                
            except Exception as download_err:
                print(f"Direct download also failed: {download_err}")
                # Continue to save error information
        
        # Save error information
        podcast_info["status"] = "error"
        podcast_info["error_message"] = str(e)
        podcast_info["download_date"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        with open(output_dir / "podcast_info.json", "w", encoding="utf-8") as f:
            json.dump(podcast_info, f, indent=4, ensure_ascii=False)
        
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python podcast_processor.py <podcast_url> <download_dir> [subkind]")
        sys.exit(1)
    
    podcast_url = sys.argv[1]
    download_dir = sys.argv[2]
    subkind = sys.argv[3] if len(sys.argv) > 3 else None
    
    print(f"podcast_processor.py invoked with URL: {podcast_url}, Download Directory: {download_dir}, SubKind: {subkind}")
    
    success = process_podcast(podcast_url, download_dir, subkind)
    sys.exit(0 if success else 1) 