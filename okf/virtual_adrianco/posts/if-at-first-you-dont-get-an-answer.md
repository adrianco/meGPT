---
type: Article
title: "If at first you don't get an answer..."
description: "give up quickly and ask someone else. That's my favorite microservices retry policy. To understand wh..."
resource: "https://dev.to/aws/if-at-first-you-don-t-get-an-answer-3e85"
tags:
  - article
---

# If at first you don't get an answer...


## Summary

give up quickly and ask someone else. That's my favorite microservices retry policy. To understand wh...





## Excerpt

give up quickly and ask someone else. That's my favorite microservices retry policy. To understand what works and doesn't work, we need to think about how distributed systems of services and databases interact with each other, not just a single call. Like my last post on why systems are slow sometimes , I will start simple, pick out key points, and gradually explain the things that will kill your distributed system, if you don't have timeouts and retries setup properly. It's also one of the easiest things to fix, once you understand what's going on, and it generally doesn't need new code, just configuration changes.

A bad timeout and retry policy can break a distributed systems architecture, but is relatively easy to fix.

A bad timeout and retry policy can break a distributed systems architecture, but is relatively easy to fix.

I often find the timeout and retry policy across an application is set to whatever the default is for the framework or sample code you copied when starting to write each microservice. If every microservice uses the same timeout, this is guaranteed to fail, because the microservices deeper in the system are still retrying when the microservices nearer the
...


## Sources

[1] Original article: https://dev.to/aws/if-at-first-you-don-t-get-an-answer-3e85
