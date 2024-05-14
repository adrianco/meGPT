# meGPT - upload my own stuff into an LLM

I have 30 years of public content I've produced and presented over my career
4 published books, ~10 forewords to books, ~100 blog posts (text)
Twitter and Mastodon archive (conversation text)
~100 presentation decks (images)
~20 podcasts, ~50 videos of talks and interviews (audio/video/YouTube playlists)
Creative Commons - attribution share-alike. Permission explicitly granted for anyone to use as a training set to develop the meGPT concept for use by any author/speaker/expert
Resulting in a Chatbot that can answer questions as if it was me, with reference to published content. I'd call my own build of this virtual_adrianco - with opinions on cloud computing, performance tools, microservices, speeding up innovation, Wardley mapping, open source, chaos engineering, resilience etc. etc. I would share the model. I don't need to monetize this, I'm semi-retired and have managed to monetize this content well enough already, I don't work for a big corporation any more.

# Notes
YouTube videos have transcripts with index offsets into the video itself but the transcript quality isn't good, and they can only be read via API by the owner of the video. It's easier to download videos with pytube and process them with whisper to generate more curated transcripts that identify when the author is talking if there is more than one speaker.

Twitter archive - need to process it to remove DMs, then the rest is public anyway

Mastodon archite - available as an RSS feed. Medium blog platform - available as an RSS feed. Need to import an RSS feed. Also would be good to have this be incremental so that the training material can be updated efficiently as new blog posts and toots appear.
