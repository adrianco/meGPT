---
type: Article
title: "The Cockcroft Headroom Plot - Part 1 - Introducing R"
description: ""
resource: "https://perfcap.blogspot.com/2006/11/cockcroft-headroom-plot-part-1.html"
tags:
  - article
---

# The Cockcroft Headroom Plot - Part 1 - Introducing R






## Excerpt

Title: The Cockcroft Headroom Plot - Part 1 - Introducing R
URL: https://perfcap.blogspot.com/2006/11/cockcroft-headroom-plot-part-1.html

I've recently written a paper for CMG06 called "Utilization is Virtually Useless as a Metric!". Regular readers of this blog will recognize much of the content in that paper. The follow-on question is what to use instead? The answer I have is to plot response time vs. throughput, and I've been thinking about a very specific way to display this kind of plot. Since I'm feeling quite opinionated about this I'm going to call it a "Cockcroft Headroom Plot" and I'm going to try and construct it using various tools. I will blog my way through the development of this, and I welcome advice and comments along the way.<br /><br />The starting point is a dataset to work with, and I found an old iostat log file that recorded a fairly busy disk at 15 minute intervals over a few days. This gives me 250 data points, which I fed into the <a href="http://www.r-project.org/">R stats package</a> to look at. I'll also have a go at making a spreadsheet version.<br /><br />The iostat data file starts like this:<br /><pre><span style="font-family:courier new;">
...


## Sources

[1] Source: https://perfcap.blogspot.com/2006/11/cockcroft-headroom-plot-part-1.html
