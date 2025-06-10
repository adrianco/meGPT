"""
Twitter Archive Conversation Extractor

This script processes a Twitter archive to extract all conversation tweets (replies)
from potentially multiple tweet files.

How to use:
1. Download your Twitter archive
2. Run the script using: python extract_conversations.py
3. Enter the path to your Twitter archive directory when prompted

The script handles:
- Multiple tweet files (tweets.js, tweets-part1.js, tweets-part2.js, etc.)
- Correctly parsing the JavaScript-wrapped JSON data
- Identifying tweets that are part of conversations by checking:
  - in_reply_to_status_id (indicating replies to specific tweets)
  - in_reply_to_user_id (indicating replies to specific users)

Features:
- Automatically finds all tweet files using glob patterns
- Provides progress updates during processing
- Consolidates conversations from all tweet parts into a single JSON file
- Saves conversations to [archive_directory]/data/conversations.json

Example output:
$ python3 extract_conversations.py
Enter the path to your Twitter archive directory: twitter-2022-11-19-[...]
Processed [...]/data/tweets.js: Found 12931 conversation tweets
Processed [...]/data/tweets-part1.js: Found 1487 conversation tweets
Extracted a total of 14418 conversation tweets to [...]/data/conversations.json
"""

import os
import json
import glob

def extract_conversations(archive_dir, output_file):
    tweet_files = glob.glob(os.path.join(archive_dir, 'data', 'tweets*.js'))
    conversations = []

    for tweet_file in tweet_files:
        if os.path.exists(tweet_file):
            with open(tweet_file, 'r') as f:
                content = f.read()
            
            # Find the JSON array within the JavaScript file
            json_content = content[content.index('['): content.rindex(']') + 1]
            tweets = json.loads(json_content)

            # Extract tweets that are part of conversations
            conversation_tweets = [
                tweet for tweet in tweets 
                if tweet.get('tweet', {}).get('in_reply_to_status_id') or tweet.get('tweet', {}).get('in_reply_to_user_id')
            ]
            conversations.extend(conversation_tweets)
            print(f"Processed {tweet_file}: Found {len(conversation_tweets)} conversation tweets")
    
    # Save conversations to a new file
    with open(output_file, 'w') as f:
        json.dump(conversations, f, indent=2)
        print(f"Extracted a total of {len(conversations)} conversation tweets to {output_file}")

if __name__ == "__main__":
    archive_directory = input("Enter the path to your Twitter archive directory: ")
    output_filename = "conversations.json"
    
    if os.path.exists(archive_directory) and os.path.isdir(archive_directory):
        output_path = os.path.join(archive_directory, 'data', output_filename)
        extract_conversations(archive_directory, output_path)
    else:
        print("Invalid directory path")
