---
type: YouTube Talk
title: "Managing Failure Modes in Microservice Architectures"
description: "QCon San Francisco, the international software conference, returns November 17-21, 2025. Join senior software practitioners from early adopter companies as they share real-world insights and action..."
resource: "https://www.youtube.com/watch?v=v5Gwi9AYvm4"
tags:
  - talk
timestamp: "2020-01-27"
author: "Adrian Cockcroft"
---

# Managing Failure Modes in Microservice Architectures

QCon San Francisco, the international software conference, returns November 17-21, 2025. Join senior software practitioners from early adopter companies as they share real-world insights and actionable advice to help you adopt the right technologies and practices.

Gain exposure to innovative approaches and fresh ideas in software development and engineering, designed to inspire and challenge you.

Don’t miss this chance to deepen your knowledge, sharpen your skills, and stay ahead in the ever-evolving world of technology.

Register now: https://bit.ly/3BYzfbe
----------------------------------------------------------------------------------------------
Video with transcript included: http://bit.ly/37sXxG0

Adrian Cockcroft explores how to apply some industry standard techniques (including Failure Modes and Effects Analysis) to cloud native microservices architectures. He looks at how chaos engineering techniques are driving the industry from annual datacenter disaster recovery testing of monolithic applications to continuous resilience assurance for cloud native microservices.

This presentation was recorded at QCon San Francisco 2019: http://bit.ly/38sivWf

#SoftwareArchitecture #Microservices #Resilience


## Transcript Excerpt

Kind: captions Language: en This is new content. Um it's pretty much the first time I presented it. I wrote I was working on my slides yesterday. And this is really the first of an installment of things. So I'm setting out the groundwork for some work I'm expecting to do a lot more on in 2020. And first I want to start with like why why do I care about this? And this is what's really happening. Um I'm starting to see more of AWS customers not just move like the front end or the back end for a mobile app or something like that to the cloud. They're closing all their data centers. They're moving everything to the cloud. This includes airlines. I want air I'm a power user of airlines. I want all the airlines that can be keep flying. Um finance, health care, manufacturing. We have substantial businesses that are moving their critical infrastructure. And they're moving that to the cloud. So as they do that, we've got to develop the patterns that make that work reliably. And we've got to understand the failure modes. We've got to have a much more sophisticated discussion about what could go wrong and what to do. So that's why I'm why I'm sort of poking at this. And if anyone wants to talk about that, if you're in a safety critical industry, very happy to continue the conversation. So in the past, we had disaster recovery. Back in the '70s they started. You had a mainframe over here and you could have another mainframe over there and you copy stuff back and forth and if something went wrong, you could switch to the other one. That was sort of the traditional disaster recovery model. That then became more institutionalized in that well, I have a backup data center. I'll talk a bit more about that later. Then um I guess you know, between Amazon and Netflix and a few other people, we came up with chaos engineering a decade or so ago. And we were starting to induce failure. The The difference in chaos engineering is it's API driven. Everything was highly automated. So we could ...


## Sources

[1] Video: https://www.youtube.com/watch?v=v5Gwi9AYvm4
[2] Channel: InfoQ
