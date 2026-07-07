---
type: Article
title: "Capture Ratio and measurement overhead"
description: ""
resource: "https://perfcap.blogspot.com/2005/03/capture-ratio-and-measurement-overhead.html"
tags:
  - article
---

# Capture Ratio and measurement overhead






## Excerpt

Title: Capture Ratio and measurement overhead
URL: https://perfcap.blogspot.com/2005/03/capture-ratio-and-measurement-overhead.html

For performance monitoring applications, we often want to know the process related information, but collecting it from /proc is very expensive compared to collecting other performance data, and the amount of work increases as the number of processes increases.<br /><br />The <b>capture ratio</b> is defined as the amount of CPU time that is gathered by looking at process data versus the total systemwide CPU used. The difference is made up by processes that stop during the intervals between measurements. Since short lived processes may start and stop between measurements, and we don't know whether a process stopped immediately before a measurement or just after a measurement, there is always an error in sampled process measures. The error is reduced by using a short measurement interval, but that increases overhead. Bypassing the /proc interface, and reading process data directly from the kernel is very implementation dependent but is used by BMC's <a href=http://www.bmc.com>PATROL® for Unix - Perform & Predict</a> data collector, so that they can colle
...


## Sources

[1] Source: https://perfcap.blogspot.com/2005/03/capture-ratio-and-measurement-overhead.html
