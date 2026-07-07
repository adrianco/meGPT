---
type: YouTube Talk
title: "Adrian Cockcroft on Chaos Architecture"
description: "Sixth in my series of short videos on technology and architecture topics, this presentation introduces the architectural concepts around Chaos Engineering, and shows how this is an efficient produc..."
resource: "https://www.youtube.com/watch?v=ja6n5etN8hk"
tags:
  - talk
timestamp: "2018-05-30"
author: "Adrian Cockcroft"
---

# Adrian Cockcroft on Chaos Architecture

Sixth in my series of short videos on technology and architecture topics, this presentation introduces the architectural concepts around Chaos Engineering, and shows how this is an efficient productization of difficult to implement and manage existing practices like disaster recovery.

- See https://youtu.be/aBcG57Gw9k0 for the first edition on The Evolution of Business Logic from Monoliths to Microservices, to Functions.
- See https://youtu.be/Y6nKD-sK6tg for the second edition on The New De-Normal - Untangling "Kitchen Sink" Database Schemas.
- See https://www.youtube.com/watch?v=XrWII4ewrXA for March’s edition on Migrating to Cloud.
- See https://youtu.be/mzIdKGCOf1g for the fourth edition on Mapping Your Stack.
- See https://youtu.be/7lDWXtNjVyQ for the fifth edition on Digital Transformation.

Learn more about Adrian’s open source team and related blog posts at - https://amzn.to/2kCeDu2.


## Transcript Excerpt

Kind: captions Language: en hi I'm Adrian khakhra over the years I've given a lot of talks on micro services and cloud architectures there are some ideas I always wanted to illustrate with a short animated sequence so I've worked with a visual design team to come up with a series of animations each illustrating a specific concept this month I'm gonna drill in a bit further to Kaos architecture which is I think of as a cloud native availability model and I start off by talking about my role as an architect when I was trying to figure out a lot of the technologies that we were using at Netflix and my role wasn't to tell other people what the architecture should be my role is really to ask awkward questions that helped other people figure out how to architect their things to meet the user needs that we were talking about and here's his one of the most interesting awkward questions what should your system do when something fails and a lot of people will say I don't want it to fail and you can go around that loop for a few times until you get them to agree that yes it will eventually fail and what should it do and there's two choices really you can either stop or you can carry on maybe with reduced functionality so let's be a bit more specific of permissions lookup fails should you stop or continue and the way to think about this is what's the real cost of continuing and what is this system doing now in the case of Netflix we were showing people movies and if something went wrong internally and we couldn't figure out whether this customer was actually a current customer or a customer that used to be a customer and maybe you know because I say our subscriber service was not was not responding it's okay to just continue because really all you're doing is letting somebody watch a movie for free because it's not their fault it's our fault so the point here is if you if it's the system's fault that you can't tell whether something should happen or not you should just probably ...


## Sources

[1] Video: https://www.youtube.com/watch?v=ja6n5etN8hk
[2] Channel: Amazon Web Services
