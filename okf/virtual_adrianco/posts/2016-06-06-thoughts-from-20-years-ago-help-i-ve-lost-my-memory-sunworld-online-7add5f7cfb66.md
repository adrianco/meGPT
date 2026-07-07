---
type: Article
title: "Thoughts from 20 years ago — Help! I’ve lost my memory! Sunworld Online"
description: ""
resource: "https://medium.com/@adrianco/2016-06-06_Thoughts-from-20-years-ago---Help--I-ve-lost-my-memory--Sunworld-Online-7add5f7cfb66"
tags:
  - article
---

# Thoughts from 20 years ago — Help! I’ve lost my memory! Sunworld Online






## Excerpt

[URL] https://medium.com/@adrianco/2016-06-06_Thoughts-from-20-years-ago---Help--I-ve-lost-my-memory--Sunworld-Online-7add5f7cfb66

Thoughts from 20 years ago — Help! I’ve lost my memory! Sunworld Online

[Just for fun, posting this for the third time]

Originally published in Unix Insider 10/1/95 Stripped of adverts, url references fixed and comments added to bring it up to date ten years later in 2006.

Dear Adrian, After a reboot I saw that most of my computer’s memory wasfree, but when I launched my application it used up almost all thememory. When I stopped the application the memory didn’t come back!Take a look at my vmstat output:
% vmstat 5procs memory page disk faults cpur b w swap free re mf pi po fr de sr s0 s1 s2 s3 in sy cs us sy id
This is before the program starts:
0 0 0 330252 80708 0 2 0 0 0 0 0 0 0 0 1 18 107 113 0 1 990 0 0 330252 80708 0 0 0 0 0 0 0 0 0 0 0 14 87 78 0 0 99
I start the program and it runs like this for a while:
0 0 0 314204 8824 0 0 0 0 0 0 0 0 0 0 0 414 132 79 24 1 740 0 0 314204 8824 0 0 0 0 0 0 0 0 0 0 0 411 99 66 25 1 74
I stop it, then almost all the swap space comes back, but the free memory does not:
0 0 0 326776 21260 0 3 0 0 0 0 0 0 1 0
...


## Sources

[1] Source: https://medium.com/@adrianco/2016-06-06_Thoughts-from-20-years-ago---Help--I-ve-lost-my-memory--Sunworld-Online-7add5f7cfb66
