import os
import pickle
import re
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import xml.etree.ElementTree as ET

# Define the scopes your application needs
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

def get_credentials():
    creds_filename = 'credentials.pkl'
    if os.path.exists(creds_filename):
        with open(creds_filename, 'rb') as f:
            credentials = pickle.load(f)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'client_secret.json',
            scopes=SCOPES)
        credentials = flow.run_local_server()
        with open(creds_filename, 'wb') as f:
            pickle.dump(credentials, f)
    print(credentials.scopes)
    return credentials

def get_youtube_service(credentials):
    return build('youtube', 'v3', credentials=credentials)

def extract_video_id(url):
    pattern = r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([\w-]+)'
    match = re.match(pattern, url)
    if match:
        return match.group(1)
    else:
        return None

def download_caption(caption_id):
    request = youtube_service.captions().download(
        id=caption_id,
        tfmt='ttml'
    )
    response = request.execute()
    return response

def parse_ttml(ttml_content):
    root = ET.fromstring(ttml_content)
    transcript = []
    for p in root.iter('{http://www.w3.org/ns/ttml}p'):
        text = p.text.strip() if p.text else ''
        transcript.append(text)
    return '\n'.join(transcript)

def get_video_captions(video_id, youtube_service):
    captions = youtube_service.captions().list(
        part='snippet',
        videoId=video_id
    ).execute()

    if 'items' in captions:
        return [(item['id'], item['snippet']['language']) for item in captions['items']]
    else:
        return []

if __name__ == "__main__":
    credentials = get_credentials()
    youtube_service = get_youtube_service(credentials)

    youtube_url = input("Enter the YouTube video URL: ")
    video_id = extract_video_id(youtube_url)
    if not video_id:
        print("Invalid YouTube URL. Please provide a valid YouTube video URL.")
    else:
        captions = get_video_captions(video_id, youtube_service)
        if captions:
            print("Captions found:")
            for caption_id, language in captions:
                caption_content = download_caption(caption_id)
                transcript = parse_ttml(caption_content)
                print(f"Language: {language}")
                print(transcript)
                print()
        else:
            print("No captions found for the specified video.")
