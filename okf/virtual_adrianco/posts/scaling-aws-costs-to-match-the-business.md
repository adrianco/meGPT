---
type: Article
title: "Scaling AWS costs to match the business"
description: "I recently wrote a Medium post on cloud native cost optimization, in part to help customers who are c..."
resource: "https://dev.to/aws/scaling-aws-costs-to-match-the-business-f9k"
tags:
  - article
---

# Scaling AWS costs to match the business


## Summary

I recently wrote a Medium post on cloud native cost optimization, in part to help customers who are c...





## Excerpt

I recently wrote a Medium post on cloud native cost optimization , in part to help customers who are currently dealing with rapid large and unexpected changes in their businesses due to the impact of COVID-19. Out of the ensuing discussion, a few things emerged. One is that I should try out dev.to for developer oriented posts, so this is my first post here. Another is that there's benefits and challenges in generating a metric that reports AWS cost per unit of business, so that's the subject of this discussion.

The first challenge is to decide what your business does, and whether there is a dominant metric that measures the value you provide to customers. I was at Netflix in 2011 when we started to build tooling to optimize our AWS spend, and Netflix has a very focused business model and measured customer value as the number of "streaming starts per second" (SPS). i.e. The rate at which people decide to start watching a show on Netflix.

We also had an AWS deployment model which tagged and attributed all the entities we created on AWS back to individuals and teams, and produced detailed billing on an hourly basis. Starting with a total AWS cost, dividing by SPS produced an hourly
...


## Sources

[1] Original article: https://dev.to/aws/scaling-aws-costs-to-match-the-business-f9k
