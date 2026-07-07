---
type: YouTube Talk
title: "Developing a Chaos Architecture Mindset - Adrian Cockcroft (AWS)"
description: "Adrian Cockcroft outlines the architectural principles of chaos engineering and shares methods engineers can use to exercise failure modes in safety and business-critical systems

Join us in person..."
resource: "https://www.youtube.com/watch?v=4VleTKY0QAM"
tags:
  - talk
timestamp: "2018-03-01"
author: "Adrian Cockcroft"
---

# Developing a Chaos Architecture Mindset - Adrian Cockcroft (AWS)

Adrian Cockcroft outlines the architectural principles of chaos engineering and shares methods engineers can use to exercise failure modes in safety and business-critical systems

Join us in person at the O'Reilly Software Architecture Conference to learn the tools, techniques, and leadership skills needed in the evolving discipline of software architecture. Learn more: https://oreil.ly/2NNTQQK

Subscribe to O'Reilly on YouTube: http://goo.gl/n3QSYi

Follow O'Reilly on: 
Twitter: http://twitter.com/oreillymedia
Facebook: http://facebook.com/OReilly
Instagram: https://www.instagram.com/oreillymedia
LinkedIn: https://www.linkedin.com/company-beta/8459/


## Transcript Excerpt

Kind: captions Language: en so I'm talking about chaos architecture and then wrap up and get Nora on to tell you how it really works in practice the way I think about chaos architecture is about four layers two teams and an attitude on the bottom layer is infrastructure this is all you observe some regions and data centers and the machines and things you've got you want to make sure you have enough redundancy here that if something goes wrong there's enough stuff left to get the work done right that's the basic principle of redundancy in the infrastructure level above that you've got a switching layer and the problem with the switching layer is that it's the thing that has to route around failures and it's probably the least well tested code in your entire system right because it only gets exercised when something goes wrong and its job is to avoid the broken thing and use something else maybe scale up some extra sources this is the code that gets executed when you failover to another data center or a zone or a region and you know how do you exercise that code it's really critical how do you switch customers so that they always can see a working system and then we have these applications what's your application do when something goes wrong is it just crash fall over go into infinite loops or does it actually have some graceful some algorithms in it that sort of get some graceful degradation in them and the top level is these pesky people the users and the operators and you can get a perfectly working incredibly reliable robust system and the users were all screwed up right there's lots and lots of examples of outages caused by confused operators when the system was trying to cope with some underlying failure or they were running through test processes and the output was like just got confused and you broke everything rebooting is usually the wrong thing so how do we train people to get through this fire drills right everyone here has been in a fire drill you've all  ...


## Sources

[1] Video: https://www.youtube.com/watch?v=4VleTKY0QAM
[2] Channel: O'Reilly
