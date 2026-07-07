---
type: Article
title: "Writing accounting records at time intervals"
description: ""
resource: "https://perfcap.blogspot.com/2005/04/writing-accounting-records-at-time.html"
tags:
  - article
---

# Writing accounting records at time intervals






## Excerpt

Title: Writing accounting records at time intervals
URL: https://perfcap.blogspot.com/2005/04/writing-accounting-records-at-time.html

A major new feature of the exacct system is the ability to get an accounting record logged without terminating the process. There are two forms of this, for tasks you can get the record to dump the delta since the last record was logged. Somehow the task remembers the data each time it cuts a record so it can do the differencing. This seems to be too much overhead at the process level, so the other option is to cut a record that logs the same data as if the process had just exited, and this option is available for both tasks and processes.<br /><br />The command that causes a record to be written is "wracct" and it takes a list of process or task id's and makes a system call to cause the record to be written. You have to be root to do this. The wracct command line syntax is a pain if you want to get it to dump multiple processes, as shown in this example from the manpage:<br /><pre><br /># /usr/sbin/wracct -i "`pgrep sendmail`" process<br /></pre><br />I want to make every process cut a record, and if you attempt to do this with wracct you need to f
...


## Sources

[1] Source: https://perfcap.blogspot.com/2005/04/writing-accounting-records-at-time.html
