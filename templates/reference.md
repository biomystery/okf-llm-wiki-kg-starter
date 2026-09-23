---
type: reference
title: "<Title (Author et al., YYYY)>"
description: <one-line summary of the source>
aliases: []
tags: []
status: stable                      # draft | stable | deprecated  (OKF §5.4)
resource: <canonical landing page>  # the thing this page describes (OKF §4.1)
year: <YYYY>
venue: <journal / publisher / site>
doi: <10.xxxx/... or omit>
pmid: <PMID / PMCID or omit>
generated: { by: <actor>, at: <YYYY-MM-DDTHH:MM:SSZ> }
# verified: { by: human:<id>, at: <YYYY-MM-DDTHH:MM:SSZ> }
sources:                            # what this page was distilled from (OKF §5.1)
  - id: source-id                             # stable slug; [^source-id] footnotes join to it
    resource: ../../raw/<topic>/<file>          # local copy under raw/ (git-ignored)
    title: <Title (Author et al., YYYY)>
    author: <author or team:...>                # optional credibility signal
    last_modified: <YYYY-MM-DDTHH:MM:SSZ>       # optional: when the source itself changed
---

# <Title (Author et al., YYYY)>

## Summary

<Distilled summary. No copyrighted full text — keep the original in raw/.>

## Key points

- <point>[^source-id]

## Citation

<Author A, Author B. Title. Venue, YYYY.> DOI: [<doi>](https://doi.org/<doi>).
Local copy: `raw/<topic>/<file>`.

[^source-id]: <Title (Author et al., YYYY)>
