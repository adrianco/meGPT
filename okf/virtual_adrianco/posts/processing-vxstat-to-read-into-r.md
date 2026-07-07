---
type: Article
title: "Processing vxstat to read into R"
description: ""
resource: "https://perfcap.blogspot.com/2006/11/processing-vxstat-to-read-into-r.html"
tags:
  - article
---

# Processing vxstat to read into R






## Excerpt

Title: Processing vxstat to read into R
URL: https://perfcap.blogspot.com/2006/11/processing-vxstat-to-read-into-r.html

I got bored with my iostat data, and found some interesting looking vxstat logs to browse with the Cockcroft Headroom Plot. To get them into a regular format I wrote a short Awk script that is shown below. It skips the first record, adds a custom header and drops the time field into the first column.<br /><br /><pre><br /># process vxstat file into regular csv format<br />BEGIN { skipping=1; printf("time,vol,reads,writes,breads,bwrites,tread,twrite\n"); }<br />NR < 4 {next}   # skip header<br />NF > 0 && skipping==1 {next} # skip first record of totals since boot<br />NF == 0 {skipping=0}<br />NF == 5 {time=$0}<br />NF == 8 {printf("%s,%s,%s,%s,%s,%s,%s,%s\n",time,$2,$3,$4,$5,$6,$7,$8);}<br /></pre><br /><br />It turns a file that looks like this:<br /><pre><br />                        OPERATIONS           BLOCKS        AVG TIME(ms)<br />TYP NAME              READ     WRITE      READ     WRITE   READ  WRITE <br /><br />Mon May 01 19:00:01 2000<br />vol home             88159    346799  17990732   3680604   13.7   15.6 <br />vol local            64308    103869
...


## Sources

[1] Source: https://perfcap.blogspot.com/2006/11/processing-vxstat-to-read-into-r.html
