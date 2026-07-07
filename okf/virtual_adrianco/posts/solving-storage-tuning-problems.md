---
type: Article
title: "Solving storage tuning problems"
description: ""
resource: "https://perfcap.blogspot.com/2005/08/solving-storage-tuning-problems.html"
tags:
  - article
---

# Solving storage tuning problems






## Excerpt

Title: Solving storage tuning problems
URL: https://perfcap.blogspot.com/2005/08/solving-storage-tuning-problems.html

I wrote a while ago about Dave Fisk's <a href=http://www.ortera.com>Ortera Atlas</a> tool for storage analysis. I recently had a chance to use a beta release of Atlas on a real problem, and they are about to do a GA release, its ready for prime time.<br /><br />Like most tools, it can produce masses of numbers and graphs, but compared to other storage analysis tools I've seen it goes further in three ways: <br /><br />1) It collects critically important data that is not provided by the OS<br />2) It processes the data to tell you exactly what is wrong<br />3) It runs heuristics to tell you how to fix the problem<br /><br />I wish more tools spent this much effort on solving the actual problem rather than making pretty graphs that only an expert would understand.<br /><br />What we actually did was run the tool on a pre-production Oracle system using Veritas Filesystem and Volume Manager with Solaris on a SAN connected to a Hitachi storage array. Atlas starts off by looking at all the active processes on the system, and ignoring any that are not doing any I/O. It co
...


## Sources

[1] Source: https://perfcap.blogspot.com/2005/08/solving-storage-tuning-problems.html
