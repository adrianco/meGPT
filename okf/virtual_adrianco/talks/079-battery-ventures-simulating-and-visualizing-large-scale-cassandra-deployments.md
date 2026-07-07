---
type: YouTube Talk
title: "Battery Ventures: Simulating and Visualizing Large Scale Cassandra Deployments"
description: "Speaker: Adrian Cockcroft, Technology Fellow

The SimianViz microservices simulator contains a model of Cassandra that allows large scale global deployments to be created and exercised by simulatin..."
resource: "https://www.youtube.com/watch?v=Ev3rIMLujTM"
tags:
  - talk
timestamp: "2016-03-14"
author: "Adrian Cockcroft"
---

# Battery Ventures: Simulating and Visualizing Large Scale Cassandra Deployments

Speaker: Adrian Cockcroft, Technology Fellow

The SimianViz microservices simulator contains a model of Cassandra that allows large scale global deployments to be created and exercised by simulating failure modes and connecting the simulation to real monitoring tools to visualize the effects. The simulator is open source Go code at github.com/adrianco/spigo and is developing rapidly.


## Transcript Excerpt

Kind: captions Language: en you I wanted to start off by asking so who was here I wasn't a Cassandra summit last year but I think I was up most of the ones before that so I wanted to just summarize a few of the things that if you were around then you might remember some of these things so back in 2011 we did some testing while i was at netflix and on scalability and we were running 24 nodes and we weren't sure what would happen when we went to 48 so we tried scaling up and it kept scaling all the way to 288 so I posted this blog post which datastax then turned into an advert which I kept popping up on websites or the web for the following year or something that's all it scales so that was good and then we we managed to persuade AWS to do solid state disks and then we hoovered up the entire supply of solid state disk based instances for about one year after that so everyone else said well they exist but you can't get them so I'm sorry about that but I did do some nice benchmarking and the bottom right it was very good to see as your this morning launching 90 Cassandra nodes I on stage right because that was three years ago I think I did that with AWS so it's you know good to see them catching up but we would I did Abba side-by-side benchmark of solid-state disk versus regular disks and that was actually one of the most fun presentations I did who they have no idea whether it was going to work and we were linked stuff live on stage and deploying hardware and running a side-by-side benchmark so that was sort of fun anyway so so I used to be at Netflix but I moved on so now i'm at Battery Ventures it's a VC firm and these are all the different things I do now I don't obviously due diligence on deals for the VC firm the companies that come in I advise portfolio companies giving technical support sort of consultant to the CTO scalability cloud migrations Cassandra migrations and I'm responsible now for four or five companies i think switching to cassandra and they've seem ...


## Sources

[1] Video: https://www.youtube.com/watch?v=Ev3rIMLujTM
[2] Channel: PlanetCassandra
