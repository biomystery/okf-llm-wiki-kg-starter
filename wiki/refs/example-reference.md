---
type: reference
title: "Example Reference (Author et al., 2026)"
description: A placeholder reference page demonstrating OKF v0.2 provenance and trust frontmatter.
aliases: [Author 2026, example ref]
tags: [meta, example]
status: stable
resource: https://example.org/canonical-landing-page
url: https://example.org/canonical-landing-page
year: 2026
venue: Journal or Publisher Name
doi: 10.0000/example.doi
pmid: 00000000
generated: { by: claude-code/opus-5, at: 2026-09-23T00:00:00Z }
verified: { by: human:your-handle, at: 2026-09-23T00:00:00Z }
sources:
  - id: example-source
    resource: ../../raw/example-topic/2026-07-13-example-source.md
    title: "Example Reference (Author et al., 2026)"
    author: human:author-a
    last_modified: 2026-07-13T00:00:00Z
---

# Example Reference (Author et al., 2026)

> Delete once you have a real source. Provenance is captured at ingest time.

## Summary

What the source says, distilled. Do not paste copyrighted full text — keep the original in
`raw/` (git-ignored) and summarize here. `sources[].resource` points at that local copy;
`resource:` at the top points at the published landing page the reader should cite, and
`url:` mirrors it because the site build turns that field into a clickable link under the
title (frontmatter itself never reaches the HTML).

## Key points

- Point one.[^example-source]
- Point two, relevant to [[example-concept]].

This page carries a `verified` entry by a `human:` actor, so a consumer reads it as
**human-reviewed** (OKF §5.3) — the tier the example concept lacks.

## Citation

Author A, Author B. *Title*. Journal, 2026. DOI: [10.0000/example.doi](https://doi.org/10.0000/example.doi).
Local copy: `raw/example-topic/2026-07-13-example-source.md`.

[^example-source]: Example Reference (Author et al., 2026)
