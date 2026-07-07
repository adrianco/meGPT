---
type: Article
title: "Enhanced headroom plot in R"
description: ""
resource: "https://perfcap.blogspot.com/2008/07/enhanced-headroom-plot-in-r.html"
tags:
  - article
---

# Enhanced headroom plot in R






## Excerpt

Title: Enhanced headroom plot in R
URL: https://perfcap.blogspot.com/2008/07/enhanced-headroom-plot-in-r.html

For some reason I seem to find time to <a href="http://www.r-project.org">write code in R</a> when I'm on an airplane. The last two trips I made resulted in significant enhancements and debugging of the code for my headroom plot. <a href="http://perfcap.blogspot.com/search?q=chp">It started off simple</a> but it now has a lot of bells and whistles, including color coding.<br /><br />Main changes: the quantile used to remove outliers now only removes outliers that exceed the 95th percentile response time by default. It keeps all the throughput values unless you use qx=True.<br /><br />In each of the throughput bins used to draw the histogram, the maximum response time for that bin is now calculated and displayed as a staircase line unless you set max=False.<br /><br />The set of data is now split into ranges and color coded. The times series plot is coded so you can see the split, and the scatterplot shows how those points fall. I have been plotting weekly data at one minute intervals with split=7, which looks pretty good.<br /><br />I read in some data that has been extrac
...


## Sources

[1] Source: https://perfcap.blogspot.com/2008/07/enhanced-headroom-plot-in-r.html
