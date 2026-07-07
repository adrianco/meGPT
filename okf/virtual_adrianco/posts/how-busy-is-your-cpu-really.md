---
type: Article
title: "How busy is your CPU, really?"
description: ""
resource: "https://perfcap.blogspot.com/2005/10/how-busy-is-your-cpu-really.html"
tags:
  - article
---

# How busy is your CPU, really?






## Excerpt

Title: How busy is your CPU, really?
URL: https://perfcap.blogspot.com/2005/10/how-busy-is-your-cpu-really.html

Just in case you thought that you could compare your CPU utilization data across Solaris releases I have a few words of caution.<br /><br />To start with there is the whole problem of interrupts, do they count as system time, or do they just make whatever they interrupted take longer?<br /><br />Then there is the question of wait-for-io, and who is waiting for which io? This is a form of idle time that tends to confuse people as it doesn't really mean anything once you have more than one CPU.<br /><br />There is one mechanism used to report the systemwide CPU utilization data. This data is reported in a per-cpu kstat data structure and is used by every tool that ever reports CPU usr, sys, wio, idle etc. Most tools sum the data over all the CPUs, mpstat gives you the per CPU data. The form of the data is a number of ticks of CPU time that accumulates, starting at zero at boot time. To measure CPU utilization over a time interval, you measure the difference in the number of ticks and divide by the time, and the tick rate. The tick rate is set by the clock interrupt, it def
...


## Sources

[1] Source: https://perfcap.blogspot.com/2005/10/how-busy-is-your-cpu-really.html
