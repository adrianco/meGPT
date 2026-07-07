---
type: Article
title: "Data logged by flow accounting"
description: ""
resource: "https://perfcap.blogspot.com/2005/03/data-logged-by-flow-accounting.html"
tags:
  - article
---

# Data logged by flow accounting






## Excerpt

Title: Data logged by flow accounting
URL: https://perfcap.blogspot.com/2005/03/data-logged-by-flow-accounting.html

The data comes in two forms, outgoing traffic is tagged with the userid and project of the initiating process, but incoming traffic is missing this information. Since TCP flows are captured in pairs they need to be matched up. The output from the provided demo program /usr/demo/libexacct/exdump -v is shown below.<br /><br />These match if the src and dest address and ports are reversed<br /><br /><pre><br />    ff  group-header                    [group of 4 object(s)]<br />     1   version                        1<br />     2   filetype                       "exacct"<br />     3   creator                        "SunOS"<br />     4   hostname                       "crun"<br />   109  group-flow                      [group of 11 object(s)]<br />  3000   src-addr-v4                    a.b.c.d  <br />  3001   dest-addr-v4                   e.f.g.h  crun<br />  3004   src-port                       80<br />  3005   dest-port                      43727<br />  3006   protocol                       6              tcp<br />  3007   diffserv-field                 0<br />  300
...


## Sources

[1] Source: https://perfcap.blogspot.com/2005/03/data-logged-by-flow-accounting.html
