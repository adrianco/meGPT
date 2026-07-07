---
type: Article
title: "Understanding and using Amazon EBS - Elastic Block Store"
description: ""
resource: "https://perfcap.blogspot.com/2011/03/understanding-and-using-amazon-ebs.html"
tags:
  - article
---

# Understanding and using Amazon EBS - Elastic Block Store






## Excerpt

Title: Understanding and using Amazon EBS - Elastic Block Store
URL: https://perfcap.blogspot.com/2011/03/understanding-and-using-amazon-ebs.html

There has been a lot of discussion in the last few days about EBS <a href="http://blog.reddit.com/2011/03/why-reddit-was-down-for-6-of-last-24.html">since it was implicated in a long outage at reddit.com</a>.<br /><br /><span style="font-weight:bold;">Rule of Thumb</span><br /><br />The benchmarking Netflix did when we started on AWS highlighted some inconsistent behavior in EBS. The conclusion we reached is a rule of thumb for EBS - If you sustain less than 100 iops (input+output per second) long term average it works fine. Short term bursts can be 1000 iops. By short term I mean less than a minute, long term more than 10 minutes. YMMV.<br /><br />If you are doing benchmarks like this, collect response time and throughput and plot your data over time. You need to run long enough that the performance shows steady state behavior. The problem with EBS is that it doesn't have a particularly steady state. To explain why we need to look at the underlying architecture. I don't know the details of how EBS is implemented, but there is enough inf
...


## Sources

[1] Source: https://perfcap.blogspot.com/2011/03/understanding-and-using-amazon-ebs.html
