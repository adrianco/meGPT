# meGPT - upload an author's content into an LLM

I have 20 years of public content I've produced and presented over my career, and I'd like to have an LLM that is trained to answer questions and generate summaries of my opinions, in my "voice", At this point, I've found a few companies that are building persona's and tried out soopra.ai. To encourage development and competition in this space I have organized my public content and references to sources in this repo.  

My own content is stored or linked to in authors/virtual_adrianco and consists of:
- 4 published books (pdf of two provided), ~10 forewords to books, ~100 blog posts (text)
- Twitter archive 2008-2022 (conversation text)
- Mastodon.social - 2021-now https://mastodon.social/@adrianco (RSS at https://mastodon.social/@adrianco.rss)
- Github projects (code)
- Blog posts from https://adrianco.medium.com extracted as text to authors/virtual_adrianco/medium_posts (with extraction script)
- Blog posts from https://perfcap.blogspot.com extracted as text to authors/virtual_adrianco/blogger_percap_posts (with extraction script)
- ~100 presentation decks (images) greatest hits: https://github.com/adrianco/slides/tree/master/Greatest%20Hits
- ~20 podcasts (audio conversations, should be good Q&A training material)
- ~50 videos of talks and interviews (audio/video/YouTube playlists)

If another author wants to use this repo as a starting point, clone it and add your own directory of content under authors. If you want to contribute the content freely for other people to use as a training data set, then send a pull request and I'll include it here. The scripts in the code directory are there to help pre-process content for an author by extracting from a twitter or medium archive that has to be downloaded by the account owner.

Creative Commons - attribution share-alike. Permission explicitly granted for anyone to use as a training set to develop the meGPT concept. Free for use by any author/speaker/expert resulting in a Chatbot that can answer questions as if it was the author, with reference to published content. I have called my own build of this virtual_adrianco - with opinions on cloud computing, sustainability, performance tools, microservices, speeding up innovation, Wardley mapping, open source, chaos engineering, resilience, Sun Microsystems, Netflix, AWS etc. etc. I'm happy to share any models that are developed. I don't need to monetize this, I'm semi-retired and have managed to monetize this content well enough already, I don't work for a big corporation any more..

# I am not a Python programmer
All the code in this repo was initially written by the free version of ChatGPT 4 or Cursor Claude Sonnet3.7 based on short prompts, with no subsequent edits, in a few minutes of my time here and there. I can read Python and mostly make sense of it but I'm not an experienced Python programmer. Look in the relevant issue for a public link to the chat thread that generated the code fro ChatGPT.  When I transitioned to Cursor I got the context included as a block comment at the start of each file. This is a ridiculously low friction and easy way to write simple code. Development was migrated to Cursor as it has a much better approach to managing the context of a whole project.

# YouTube Downloads
YouTube has strict bot detection measures that can make automatic downloads challenging. The script attempts multiple methods to download YouTube content:

1. First, it tries advanced options with yt-dlp to bypass the "Sign in to confirm you're not a robot" check
2. If that fails, it attempts to use pytube with OAuth (may require user interaction)
3. Next, it tries using alternative client settings for yt-dlp
4. Finally, it attempts to download via an Invidious proxy

Despite these measures, YouTube's bot detection is sophisticated and some videos may still fail to download automatically. In such cases, you may need to download the videos manually.

For best results, you can try:
- Using a different network (some IP addresses are more likely to trigger bot detection)
- Using a VPN
- Downloading from mobile networks (often has fewer restrictions)
- Downloading directly from Invidious instances (e.g., https://invidious.snopyta.org) 

# Building an Author
To use this repo, clone it to a local disk, setup the python environment, run the build.py script for an author and it will walk through the published content table for that author processing each line in turn. The build script will create a downloads/<author> directory and create a state.json file in it which records successful processing steps so that incremental runs of build.py will not re-run the same downloads. Each kind of data needs a corresponding script in the processors directory.

```
git clone https://github.com/adrianco/megpt.git
cd megpt
python3 -m venv venv
```
Windows:
```
venv\Scripts\activate
```
macOS/Linux:
```
source venv/bin/activate
```
```
pip install -r requirements.txt
```

If any additional packages are installed during development, regenerate requirements via
```
pip freeze > requirements.txt
```

Run the build script
```
Usage: build.py <author>
python build.py virtual_adrianco
```

For test purposes process a single kind of data from an arbitrary URL, output to downloads without updating the state.json file
```
Usage: python process.py <author> <Kind> <SubKind> <URL>
```

# Creating a RAG based LLM Persona
See this presentation for details on how to get RAGs to work better https://github.com/datastaxdevs/conference-2024-devoxx/
See this issue https://github.com/adrianco/meGPT/issues/11 for my experiments using soopra.ai - currently trained on a subset of this content, and try it out at https://app.soopra.ai/Cockcroft/chat

# Current functional status
Build.py and process.py appear to be operating correctly.
book_processor.py correctly downloads pdfs of books, and extracts page ranges so that relevant sections can be picked out, or mutiple authors can be separated.
Each story download is going to need customized extraction, and the correct div name for The New Stack (thenewstack.io) has been added as a Subkind, and correct text content download is working for the story kind of content.
Medium blog downloads are processed from an archive that can be requested by the author, into text files in the author's medium_posts directory.
Blogger.com archives are processed into text files that include URLs to the original story.
Twitter archives are processed to extract conversations from the archive, ignoring anything other than public tweets that were part of a conversation involving more than one tweet. The archive I used was saved before the naming transition from Twitter to X.

# Notes
I have been assembling my content for a while, and will update the references table and medium download now and again https://github.com/adrianco/meGPT/blob/main/authors/virtual_adrianco/published_content.csv

YouTube videos have transcripts with index offsets into the video itself but the transcript quality isn't good, and they can only be read via API by the owner of the video. It's easier to download videos with pytube and process them with whisper to generate more curated transcripts that identify when the author is talking if there is more than one speaker.

Twitter archive - the raw archive files were over 100MB and too big for github. The extract_conversations script was used to pull out only the tweets that were part of a conversation, so they can be further analyzed to find questions and answers. The code to do this was written by ChatGPT, worked first time, but if there are any problems with the output I'm happy to share the raw tweets. File an issue.

Mastodon archive - available as an RSS feed.

Medium blog platform - available as an RSS feed of the last ten posts. Archive download is processed by code/medium_posts.py to extract text of public posts, ignoring drafts.

Issues have been created to track development of ingestion processing code.
