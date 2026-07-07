---
type: Article
title: "Automated rotating exdump"
description: ""
resource: "https://perfcap.blogspot.com/2005/04/automated-rotating-exdump.html"
tags:
  - article
---

# Automated rotating exdump






## Excerpt

Title: Automated rotating exdump
URL: https://perfcap.blogspot.com/2005/04/automated-rotating-exdump.html

I've added an option that automates the processing of exacct data to text file format and rotates the logs, it is hard wired to create a new log file in /var/adm/exacct (which is an empty directory created during Solaris install as standard) and it includes the hostname and the date+time in the new file.<br /><br />The previous log name is used as the base of the output file, which is written to a specified directory with a .txt extension.<br /><br />The file /etc/acctadm.conf is maintained by the acctadm command, I read the log file names from it, and if there is no log file I don't start one. i.e. you need to manually start accounting with acctadm the first time to decide which logs you want to generate. The command syntax now looks like this:<br /><br /><span style="font-size:85%;"><span style="font-family:courier new;"># ./exdump</span><br /><span style="font-family:courier new;">Usage: exdump [-vwr] [<file> file | -a dir ]<br /></file></span></span><span style="font-size:85%;"><span style="font-family:courier new;"><dir></dir></span></span> <div style="text-align: left;">
...


## Sources

[1] Source: https://perfcap.blogspot.com/2005/04/automated-rotating-exdump.html
