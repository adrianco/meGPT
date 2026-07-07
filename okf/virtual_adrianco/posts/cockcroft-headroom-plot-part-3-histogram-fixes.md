---
type: Article
title: "Cockcroft Headroom Plot - Part 3 - Histogram Fixes"
description: ""
resource: "https://perfcap.blogspot.com/2006/11/cockcroft-headroom-plot-part-3.html"
tags:
  - article
---

# Cockcroft Headroom Plot - Part 3 - Histogram Fixes






## Excerpt

Title: Cockcroft Headroom Plot - Part 3 - Histogram Fixes
URL: https://perfcap.blogspot.com/2006/11/cockcroft-headroom-plot-part-3.html

I found that I had some scaling issues with the histograms that needed fixing. Ultimately this made the code look a lot more complex, but it now deals with scaling the plot and the histogram with a fixed zero origin on both axes. I think its important to maintain the zero origin for a throughput vs. response time plot.<br /><br />The tricky part is that the main plot is automatically oversized from its data range by a few percent, and the units used in the histogram are completely different. A histogram with 6 bars is scaled to have the bars at unit intervals and is 6 wide plus the width of the bars etc. After lots of trial and error, I made the main plot use the maximum bucket size of the histogram as its max value, and artificially offset the histograms by what looks like about the right amount. The plot below uses fixed data as a test. You can see that the first bar includes two points, thats due to the particular algorithm used by R. Some alternative histogram algorithms are available, but this one seems to be most appropriate to throughput/re
...


## Sources

[1] Source: https://perfcap.blogspot.com/2006/11/cockcroft-headroom-plot-part-3.html
