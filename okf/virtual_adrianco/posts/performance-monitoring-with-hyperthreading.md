---
type: Article
title: "Performance monitoring with Hyperthreading"
description: ""
resource: "https://perfcap.blogspot.com/2005/05/performance-monitoring-with.html"
tags:
  - article
---

# Performance monitoring with Hyperthreading






## Excerpt

Title: Performance monitoring with Hyperthreading
URL: https://perfcap.blogspot.com/2005/05/performance-monitoring-with.html

Hyperthreading is used by most recent Intel servers, <a href="http://www.intel.com/technology/hyperthread/">Intel describe it here.</a><br /><br />I tried searching for information on the performance impact and performance monitoring impact and found several studies that describe improvements in terms of throughput that ranged from negative impact (a slowdown) to speedups of 15-20% per CPU. I didn't see much discussion of the effects on observability or of effects on response time, so thats what I'm going to concentrate on writing about.<br /><br />First, to summarize the information that I could find, the early measurements of performance included most of the negative impact cases. This is due to two separate effects, software and hardware improvements mean that the latest operating systems on the most recent Intel Pentium  4 and Xeon chipsets have a larger benefit and minimise any negative effects.<br /><br />From a software point of view, Intel advises that Hyperthreading should be disabled for anything other than Windows XP and recent releases of RedHat
...


## Sources

[1] Source: https://perfcap.blogspot.com/2005/05/performance-monitoring-with.html
