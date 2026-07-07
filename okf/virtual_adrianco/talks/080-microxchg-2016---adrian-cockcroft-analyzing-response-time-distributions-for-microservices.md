---
type: YouTube Talk
title: "microXchg 2016 - Adrian Cockcroft : Analyzing Response Time Distributions for Microservices"
description: "The end to end response time of a network of microservices tends to have a wide distribution with a long tail at the 99th percentile, even if the mean is short. By collecting the response time dist..."
resource: "https://www.youtube.com/watch?v=5DPr4x76nvQ"
tags:
  - talk
timestamp: "2016-02-05"
author: "Adrian Cockcroft"
---

# microXchg 2016 - Adrian Cockcroft : Analyzing Response Time Distributions for Microservices

The end to end response time of a network of microservices tends to have a wide distribution with a long tail at the 99th percentile, even if the mean is short. By collecting the response time distributions and throughput for request traces we can see how the individual microservices respond, but to combine these distributions and find which microservice is contributing the most to the 99th percentile requires application of montecarlo simulation. This talk will explain how this technique works and investigate tools ranging from Excel plugins to R packages that can implement montecarlo models.


## Transcript Excerpt

Kind: captions Language: en right yeah slides okay ready to get going all right so just listening to a band called black tiger which you've never heard before because it's unreleased and the songs called don't look back so don't look back on your monolith as you go to microservices so I help write that song about 35 years ago that was the May yeah when I was in college band and we have a few mp3s of slightly crappy recordings of it anyway so this is trying to just set you up here for this afternoon when Russ will be playing live guitar on stage because he does that so I just don't miss Russ this afternoon anyway so this is interesting for me I finished writing these slides this morning it talks about code that was written yesterday during some of the presentations I planned on doing it all over Christmas and didn't quite get there so it got done at the last minute I also what I wanted to do was talk about something since this is one of the sort of conferences where we all I assume that everyone already knows about micro services I wanted to talk about something that would be new and interesting and sort of push the boundaries a bit so this is really a research paper I did post the slides I tweeted it so slideshare.net slash Adrian Cockcroft these slides are up there if you find any bugs and my go code then you can point them out to me all right so first of all introduce myself a little bit I work for a venture capital firm called Battery Ventures so 30 35 year old firm based in Boston Tel Aviv and Silicon Valley I'm based in Silicon Valley so we have an office in Menlo Park another one in San Francisco and I obviously do that due diligence stuff helps portfolio companies with scaling and moving to micro services and all that kind of stuff network with interesting people that's all a few people today so by definition you're in the audience so part of my job is to just build an interesting network of people that might want to do startups or might want to work at a sta ...


## Sources

[1] Video: https://www.youtube.com/watch?v=5DPr4x76nvQ
[2] Channel: microXchg
