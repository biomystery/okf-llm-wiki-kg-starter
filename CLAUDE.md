# CLAUDE.md — Schema layer for the OKF LLM Wiki

This file is the **schema layer** the LLM follows when maintaining this vault. It generalizes
the Karpathy LLM-wiki pattern and adapts it to the [Open Knowledge Format (OKF) v0.2](OKF.md).
For ingest/query/lint, use the bundled project skill
[`okf-wiki`](.claude/skills/okf-wiki/SKILL.md) — **not** the stock `karpathy-llm-wiki`
skill, whose output format does not match this vault (see "Divergence" below).

## Architecture

- **`raw/`** — immutable sources. Read, never modify. Git-ignored. Organized by topic:
  `raw/<topic>/`. Plays the role of OKF's `references/` convention (§6.3): `sources[].resource`
  points into it.
- **`wiki/`** — LLM-maintained OKF pages. You own these fully. Organized **by type**:
  `wiki/<type>/<concept>.md` (one level of subdirectory) — every typed page lives in its
  type dir, including projects (`wiki/projects/`) and topic MOCs (`wiki/mocs/`).
  The only top-level files are the two OKF reserved ones:
  - `wiki/index.md` — catalog / progressive-disclosure entry point (the root MOC).
    **Read first** on query.
  - `wiki/log.md` — change history, newest first.
- **`notes/`** — working notes (review findings, source comparisons, open questions). Not
  OKF pages: not linted, indexed, logged, or published. Put findings here when the user
  wants them recorded but **not** ingested; see `notes/README.md`.
- **`templates/`** — OKF frontmatter templates for new pages (`concept.md`, `reference.md`,
  `person.md`, `project.md`, `experiment.md`, `moc.md`, `attested-computation.md`,
  `raw-source.md`). Doubles as the **schema registry** (see "Flexible schema" below).
- **`.claude/skills/okf-wiki/`** — the vault's own ingest/query/lint skill.
- **`scripts/lint-wiki.py`** — deterministic lint (stdlib-only); run before the heuristic pass.

### Type-based subdirectories

Default types (create more as needed; the build's navigation adapts automatically):
`concepts/`, `refs/`, `people/`, `projects/`, `experiments/`.

### Flexible schema: the type set is open, but registered

`type` is the only hard-required frontmatter field (per OKF). Beyond that, **`templates/` is
the schema registry**: each `templates/<type>.md` documents that type's frontmatter contract.
To add a type: (1) create `templates/<type>.md`, (2) create `wiki/<type>/` and a matching
`wiki/index.md` section, (3) log it under today's date as `* **Schema**: Added type <type>.`
The linter warns on pages whose `type` has no template. Prefer reusing an existing type
(`reference` covers papers, talks, and blog posts alike) over minting near-duplicates —
types earn their place the same way plugins do.

## OKF page format (divergence from stock skill)

Author pages as **Obsidian Markdown + YAML frontmatter**, not the stock skill's blockquote
headers. The build resolver converts `[[wikilinks]]` → relative Markdown links, so the
**published** output is OKF-conformant while authoring stays Obsidian-native.

**Frontmatter** — `type` is the only OKF-required field; include the rest when known:

```yaml
---
type: concept            # REQUIRED. concept | reference | person | project | moc | ...
title: Human Readable Name
description: One-line explanation (queryable).
aliases: [shorthand, "alternate name"]   # search/autocomplete only — links target the filename
tags: [topic-a, topic-b]
status: stable           # OKF lifecycle: draft | stable | deprecated (absent ⇒ stable)
resource: https://…      # optional: canonical URI of the thing this page describes
generated: { by: claude-code/opus-5, at: 2026-09-23T14:02:00Z }   # who wrote it, when
verified: { by: human:<id>, at: 2026-09-23T15:00:00Z }            # only when confirmed
stale_after: 2027-01-01T00:00:00Z                                 # optional
sources:                 # what this page was distilled from
  - id: smith-2026
    resource: ../../raw/papers/2026-05-01-smith.pdf
    title: Smith et al. 2026
---
```

**Trust rules (OKF §5, §7) — these are not optional decoration:**

- Every page you create or materially change gets `generated: { by, at }`. `by` is
  **you, the agent** (`claude-code/<model>`) when you wrote the content; `human:<id>` when
  the user did. `at` is an ISO 8601 datetime **with an explicit UTC offset** (`…Z`).
- **Never write a `verified:` entry for your own output.** `verified` records confirmation
  against the sources, by `human:<id>` (the user signing off) or `process:<id>` (an automated
  check). Add one only when the user explicitly confirms a page.
- `status` uses the OKF vocabulary only (`draft` | `stable` | `deprecated`). Domain state
  (a project's `active`/`paused`/`done`, an experiment's `planned`/`running`/…) lives in
  `stage:`, never in `status:`.
- Use `stale_after` when knowledge has a known expiry (a plan, a release-specific fact).
- There is no `timestamp:` field. `generated.at` replaces it (OKF §13.1); the linter warns
  on any survivor.

**Reference (source/paper) pages** carry the provenance of the material they describe in
`sources:` (one entry per local copy or canonical artifact) plus bibliographic keys in
frontmatter — capture at ingest: `year:`, `venue:` (journal/publisher/site), and whenever
available `doi:`, `pmid:`/`pmcid:`, and `resource:` (canonical landing page). Mirror
`resource:` into `url:` on reference pages — the site build renders `url:` as a clickable
link under the title, and frontmatter otherwise never reaches the HTML. Put the clickable
URL/DOI in the body's citation line too.

**Per-claim attribution:** cite a specific source with a Markdown footnote whose label is
that source's `sources[].id` — `…as Smith reports.[^smith-2026]` — and define the footnote
at the bottom. The label is the join key; keep ids stable when rewriting a page.

**Line breaks:** never hard-wrap prose in `wiki/` or `notes/`. Write each paragraph, list
item and callout line as **one line**: Obsidian (default settings) and the site renderer
show single newlines as visible breaks. Tables, code/mermaid blocks and frontmatter are
unaffected.

**Links:** use Obsidian `[[wikilinks]]` in the body to build the knowledge graph. Target
the **filename** — `[[leukapheresis-receipt]]` or `[[leukapheresis-receipt|Leukapheresis
receipt]]` — never a bare title or alias: Obsidian resolves links by filename only, so
`[[Leukapheresis receipt]]` creates a phantom note (the linter flags it; `--fix` rewrites). Each page
should link to its relevant MOC/project page. Cross-link related concepts liberally.

## Ingest (add a source)

1. Save the source under `raw/<topic>/` (dated slug). Record provenance (URL/DOI/etc.).
2. Determine placement:
   - extends an existing page → **merge**, add the new source, refresh affected sections;
   - a distinct concept/entity → **create** a new page in the best type dir;
   - spans topics → place in the most relevant dir + add `[[wikilinks]]` cross-refs.
3. Add a `sources:` entry for the new material on every page distilled from it, and attribute
   the claims it supports with `[^id]` footnotes.
4. Check for contradictions with existing content; annotate with source attribution.
5. Cascade: update other pages materially affected; refresh their `generated: { by, at }`
   (a materially changed page is newly generated). Leave `verified` untouched — content that
   changed after a sign-off is no longer covered by it.
6. Update `wiki/index.md`; prepend to `wiki/log.md` under today's `## YYYY-MM-DD` heading:
   `* **Ingest**: <primary page title>` plus `* **Update**: <page>` lines for cascades.

**Preprint → published:** when a preprint publishes, update `venue`/`year`/`doi`/`resource`,
add a `version_note:` if the local PDF is still the preprint, refresh the H1 and
`generated.at`, and log `* **Update**: <ref> preprint→published.`

## Query (answer questions)

1. Read `wiki/index.md` to locate relevant pages.
2. Read them; synthesize an answer. Prefer wiki content over training knowledge.
3. Weigh trust when answering: flag a claim taken from a `status: draft` or unverified page,
   and say so when a page is past its `stale_after`.
4. Cite with links. Do not write files unless asked (then create an **archive** page — a
   new synthesized page, never merged into a source page; prefix its index entry with
   `[Archived]` and log `* **Query**: Archived <title>.`).

## Lint (quality checks)

Run `python3 scripts/lint-wiki.py` first — it deterministically checks frontmatter validity,
the v0.2 trust/provenance/lifecycle families, reserved-file structure (§8/§9),
broken/ambiguous wikilinks, index ↔ file consistency, `sources[].resource` paths, footnote
↔ source-id joins, legacy v0.1 fields, unregistered types, and orphans.

**Auto-fix:** index ↔ files consistency; broken `[[wikilink]]` targets (fix if exactly one
match, else report); provenance paths; missing/dead See-Also cross-refs; legacy-field
migration (`timestamp:` → `generated`, `raw:` → a `sources` entry).

**Report only (never auto-delete):** contradictions, stale claims, orphan pages, missing
cross-topic refs, concepts frequently referenced but lacking a page. Never add or edit a
`verified:` entry during lint — verification is the user's, not yours.
Log it under today's date: `* **Lint**: <N> issues found, <M> auto-fixed.`

## Divergence from the `karpathy-llm-wiki` skill

The stock skill uses **markdown relative links + `> Sources:`/`> Raw:` blockquote headers +
topic-based dirs**. This vault uses **`[[wikilinks]]` + YAML frontmatter + type-based dirs**
(for OKF + the `wiki-hosting-project` resolver). The bundled
[`okf-wiki`](.claude/skills/okf-wiki/SKILL.md) project skill implements ingest/query/lint
for this vault's format — always prefer it over the stock skill here. The stock skill remains
useful in *other* projects that follow its native format.

## Sensitive-data checklist (run before sharing/publishing)

- [ ] No patient-identifiable, personal, or confidential data in `wiki/` or committed files —
      such material belongs in `raw/` (git-ignored) only, or not at all.
- [ ] No secrets/keys/tokens in any tracked file.
- [ ] No copyrighted full-text in `wiki/` (distill; keep the PDF in `raw/`).
- [ ] `sources[].resource` paths point into `raw/` — they are paths, not content; check none
      of them leaks a sensitive filename.
- [ ] Nothing sensitive pasted into the LLM chat itself.
- [ ] `git status` shows `raw/` is not staged.

**Internal / confidential vaults.** When the sources are company-internal (SOPs, batch
data, training decks), the distilled `wiki/` is confidential too — a summary of a
confidential process is still confidential. Then: host the repo **private** in the owning
organization, serve the site only behind the org's auth, never copy pages into a public
vault or this starter, and prefer process/role descriptions over names of individual
operators or patients/donors (lot and batch IDs are fine if they're not identifying).

## Obsidian plugins (keep it lean)

This vault bundles **no community plugins**. Add only what earns its place. Recommended
optional set for a KG wiki: **Breadcrumbs** (typed relations/graph), **Templater** (apply the
`templates/`). Avoid unrelated plugins (PDF export, terminals, slides) in the shared
template — install them per-user if needed. A terminal-style plugin (e.g. **Shell commands**)
is the sanctioned per-user way to launch `claude` from inside Obsidian for in-vault Q&A.

> Note: an auto-`timestamp`-on-edit plugin is deliberately *not* recommended any more —
> `generated.at` means "when the knowledge last changed", which is not file mtime.
