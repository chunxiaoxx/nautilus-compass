"""Slice the top-most release section out of CHANGELOG.md.

Used by .github/workflows/release.yml to build the body of a GitHub
release without duplicating copy. The first line matching
`## [VERSION] ...` starts the slice; the slice ends at the next `## [...]`
header or EOF. Result is written to `release-notes-<tag>.md` next to
CHANGELOG.md (or a custom --out path).

Usage:
    python scripts/release_notes_extract.py                 # auto-pick top section
    python scripts/release_notes_extract.py --version 1.0.0-rc1
    python scripts/release_notes_extract.py --out /tmp/n.md

Exit codes:
    0   slice extracted + written
    1   CHANGELOG.md not found
    2   requested --version header not present
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


HEADER_RE = re.compile(r"^##\s+\[(?P<version>[^\]]+)\]")


def _find_slice(lines: list[str], version: str | None) -> tuple[int, int, str]:
    """Return (start, end, version) · lines[start:end] is the slice (header included)."""
    start = -1
    found_version = ""
    for i, line in enumerate(lines):
        m = HEADER_RE.match(line)
        if not m:
            continue
        this_version = m.group("version")
        if version is None:
            start, found_version = i, this_version
            break
        if this_version == version:
            start, found_version = i, this_version
            break
    if start < 0:
        raise LookupError(version or "<top>")

    end = len(lines)
    for j in range(start + 1, len(lines)):
        if HEADER_RE.match(lines[j]):
            end = j
            break
    return start, end, found_version


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--changelog", default="CHANGELOG.md")
    p.add_argument("--version", default=None,
                   help="If set, extract that specific version header; default picks the top-most.")
    p.add_argument("--out", default=None,
                   help="Output path. Defaults to release-notes-<version>.md next to CHANGELOG.")
    args = p.parse_args()

    src = Path(args.changelog)
    if not src.exists():
        print(f"ERR · {src} not found", file=sys.stderr)
        return 1

    lines = src.read_text(encoding="utf-8").splitlines(keepends=True)
    try:
        start, end, version = _find_slice(lines, args.version)
    except LookupError as missing:
        print(f"ERR · version header [{missing}] not found in {src}", file=sys.stderr)
        return 2

    # Trim trailing blank lines in the slice.
    slice_lines = lines[start:end]
    while slice_lines and not slice_lines[-1].strip():
        slice_lines.pop()

    out = Path(args.out) if args.out else src.parent / f"release-notes-{version}.md"
    out.write_text("".join(slice_lines) + "\n", encoding="utf-8")
    print(f"OK  · wrote {out} · version={version} · {len(slice_lines)} lines")
    return 0


if __name__ == "__main__":
    sys.exit(main())
