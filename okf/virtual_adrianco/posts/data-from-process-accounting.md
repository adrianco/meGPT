---
type: Article
title: "Data from process accounting"
description: ""
resource: "https://perfcap.blogspot.com/2005/03/data-from-process-accounting.html"
tags:
  - article
---

# Data from process accounting






## Excerpt

Title: Data from process accounting
URL: https://perfcap.blogspot.com/2005/03/data-from-process-accounting.html

The process accounting record is far more detailed than the standard sysV acct record used by most Unix based systems. For a start it includes the pid of the process and the pid of the parent process so you can stitch the records together properly. The Solaris project and task id's let you manage and control workloads effectively, and since microstate accounting is on by default in Solaris 10, the CPU usage numbers are accurate and high resolution. By default everything is in the global zone. Zones are the virtual machine containers used for fault isolation and resource management in Solaris 10, so data needs to be separated by zone as well as workload.<br /><br /><pre><br />    ff  group-header                    [group of 4 object(s)]<br />     1   version                        1<br />     2   filetype                       "exacct"<br />     3   creator                        "SunOS"<br />     4   hostname                       "crun"<br />   100  group-proc                      [group of 34 object(s)]<br />  1000   pid                            1748<br />  1001   u
...


## Sources

[1] Source: https://perfcap.blogspot.com/2005/03/data-from-process-accounting.html
