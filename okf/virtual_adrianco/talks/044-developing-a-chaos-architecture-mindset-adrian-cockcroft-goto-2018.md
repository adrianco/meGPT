---
type: YouTube Talk
title: "Developing a Chaos Architecture Mindset • Adrian Cockcroft • GOTO 2018"
description: "This presentation was recorded at GOTO Chicago 2018. #gotocon #gotochgo
http://gotochgo.com

Adrian Cockcroft - Vice President Cloud Architecture Strategy at Amazon Web Services @adriancockcroft 

..."
resource: "https://www.youtube.com/watch?v=vHl7EZ5o0uY"
tags:
  - talk
timestamp: "2018-09-28"
author: "Adrian Cockcroft"
---

# Developing a Chaos Architecture Mindset • Adrian Cockcroft • GOTO 2018

This presentation was recorded at GOTO Chicago 2018. #gotocon #gotochgo
http://gotochgo.com

Adrian Cockcroft - Vice President Cloud Architecture Strategy at Amazon Web Services @adriancockcroft 

ABSTRACT
We’ve seen cloud usage patterns begin with a faster data center and greenfield applications, move to cloud-native migrations, and end up with complete data center replacement strategies. These patterns are driving even more business-critical backend workloads to the cloud, and new patterns are emerging for highly automated, available, and durable cloud-based [...]

Download slides and read the full abstract here:
https://gotochgo.com/2018/sessions/454

RECOMMENDED BOOKS
Aaron Rinehart • Security Chaos Engineering • https://www.verica.io/sce-book
Nora Jones & Casey Rosenthal • Chaos Engineering • https://www.verica.io/book
Nora Jones & Casey Rosenthal • Chaos Engineering • https://amzn.to/3hUmuAH
Mikolaj Pawlikowski • Chaos Engineering • https://amzn.to/2SQ5Olf
Russ Miles • Learning Chaos Engineering • https://amzn.to/3hCiUe8
Murphy, Beyer, Jones & Petoff • Site Reliability Engineering • https://amzn.to/2Vg6Mbr

https://twitter.com/gotochgo
https://www.facebook.com/GOTOConference
http://gotocon.com
#ChaosArchitecture #ChaosEngineering #CloudNative #SoftwareArchitecture

Looking for a unique learning experience?
Attend the next GOTO Conference near you! Get your ticket at http://gotocon.com

SUBSCRIBE TO OUR CHANNEL - new videos posted almost daily.
https://www.youtube.com/user/GotoConferences/?sub_confirmation=1


## Transcript Excerpt

Kind: captions Language: en [Music] hello everybody again anyone who didn't make it to the keynote earlier you're one of the little events that didn't happen things we were talking about selection bias for people that didn't turn up to my keynote but anyway I'm gonna go through talking about chaos architecture right now for me this is this really comes out of it being the availability model for a cloud native applications if you're trying to build stuff that is really cloud native taking advantage of all the things well how should you think about the the right model for building highly available applications then so I'm gonna start off with some questions because back when I was a overall you know architect I was the overall architect at Netflix and my job then wasn't to tell people what the architecture should be it was the US people awkward questions and try and get people to remember these awkward questions and ask each other those awkward questions and that helped steer people into a good architecture certainly go through a few of these questions and this is this is one of those questions what should your system do when something fails and the usual responses I don't want it to fail and then you go around now a couple of hours later you finally admit that what if when it fails it should do something and it's going to have to do one of two things and it's either going to have to stop because you're not sure what state everything's in and that's worrying because doing things to start or it's going to carry on with some kind of reduced functionality all right and maybe you can hide the failure enough if you're careful to make sure that it carries on or ignores the fact that something's failed so there's that sort of the thing but that's basically the two choices you get and let's be a bit more specific of permissions lookup fails what's the right thing to do there this is becomes a bit more application dependent because a lot of the time people go if something fail ...


## Sources

[1] Video: https://www.youtube.com/watch?v=vHl7EZ5o0uY
[2] Channel: GOTO Conferences
