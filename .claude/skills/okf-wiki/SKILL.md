---
name: okf-wiki
description: "Ingest, query, and lint THIS vault's OKF wiki (wikilinks + YAML frontmatter + type-based dirs). Use for: 'add to wiki', 'ingest <source>', 'what do I know about', 'lint the wiki', or any LLM-wiki maintenance in this repo. Supersedes the stock karpathy-llm-wiki skill here — the stock skill's format (topic dirs, blockquote headers, markdown links) does NOT match this vault."
---

# OKF Wiki — this vault's ingest / query / lint

This vault follows the Karpathy LLM-wiki pattern adapted to [OKF v0.1](../../../OKF.md).
[CLAUDE.md](../../../CLAUDE.md) is the authoritative schema layer; this skill is the
operational checklist. **Do not use the stock `karpathy-llm-wiki` skill's formats** — it
produces topic dirs + `> Sources:` blockquote headers + markdown relative links, which this
vault does not use.

## Format rules (always)

- Pages live at `wiki/<type>/<concept>.md` — **type-based** dirs (`concepts/`, `refs/`,
  `people/`, `projects/`, `experiments/`, …), one level deep.
- Every page starts with YAML frontmatter; `type:` is required. Copy the matching file in
  `templates/` for the full field set (references carry provenance: `year`, `source`,
  `doi`/`pmid`, `url`, `raw`).
- Cross-references are Obsidian `[[wikilinks]]` in the body (aliases resolve too). Link
  liberally; every page links to its MOC/project page.
- `timestamp:` = when the knowledge content last changed (ISO date), not file mtime.
- The type set is **open** (see "Schema" below).

## Ingest

1. Save the source under `raw/<topic>/YYYY-MM-DD-slug.md` (or `.pdf`) using
   `templates/raw-source.md` for pasted text. Record provenance (URL/DOI). `raw/` is
   immutable and git-ignored — never edit an existing raw file.
2. Placement: extends an existing page → **merge** + add source + refresh sections;
   distinct concept/entity → **create** from the right template; spans topics → best-fit
   dir + `[[wikilink]]` cross-refs. A source page itself gets a `refs/` page with
   provenance frontmatter.
3. Check contradictions with existing pages; annotate disagreements with source attribution
   in every affected page, cross-linked.
4. Cascade: update materially affected pages; refresh each one's `timestamp:`.
5. Update `wiki/index.md` (one table row per page, grouped by type) and append to
   `wiki/log.md`: `## [YYYY-MM-DD] ingest | <primary page title>` plus `- Updated: <page>`
   lines for cascades.

## Query

1. Read `wiki/index.md` to locate pages; read them; synthesize.
2. Prefer wiki content over training knowledge; cite pages with links.
3. Write nothing unless asked to archive: then create a **new** page (never merge into a
   source page), prefix its index Summary with `[Archived]`, and log
   `## [YYYY-MM-DD] query | Archived: <title>`.

## Lint

1. Run the deterministic pass first: `python3 scripts/lint-wiki.py` (frontmatter validity,
   broken wikilinks, index ↔ file consistency, `raw:` paths, orphans, unknown types).
2. Auto-fix what the script flags as fixable-by-rule: broken wikilink with exactly one
   matching page → fix; page missing from index → add a row; index row for a deleted page →
   mark `[MISSING]`, don't delete.
3. Heuristic pass (report only, never auto-delete): contradictions, stale claims, missing
   cross-topic refs, concepts frequently mentioned but lacking a page.
4. Append `## [YYYY-MM-DD] lint | <N> issues found, <M> auto-fixed` to `wiki/log.md`.

## Schema (flexible, template-governed)

`type:` is the only hard-required field (OKF). The type set is open — but a new type must
be **registered**, not improvised:

1. Create `templates/<type>.md` with its frontmatter contract (this is the schema record).
2. Create `wiki/<type>/` and a matching section in `wiki/index.md`.
3. Log it: `## [YYYY-MM-DD] schema | added type <type>`.

`lint-wiki.py` warns on any page whose `type` has no template. Prefer reusing an existing
type over minting a near-duplicate (e.g. use `reference` for talks/blog posts, don't add
`talk`).
