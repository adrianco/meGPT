# meGPT - upload my own stuff into an LLM

I have 30 years of public content I've produced and presented over my career
- 4 published books, ~10 forewords to books, ~100 blog posts (text)
- Twitter archive 2008-2022 (conversation text)
- Mastodon.social - 2021-now https://mastodon.social/@adrianco (RSS at https://mastodon.social/@adrianco.rss)
- Github projects (code)
- Blog posts mostly at https://adrianco.medium.com
- ~100 presentation decks (images) greatest hits: https://github.com/adrianco/slides/tree/master/Greatest%20Hits
- ~20 podcasts (audio conversations, should be good Q&A training material)
- ~50 videos of talks and interviews (audio/video/YouTube playlists)

Creative Commons - attribution share-alike. Permission explicitly granted for anyone to use as a training set to develop the meGPT concept for use by any *author*/speaker/expert
Resulting in a Chatbot that can answer questions as if it was me, with reference to published content. I'd call my own build of this virtual_adrianco - with opinions on cloud computing, sustainability, performance tools, microservices, speeding up innovation, Wardley mapping, open source, chaos engineering, resilience, Sun Microsystems, Netflix, AWS etc. etc. I would share the model. I don't need to monetize this, I'm semi-retired and have managed to monetize this content well enough already, I don't work for a big corporation any more.

# Notes
I have been assembling my content for a while, and will update the references table now and again https://github.com/adrianco/meGPT/blob/main/Published%20Content%20-%20July%202024.csv

YouTube videos have transcripts with index offsets into the video itself but the transcript quality isn't good, and they can only be read via API by the owner of the video. It's easier to download videos with pytube and process them with whisper to generate more curated transcripts that identify when the author is talking if there is more than one speaker.

Twitter archive - the raw archive files were over 100MB and too big for github. The extract_conversations script was used to pull out only the tweets that were part of a conversation, so they can be further analyzed to find questions and answers. The code to do this was written by ChatGPT, worked first time, but if there are any problems with the output I'm happy to share the raw tweets. File an issue.

Mastodon archive - available as an RSS feed. Medium blog platform - available as an RSS feed. Need to import an RSS feed. Also would be good to have this be incremental so that the training material can be updated efficiently as new blog posts and toots appear.

Issues have been created to track development of ingestion processing code.
