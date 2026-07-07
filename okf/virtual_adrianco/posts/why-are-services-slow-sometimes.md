---
type: Article
title: "Why are services slow sometimes?"
description: "You've built a service, you call it, it does something and returns a result, but how long does it tak..."
resource: "https://dev.to/aws/why-are-services-slow-sometimes-mn3"
tags:
  - article
---

# Why are services slow sometimes?


## Summary

You've built a service, you call it, it does something and returns a result, but how long does it tak...





## Excerpt

You've built a service, you call it, it does something and returns a result, but how long does it take, and why does it take longer than your users would like some of the time? In this post I'll start with the basics and gradually introduce standardized terminology and things that make the answer to this question more complicated, while highlighting key points to know.

To start with, we need a way to measure how long it takes, and to understand two fundamentally different points of view. If we measure the experience as an outside user calling the service we measure how long it takes to respond. If we instrument our code to measure the requests from start to finish as they run, we're only measuring the service. This leads to the first key point, people get sloppy with terminology and often aren't clear where they got their measurements.

Be careful to measure Response Time at the user, and Service Time at the service itself.

Be careful to measure Response Time at the user, and Service Time at the service itself.

For real world examples, there are many steps in a process, and each step takes time. That time for each step is the Residence time, and consists of some Wait Time and so
...


## Sources

[1] Original article: https://dev.to/aws/why-are-services-slow-sometimes-mn3
