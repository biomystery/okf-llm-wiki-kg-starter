#!/usr/bin/env bash
# Stamp out a fresh, domain-specific vault from this starter.
#
# Usage:
#   ./scripts/new-vault.sh <DEST_DIR> [SITE_NAME]
#
#   DEST_DIR   new directory to create (must not exist), e.g. ~/projects/acme-wiki
#   SITE_NAME  human title for the vault/site (default: DEST_DIR's basename)
#
# What it does:
#   1. copies the starter's *tracked* files (git archive — no raw/, _site/, .cache/, local
#      Obsidian workspace) into DEST_DIR,
#   2. removes the example pages and creates the default type dirs,
#   3. resets wiki/index.md and wiki/log.md to an empty §8/§9 skeleton,
#   4. titles the README and records which starter commit the vault came from
#      (.starter-version) so later starter improvements can be diffed and pulled in,
#   5. `git init`s DEST_DIR with an initial commit (no remote — add one yourself).
#
# Requires: git. Run from anywhere; it locates the starter from its own path.
set -euo pipefail

STARTER="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${1:?usage: new-vault.sh <DEST_DIR> [SITE_NAME]}"
NAME="${2:-$(basename "$DEST")}"
TODAY="$(date -u +%Y-%m-%d)"
TYPES=(concepts refs people projects experiments mocs)

if [[ -e "$DEST" ]]; then
  echo "error: '$DEST' already exists" >&2
  exit 1
fi
if [[ -n "$(git -C "$STARTER" status --porcelain)" ]]; then
  echo "warning: starter has uncommitted changes — only committed files are copied" >&2
fi

echo "==> Copying starter ($STARTER @ $(git -C "$STARTER" rev-parse --short HEAD)) -> $DEST"
mkdir -p "$DEST"
git -C "$STARTER" archive HEAD | tar -x -C "$DEST"
git -C "$STARTER" rev-parse HEAD > "$DEST/.starter-version"

echo "==> Removing example pages; creating type dirs"
find "$DEST/wiki" -name 'example-*.md' -delete
for t in "${TYPES[@]}"; do
  mkdir -p "$DEST/wiki/$t"
  touch "$DEST/wiki/$t/.gitkeep"
done

cat > "$DEST/wiki/index.md" <<EOF
---
okf_version: "0.2"
---

# $NAME — Index

> The catalog / entry point (OKF \`index.md\`, §8). One bullet per page, grouped by type, each
> carrying the page's \`description\`. The LLM keeps this in sync on ingest and lint.

## mocs

Topic hubs (maps of content).

## projects

Efforts with a goal and a \`stage\`.

## concepts

Distilled ideas, methods, definitions.

## refs

Source pages with provenance (\`sources\`, URL/DOI, year).

## people

People, teams, organizations.

## experiments

Questions tested, with setup and results.
EOF

cat > "$DEST/wiki/log.md" <<EOF
# Wiki Update Log

> Change history for this bundle (OKF \`log.md\`, §9). Date-grouped, **newest first**,
> ISO \`## YYYY-MM-DD\` headings. Entries lead with a bold kind — \`**Ingest**\`, \`**Update**\`,
> \`**Query**\`, \`**Lint**\`, \`**Schema**\`, \`**Creation**\`, \`**Deprecation**\` — by convention.

## $TODAY

* **Creation**: Created vault "$NAME" from okf-llm-wiki-kg-starter @ $(git -C "$STARTER" rev-parse --short HEAD).
EOF

# Retitle the README; keep the rest of the starter docs as the vault's workflow docs.
{
  echo "# $NAME"
  echo
  echo "An OKF v0.2 LLM-wiki vault created from"
  echo "[okf-llm-wiki-kg-starter](https://github.com/biomystery/okf-llm-wiki-kg-starter)"
  echo "(commit in \`.starter-version\`). Workflow: [WORKFLOW.md](WORKFLOW.md) ·"
  echo "schema layer: [CLAUDE.md](CLAUDE.md) · format: [OKF.md](OKF.md)."
  echo
  echo "Start at [wiki/index.md](wiki/index.md). Sources live in \`raw/\` (git-ignored, local only)."
  echo
  echo "\`\`\`sh"
  echo "python3 scripts/lint-wiki.py                         # deterministic checks"
  echo "SITE_NAME=\"$NAME\" ./scripts/build-site.sh ./ ./_site  # static site"
  echo "\`\`\`"
} > "$DEST/README.md"

echo "==> git init"
git -C "$DEST" init -q
git -C "$DEST" add -A
git -C "$DEST" commit -q -m "Scaffold $NAME from okf-llm-wiki-kg-starter"

echo "==> Done: $DEST"
echo "    Next: add a remote (e.g. gh repo create <org>/<name> --private --source \"$DEST\" --push),"
echo "    drop sources into raw/<topic>/, and ask Claude to ingest them."
