---
type: Article
title: "Data from task accounting record"
description: ""
resource: "https://perfcap.blogspot.com/2005/03/data-from-task-accounting-record.html"
tags:
  - article
---

# Data from task accounting record






## Excerpt

Title: Data from task accounting record
URL: https://perfcap.blogspot.com/2005/03/data-from-task-accounting-record.html

A task is a group of related processes, when the last one exits, a task record is written. The information is very similar to the process record.<br /><br /><pre><br />    ff  group-header                    [group of 4 object(s)]<br />     1   version                        1<br />     2   filetype                       "exacct"<br />     3   creator                        "SunOS"<br />     4   hostname                       "crun"<br />   101  group-task                      [group of 25 object(s)]<br />  2000   taskid                         61<br />  2001   projid                         1              user.root<br />  2007   cpu-user-sec                   0<br />  2008   cpu-user-nsec                  0<br />  2009   cpu-sys-sec                    0<br />  200a   cpu-sys-nsec                   0<br />  2003   start-sec                      1109844060     03/03/05 02:01:00<br />  2004   start-nsec                     907341842<br />  2005   finish-sec                     1109844060     03/03/05 02:01:00<br />  2006   finish-nsec                    925962473<b
...


## Sources

[1] Source: https://perfcap.blogspot.com/2005/03/data-from-task-accounting-record.html
