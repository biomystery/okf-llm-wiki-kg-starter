#!/usr/bin/env bash
# Render this vault's wiki/ into a static, searchable HTML site using
# biomystery/wiki-hosting-project (resolves [[wikilinks]] + aliases, callouts,
# full-text search, type-folder navigation).
#
# Usage:
#   ./scripts/build-site.sh [VAULT_DIR] [OUTPUT_DIR]
#
#   VAULT_DIR   root containing wiki/ (default: repo root, i.e. the script's parent)
#   OUTPUT_DIR  where the static site is written (default: ./_site)
#
# Env:
#   WIKI_HOSTING_DIR   path to a local clone of wiki-hosting-project.
#                      If unset, the repo is cloned into .cache/wiki-hosting-project.
#   SITE_NAME          header title for the generated site (default: "Knowledge Base")
#
# Requires: git, python3 (the resolver + mkdocs deps). See wiki-hosting-project/README.md.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VAULT_DIR="${1:-$REPO_ROOT}"
OUTPUT_DIR="${2:-$REPO_ROOT/_site}"
SITE_NAME="${SITE_NAME:-Knowledge Base}"
WIKI_HOSTING_REPO="https://github.com/biomystery/wiki-hosting-project.git"
WIKI_HOSTING_DIR="${WIKI_HOSTING_DIR:-$REPO_ROOT/.cache/wiki-hosting-project}"

if [[ ! -d "$VAULT_DIR/wiki" ]]; then
  echo "error: no wiki/ found under '$VAULT_DIR'" >&2
  exit 1
fi

# Fetch the hosting toolchain if not provided locally.
if [[ ! -d "$WIKI_HOSTING_DIR" ]]; then
  echo "==> Cloning wiki-hosting-project into $WIKI_HOSTING_DIR"
  mkdir -p "$(dirname "$WIKI_HOSTING_DIR")"
  git clone --depth 1 "$WIKI_HOSTING_REPO" "$WIKI_HOSTING_DIR"
fi

# wiki-hosting-project's build-site.sh takes: <vault> <output-dir>.
# It renders the vault (which contains wiki/) to static HTML.
echo "==> Building site: '$VAULT_DIR/wiki' -> '$OUTPUT_DIR' (title: $SITE_NAME)"
SITE_NAME="$SITE_NAME" "$WIKI_HOSTING_DIR/build-site.sh" "$VAULT_DIR/wiki" "$OUTPUT_DIR"

echo "==> Done. Serve '$OUTPUT_DIR' behind your own auth proxy (content is private)."
echo "    e.g.  python3 -m http.server -d '$OUTPUT_DIR' 8090   # local preview only"
