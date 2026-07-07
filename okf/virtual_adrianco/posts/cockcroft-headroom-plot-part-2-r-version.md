---
type: Article
title: "Cockcroft Headroom Plot - Part 2 - R Version"
description: ""
resource: "https://perfcap.blogspot.com/2006/11/cockcroft-headroom-plot-part-2-r.html"
tags:
  - article
---

# Cockcroft Headroom Plot - Part 2 - R Version






## Excerpt

Title: Cockcroft Headroom Plot - Part 2 - R Version
URL: https://perfcap.blogspot.com/2006/11/cockcroft-headroom-plot-part-2-r.html

I kept tweaking the code, and came up with a prettier version, that also has a small time series view of the throughput in the top right corner.<br /><br /><a onblur="try {parent.deselectBloggerImageGracefully();} catch(e) {}" href="http://photos1.blogger.com/x/blogger2/3864/907/1600/207207/chp.gif"><img style="display:block; margin:0px auto 10px; text-align:center;cursor:pointer; cursor:hand;" src="http://photos1.blogger.com/x/blogger2/3864/907/400/212741/chp.png" border="0" alt="" /></a><br /><br />The code for this is<br /><pre><br />chp <- function(x,y,xl="Throughput",yl="Response",tl="Throughput Time Series", ml="Cockcroft Headroom Plot") {<br />       xhist <- hist(x,plot=FALSE)<br />       yhist <- hist(y, plot=FALSE)<br />       xrange <- c(0,max(x))<br />       yrange <- c(0,max(y))<br />       nf <- layout(matrix(c(2,4,1,3),2,2,byrow=TRUE), c(3,1), c(1,3), TRUE)<br />       layout.show(nf)<br />       par(mar=c(5,4,0,0))<br />       plot(x, y, xlim=xrange, ylim=yrange, xlab=xl, ylab=yl)<br />       par(mar=c(0,4,3,0))<br />       barplot(xhi
...


## Sources

[1] Source: https://perfcap.blogspot.com/2006/11/cockcroft-headroom-plot-part-2-r.html
