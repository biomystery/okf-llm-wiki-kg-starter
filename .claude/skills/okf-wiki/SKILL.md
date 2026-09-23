---
name: okf-wiki
description: "Ingest, query, and lint THIS vault's OKF wiki (wikilinks + YAML frontmatter + type-based dirs). Use for: 'add to wiki', 'ingest <source>', 'what do I know about', 'lint the wiki', or any LLM-wiki maintenance in this repo. Supersedes the stock karpathy-llm-wiki skill here — the stock skill's format (topic dirs, blockquote headers, markdown links) does NOT match this vault."
---

# OKF Wiki — this vault's ingest / query / lint

This vault follows the Karpathy LLM-wiki pattern adapted to [OKF v0.2](../../../OKF.md).
[CLAUDE.md](../../../CLAUDE.md) is the authoritative schema layer; this skill is the
operational checklist. **Do not use the stock `karpathy-llm-wiki` skill's formats** — it
produces topic dirs + `> Sources:` blockquote headers + markdown relative links, which this
vault does not use.

## Format rules (always)

- Pages live at `wiki/<type>/<concept>.md` — **type-based** dirs (`concepts/`, `refs/`,
  `people/`, `projects/`, `experiments/`, `mocs/`, …), one level deep. Only `index.md`
  (the root MOC) and `log.md` sit at the top of `wiki/`; those two are OKF's reserved
  filenames and follow §8/§9, not the page format.
- Every page starts with YAML frontmatter; `type:` is required. Copy the matching file in
  `templates/` for the full field set (references carry bibliography: `year`, `venue`,
  `doi`/`pmid`, `resource`).
- **Trust (OKF §5/§7), on every page you touch:**
  - `generated: { by: claude-code/<model>, at: <ISO 8601 with UTC offset> }` — refresh `at`
    whenever the content materially changes. This replaces v0.1's `timestamp:`.
  - `verified:` is **never yours to write**. Only the user (`human:<id>`) or an automated
    check (`process:<id>`) verifies. Never touch an existing `verified` entry.
  - `status:` is the OKF lifecycle vocabulary (`draft` | `stable` | `deprecated`) only.
    Project/experiment state goes in `stage:`.
  - `sources:` lists what the page was distilled from, one entry per source, each with
    `resource:` (a `raw/` path or URL) and a stable `id:`. Cite a claim with a `[^id]`
    footnote keyed to that id.
- Cross-references are Obsidian `[[wikilinks]]` in the body, targeting the **filename**
  (`[[page-stem]]` or `[[page-stem|Display text]]`). Obsidian does not resolve titles or
  aliases in links; a `[[Title]]` link makes a phantom graph node. Link liberally; every
  page links to its MOC/project page.
- The type set is **open** (see "Schema" below).

## Ingest

1. Save the source under `raw/<topic>/YYYY-MM-DD-slug.md` (or `.pdf`) using
   `templates/raw-source.md` for pasted text. Record provenance (URL/DOI). `raw/` is
   immutable and git-ignored — never edit an existing raw file.
   **Document-store sources** (SharePoint/OneDrive/Drive/Confluence): the same file often
   exists in several places. Pick one canonical copy (prefer the owning team's or the
   user's named copy; ask only if the copies differ in content), and record the others under
   `Other copies:`. If the connector returns text rather than the binary, save that
   extraction as `raw/<topic>/YYYY-MM-DD-slug.md` with `Capture:` saying what was lost
   (images, charts, tables), and point `resource:`/`url:` on the ref page at the store's
   web URL. For decks, keep `## Slide N` headings so footnotes can cite slide numbers.
2. Placement: extends an existing page → **merge** + add source + refresh sections;
   distinct concept/entity → **create** from the right template; spans topics → best-fit
   dir + `[[wikilink]]` cross-refs. A source page itself gets a `refs/` page.
3. Provenance: add a `sources:` entry (`id`, `resource`, `title`; `author`/`last_modified`
   when known) on every page distilled from the new material, and attribute the claims it
   supports with `[^id]` footnotes. New pages start `status: draft` unless the user reviews
   them on the spot.
4. Check contradictions with existing pages; annotate disagreements with source attribution
   in every affected page, cross-linked.
5. Cascade: update materially affected pages and refresh each one's `generated.at` (and `by`,
   if a different actor). Leave `verified:` alone — a page whose content changed after a
   sign-off is no longer covered by it, and dropping the entry is the user's call.
6. Update `wiki/index.md` (a `* [[page]] — description` bullet under its type section,
   optionally suffixed with the page's derived trust tier as `*(draft, unverified)*`) and
   **prepend** to `wiki/log.md` under today's `## YYYY-MM-DD` heading (newest first):
   `* **Ingest**: <primary page title>` plus `* **Update**: <page>` lines for cascades.

**Decomposing a large source** (a training deck, SOP, or report): one `refs/` page for the
source itself, then pages for the durable ideas it teaches (a process step, an instrument, a
quality attribute) — not one page per slide. Put numbers that define a process (setpoints,
ratios, timings) on the page for the thing they parameterize, each footnoted, so a later
source that changes a number updates one place. Add a `mocs/` hub when a topic has more than
a handful of pages, and link every new page to it. When the source describes a sequence (a process, pipeline,
protocol, timeline), also write one **end-to-end overview page** first, and link it as
"Start here" from the MOC and `index.md`. That page should tell the whole story: a short
narrative, the phases, a step-by-step table with the *why* for each step, and how the
state changes along the way. Detail pages are for lookup; the overview is where a reader
learns how the parts fit together. A table of links to the detail pages is not an overview.

## Query

1. Read `wiki/index.md` to locate pages; read them; synthesize.
2. Prefer wiki content over training knowledge; cite pages with links.
3. Surface trust: note when an answer rests on a `draft`/unverified page, or one past its
   `stale_after`.
4. Write nothing unless asked to archive: then create a **new** page (never merge into a
   source page), prefix its index entry with `[Archived]`, and log
   `* **Query**: Archived <title>.`

## Lint

1. Run the deterministic pass first: `python3 scripts/lint-wiki.py` (frontmatter validity,
   trust/provenance/lifecycle families, reserved-file structure, broken wikilinks, index ↔
   file consistency, source paths, footnote ↔ `sources[].id` joins, legacy v0.1 fields,
   unknown types, orphans).
2. Auto-fix what the script flags as fixable-by-rule: broken wikilink with exactly one
   matching page → fix; page missing from index → add a bullet; index entry for a deleted
   page → mark `[MISSING]`, don't delete; legacy `timestamp:` → `generated: { by, at }`
   (`by: human:<id>` if the page predates agent authorship and you cannot tell — ask);
   legacy `raw:` → a `sources` entry.
3. Heuristic pass (report only, never auto-delete): contradictions, stale claims, missing
   cross-topic refs, concepts frequently mentioned but lacking a page. Never add `verified:`.
4. Log it under today's date: `* **Lint**: <N> issues found, <M> auto-fixed.`

## Schema (flexible, template-governed)

`type:` is the only hard-required field (OKF). The type set is open — but a new type must
be **registered**, not improvised:

1. Create `templates/<type>.md` with its frontmatter contract (this is the schema record).
2. Create `wiki/<type>/` and a matching section in `wiki/index.md`.
3. Log it: `* **Schema**: Added type <type>.`

`lint-wiki.py` warns on any page whose `type` has no template. Prefer reusing an existing
type over minting a near-duplicate (e.g. use `reference` for talks/blog posts, don't add
`talk`). `attested-computation` (OKF §10) is registered but unused by default — delete the
template if the vault will never carry sanctioned computations.
