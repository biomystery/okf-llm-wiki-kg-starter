# OKF LLM Wiki + KG Starter

A generalizable, topic-agnostic starter for building a **personal LLM-powered knowledge
base** that is:

- authored as an **Obsidian vault** (write in `[[wikilinks]]`, live graph, backlinks),
- maintained by an LLM using the **Karpathy LLM-wiki pattern** (`raw/` → `wiki/`; ingest / query / lint),
- conformant to the **[Open Knowledge Format (OKF) v0.1](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)**
  so the knowledge is portable and agent-readable across tools, and
- publishable as a **static, searchable website** via
  [`wiki-hosting-project`](https://github.com/biomystery/wiki-hosting-project).

This repo is a **clean template** — no domain content. Clone it, drop your sources into
`raw/`, and let the workflow compound your knowledge over time.

## The workflow at a glance

```
topic sources ─▶ raw/ (immutable) ─▶ [LLM: ingest] ─▶ wiki/ (OKF pages) ─▶ [resolver+mkdocs] ─▶ static HTML site
                                          │                                        ▲
                                          └── query / lint ───────────────────────┘
```

See **[WORKFLOW.md](WORKFLOW.md)** for the full step-by-step. The LLM's operating rules
live in **[CLAUDE.md](CLAUDE.md)** (the "schema layer"). How this maps onto OKF is in
**[OKF.md](OKF.md)**.

## Layout

| Path | Tracked? | Purpose |
|---|---|---|
| `raw/` | ❌ git-ignored | Immutable source material (PDFs, pasted text, exports). Read, never modify. |
| `wiki/` | ✅ | LLM-maintained OKF knowledge pages. Type-based subdirs + `index.md` + `log.md`. |
| `templates/` | ✅ | OKF-adapted frontmatter templates for new pages. |
| `scripts/` | ✅ | `build-site.sh` — render `wiki/` to a static site. |
| `.obsidian/` | ✅ | Minimal, clean vault config (no community plugins bundled). |
| `CLAUDE.md`, `WORKFLOW.md`, `OKF.md` | ✅ | Schema layer + docs. |

> **Why `raw/` is ignored:** raw material is often large, copyrighted, or private. Keep it
> local (or on shared storage) and let the `wiki/` — your distilled, shareable knowledge —
> be the version-controlled artifact. Adjust `.gitignore` if your raw material is public.

## Quickstart

1. **Clone this template**, then open the folder as a vault in [Obsidian](https://obsidian.md).
2. **Add a source:** drop a file into `raw/<topic>/`, or paste text and ask your LLM to ingest.
3. **Ingest** (in Claude Code, with the `karpathy-llm-wiki` skill):
   > "Add this to the wiki" / "Ingest raw/papers/foo.pdf"

   The LLM creates/updates OKF pages under `wiki/`, wires `[[wikilinks]]`, and logs it.
4. **Query:** "What do I know about X?" — the LLM reads `wiki/index.md` and answers with citations.
5. **Lint** periodically: "Lint the wiki" — fixes broken links, flags orphans/contradictions.
6. **Publish** to a static site:
   ```sh
   ./scripts/build-site.sh ./ ./_site        # renders wiki/ → ./_site
   ```

## Publishing

`scripts/build-site.sh` wraps
[`wiki-hosting-project`](https://github.com/biomystery/wiki-hosting-project), which resolves
Obsidian `[[wikilinks]]` and frontmatter `aliases:` into standard relative Markdown links
(OKF-conformant output), converts callouts, builds a client-side full-text search, and
auto-generates navigation from the type-based folders. See that repo's README for Docker
serving and cron auto-rebuild.

## License

Template scaffolding only; add your own license. Your `wiki/` content is yours.
