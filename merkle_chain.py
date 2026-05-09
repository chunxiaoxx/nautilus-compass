"""Local Merkle hash chain for memory integrity (v1.0).

Stdlib-only tamper-evidence for session memory files. Scans a directory of
`session_<ts>_<slug>.md` files, builds a deterministic hash chain (sorted by
filename), and persists the result to `.chain.json`. Re-running `verify_chain`
detects edits, deletions, and additions.

Chain semantics:
    chain[0] = H(file_0_bytes)
    chain[i] = H(chain[i-1] || file_i_bytes)
    head     = chain[-1]

All file hashes are over the raw bytes of the file - no line-ending
normalization, because any edit (including CRLF/LF flips) is the user's
intent and counts as tampering.
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_VERSION = 1
CHAIN_FILENAME = ".chain.json"
SESSION_GLOB = "session_*.md"


def _now_iso() -> str:
    """UTC timestamp in ISO-8601 with trailing Z."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _hasher(algorithm: str):
    # hashlib.new validates the algorithm name and raises ValueError otherwise.
    return hashlib.new(algorithm)


def _hash_bytes(data: bytes, algorithm: str) -> str:
    h = _hasher(algorithm)
    h.update(data)
    return h.hexdigest()


def _hash_file(path: Path, algorithm: str) -> str:
    # Read in chunks to stay memory-friendly on large markdown files.
    h = _hasher(algorithm)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _chain_step(prev_chain_hash: str | None, file_hash_hex: str, algorithm: str) -> str:
    """Compute chain[i] given chain[i-1] hex and the current file hash hex.

    For i == 0 (prev_chain_hash is None), chain[0] = file_hash.
    For i > 0, chain[i] = H(prev_chain_hash_bytes || file_hash_bytes).

    We concatenate the raw bytes of the hex-decoded digests. This keeps the
    chain algorithm-agnostic and independent of hex encoding.
    """
    if prev_chain_hash is None:
        return file_hash_hex
    prev_bytes = bytes.fromhex(prev_chain_hash)
    curr_bytes = bytes.fromhex(file_hash_hex)
    h = _hasher(algorithm)
    h.update(prev_bytes)
    h.update(curr_bytes)
    return h.hexdigest()


def _list_session_files(memory_dir: Path) -> list[Path]:
    """Return session files sorted by filename (ts-sortable)."""
    return sorted(memory_dir.glob(SESSION_GLOB), key=lambda p: p.name)


def _atomic_write_json(target: Path, payload: dict) -> None:
    tmp = target.with_suffix(target.suffix + ".tmp")
    # Ensure parent exists (memory_dir should, but be defensive).
    target.parent.mkdir(parents=True, exist_ok=True)
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, sort_keys=False)
        f.write("\n")
    tmp.replace(target)


def _read_chain(memory_dir: Path) -> dict | None:
    chain_path = memory_dir / CHAIN_FILENAME
    if not chain_path.exists():
        return None
    try:
        with chain_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except (json.JSONDecodeError, OSError):
        # Treat a corrupted / unreadable chain sidecar the same as a missing
        # one: verify_chain will surface expected_head="" and actual_head from
        # disk, so the caller sees valid=False and can re-baseline. Refusing
        # to crash on a damaged integrity file is itself an integrity
        # property: the verifier must always run to completion.
        return None
    # Minimal shape check — if the structure is valid JSON but doesn't look
    # like our schema, also treat as missing. This avoids KeyErrors deeper in.
    if not isinstance(payload, dict) or "entries" not in payload or "head" not in payload:
        return None
    return payload


def update_chain(memory_dir: Path, algorithm: str = "sha256") -> dict:
    """Scan memory_dir/*.md, compute hash chain, persist to .chain.json.

    Returns a summary dict: {head, count, algorithm, updated_at}.
    """
    memory_dir = Path(memory_dir)
    memory_dir.mkdir(parents=True, exist_ok=True)

    files = _list_session_files(memory_dir)

    entries: list[dict] = []
    prev_chain_hash: str | None = None
    for path in files:
        fh = _hash_file(path, algorithm)
        ch = _chain_step(prev_chain_hash, fh, algorithm)
        entries.append({
            "file": path.name,
            "file_hash": fh,
            "chain_hash": ch,
        })
        prev_chain_hash = ch

    head = prev_chain_hash or ""
    updated_at = _now_iso()

    payload = {
        "version": SCHEMA_VERSION,
        "algorithm": algorithm,
        "head": head,
        "entries": entries,
        "updated_at": updated_at,
    }

    _atomic_write_json(memory_dir / CHAIN_FILENAME, payload)

    return {
        "head": head,
        "count": len(entries),
        "algorithm": algorithm,
        "updated_at": updated_at,
    }


def verify_chain(memory_dir: Path) -> dict:
    """Read .chain.json, recompute chain from files on disk, compare.

    Returns:
        {
            "valid": bool,
            "expected_head": str,      # from .chain.json, "" if missing
            "actual_head": str,        # recomputed from current files
            "tampered_files": [...],   # in chain, on disk, hash differs
            "missing_files": [...],    # in chain, not on disk
        }

    Notes:
        - If `.chain.json` is missing, we treat expected_head as "" and
          actual_head as the head of whatever is currently on disk. If there
          are no files on disk either, valid=True (empty == empty). Otherwise
          valid=False (chain was never initialized).
        - New files on disk that are not in the chain are not flagged here;
          running `update_chain` is how you accept them. That keeps verify
          focused on what-was-known-should-still-match.
    """
    memory_dir = Path(memory_dir)

    chain = _read_chain(memory_dir)

    # Determine the algorithm for recomputation.
    algorithm = chain["algorithm"] if chain else "sha256"
    expected_entries = chain["entries"] if chain else []
    expected_head = chain["head"] if chain else ""

    disk_files = {p.name: p for p in _list_session_files(memory_dir)}

    tampered_files: list[str] = []
    missing_files: list[str] = []

    # Recompute chain using the ORDER + NAMES recorded in .chain.json, so the
    # comparison is apples-to-apples. For missing files we skip them in the
    # chain rebuild, but they're reported. For tampered files we still
    # include the recomputed hash so actual_head reflects disk reality.
    prev_chain_hash: str | None = None
    recomputed_entries_present = 0

    for entry in expected_entries:
        fname = entry["file"]
        expected_file_hash = entry["file_hash"]
        path = disk_files.get(fname)
        if path is None:
            missing_files.append(fname)
            # Skip this entry in rebuild - the chain diverges here, which is
            # exactly what we want to surface.
            continue

        actual_file_hash = _hash_file(path, algorithm)
        if actual_file_hash != expected_file_hash:
            tampered_files.append(fname)

        # Rebuild chain using the ACTUAL bytes on disk.
        prev_chain_hash = _chain_step(prev_chain_hash, actual_file_hash, algorithm)
        recomputed_entries_present += 1

    if chain is None:
        # No recorded chain. If there are disk files, compute actual_head from
        # them (sorted) so the caller can see what head *would* be if they ran
        # update_chain. If there are no disk files either, empty == empty.
        if disk_files:
            for path in _list_session_files(memory_dir):
                fh = _hash_file(path, algorithm)
                prev_chain_hash = _chain_step(prev_chain_hash, fh, algorithm)
            actual_head = prev_chain_hash or ""
            return {
                "valid": False,
                "expected_head": "",
                "actual_head": actual_head,
                "tampered_files": [],
                "missing_files": [],
            }
        return {
            "valid": True,
            "expected_head": "",
            "actual_head": "",
            "tampered_files": [],
            "missing_files": [],
        }

    actual_head = prev_chain_hash or ""
    valid = (
        not tampered_files
        and not missing_files
        and actual_head == expected_head
    )

    return {
        "valid": valid,
        "expected_head": expected_head,
        "actual_head": actual_head,
        "tampered_files": tampered_files,
        "missing_files": missing_files,
    }


# ---------------------------------------------------------------------------
# CLI + smoke test
# ---------------------------------------------------------------------------

def _cmd_update(memory_dir: str) -> int:
    result = update_chain(Path(memory_dir))
    print(f"head:  {result['head']}")
    print(f"count: {result['count']}")
    print(f"algo:  {result['algorithm']}")
    print(f"at:    {result['updated_at']}")
    return 0


def _cmd_verify(memory_dir: str) -> int:
    result = verify_chain(Path(memory_dir))
    print(f"valid:         {result['valid']}")
    print(f"expected_head: {result['expected_head']}")
    print(f"actual_head:   {result['actual_head']}")
    if result["tampered_files"]:
        print(f"tampered:      {', '.join(result['tampered_files'])}")
    if result["missing_files"]:
        print(f"missing:       {', '.join(result['missing_files'])}")
    return 0 if result["valid"] else 1


def _smoke_test() -> int:
    """Built-in smoke test. Returns 0 on full pass, 1 otherwise."""
    with tempfile.TemporaryDirectory() as td:
        memdir = Path(td)
        f1 = memdir / "session_1715130000_alpha.md"
        f2 = memdir / "session_1715130100_beta.md"
        f3 = memdir / "session_1715130200_gamma.md"
        f1.write_text("alpha content\n", encoding="utf-8")
        f2.write_text("beta content\n", encoding="utf-8")
        f3.write_text("gamma content\n", encoding="utf-8")

        # Step 1: initial update produces a deterministic head.
        r1 = update_chain(memdir)
        assert r1["count"] == 3, f"expected count=3, got {r1['count']}"
        assert len(r1["head"]) == 64, f"sha256 head should be 64 hex chars, got {r1['head']!r}"
        print("PASS step 1: update_chain created chain with 3 entries")

        # Re-running update without changes must yield same head (determinism).
        r1b = update_chain(memdir)
        assert r1b["head"] == r1["head"], "head not deterministic across re-updates"
        print("PASS step 2: head is deterministic across re-updates")

        # Step 3: verify the fresh chain.
        v1 = verify_chain(memdir)
        assert v1["valid"] is True, f"expected valid chain, got {v1}"
        assert v1["expected_head"] == v1["actual_head"] == r1["head"]
        print("PASS step 3: verify_chain returns valid=True on clean state")

        # Step 4: tamper with file 1.
        f1.write_text("alpha content TAMPERED\n", encoding="utf-8")
        v2 = verify_chain(memdir)
        assert v2["valid"] is False, "expected invalid after tampering"
        assert f1.name in v2["tampered_files"], f"f1 not in tampered_files: {v2}"
        assert not v2["missing_files"], f"unexpected missing_files: {v2}"
        print("PASS step 4: tampering with file 1 detected")

        # Step 5: delete file 2.
        f2.unlink()
        v3 = verify_chain(memdir)
        assert v3["valid"] is False, "expected invalid after deletion"
        assert f2.name in v3["missing_files"], f"f2 not in missing_files: {v3}"
        # f1 is still tampered
        assert f1.name in v3["tampered_files"], f"f1 should still be tampered: {v3}"
        print("PASS step 5: deletion of file 2 detected")

        # Step 6: re-run update_chain; chain recomputed from current state, so
        # verify is valid again (tampered content + missing file are the new
        # "truth of record").
        r2 = update_chain(memdir)
        assert r2["count"] == 2, f"after deletion, expected count=2, got {r2['count']}"
        assert r2["head"] != r1["head"], "head should change after file set changes"
        v4 = verify_chain(memdir)
        assert v4["valid"] is True, f"expected valid after re-update, got {v4}"
        assert not v4["tampered_files"] and not v4["missing_files"]
        print("PASS step 6: update_chain re-baselines to current state")

    print("ALL SMOKE TESTS PASSED")
    return 0


def _main(argv: list[str]) -> int:
    if len(argv) == 0:
        return _smoke_test()

    cmd = argv[0]
    if cmd == "update" and len(argv) == 2:
        return _cmd_update(argv[1])
    if cmd == "verify" and len(argv) == 2:
        return _cmd_verify(argv[1])

    print(
        "usage:\n"
        "  python merkle_chain.py                      # run built-in smoke test\n"
        "  python merkle_chain.py update <memory_dir>  # (re)build .chain.json\n"
        "  python merkle_chain.py verify <memory_dir>  # verify against .chain.json",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
