---
type: YouTube Talk
title: "Keynote: Cloud Native at AWS - Adrian Cockcroft, Amazon Web Services"
description: "Keynote: Cloud Native at AWS - Adrian Cockcroft, Vice President Cloud Architecture Strategy, Amazon Web Services

About Adrian Cockcroft
Adrian Cockcroft has had a long career working at the leadin..."
resource: "https://www.youtube.com/watch?v=5U-6sxR5DaQ"
tags:
  - talk
timestamp: "2017-12-15"
author: "Adrian Cockcroft"
---

# Keynote: Cloud Native at AWS - Adrian Cockcroft, Amazon Web Services

Keynote: Cloud Native at AWS - Adrian Cockcroft, Vice President Cloud Architecture Strategy, Amazon Web Services

About Adrian Cockcroft
Adrian Cockcroft has had a long career working at the leading edge of technology, and is fascinated by what happens next. In his role at AWS, Cockcroft is focused on the needs of cloud native and “all-in” customers, and leads the AWS open source community development program.

Prior to AWS, Cockcroft started out as a developer in the UK, joined Sun Microsystems and then moved to the United States in 1993, ending up as a Distinguished Engineer. Cockcroft left Sun in 2004, was a founding member of eBay research labs, and started at Netflix in 2007. He initially directed a team working on personalization algorithms and then became cloud architect, helping teams scale and migrate to AWS. As Netflix shared its architecture publicly, Cockcroft became a regular speaker at conferences and executive summits, and he created and led the Netflix open source program. In 2014, he joined VC firm Battery Ventures, promoting new ideas around DevOps, microservices, cloud and containers, and moved into his current role at AWS in October 2016.

Cockcroft holds a degree in Applied Physics from The City University, London and is a published author of four books, notably Sun Performance and Tuning (Prentice Hall, 1998).
Join us for KubeCon + CloudNativeCon in Barcelona May 20 - 23, Shanghai June 24 - 26, and San Diego November 18 - 21!  Learn more at https://kubecon.io. The conference features presentations from developers and end users of Kubernetes, Prometheus, Envoy and all of the other CNCF-hosted projects.


## Transcript Excerpt

Kind: captions Language: en so originally a certain talk about cloud native at AWS and I got a few new things we announced last week that we actually want to talk about so a little bit about the cloud native principles and I'm going to talk about open source add AWS and then dive into a few of the things we've been doing on CNI what is this new Fargate thing that we used for container provisioning what we're doing to help kubernetes run on AWS and then just end up with eks Cube natives as a service ok so cloud native principles I've got a whole long presentation on this and if you wanted the hour-long version of it there's a video up from from reinvent last week you can go google for arc 209 if you're trying to find that but these are the principles that I think are important that make something cloud native that it's pay-as-you-go and you're paying after the event you're not having to invest in a data center and guess how much capacity you're going to need next year it's self-service it's no waiting everything is the API deployed and provisioned globally distributed by default the cloud is out there you can go use things around the world you don't have to be constrained to just wait happen to a built a data center the availability models take into account zones and regions and then the other really important thing is to get very high utilization you can save a lot of money by turning things off extremely aggressively and then immutable code deployments and I think some of the things that we came up with back in the days with Netflix we were using Amazon machine images as containers and we were baking those containers and then we weren't changing that we were replacing them and that is some of that that's kind of the deployment model that docker picked up on when they containerized it so you know it's it's there is a Linux container but the idea of a container is basically an immutable deployment entity that you bake as the as you go through so all of these things t ...


## Sources

[1] Video: https://www.youtube.com/watch?v=5U-6sxR5DaQ
[2] Channel: CNCF [Cloud Native Computing Foundation]
