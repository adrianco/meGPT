---
type: Article
title: "Percentiles don’t work: Analyzing the distribution of response times for web services (Updated with code)"
description: ""
resource: "https://medium.com/@adrianco/2023-01-29_Percentiles-don-t-work--Analyzing-the-distribution-of-response-times-for-web-services--Updated-with--ace36a6a2a19"
tags:
  - article
---

# Percentiles don’t work: Analyzing the distribution of response times for web services (Updated with code)






## Excerpt

[URL] https://medium.com/@adrianco/2023-01-29_Percentiles-don-t-work--Analyzing-the-distribution-of-response-times-for-web-services--Updated-with--ace36a6a2a19

Percentiles don’t work: Analyzing the distribution of response times for web services (Updated with code)
Plot showing the final result of fitting multiple normal distributions to a response time curve
Most people have figured out that the average response time for a web service is a very poor estimate of it’s behavior, as responses are usually much faster than the average, but there’s a long tail of much slower responses. The common way to deal with this is to measure percentiles, and track the 90%, 99% response times for example. The difficulty with percentiles is that you can’t combine them, so if you measure percentiles at one minute intervals, you can’t average them together to get hourly or daily percentiles. If you do this, you end up with a number on a dashboard that may be useful as an indicator of trends, but it can’t tell you what the actual percentile was for that hour or day. Another common method is to measure the proportion of responses that exceeded a service level agreement (SLA) expressed as a percentile l
...


## Sources

[1] Source: https://medium.com/@adrianco/2023-01-29_Percentiles-don-t-work--Analyzing-the-distribution-of-response-times-for-web-services--Updated-with--ace36a6a2a19
