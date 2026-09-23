# OKF conformance

How this vault maps onto the [Open Knowledge Format (OKF) **v0.2**](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
([spec & samples](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf),
[announcement](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)).

OKF is a vendor-neutral spec for knowledge that AI systems need: **directories of Markdown
files with YAML frontmatter**, human-readable and agent-parseable, git-friendly, no SDK.
v0.2 adds the frontmatter families that make an *agent-maintained* corpus trustable:
provenance (`sources`), trust (`generated` / `verified`), lifecycle (`status`,
`stale_after`), and attested computations.

This vault targets **v0.2**. `wiki/index.md` declares it with `okf_version: "0.2"` — the one
place OKF permits frontmatter in an index file.

## Mapping

| OKF concept (§ of spec) | This vault |
|---|---|
| Bundle = directory tree of Markdown files (§3) | `wiki/` |
| One concept = one Markdown file; path minus `.md` = concept ID (§2) | `wiki/<type>/<concept>.md` |
| Reserved filenames `index.md`, `log.md` (§3.1) | `wiki/index.md`, `wiki/log.md` — nothing else at the top of `wiki/` |
| YAML frontmatter, **`type` required** (§4.1) | every page's frontmatter (see [CLAUDE.md](CLAUDE.md)) |
| Recommended `title`, `description`, `resource`, `tags` (§4.1) | in frontmatter |
| Provenance `sources` + credibility signals (§5.1) | `sources:` — one entry per `raw/` file, URL, or DOI a page was distilled from |
| Per-claim attribution via footnotes keyed to `sources[].id` (§4.2, §5.1) | `[^source-id]` footnotes in the body |
| Trust `generated` / `verified` (§5.2) | `generated: { by, at }` on every page; `verified:` when a human or process confirms it |
| Trust tiers derived from `verified` (§5.3) | not stored — derived by consumers and by `lint-wiki.py` |
| Lifecycle `status` (§5.4) | `status: draft \| stable \| deprecated` |
| Lifecycle `stale_after` (§5.5) | optional absolute instant; the linter warns once passed |
| Actor convention (§7) | `human:<id>`, `claude-code/<model>`, `process:<id>` |
| Cross-references as Markdown links (§6) | authored as `[[wikilinks]]`, **resolved to relative Markdown links at build** |
| `references/` convention (§6.3) | `raw/` (git-ignored) holds mirrored source material; `sources[].resource` points into it |
| `index.md` progressive disclosure (§8) | `wiki/index.md` — sections of `* [[page]] — description` bullets, no frontmatter except `okf_version` |
| `log.md` update history (§9) | `wiki/log.md` — `## YYYY-MM-DD` headings, newest first, `* **Ingest**: …` entries |
| Attested Computation (§10) | optional; `templates/attested-computation.md` registers the type when a vault needs it |
| Extensions — any additional keys (§4.1) | `aliases:`, `stage:`, `venue:`, `year:`, `doi:`, `pmid:` |

`type` values here are lowercase and singular (`concept`, `reference`, `person`) rather than
the spec's Title Case examples (`BigQuery Table`, `Metric`). OKF does not register type
values centrally (§4.1) — consumers must tolerate any string — and lowercase keeps
`type` identical to the directory name under `wiki/`. The one place this costs something is
`attested-computation`: §10.5 has consumers *discover* computations by the literal
`type: Attested Computation`, so a generic OKF consumer will not find this vault's
lowercase spelling. Rename the type (and `templates/attested-computation.md`) if you ever
need that discovery path.

Two caveats on the mapping above. `raw/` is git-ignored and sits *outside* the bundle root,
so `sources[].resource` paths into it resolve locally but dangle for anyone who receives
only `wiki/` — the linter warns on every one of them, which on a fresh clone is expected
rather than a defect. And `lint-wiki.py` is a **producer-side** check, deliberately stricter
than §11: it errors on broken wikilinks, a page missing from `index.md`, and malformed trust
fields, none of which may make a *consumer* reject a bundle.

## The one wrinkle: wikilinks vs. Markdown links

OKF specifies cross-references as normal Markdown links (`[customers](/tables/customers.md)`).
This vault authors them as Obsidian `[[wikilinks]]` for editing ergonomics (autocomplete,
backlinks, graph). The [`wiki-hosting-project`](https://github.com/biomystery/wiki-hosting-project)
resolver rewrites `[[Target]]` / `[[Target|display]]` / `[[Target#Heading]]` and frontmatter
`aliases:` into standard relative Markdown links at build time.

**So:** the **source** is Obsidian-native; the **published/exported** bundle is
OKF-conformant Markdown. If you need the *source tree itself* to be strictly OKF-link-conformant
(e.g. to hand the raw `wiki/` to another agent), run the resolver's export and ship that
output instead of the wikilink source.

## Trust, in practice

Two fields carry the weight, and they answer different questions (§5.2):

- **`generated: { by, at }`** — who *wrote* the current content and when it last meaningfully
  changed. Written on every ingest. `by` is the agent (`claude-code/opus-5`) when the LLM
  distilled the page, `human:<id>` when you wrote it by hand.
- **`verified: [{ by, at }, …]`** — who *confirmed* it against its sources. Never written by
  the agent that generated the page: verification is your sign-off (`human:<id>`) or an
  automated check (`process:<id>`). A page you have read and agree with earns a `verified`
  entry; one the agent merely wrote does not.

Trust tiers are **derived, not stored** (§5.3): no `verified` ⇒ unverified; machine-only
`verified` ⇒ machine-confirmed; any `human:` verifier ⇒ human-reviewed. `lint-wiki.py`
reports the tier mix so you can see how much of the vault has actually been reviewed.

## Migrating a v0.1 vault

Clones made before this change carry v0.1 frontmatter. Legacy *fields* — `timestamp:`,
`raw:`, a body `## Citations` list — are warnings, so migrate those at your own pace. Three
rows below are hard errors instead, because §5.4, §8, and §9 define their shape rather than
leaving it optional: a `status:` outside the lifecycle vocabulary, frontmatter in
`wiki/index.md`, and a non-ISO `log.md` date heading. Do those three first and the linter
goes green; the rest can follow page by page.

| v0.1 | v0.2 | Notes |
|---|---|---|
| `timestamp: 2026-07-13` | `generated: { by: <actor>, at: 2026-07-13T00:00:00Z }` | Spec §13.1. Datetimes need an explicit UTC offset. A consumer MAY fall back to a bare `timestamp:`; this vault's linter warns on one. |
| `raw: ../../raw/topic/file.md` | `sources: [{ id: …, resource: ../../raw/topic/file.md, title: … }]` | Spec §5.1. `raw:` is still checked, but `sources` is where provenance belongs. |
| `source: Journal Name` on a reference | `venue: Journal Name` | Renamed so it cannot be confused with the `sources:` provenance list. |
| body `## Citations` list | `sources` + `[^id]` footnotes | Spec §13.1. |
| `status: active` on a project | `stage: active` + `status: stable` | `status` is now reserved for the OKF lifecycle vocabulary (`draft`/`stable`/`deprecated`); project and experiment state moved to `stage:`. |
| `wiki/index.md` frontmatter block | `okf_version: "0.2"` only | Spec §8 — index files carry no other frontmatter. |
| `wiki/index.md` tables | `## Section` + `* [[page]] — description` bullets | Spec §8. |
| `## [2026-07-13] ingest \| …` log lines, oldest first | `## 2026-07-13` + `* **Ingest**: …`, newest first | Spec §9. |

## Conformance checklist

Structural (§11 — a bundle is conformant if all three hold):

- [x] Every non-reserved `.md` file under `wiki/` has a parseable YAML frontmatter block.
- [x] Every frontmatter block has a non-empty `type`.
- [x] `wiki/index.md` follows §8 (sections of links; no frontmatter but `okf_version`) and
      `wiki/log.md` follows §9 (ISO `## YYYY-MM-DD` headings, newest first).

Producer conventions this vault also holds itself to:

- [x] File paths serve as concept identities; cross-references are Markdown links
      (post-resolve) / wikilinks (source).
- [x] Every page carries `generated: { by, at }` with an actor per §7.
- [x] Pages distilled from a source carry `sources:`; claims tied to a specific source cite
      it with a `[^id]` footnote.
- [x] Timestamps are ISO 8601 with an explicit UTC offset.
- [x] `status` uses the §5.4 vocabulary only.
- [x] `wiki/log.md` records change history.

`python3 scripts/lint-wiki.py` checks these deterministically — the structural three as
errors, the producer conventions mostly as warnings. The link box is the exception: the
linter checks that every `[[wikilink]]` resolves, but the rewrite into Markdown links
happens in the build, not here.
