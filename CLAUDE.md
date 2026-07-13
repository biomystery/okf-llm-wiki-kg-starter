# CLAUDE.md — Schema layer for the OKF LLM Wiki

This file is the **schema layer** the LLM follows when maintaining this vault. It generalizes
the Karpathy LLM-wiki pattern and adapts it to the [Open Knowledge Format (OKF) v0.1](OKF.md).
For ingest/query/lint, use the bundled project skill
[`okf-wiki`](.claude/skills/okf-wiki/SKILL.md) — **not** the stock `karpathy-llm-wiki`
skill, whose output format does not match this vault (see "Divergence" below).

## Architecture

- **`raw/`** — immutable sources. Read, never modify. Git-ignored. Organized by topic:
  `raw/<topic>/`.
- **`wiki/`** — LLM-maintained OKF pages. You own these fully. Organized **by type**:
  `wiki/<type>/<concept>.md` (one level of subdirectory), plus top-level project/MOC pages.
  Two special files:
  - `wiki/index.md` — catalog / progressive-disclosure entry point. **Read first** on query.
  - `wiki/log.md` — append-only operation log.
- **`templates/`** — OKF frontmatter templates for new pages (`concept.md`, `reference.md`,
  `person.md`, `project.md`, `moc.md`, `raw-source.md`). Doubles as the **schema registry**
  (see "Flexible schema" below).
- **`.claude/skills/okf-wiki/`** — the vault's own ingest/query/lint skill.
- **`scripts/lint-wiki.py`** — deterministic lint (stdlib-only); run before the heuristic pass.

### Type-based subdirectories

Default types (create more as needed; the build's navigation adapts automatically):
`concepts/`, `refs/`, `people/`, `projects/`, `experiments/`.

### Flexible schema: the type set is open, but registered

`type` is the only hard-required frontmatter field (per OKF). Beyond that, **`templates/` is
the schema registry**: each `templates/<type>.md` documents that type's frontmatter contract.
To add a type: (1) create `templates/<type>.md`, (2) create `wiki/<type>/` and a matching
`wiki/index.md` section, (3) log `## [YYYY-MM-DD] schema | added type <type>`. The linter
warns on pages whose `type` has no template. Prefer reusing an existing type (`reference`
covers papers, talks, and blog posts alike) over minting near-duplicates — types earn their
place the same way plugins do.

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
aliases: [shorthand, "alternate name"]   # so [[shorthand]] resolves
tags: [topic-a, topic-b]
timestamp: 2026-07-13     # ISO 8601; when knowledge content last changed
resource: https://…       # optional: canonical URL to the underlying resource
---
```

**Reference (source/paper) pages** additionally carry provenance in frontmatter — capture at
ingest time: `year:`, `source:` (journal/publisher/site), and whenever available `doi:`,
`pmid:`/`pmcid:`, `url:` (canonical landing page), and `raw:` (local path under `raw/`). Put
the clickable `url:`/`doi:` in the body's citation line too.

**Links:** use Obsidian `[[wikilinks]]` in the body to build the knowledge graph. Each page
should link to its relevant MOC/project page. Cross-link related concepts liberally.

## Ingest (add a source)

1. Save the source under `raw/<topic>/` (dated slug). Record provenance (URL/DOI/etc.).
2. Determine placement:
   - extends an existing page → **merge**, add the new source, refresh affected sections;
   - a distinct concept/entity → **create** a new page in the best type dir;
   - spans topics → place in the most relevant dir + add `[[wikilinks]]` cross-refs.
3. Check for contradictions with existing content; annotate with source attribution.
4. Cascade: update other pages materially affected; refresh their `timestamp`.
5. Update `wiki/index.md`; append to `wiki/log.md`:
   `## [YYYY-MM-DD] ingest | <primary page title>` (+ `- Updated: <page>` lines).

**Preprint → published:** when a preprint publishes, update `source`/`year`/`doi`/`url`, add a
`version_note:` if the local PDF is still the preprint, refresh the H1, and log
`## [YYYY-MM-DD] update | <ref> preprint→published`.

## Query (answer questions)

1. Read `wiki/index.md` to locate relevant pages.
2. Read them; synthesize an answer. Prefer wiki content over training knowledge.
3. Cite with links. Do not write files unless asked (then create an **archive** page — a
   new synthesized page, never merged into a source page; prefix its index Summary with
   `[Archived]` and log `## [YYYY-MM-DD] query | Archived: <title>`).

## Lint (quality checks)

Run `python3 scripts/lint-wiki.py` first — it deterministically checks frontmatter validity,
broken wikilinks, index ↔ file consistency, `raw:` paths, unregistered types, and orphans.
Then:
Auto-fix: index ↔ files consistency; broken `[[wikilink]]` targets (fix if exactly one match,
else report); Raw-provenance paths; missing/dead See-Also cross-refs.
Report only (never auto-delete): contradictions, stale claims, orphan pages, missing
cross-topic refs, concepts frequently referenced but lacking a page.
Append `## [YYYY-MM-DD] lint | <N> issues found, <M> auto-fixed` to `wiki/log.md`.

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
- [ ] Nothing sensitive pasted into the LLM chat itself.
- [ ] `git status` shows `raw/` is not staged.

## Obsidian plugins (keep it lean)

This vault bundles **no community plugins**. Add only what earns its place. Recommended
optional set for a KG wiki: **Breadcrumbs** (typed relations/graph), **Templater** (apply the
`templates/`), **Update time on edit** (auto `timestamp`). Avoid unrelated plugins (PDF
export, terminals, slides) in the shared template — install them per-user if needed. A
terminal-style plugin (e.g. **Shell commands**) is the sanctioned per-user way to launch
`claude` from inside Obsidian for in-vault Q&A.
