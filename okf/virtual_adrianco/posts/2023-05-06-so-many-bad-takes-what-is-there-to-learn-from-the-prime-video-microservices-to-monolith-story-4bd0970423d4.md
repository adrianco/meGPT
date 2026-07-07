---
type: Article
title: "So many bad takes — What is there to learn from the Prime Video microservices to monolith story"
description: ""
resource: "https://medium.com/@adrianco/2023-05-06_So-many-bad-takes---What-is-there-to-learn-from-the-Prime-Video-microservices-to-monolith-story-4bd0970423d4"
tags:
  - article
---

# So many bad takes — What is there to learn from the Prime Video microservices to monolith story






## Excerpt

[URL] https://medium.com/@adrianco/2023-05-06_So-many-bad-takes---What-is-there-to-learn-from-the-Prime-Video-microservices-to-monolith-story-4bd0970423d4

So many bad takes — What is there to learn from the Prime Video microservices to monolith story
Excerpt from Serverless First deck first published in 2019
The Prime Video team published this story: Scaling up the audio/video monitoring service and reducing costs by 90%, and the internet piled in with opinions and bad takes, mostly missing the point. What the team did follows the advice I’ve been giving for years (here’s a video from 2019):
“Where needed, optimize serverless applications by also building services using containers to solve for lower startup latency, long running compute jobs, and predictable high traffic”
The Prime Video team had followed a path I call Serverless First, where the first try at building something is put together with Step Functions and Lambda calls. They state in the blog that this was quick to build, which is the point. When you are exploring how to construct something, building a prototype in a few days or weeks is a good approach. Then they tried to scale it to cope with high traffic and discover
...


## Sources

[1] Source: https://medium.com/@adrianco/2023-05-06_So-many-bad-takes---What-is-there-to-learn-from-the-Prime-Video-microservices-to-monolith-story-4bd0970423d4
