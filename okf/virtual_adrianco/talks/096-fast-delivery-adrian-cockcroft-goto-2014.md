---
type: YouTube Talk
title: "Fast Delivery • Adrian Cockcroft • GOTO 2014"
description: "This presentation was recorded at GOTO Aarhus 2014
http://gotocon.com

Adrian Cockcroft - Technology Fellow, Architect Behind Netflix Cloud Infrastructure @adriancockcroft 

ABSTRACT
Companies of a..."
resource: "https://www.youtube.com/watch?v=hvFo3Q2PIQ0"
tags:
  - talk
timestamp: "2015-01-05"
author: "Adrian Cockcroft"
---

# Fast Delivery • Adrian Cockcroft • GOTO 2014

This presentation was recorded at GOTO Aarhus 2014
http://gotocon.com

Adrian Cockcroft - Technology Fellow, Architect Behind Netflix Cloud Infrastructure @adriancockcroft 

ABSTRACT
Companies of all sizes and backgrounds are having to deal with the transition to a world where software development is central to their existence and competitiveness. To deliver software products at high velocity requires four things. First, a culture of innovation that can see and respond to opportunities. Second, the data and analytics to evaluate alternatives. Third, a culture that can make decisions and assign resources quickly. Fourth, agile development and self service deployment. A fine grain loosely coupled architecture scales as the team size grows, a freedom and responsibility culture provides autonomy for innovation and fast decision making, unstructured "big data" analytics gets answers quickly, cloud removes the latency of resource allocation, and devops removes the coordination latency that slows down deployment. These ideas have made Netflix very successful, and Adrian is now taking them to a broader audience in his new role at Battery Ventures.

TIMECODES
0:00 Introduction
1:22 Typical reactions to my Netflix talks...
3:53 What I learned from my time at Netflix
9:10 Cloud Adoption
16:19 Process Hand-Off Steps for Product Development on laas
17:30 Process Hand-Off Steps for Feature Development on Paas
18:47 Saas Based Business Application Development
24:11 Non-Destructive Production Updates
25:46 What Happened?
28:48 Separate Concerns with Microservices
31:35 NetflixOSS - High Availability Patterns
32:22 Open Source Ecosystems
33:06 Microservices Development
35:45 Microservice Datastores
38:37 Cloud Native
39:49 Microservice Based Architectures
40:12 "Death Star" Architecture Diagrams
41:19 Continuous Delivery and DevOps
43:02 Netflixoss Hystrix/Turbine Circuit Breaker
44:07 Low Latency SaaS Based Monitors
45:29 Forward Thinking
48:12 Any Questions?

https://twitter.com/gotocon
https://www.facebook.com/GOTOConference
http://gotocon.com

Looking for a unique learning experience?
Attend the next GOTO conference near you! Get your ticket at https://gotopia.tech
Sign up for updates and specials at https://gotopia.tech/newsletter


## Transcript Excerpt

Kind: captions Language: en very happy to be back here I was in uh I was here two years ago and I was just telling jez there was a incident where at the end of my talk that was mostly about Cassandra um somebody asked me a question about solid state discs in Cassandra and the on AWS and they said well what if these discs wear out and I go I I don't care I rent them from AWS I don't have to worry about it SSD wear out then I moved on if any of you have seen Scott Hanselman do one of his Keynotes in the last year this has been turned into an enormous piece of performance art where he goes on about it for about 10 minutes but it happened here on this stage so I'm wondering what will happen from this time maybe someone in the audience will write a keynote no maybe it won't all right okay so I'm going to talk fast delivery hopefully I'll keep you awake since this is the after lunch crowd um so who am I and what have I been doing recently so this this is really my summary of my career in the last four or five years I've been baffling later doctors and I do it as a service so that's basically it um I was the cloud architect for Netflix I was at Netflix for seven years and I'll talk a bit in in a minute about what I'm currently doing but um what I've got next is all the different talks I was giving over that time and what were the reactions to it back in 2009 Netflix said we're going to go to the cloud and most people thought we were just making stuff up there was just you know no way um but we started we ran some encoding some back some non-customer facing stuff was actually running in on AWS in 2009 because we'd run out of space in our data center for movie encoding in 2010 it moved on to okay we believe you are doing something in the cloud but it's not going to work and at the beginning of 2010 the very first piece of customer facing code was actually running on AWS by the end of the year all of the customer facing code was running on AWS basically all of the user interf ...


## Sources

[1] Video: https://www.youtube.com/watch?v=hvFo3Q2PIQ0
[2] Channel: GOTO Conferences
