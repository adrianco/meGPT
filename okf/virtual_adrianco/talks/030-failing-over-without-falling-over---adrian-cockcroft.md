---
type: YouTube Talk
title: "Failing Over without Falling Over - Adrian Cockcroft"
description: "Many organizations have disaster recovery (DR) failover plans that are poorly tested and implemented, and they are scared to test or use them in a realistic manner. This talk will show how we can u..."
resource: "https://www.youtube.com/watch?v=R3_ccsuPoD8"
tags:
  - talk
timestamp: "2020-10-15"
author: "Adrian Cockcroft"
---

# Failing Over without Falling Over - Adrian Cockcroft

Many organizations have disaster recovery (DR) failover plans that are poorly tested and implemented, and they are scared to test or use them in a realistic manner. This talk will show how we can use System Theoretic Process Analysis (STPA), as advocated by Professor Nancy Leveson’s team at MIT, to analyze failover hazards. Observability and human understanding of safety margins and the state of a failover are critical to having a real DR capability. Chaos engineering, game days and a high level of automation provides continuously tested resilience, and confidence that systems will fail over, without falling over.


## Transcript Excerpt

Kind: captions Language: en i'm going to talk today about failing over without falling over and you know many of us have seen systems that we built out and we built in all the reliability systems and we've got all the failover plans but what happens in practice is that we end up in a big heap with everything broken so why is that and i'll just give a brief view of what something we might be able to do about that so to start off with i like to ask people do you have a backup data center how often do you fail over apps to it get a few answers to that that were okay how often do you fell over the whole data center at once people typically get pretty embarrassed about that point and i call this availability theater if you've got a backup data center and you've never really failed over to it or you're not confident that you could fail over to in a moment's notice you invest a lot of money for a sort of a facade of availability and if we look at some data from the uptime institute historically most recorded outages have been because of power failure across all data centers for all all over all sort of public reportings of outages that to do with it but more recently the most recent report they find that i.t and network problems have moved into the lead and they are now causing more failures than power problems so why is this well here's a an interesting sort of book about this sort of type of failure failures result from an unanticipated interaction of multiple failures in a complex system that's what we built and pero calls these normal accidents because yeah they're unexpected they're incomprehensible they're uncontrollable they're also unavoidable you're definitely going to get these so that's why they are normal you should regard them as a normal outcome and something that you should be trying to manage from and you know because of this we try to build redundancy into our systems if something fails we've got an alternative to failover too the problem is that the abili ...


## Sources

[1] Video: https://www.youtube.com/watch?v=R3_ccsuPoD8
[2] Channel: Gremlin
