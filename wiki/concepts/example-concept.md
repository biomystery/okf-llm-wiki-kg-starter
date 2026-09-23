---
type: concept
title: Example Concept
description: A placeholder concept page demonstrating the OKF v0.2 frontmatter + wikilink pattern.
aliases: [example, sample concept]
tags: [meta, example]
status: draft
generated: { by: claude-code/opus-5, at: 2026-09-23T00:00:00Z }
sources:
  - id: example-source
    resource: ../../raw/example-topic/2026-07-13-example-source.md
    title: Example source material
---

# Example Concept

> Delete this page once you have real content. It shows the shape the LLM produces on ingest.

## Overview

One paragraph distilling the concept. Written by the LLM from one or more sources in `raw/`,
never copied verbatim. Link related pages inline, e.g. this concept relates to
[[example-reference]] and was discussed by [[example-person]].

## Details

Body sections synthesized from the sources. A claim that comes from one specific source gets
a footnote keyed to that source's `id` in frontmatter — that key, not the footnote prose, is
what a consumer resolves.[^example-source] Use callouts where helpful:

> [!note]
> Callouts render as admonitions in the published site.

`status: draft` marks this page as not yet reviewed; it carries no `verified` entry, so a
consumer reads it as **unverified** (OKF §5.3).

## See Also

- [[example-reference]]

[^example-source]: Example source material
