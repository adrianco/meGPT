---
type: Article
title: "Load Average Differences Between Solaris and Linux"
description: ""
resource: "https://perfcap.blogspot.com/2007/04/load-average-differences-between.html"
tags:
  - article
---

# Load Average Differences Between Solaris and Linux






## Excerpt

Title: Load Average Differences Between Solaris and Linux
URL: https://perfcap.blogspot.com/2007/04/load-average-differences-between.html

A lot of people monitor their servers using load average as the primary metric. Tools such as <a href="http://ganglia.sourceforge.net/">Ganglia</a> colorize all the nodes in a cluster view using load average. However there are a few things that aren't well understood about the calculation and how it varies between Solaris and Linux.<br />
<br />
For a detailed explanation of the algorithm behind the metric, <a href="http://www.perfdynamics.com/Manifesto/gcaprules.html" target="_blank">Neil Gunther has posted a series of articles</a> that show how Load Average is a time-decayed metric that reports the number of active processes on the system with a one, five and fifteen minute decay period.<br />
<br />
The source of the number of active processes can be seen in vmstat as the first few columns, and this is where Solaris and Linux differ. For example, some Linux vmstat from a busy file server is shown below.<br />
<pre>procs -----------memory---------- ---swap-- -----io---- --system-- ----cpu----
 r  b   swpd   free   buff  cache   si   so    bi
...


## Sources

[1] Source: https://perfcap.blogspot.com/2007/04/load-average-differences-between.html
