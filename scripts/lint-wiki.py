#!/usr/bin/env python3
"""Deterministic lint for the OKF v0.2 wiki. Stdlib only — no PyYAML.

Errors (exit 1):
  - page missing YAML frontmatter, an unterminated frontmatter block, or a missing /
    non-scalar `type:` field
  - [[wikilink]] with no matching page (by filename, title, or alias)
  - wiki/index.md entry pointing at a nonexistent page
  - page absent from wiki/index.md
  - malformed OKF v0.2 frontmatter: bad `generated`/`verified` actor or datetime,
    `status` outside the lifecycle vocabulary, `sources` entry without `resource`,
    duplicate `sources[].id`, `attested-computation` without `runtime`
  - reserved-file structure: frontmatter in an `index.md` (other than the bundle-root
    `okf_version`), or a `log.md` date heading that is not ISO `## YYYY-MM-DD`

Warnings (exit 0):
  - legacy v0.1 fields: `timestamp:`, `raw:`, a body `# Citations` list
  - page with no `generated:` (unknown provenance)
  - page past its `stale_after`
  - ambiguous [[wikilink]] matching more than one page (alias collision)
  - `sources[].resource` / `raw:` path that doesn't exist locally (raw/ is git-ignored,
    so this is expected on fresh clones)
  - footnote `[^id]` with no definition, or not matching any `sources[].id`
  - page whose `type` has no templates/<type>.md (unregistered schema — see CLAUDE.md)
  - orphan page: no inbound wikilinks from any page other than index/log
  - log.md entries not in newest-first order; bundle root without `okf_version`

The heuristic checks (contradictions, staleness of *content*, missing cross-topic refs) are
the LLM's job — see .claude/skills/okf-wiki/SKILL.md.
"""
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
TEMPLATES = ROOT / "templates"
SPECIAL = {"index.md", "log.md"}

# [[Target]], [[Target|display]], [[Target#Heading]], ![[Embed]]
WIKILINK = re.compile(r"(!?)\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
FENCE = re.compile(r"^(```|~~~).*?^\1\s*$", re.M | re.S)
INLINE_CODE = re.compile(r"`[^`\n]*`")
KEY = re.compile(r"^([A-Za-z_][\w.-]*):\s*(.*)$")
# OKF §7 actors: <producer>/<version>, human:<id>, process:<id>. team:<id> is used by the
# spec's own credibility-signal examples for `sources[].author`.
ACTOR = re.compile(r"^(?:human:|process:|team:)[\w.@+-]+$|^[\w.@+-]+/[\w.@+-]+$")
# OKF §5: ISO 8601 datetime with an explicit UTC offset.
DATETIME = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})$")
DATE_ONLY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ISO_DATE_HEADING = re.compile(r"^##\s+(.+?)\s*$", re.M)
STATUSES = {"draft", "stable", "deprecated"}
# Link targets with these extensions are attachments, not pages — out of scope.
ASSET_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".pdf",
              ".mp3", ".mp4", ".mov", ".canvas", ".base"}


# --------------------------------------------------------------------------- YAML subset

def _strip_comment(line):
    """Drop a trailing ` # comment`, respecting quotes (so URLs with # survive)."""
    out, quote = [], None
    for i, c in enumerate(line):
        if quote:
            out.append(c)
            if c == quote:
                quote = None
        # A quote only opens a scalar at a token boundary, so an apostrophe inside a
        # bare value (`description: Smith's paper # note`) does not swallow the comment.
        elif c in "\"'" and (i == 0 or line[i - 1] in " \t[{,:"):
            quote = c
            out.append(c)
        elif c == "#" and (i == 0 or line[i - 1] in " \t"):
            break
        else:
            out.append(c)
    return "".join(out).rstrip()


def _split_flow(s):
    """Split a flow collection's interior on top-level commas."""
    parts, depth, quote, buf = [], 0, None, []
    for c in s:
        if quote:
            if c == quote:
                quote = None
        elif c in "\"'":
            quote = c
        elif c in "[{":
            depth += 1
        elif c in "]}":
            depth -= 1
        elif c == "," and depth == 0:
            parts.append("".join(buf))
            buf = []
            continue
        buf.append(c)
    if "".join(buf).strip():
        parts.append("".join(buf))
    return parts


def _scalar(s):
    s = s.strip()
    if s.startswith("{") and s.endswith("}"):
        out = {}
        for part in _split_flow(s[1:-1]):
            m = KEY.match(part.strip())
            if m:
                out[m.group(1)] = _scalar(m.group(2))
        return out
    if s.startswith("[") and s.endswith("]"):
        return [_scalar(p) for p in _split_flow(s[1:-1])]
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    return s


def _parse_block(lines, i, indent):
    """Parse a block-style mapping or sequence at `indent`. Returns (value, next_i)."""
    if i >= len(lines):
        return {}, i
    if lines[i][1].startswith("- ") or lines[i][1] == "-":
        items = []
        while i < len(lines) and lines[i][0] == indent and (
                lines[i][1].startswith("- ") or lines[i][1] == "-"):
            head = lines[i][1][1:].strip()
            i += 1
            cont = []
            while i < len(lines) and lines[i][0] > indent:
                cont.append(lines[i])
                i += 1
            if head and not head.startswith(("{", "[")) and KEY.match(head):
                sub_indent = cont[0][0] if cont else indent + 2
                value, _ = _parse_block([(sub_indent, head)] + cont, 0, sub_indent)
            elif head:
                value = _scalar(head)
            elif cont:
                value, _ = _parse_block(cont, 0, cont[0][0])
            else:
                value = ""
            items.append(value)
        return items, i
    mapping = {}
    while i < len(lines) and lines[i][0] >= indent:
        if lines[i][0] > indent:  # stray deeper line — skip rather than loop forever
            i += 1
            continue
        m = KEY.match(lines[i][1])
        if not m:
            i += 1
            continue
        key, rest = m.group(1), m.group(2).strip()
        i += 1
        if rest:
            mapping[key] = _scalar(rest)
        elif i < len(lines) and lines[i][0] > indent:
            mapping[key], i = _parse_block(lines, i, lines[i][0])
        elif i < len(lines) and lines[i][0] == indent and lines[i][1].startswith("- "):
            mapping[key], i = _parse_block(lines, i, indent)  # sequence under its key
        else:
            mapping[key] = ""
    return mapping, i


def split_frontmatter(text):
    """Return (frontmatter dict or None, body). CRLF is normalized by read_text()."""
    text = text.lstrip("\ufeff")  # an editor's UTF-8 BOM still has frontmatter behind it
    if not text.startswith("---\n"):
        return None, text
    # Closing delimiter is a line that is exactly `---` (not `----`, not `--- x`).
    end_m = re.search(r"^---[ \t]*$", text[4:], re.M)
    if not end_m:
        return None, text
    block, body = text[4:4 + end_m.start()], text[4 + end_m.end():]
    lines = []
    for raw in block.splitlines():
        stripped = _strip_comment(raw)
        if not stripped.strip():
            continue
        lines.append((len(stripped) - len(stripped.lstrip()), stripped.strip()))
    fm, _ = _parse_block(lines, 0, lines[0][0]) if lines else ({}, 0)
    return (fm if isinstance(fm, dict) else {}), body


def as_list(val):
    """Normalize a frontmatter value to a list (absent/empty -> [])."""
    if val is None or val == "" or val == "[]":
        return []
    return val if isinstance(val, list) else [val]


def as_entries(val):
    """Normalize a field that is a mapping or a list of mappings (OKF §5.2) to a list."""
    if isinstance(val, dict):
        return [val]
    return [v for v in as_list(val) if isinstance(v, dict)]


def strip_code(body):
    return INLINE_CODE.sub("", FENCE.sub("", body))


def parse_dt(val):
    try:
        return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
    except ValueError:
        return None


# --------------------------------------------------------------------------- checks

def check_trust(rel, fm, errors, warnings):
    """OKF §5 families: generated, verified, status, stale_after, sources."""
    gen = fm.get("generated")
    if gen in (None, ""):
        warnings.append(f"{rel}: no `generated:` — provenance unknown (OKF §5.2)")
    elif not isinstance(gen, dict):
        errors.append(f"{rel}: `generated:` must be a mapping `{{ by, at }}` (OKF §5.2)")
    else:
        if not gen.get("by"):
            errors.append(f"{rel}: `generated.by` is required (OKF §5.2)")
        elif not ACTOR.match(str(gen["by"])):
            errors.append(f"{rel}: `generated.by: {gen['by']}` is not an actor — use "
                          f"`human:<id>`, `process:<id>`, or `<producer>/<version>` (OKF §7)")
        at = gen.get("at")
        if at and not DATETIME.match(str(at)):
            errors.append(f"{rel}: `generated.at: {at}` is not an ISO 8601 datetime with a "
                          f"UTC offset, e.g. 2026-09-23T00:00:00Z (OKF §5)")

    for v in as_entries(fm.get("verified")):
        if not v.get("by") or not v.get("at"):
            errors.append(f"{rel}: each `verified` entry needs `by` and `at` (OKF §5.2)")
            continue
        if not ACTOR.match(str(v["by"])):
            errors.append(f"{rel}: `verified.by: {v['by']}` is not an actor (OKF §7)")
        if not DATETIME.match(str(v["at"])):
            errors.append(f"{rel}: `verified.at: {v['at']}` is not an ISO 8601 datetime with "
                          f"a UTC offset (OKF §5)")

    status = fm.get("status")
    if status and str(status) not in STATUSES:
        errors.append(f"{rel}: `status: {status}` is not one of "
                      f"{'/'.join(sorted(STATUSES))} — domain state belongs in `stage:` (OKF §5.4)")

    stale = fm.get("stale_after")
    if stale:
        if not DATETIME.match(str(stale)):
            errors.append(f"{rel}: `stale_after: {stale}` is not an ISO 8601 datetime with a "
                          f"UTC offset (OKF §5.5)")
        else:
            dt = parse_dt(stale)
            if dt and datetime.now(timezone.utc) >= dt:
                warnings.append(f"{rel}: stale — `stale_after: {stale}` has passed (OKF §5.5)")


def check_sources(rel, page, fm, body, errors, warnings):
    """OKF §5.1 provenance entries and the footnotes that cite them."""
    ids = []
    for entry in as_entries(fm.get("sources")):
        if entry.get("id"):
            ids.append(str(entry["id"]))
        lm = entry.get("last_modified")
        if lm and not DATETIME.match(str(lm)):
            errors.append(f"{rel}: `sources[].last_modified: {lm}` is not an ISO 8601 "
                          f"datetime with a UTC offset (OKF §5)")
        res = entry.get("resource")
        if not res:
            errors.append(f"{rel}: `sources` entry without `resource` (OKF §5.1)")
            continue
        check_path(rel, page, str(res), "sources[].resource", warnings)
    dupes = {i for i in ids if ids.count(i) > 1}
    for d in sorted(dupes):
        errors.append(f"{rel}: duplicate `sources[].id: {d}` — ids key footnote attribution "
                      f"and must be unique (OKF §5.1)")

    clean = strip_code(body)
    refs = {m.group(1) for m in re.finditer(r"\[\^([^\]\s]+)\](?!:)", clean)}
    defs = {m.group(1) for m in re.finditer(r"^\[\^([^\]\s]+)\]:", body, re.M)}
    for r in sorted(refs - defs):
        warnings.append(f"{rel}: footnote [^{r}] has no definition")
    if ids:
        for r in sorted(refs - set(ids)):
            warnings.append(f"{rel}: footnote [^{r}] matches no `sources[].id` — per-claim "
                            f"attribution resolves through that key (OKF §5.1)")


def check_path(rel, page, value, label, warnings):
    """Warn when a path-valued field (OKF §6.2) names a local file that isn't there."""
    if re.match(r"^[a-z][a-z0-9+.-]*://", value) or " " in value:
        return  # absolute URL, or a scope descriptor (OKF §5.1) — nothing to resolve
    target = (WIKI / value.lstrip("/")) if value.startswith("/") else (page.parent / value)
    if not target.resolve().exists():
        warnings.append(f"{rel}: {label} not found locally: {value}")


def check_legacy(rel, page, fm, body, warnings):
    """OKF §13.1 — fields v0.2 supersedes."""
    if fm.get("timestamp"):
        warnings.append(f"{rel}: legacy `timestamp:` — superseded by "
                        f"`generated: {{ by, at }}` (OKF §13.1)")
    raw = fm.get("raw")
    if raw:
        warnings.append(f"{rel}: legacy `raw:` — record it as a `sources` entry (OKF §5.1)")
        check_path(rel, page, str(raw), "raw:", warnings)
    if re.search(r"^#{1,3}\s+Citations\s*$", body, re.M):
        warnings.append(f"{rel}: legacy `# Citations` body list — superseded by "
                        f"`sources` + `[^id]` footnotes (OKF §13.1)")


def check_computation(rel, page, fm, body, errors, warnings):
    """OKF §10 — the Attested Computation contract."""
    if not fm.get("runtime"):
        errors.append(f"{rel}: `attested-computation` requires `runtime:` (OKF §10.2)")
    for field in ("computation",):
        if fm.get(field):
            check_path(rel, page, str(fm[field]), f"`{field}`", warnings)
    for field in ("executor", "attester"):
        block = fm.get(field)
        if isinstance(block, dict) and block.get("resource"):
            check_path(rel, page, str(block["resource"]), f"`{field}.resource`", warnings)
    if not fm.get("computation") and not re.search(r"^#{1,3}\s+Computation\s*$", body, re.M):
        warnings.append(f"{rel}: no `computation:` path and no `# Computation` heading — "
                        f"the computation is unspecified (OKF §10.3)")


def check_reserved(pages, errors, warnings):
    """OKF §3.1/§8/§9 — index.md and log.md structure."""
    for p, (fm, body) in pages.items():
        rel = p.relative_to(ROOT)
        if p.name == "index.md":
            allowed = {"okf_version"} if p.parent == WIKI else set()
            extra = sorted(set(fm or {}) - allowed)
            if extra:
                errors.append(f"{rel}: index files carry no frontmatter"
                              f"{' except `okf_version`' if allowed else ''} — found: "
                              f"{', '.join(extra)} (OKF §8)")
            if p.parent == WIKI and not (fm or {}).get("okf_version"):
                warnings.append(f"{rel}: bundle root does not declare `okf_version: \"0.2\"` (OKF §12)")
        elif p.name == "log.md":
            dates = [m.group(1) for m in ISO_DATE_HEADING.finditer(body)]
            for d in dates:
                if not DATE_ONLY.match(d):
                    errors.append(f"{rel}: log heading `## {d}` is not ISO `YYYY-MM-DD` (OKF §9)")
            valid = [d for d in dates if DATE_ONLY.match(d)]
            if valid != sorted(valid, reverse=True):
                warnings.append(f"{rel}: date headings are not newest-first (OKF §9)")


def main():
    errors, warnings = [], []
    pages = {}  # path -> (frontmatter, body)
    for p in sorted(WIKI.rglob("*.md")):
        text = p.read_text(encoding="utf-8")
        fm, body = split_frontmatter(text)
        pages[p] = (fm, body)
        if p.name in SPECIAL:
            continue
        if fm is None:
            unclosed = text.lstrip("\ufeff").startswith("---\n")
            errors.append(f"{p.relative_to(ROOT)}: " + (
                "frontmatter block is never closed by a `---` line" if unclosed
                else "no YAML frontmatter"))
        elif "type" not in fm or not fm["type"]:
            errors.append(f"{p.relative_to(ROOT)}: frontmatter missing required `type:`")
        elif not isinstance(fm["type"], str):
            errors.append(f"{p.relative_to(ROOT)}: `type:` must be a single string, "
                          f"not a list or mapping (OKF §4.1)")

    content_pages = {p for p in pages if p.name not in SPECIAL}
    check_reserved(pages, errors, warnings)

    # Link-target index: filename stem, title, and aliases (lowercased).
    targets = {}
    for p in content_pages:
        fm, _ = pages[p]
        names = {p.stem}
        if fm:
            if fm.get("title"):
                names.add(str(fm["title"]))
            names.update(str(a) for a in as_list(fm.get("aliases")))
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
            names = {p.stem.lower()} | {str(n).lower() for n in as_list(fm.get("aliases") if fm else None)}
            if fm and fm.get("title"):
                names.add(str(fm["title"]).lower())
            if not names & listed:
                errors.append(f"wiki/index.md: missing entry for {p.relative_to(WIKI)}")
    else:
        errors.append("wiki/index.md: file not found")

    # Per-page frontmatter families, provenance, legacy fields, types, orphans.
    known_types = {t.stem for t in TEMPLATES.glob("*.md")}
    tiers = {"unverified": 0, "machine-confirmed": 0, "human-reviewed": 0}
    for p in sorted(content_pages):
        fm, body = pages[p]
        if fm is None:
            continue
        rel = p.relative_to(ROOT)
        check_trust(rel, fm, errors, warnings)
        check_sources(rel, p, fm, body, errors, warnings)
        check_legacy(rel, p, fm, body, warnings)
        if fm.get("type") == "attested-computation":
            check_computation(rel, p, fm, body, errors, warnings)
        if fm.get("resource"):
            check_path(rel, p, str(fm["resource"]), "`resource`", warnings)

        verifiers = [str(v.get("by", "")) for v in as_entries(fm.get("verified"))]
        if not verifiers:
            tiers["unverified"] += 1
        elif any(v.startswith("human:") for v in verifiers):
            tiers["human-reviewed"] += 1
        else:
            tiers["machine-confirmed"] += 1

        t = fm.get("type")
        t = t if isinstance(t, str) else None
        if t and t not in known_types:
            warnings.append(f"{rel}: type `{t}` has no templates/{t}.md (register it — see CLAUDE.md)")
        if inbound[p] == 0 and t != "moc":
            warnings.append(f"{rel}: orphan — no inbound wikilinks from other pages")

    for e in errors:
        print(f"ERROR   {e}")
    for w in warnings:
        print(f"warning {w}")
    print(f"\nlint: {len(errors)} error(s), {len(warnings)} warning(s) across {len(content_pages)} page(s)")
    print("trust: " + ", ".join(f"{n} {k}" for k, n in tiers.items()))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
