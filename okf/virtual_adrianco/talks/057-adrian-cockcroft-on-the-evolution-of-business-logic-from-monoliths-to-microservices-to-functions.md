---
type: YouTube Talk
title: "Adrian Cockcroft on the Evolution of Business Logic from Monoliths, to Microservices, to Functions"
description: "Learn more about Open Source at AWS at - http://amzn.to/2mj6Pih.
As technology has progressed over the last decade, we’ve seen an evolution from monolithic applications to microservices and are now..."
resource: "https://www.youtube.com/watch?v=aBcG57Gw9k0"
tags:
  - talk
timestamp: "2018-01-23"
author: "Adrian Cockcroft"
---

# Adrian Cockcroft on the Evolution of Business Logic from Monoliths, to Microservices, to Functions

Learn more about Open Source at AWS at - http://amzn.to/2mj6Pih.
As technology has progressed over the last decade, we’ve seen an evolution from monolithic applications to microservices and are now seeing the rise of serverless event driven functions, led by AWS Lambda. What factors have driven this evolution? We've seen the same service oriented architecture principles track advancements in technology from the coarse grain services of SOA a decade ago, through microservices that are usually scoped to a more fine grain single area of responsibility, and now functions as a service, serverless architectures where each function is a separately deployed and invoked unit. Large teams would work for months between releases of SOA components. Small teams down to a single developer would release microservices perhaps on a daily basis. One developer may release many functions many times a day.


## Transcript Excerpt

Kind: captions Language: en hi I'm Adrian khakhra over the years I've given a lot of talks on micro services and cloud architectures there are some ideas I always wanted to illustrate with a short animated sequence so I've worked with a visual design team to come up with a series of animations each illustrating a specific concept so this talks on the evolution of business logic as we went from monoliths through micro services and now we're looking at functions back about 10 years ago we had monoliths and when we tried to split them up we found that it was a lot of hard work the networks were too slow the CPUs were too slow and the messaging protocols we used were based on XML and soap and they were heavyweight so when we tried to split things up we ended up with fairly large services which had a lot of functionality in them and we had a relatively small number of monolithic services that we built out moving forward a bit what we found was that CPUs got a lot faster networks got a lot faster and we moved a much more efficient protocols so it's maybe a hundred or a thousand times more efficient now to make calls between services that let us take our monolithic services and break them up into micro services those services form a fairly complex looking Network with a lot of messages flowing backwards and forwards between them you can see here our service network and service mesh where we go from the edge we flow through many layers of services to reach on the right hand side storage services and caches now we take that environment we think about the way that these services are becoming more standardized so rather than building all these services ourselves we're starting to use off-the-shelf services that are scaled they're highly available and they come from AWS so we have sqs dynamodb Kinesis SNS and s3 and we feed them all from the api gateway the micro services that we built in between these provide the is where the business logic lives so if we look at that business ...


## Sources

[1] Video: https://www.youtube.com/watch?v=aBcG57Gw9k0
[2] Channel: Amazon Web Services
