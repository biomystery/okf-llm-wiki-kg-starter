---
type: experiment
title: <Experiment Name>
description: <one-line: the question this experiment answers>
aliases: []
tags: []
status: stable                      # OKF lifecycle: draft | stable | deprecated  (§5.4)
stage: planned                      # experiment state: planned | running | done | abandoned
generated: { by: <actor>, at: <YYYY-MM-DDTHH:MM:SSZ> }
# verified: { by: human:<id>, at: <YYYY-MM-DDTHH:MM:SSZ> }
sources:                            # data, notebooks, protocols this writeup derives from
  - id: source-id                   # stable slug; the body's [^source-id] footnote joins to it
    resource: ../../raw/<topic>/<file>
    title: <human-readable source name>
---

# <Experiment Name>

## Question / hypothesis

<What you expect and why.>

## Setup

<Method, data, parameters — enough to reproduce.>

## Results

<What happened; link evidence in raw/ via a [[reference]] page.>[^source-id]

## Conclusions

- <takeaway; feeds back into [[<concept-or-project>]]>

[^source-id]: <human-readable source name>
