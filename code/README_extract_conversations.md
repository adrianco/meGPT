# Extract Conversations from Twitter Archive

In a Twitter archive, the presence of files like `tweets.js`, `tweets-part1.js`, `tweets-part2.js`, etc., indicates that your tweet data has been split into multiple parts due to the large number of tweets. Twitter splits these files to make it easier to manage and process the data without hitting file size limits.

## Twitter Archive File Structure

- **`tweets.js`**: Contains the first portion of your tweet data. This file is usually named `tweets-part0.js` in the context of multiple parts but is sometimes simply called `tweets.js` if there's only one part or if it is the first file.

- **`tweets-part1.js`**, **`tweets-part2.js`**, etc.: These are additional parts containing subsequent tweets. They follow the same structure as `tweets.js` but contain different tweet data.

Each file typically has the following structure:

```js
window.YTD.tweets.part0 = [ ... ];
window.YTD.tweets.part1 = [ ... ];
window.YTD.tweets.part2 = [ ... ];
```

The variable `window.YTD.tweets.partX` indicates which part of the tweet data is being represented. The JSON array following the assignment contains tweet objects.

## Using the Extraction Script

To extract all your conversation tweets from a Twitter archive:

1. Download your Twitter archive from Twitter.
2. Run the `extract_conversations.py` script using:
   ```
   python code/extract_conversations.py
   ```
3. When prompted, enter the path to your Twitter archive directory.
4. The script will extract all conversation tweets and save them to a `conversations.json` file in the archive's data directory.

## What Gets Extracted

The script identifies and extracts tweets that are part of conversations, which includes:
- Tweets with a non-null `in_reply_to_status_id` (indicating they are replies to specific tweets)
- Tweets with a non-null `in_reply_to_user_id` (indicating they are replies to another user's tweet)

This allows you to focus on the interactive parts of your Twitter history rather than standalone tweets or retweets.

