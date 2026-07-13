# OKF conformance

How this vault maps onto the [Open Knowledge Format (OKF) v0.1](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)
([spec & samples](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf)).

OKF is a vendor-neutral spec for knowledge that AI systems need: **directories of Markdown
files with YAML frontmatter**, human-readable and agent-parseable, git-friendly, no SDK.

## Mapping

| OKF concept | This vault |
|---|---|
| Bundle = directory of Markdown files | `wiki/` |
| One concept = one Markdown file; file path = identity | `wiki/<type>/<concept>.md` |
| YAML frontmatter, **`type` required** | every page's frontmatter (see [CLAUDE.md](CLAUDE.md)) |
| Standard fields: `title`, `description`, `resource`, `tags`, `timestamp` | in frontmatter |
| Cross-references via Markdown links | authored as `[[wikilinks]]`, **resolved to relative Markdown links at build** |
| Optional `index.md` (progressive disclosure) | `wiki/index.md` |
| Optional `log.md` (change history) | `wiki/log.md` |

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

## Conformance checklist

- [x] Concepts are Markdown files under `wiki/`.
- [x] Every page has YAML frontmatter with at least `type`.
- [x] File paths serve as concept identities.
- [x] Cross-references are Markdown links (post-resolve) / wikilinks (source).
- [x] `wiki/index.md` provides hierarchy navigation.
- [x] `wiki/log.md` records change history.
