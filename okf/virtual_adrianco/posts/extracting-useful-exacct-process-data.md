---
type: Article
title: "Extracting useful exacct process data"
description: ""
resource: "https://perfcap.blogspot.com/2005/03/extracting-useful-exacct-process-data.html"
tags:
  - article
---

# Extracting useful exacct process data






## Excerpt

Title: Extracting useful exacct process data
URL: https://perfcap.blogspot.com/2005/03/extracting-useful-exacct-process-data.html

I modified the /usr/demo/libexacct/exdump.c example code to include the data structures described in previous posts, and made the code update each item in the structure. Then I added a printf from the data structure so I could check that all the data is being captured correctly. Part of the output is shown below. I hand edited the column headers a bit for the first two lines to make them line up.<br /><br /><pre><br /><span style="font-size:85%;">procid ppid uid  usr  sys time      majf minf rwKB     vcxK   icxK sigK sycK  arMB mrMB command<br />1693  1679 100 40.23 3.53 416930.11 237    0 58745.32 261.17 4.22 0.00 801.7 38.4 44.6 mozilla-bin<br />procid ppid uid  usr  sys time      majf minf rwKB    vcxK icxK sigK sycK arMB mrMB command<br />1679  1647 100 0.00 0.00 416930.16    0    0 15.11   0.02 0.00 0.00  0.6  0.6 26.4 run-mozilla.sh<br />procid ppid uid  usr  sys time      majf minf rwKB vcxK icxK sigK sycK arMB mrMB command<br />1647  1646 100 0.00 0.01 416930.30    0    0 8.29 0.03 0.00 0.00  0.8  0.4 26.4 mozilla</span><br /></pre><br /><br />R
...


## Sources

[1] Source: https://perfcap.blogspot.com/2005/03/extracting-useful-exacct-process-data.html
