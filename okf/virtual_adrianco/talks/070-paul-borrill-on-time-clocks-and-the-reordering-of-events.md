---
type: YouTube Talk
title: "Paul Borrill on Time clocks and the reordering of events"
description: "Mini 

Adrian Cockcroft on Communicating Sequential Processes (http://spinroot.com/courses/summer/Papers/hoare_1978.pdf)



Main Talk

Paul Borrill on Lamport’s unfinished revolution.

This talk re..."
resource: "https://www.youtube.com/watch?v=CWF3QnfihL4"
tags:
  - talk
timestamp: "2016-08-20"
author: "Adrian Cockcroft"
---

# Paul Borrill on Time clocks and the reordering of events

Mini 

Adrian Cockcroft on Communicating Sequential Processes (http://spinroot.com/courses/summer/Papers/hoare_1978.pdf)



Main Talk

Paul Borrill on Lamport’s unfinished revolution.

This talk reviews Lamport’s seminal 1978 paper on Time, Clocks and the Ordering of Events, the 2nd most cited paper in all of computer science.

Almost all software engineers claim to have read it.  Many who haven’t read it, use (and basically understand) the fundamental idea of logical clocks, and their progeny (vector clocks, matrix clocks, etc.). More than a few understand the current state of the art: dotted version vectors and bounded version vectors. Paradoxically, almost everyone missed some of the more subtle concepts, and questions that Lamport introduced in this paper.

In the intervening years. Progress has occurred, and the state of the art has evolved. This talk is therefore in three parts. The first being a review of the paper itself, the concepts it introduced, and the assumptions behind these concepts. The second part reflects what we’ve learned in the intervening years, and especially the relationship of Lamport’s (original) understanding of time, which was superior to almost all other computer scientists at the time, and what (in contrast) we know now. The third part will be entirely devoted to questions and answers: Where anyone can ask a question, and anyone can try to answer it. The speaker will try to answer the question if no one else wants to, or if the audience appears dissatisfied. The discussion is expected to be lively, insightful, and potentially, mind blowing.

In order to prepare yourself for this talk. Anticipate there will come a point where you are asked to take a blue pill vs. a red pill.  If you watch these videos, your red pill transition will be gentler.  Most of you may prefer to take the blue pill and go back to your old way of thinking about time. In which case, you won’t find this talk very interesting, because of course you already know all the answers.

Those who want to be more prepared for the red/blue pill experience, will benefit from both reading the paper, and watching the most recent PBS videos on the nature of spacetime:

1. Does the Speed of Light have anything to do with light?   https://www.youtube.com/watch?v=msVuCEs8Ydo   

PBS Digital Studios.  A 12 minute and 45 second Red Pill: The Speed of Causality

2. Are Space and Time an Illusion/ https://www.youtube.com/watch?v=YycAzdtUIko

An 8 minute and 54 second Red Pill.  The Space Time Illusion

3. The original paper can be found here: http://research.microsoft.com/users/lamport/pubs/time-clocks.pdf



Paul's Bio 

Paul Borrill Recently left the Infrastructure team at Apple. Previously, CEO of REPLICUS Research, REPLICUS Software, VP/CTO for VERITAS Software; VP/Chief Architect for Quantum Corporation; Distinguished Engineer, Director of Architecture & Performance, and Chief Scientist for IR at Sun Microsystems. Paul was Founding Chairman for the Storage Networking Industry Association (SNIA). He served as VP of Technical activities and VP Standards for the IEEE Computer Society. His passion for dependable computing came from designing systems and software for an experiment which performed extraordinarily well on NASA’s Space Shuttle. Paul earned his Ph.D in physics from University College London and is a graduate of the Stanford Executive Program.

And for fun … Paul likes to skydive out of Russian Jets over the North Pole, scuba dive with sharks and investigate the implications of dark matter and dark energy in the universe.

http://www.meetup.com/papers-we-love-too/events/228341271/


## Transcript Excerpt

Kind: captions Language: en [Music] so Adrian works at battery Ventures where he advises the firm and its portfolio companies about technology issues and also assists with the with deal sourcing and due diligence he was a founding member of eBay research Labs developing Advanced mobile applications and even building his own Homebrew phone years before iPhone and Android launch you may also recognize him from his work at Netflix and his many cameos on the hit TV series Mr Robot let's give it up for for [Music] Aden and we have thanks in US Pink Champagne excellent that's the first all right so as in said I work for battery Ventures um and I I look after portfolio companies we have an office couple of blocks from here like all the other VC firms um and I also Tinker around with some technologies and I built some things and I'll get to that this this talk is pretty much about how I ended up with the the path that took me to tinkering with with the latest things I've been playing with and I like networking with interesting people that's all of you guys thanks for coming um and I do lots of talks at conferences and advice people and bit Consulting and things and um yeah and one of the things I noticed lots of stuff was written in go like over the last couple of years companies come in and they say hey we built this thing what did you and any know the VC rest of the VC guys ask you know how much they're selling and who they're selling it to and all those sort of VC questions and how much money did you raise and I ask well what did you write it in how does it scale and they typically everyone's been saying go so go is interesting because it's got extra stuff in it that is based on and people say well go well it's based on communicating sequential processes and a bunch of stuff like that so I'm going to go into some things that kind of lead up to doing fun more fun things with go and this is actually going to be communicating sequential papers because I'm actually going to  ...


## Sources

[1] Video: https://www.youtube.com/watch?v=CWF3QnfihL4
[2] Channel: PapersWeLove
