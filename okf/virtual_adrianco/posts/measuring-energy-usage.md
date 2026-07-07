---
type: Article
title: "Measuring Energy Usage"
description: "Decided to figure out how to measure the energy used by a desktop computer and see if I can figure..."
resource: "https://dev.to/adrianco/measuring-energy-usage-5ip"
tags:
  - article
---

# Measuring Energy Usage


## Summary

Decided to figure out how to measure the energy used by a desktop computer and see if I can figure...





## Excerpt

Decided to figure out how to measure the energy used by a desktop computer and see if I can figure out a way to identify different workloads.

I have a Mac Studio M1 to run the workload, and an old MacBook laptop to run data collection on, so that it doesn't add to the workload.

First thing we need is a power monitoring plug that has an API. The TP-Link Kasa platform seems like a good place to start. It has a python based API available on GitHub .

I ordered a Kasa KP115 smart plug from Amazon for $22.99.

Setup the plug using the mobile app, then:

Next - you have to specify host, or it will crash, and specifying type saves it an extra API call, and you get a single result

Using a csh loop to get a 1 second trace of the data it's clear that the data changes about every 4 seconds.

The output formatting is defined in cli.py

That's all I have time to do for now, to be continued...
...


## Sources

[1] Original article: https://dev.to/adrianco/measuring-energy-usage-5ip
