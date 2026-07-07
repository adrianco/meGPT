---
type: YouTube Talk
title: "Deep Dive into the Cloud Native Open Source with NetflixOSS • Adrian Cockcroft • GOTO 2014"
description: "This presentation was recorded at GOTO Aarhus 2014
http://gotocon.com

Adrian Cockcroft - Technology Fellow, Architect Behind Netflix Cloud Infrastructure @adriancockcroft 

RECOMMENDED BOOKS
Liz R..."
resource: "https://www.youtube.com/watch?v=R2kKmMyqTfc"
tags:
  - talk
timestamp: "2014-11-25"
author: "Adrian Cockcroft"
---

# Deep Dive into the Cloud Native Open Source with NetflixOSS • Adrian Cockcroft • GOTO 2014

This presentation was recorded at GOTO Aarhus 2014
http://gotocon.com

Adrian Cockcroft - Technology Fellow, Architect Behind Netflix Cloud Infrastructure @adriancockcroft 

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

https://twitter.com/gotocon
https://www.facebook.com/GOTOConference
http://gotocon.com

Looking for a unique learning experience?
Attend the next GOTO conference near you! Get your ticket at https://gotopia.tech
Sign up for updates and specials at https://gotopia.tech/newsletter


## Transcript Excerpt

Kind: captions Language: en okay hopefully this is what you're here for you were just here for the cartoons uh okay so this a double session um we're going to it's just one continuous set of slides when I gave it last week I ran out of time so I'll try and go a little bit faster at the beginning this time and um there's a little bit of audience participation coming up so don't all fall asleep uh I'm I'm Adrian ccraft I was previously with Netflix and I was in uh Aus two years ago presenting about the Netflix architecture and open source and things uh didn't come last year we sent um I think it was Ben Christensen who talked about reactive and RX Java and things uh Roslin meshenberg would come and talk about the Netflix Open Source tools but he couldn't leave uh probably something to do with launching Netflix in Germany Austria France Belgium Luxembourg and Lin or something um which happened last week I think they got a bit too busy so uh I offered to give this so this is a extended version of a talk that was originally given at the Amazon reinvent conference last fall which is why the background is black because that's the template that Amazon gave us um and I'm going to go through the different open- Source projects that Netflix has put up and try and explain what they are and how they fit together and you'll sort of get get some idea of the Netflix Cloud native architecture from just looking at all these projects and I can talk a bit about why they are the way they are and some of the non-obvious things but you know this is all code that's on GitHub all right so to start with I'm going to assume that you you've started off when you you had an architecture sort of Ruby on Rails running on a single Amazon Zone you've got a mic SQL Server you've got a middle tier machine maybe a handful of front ends and a handful of customers okay so that's a typical starting point we see this a lot uh I know work for a venture capital company and we see lots of companies that have  ...


## Sources

[1] Video: https://www.youtube.com/watch?v=R2kKmMyqTfc
[2] Channel: GOTO Conferences
