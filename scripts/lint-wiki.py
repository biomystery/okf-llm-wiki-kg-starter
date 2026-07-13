#!/usr/bin/env python3
"""Deterministic lint for the OKF wiki. Stdlib only — no PyYAML.

Errors (exit 1):
  - page missing YAML frontmatter or the required `type:` field
  - [[wikilink]] with no matching page (by filename, title, or alias)
  - wiki/index.md row pointing at a nonexistent page
  - page absent from wiki/index.md

Warnings (exit 0):
  - ambiguous [[wikilink]] matching more than one page (alias collision)
  - `raw:` frontmatter path that doesn't exist locally (raw/ is git-ignored, so
    this is expected on fresh clones)
  - page whose `type` has no templates/<type>.md (unregistered schema — see CLAUDE.md)
  - orphan page: no inbound wikilinks from any page other than index/log

The heuristic checks (contradictions, staleness, missing cross-topic refs) are the
LLM's job — see .claude/skills/okf-wiki/SKILL.md.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
TEMPLATES = ROOT / "templates"
SPECIAL = {"index.md", "log.md"}

# [[Target]], [[Target|display]], [[Target#Heading]], ![[Embed]]
WIKILINK = re.compile(r"(!?)\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
FENCE = re.compile(r"^(```|~~~).*?^\1\s*$", re.M | re.S)
INLINE_CODE = re.compile(r"`[^`\n]*`")
# Link targets with these extensions are attachments, not pages — out of scope.
ASSET_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".pdf",
              ".mp3", ".mp4", ".mov", ".canvas", ".base"}


def split_frontmatter(text):
    """Return (frontmatter dict or None, body)."""
    if not text.startswith("---\n"):
        return None, text
    # Closing delimiter is a line that is exactly `---` (not `----`, not `--- x`).
    end_m = re.search(r"^---[ \t]*$", text[4:], re.M)
    if not end_m:
        return None, text
    block, body = text[4:4 + end_m.start()], text[4 + end_m.end():]
    fm, key = {}, None
    for line in block.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        kv = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if kv:
            key, val = kv.group(1), kv.group(2).strip().strip("\"'")
            fm[key] = val
        elif key is not None:
            item = re.match(r"^\s*-\s+(.*)$", line)
            if item:
                v = item.group(1).strip().strip("\"'")
                prev = fm.get(key)
                fm[key] = (prev if isinstance(prev, list) else ([prev] if prev else [])) + [v]
    return fm, body


def as_list(val):
    if val is None or val == "" or val == "[]":
        return []
    if isinstance(val, list):
        return val
    if val.startswith("[") and val.endswith("]"):
        # Quote-aware split: `[foo, "bar, baz"]` -> ['foo', 'bar, baz'].
        items = re.findall(r'\s*("[^"]*"|\'[^\']*\'|[^,]+)', val[1:-1])
        return [x.strip().strip("\"'") for x in items if x.strip()]
    return [val]


def strip_code(body):
    return INLINE_CODE.sub("", FENCE.sub("", body))


def main():
    errors, warnings = [], []
    pages = {}  # path -> (frontmatter, body)
    for p in sorted(WIKI.rglob("*.md")):
        fm, body = split_frontmatter(p.read_text(encoding="utf-8"))
        pages[p] = (fm, body)
        if p.name == "log.md":
            continue
        if fm is None:
            errors.append(f"{p.relative_to(ROOT)}: no YAML frontmatter")
        elif "type" not in fm:
            errors.append(f"{p.relative_to(ROOT)}: frontmatter missing required `type:`")

    content_pages = {p for p in pages if p.name not in SPECIAL}

    # Link-target index: filename stem, title, and aliases (lowercased).
    targets = {}
    for p in content_pages:
        fm, _ = pages[p]
        names = {p.stem}
        if fm:
            if fm.get("title"):
                names.add(str(fm["title"]))
            names.update(as_list(fm.get("aliases")))
        for n in names:
            targets.setdefault(n.lower(), set()).add(p)

    # Wikilink resolution + inbound-link counts.
    inbound = {p: 0 for p in content_pages}
    for p, (fm, body) in pages.items():
        for m in WIKILINK.finditer(strip_code(body)):
            name = m.group(2).strip()
            if Path(name).suffix.lower() in ASSET_EXTS:
                continue  # attachment (image/pdf/canvas), out of scope
            hits = targets.get(name.removesuffix(".md").lower(), set())
            if not hits:
                errors.append(f"{p.relative_to(ROOT)}: broken wikilink [[{name}]]")
            elif len(hits) > 1:
                candidates = ", ".join(sorted(str(h.relative_to(WIKI)) for h in hits))
                warnings.append(f"{p.relative_to(ROOT)}: ambiguous wikilink [[{name}]] matches {len(hits)} pages: {candidates}")
            for h in hits:
                if h != p and p.name not in SPECIAL:
                    inbound[h] += 1

    # Index consistency.
    index = WIKI / "index.md"
    if index in pages:
        listed = {m.group(2).strip().lower() for m in WIKILINK.finditer(pages[index][1])}
        for p in content_pages:
            fm, _ = pages[p]
            names = {p.stem.lower()} | {n.lower() for n in as_list(fm.get("aliases") if fm else None)}
            if fm and fm.get("title"):
                names.add(str(fm["title"]).lower())
            if not names & listed:
                errors.append(f"wiki/index.md: missing entry for {p.relative_to(WIKI)}")
    else:
        errors.append("wiki/index.md: file not found")

    # raw: provenance paths (warn only — raw/ is git-ignored).
    for p in content_pages:
        fm, _ = pages[p]
        raw = fm.get("raw") if fm else None
        if raw and not (p.parent / raw).resolve().exists():
            warnings.append(f"{p.relative_to(ROOT)}: raw source not found locally: {raw}")

    # Unregistered types (no template) and orphans.
    known_types = {t.stem for t in TEMPLATES.glob("*.md")}
    for p in content_pages:
        fm, _ = pages[p]
        t = fm.get("type") if fm else None
        if t and t not in known_types:
            warnings.append(f"{p.relative_to(ROOT)}: type `{t}` has no templates/{t}.md (register it — see CLAUDE.md)")
        if inbound[p] == 0 and (fm or {}).get("type") != "moc":
            warnings.append(f"{p.relative_to(ROOT)}: orphan — no inbound wikilinks from other pages")

    for e in errors:
        print(f"ERROR   {e}")
    for w in warnings:
        print(f"warning {w}")
    print(f"\nlint: {len(errors)} error(s), {len(warnings)} warning(s) across {len(content_pages)} page(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
