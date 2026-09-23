# notes/

Working notes: review findings, source comparisons, open questions, and drafts that aren't
ready for (or don't belong in) the wiki.

- **Not part of the OKF bundle.** Not linted, not in `wiki/index.md` or `wiki/log.md`, and not
  published by `build-site.sh`. No frontmatter contract; a small header (`date`, `author`,
  `topic`, `status: open | closed`) is enough.
- **Tracked in git**, unlike `raw/`. Treat notes with the same sensitivity as the wiki.
- **Name files** `YYYY-MM-DD-slug.md`.
- **Links:** notes may link into the wiki (`[[page-stem|text]]`). Wiki pages never link to
  notes, so the published bundle stays self-contained.
- **Promotion:** when a note's content is settled (for example, a discrepancy resolved
  against the source of record), ingest it into the proper wiki page and set the note to
  `status: closed`, recording where it went.
