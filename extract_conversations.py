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
