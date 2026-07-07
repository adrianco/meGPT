---
type: YouTube Talk
title: "Migrating to Cloud Native with Microservices • Adrian Cockcroft • GOTO 2014"
description: "This presentation was recorded at GOTO Berlin 2014
http://gotober.com

Adrian Cockcroft - Technology Fellow & Architect Behind Netflix Cloud Infrastructure @adriancockcroft 

ABSTRACT
Traditional e..."
resource: "https://www.youtube.com/watch?v=DvLvHnHNT2w"
tags:
  - talk
timestamp: "2014-12-15"
author: "Adrian Cockcroft"
---

# Migrating to Cloud Native with Microservices • Adrian Cockcroft • GOTO 2014

This presentation was recorded at GOTO Berlin 2014
http://gotober.com

Adrian Cockcroft - Technology Fellow & Architect Behind Netflix Cloud Infrastructure @adriancockcroft 

ABSTRACT
Traditional enterprise architectures are based on monolithic applications and relational databases. Cloud native architectures are based on building single function REST-based microservices [...]

Download slides and read the full abstract here:
http://gotocon.com/berlin-2014/presentation/Migrating%20to%20Cloud%20Native%20with%20Microservices

RECOMMENDED BOOKS
Liz Rice • Container Security • https://amzn.to/3oU4iJe
Liz Rice • Kubernetes Security • https://www.oreilly.com/library/view/kubernetes-security/9781492039075
Brendan Burns, Joe Beda & Kelsey Hightower • Kubernetes: Up and Running • https://amzn.to/3wrtwlp
John Arundel & Justin Domingus • Cloud Native DevOps with Kubernetes • https://amzn.to/3hKZvI5
Kasun Indrasiri & Sriskandarajah Suhothayan • Design Patterns for Cloud Native Applications • https://amzn.to/3yCFxWE
Michael Hausenblas & Stefan Schimanski • Programming Kubernetes • https://amzn.to/3qTvKch
Alexander Raul • Cloud Native with Kubernetes • https://amzn.to/3yw9ckc
Nigel Poulton • The Kubernetes Book • https://amzn.to/3dW8ViU
Marko Luksa • Kubernetes in Action • https://amzn.to/3dXk2Im

https://twitter.com/gotober
https://www.facebook.com/GOTOConference
http://gotocon.com
#CloudNative #Microservices

Looking for a unique learning experience?
Attend the next GOTO conference near you! Get your ticket at https://gotopia.tech
Sign up for updates and specials at https://gotopia.tech/newsletter


## Transcript Excerpt

Kind: captions Language: en [Music] so I've been giving versions of this talk for quite a long time and several years and for a long time it felt like you could summarize it up as baffling later doctors as a service that was what I did that was that was my job to go out and talk about these things people just get baffled by it so I'm going to sort of go through how that evolved over time and so starting in 2009 we started talking about Netflix doing stuff in the cloud and everyone just said we're just crazy people and we weren't even doing that we couldn't there's no way we could be possibly doing that we were just trying to get some press and making stuff up um what we actually did in 2009 was we moved the movie encoding back end which is several thousand machines because we only had a few hundred machines in the data center and we had to encode more and more movies so the encoding was a huge back job it's not customer facing if anything went wrong with it it didn't matter we use that as the first test to see how the relationship with AWS would work right it was a fairly large scale we ended up with several probably a few thousand machines in that account and we developed the support relationship but it was not customer facing so if you're looking at moving to the cloud working with a cloud vendor for the first time put something that's not customer facing but is as big as you can get so big batch processing kind of jobs is good the other thing that moved to the cloud then was the logging we overflowed the dis space in the data center for all the logging information so we started writing it to S3 and then we started processing it in the cloud by using Hadoop in the cloud and we used Amazon's EMR because it was easy and then it just stayed easy so Netflix is one of the big users of the elastic map reduce function that Amazon has and uh well these people that keep complaining it's hard to install hop clusters I have no understanding of what that's about CU you just s ...


## Sources

[1] Video: https://www.youtube.com/watch?v=DvLvHnHNT2w
[2] Channel: GOTO Conferences
