---
type: Article
title: "Sequencing exacct logs"
description: ""
resource: "https://perfcap.blogspot.com/2005/04/sequencing-exacct-logs.html"
tags:
  - article
---

# Sequencing exacct logs






## Excerpt

Title: Sequencing exacct logs
URL: https://perfcap.blogspot.com/2005/04/sequencing-exacct-logs.html

I decided to simplify the next step and to just get raw data logged in a useful manner. To do this there needs to be a periodic process that generates readable log files. After thinking about this for a while, I think I have a simple and effective way to do it.<br /><br />I will modify the exdump code to add another option "-a". This will invoke acctadm to switch to a new set of log files, with a datestamped name. Before it does the switch, it will need to cause all current processes to write accounting entries, so "-a" will normally be used in conjunction with the "-w" option I added already. After the log switch, the old log files will be processed from their binary form to a text file with one record per line, ready for consumption by futher processing steps.<br />When "-a" is specified, a directory can be specified on the command line to hold output files, the input filename does not need to be specified as it was for the original version. This makes it easy to invoke exdump directly from cron without needing a wrapper script.<br /><br />The sequence is:<br /><pre><br />Obtain e
...


## Sources

[1] Source: https://perfcap.blogspot.com/2005/04/sequencing-exacct-logs.html
