"""D.fix-1/2/3 tests · audit-driven contract scanner fixes.

Background:
- Audit 2026-05-30 (Phase 1.D.1) found that 3/3 real close_loop files use
  `metadata.contracts:` nested protocol, but `parse_contracts_from_frontmatter`
  only reads top-level `contracts:`. Result: scanner reports consumed=0
  despite 3 real close_loop files (one 5/30 17:30 just shipped by Soul).
- Plan §D.2 proposed a new top-level `consumes:` field protocol · 0 real users
  exist · would add a 3rd parallel protocol · rejected in favor of fixing the
  parser to read the protocol agents are actually using.

Fixes under test:
- D.fix-1: `parse_contracts_from_frontmatter` reads both top-level `contracts:`
  and `metadata.contracts:`.
- D.fix-2: `scan_sessions_for_contracts` calls `append_to_ledger` when a
  contract resolves to consumed · idempotent on rescan.
- D.fix-3: scanner globs `contract_close_*.md` in addition to `session_*.md`;
  default `within_hours` bumped 168h → 720h (30d) to cover historic close_loop.

Flat layout (file directly under tests/) chosen per C.3 lesson — `tests/contract/`
would create a package-shadow trap with the project-root scanner module.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Ensure repo root on sys.path so `import contract` resolves the project module
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import contract as contract_mod  # noqa: E402
from contract import (  # noqa: E402
    Contract,
    parse_contracts_from_frontmatter,
    scan_sessions_for_contracts,
)


# ─── D.fix-1: parse metadata.contracts nested ────────────────────


def test_parse_top_level_contracts_still_works():
    """Regression · outbound protocol uses top-level contracts: · must still parse."""
    text = (
        "---\n"
        "name: outbound\n"
        "contracts:\n"
        "  - id: cnt_top1\n"
        "    giver: a\n"
        "    receiver: b\n"
        "    deadline: 2026-06-01\n"
        "    deliverable: top-level test\n"
        "    status: outstanding\n"
        "---\n\n"
        "body\n"
    )
    cs = parse_contracts_from_frontmatter(text)
    assert len(cs) == 1
    assert cs[0].id == "cnt_top1"
    assert cs[0].status == "outstanding"


def test_parse_metadata_nested_contracts():
    """D.fix-1 · close_loop protocol nests under metadata: · scanner must read it."""
    text = (
        "---\n"
        "name: close-loop\n"
        "metadata:\n"
        "  type: handoff\n"
        "  contracts:\n"
        "    - id: cnt_nested1\n"
        "      giver: a\n"
        "      receiver: b\n"
        "      deadline: 2026-06-01\n"
        "      deliverable: nested test\n"
        "      status: consumed\n"
        "      consumed_by: this_file.md\n"
        "      consumed_at: 2026-05-30T17:30+0800\n"
        "---\n\n"
        "body\n"
    )
    cs = parse_contracts_from_frontmatter(text)
    assert len(cs) == 1, f"expected 1 contract from metadata.contracts · got {len(cs)}"
    assert cs[0].id == "cnt_nested1"
    assert cs[0].status == "consumed"
    assert cs[0].consumed_by == "this_file.md"


def test_parse_both_top_level_and_metadata_returns_both():
    """Edge · when both shapes present · return both raw entries · merge handled by scanner."""
    text = (
        "---\n"
        "contracts:\n"
        "  - id: cnt_both\n"
        "    giver: a\n"
        "    receiver: b\n"
        "    deadline: 2026-06-01\n"
        "    deliverable: both shapes\n"
        "    status: outstanding\n"
        "metadata:\n"
        "  contracts:\n"
        "    - id: cnt_both\n"
        "      giver: a\n"
        "      receiver: b\n"
        "      deadline: 2026-06-01\n"
        "      deliverable: both shapes\n"
        "      status: consumed\n"
        "      consumed_by: x.md\n"
        "---\n"
    )
    cs = parse_contracts_from_frontmatter(text)
    statuses = sorted(c.status for c in cs)
    assert statuses == ["consumed", "outstanding"], f"got statuses={statuses}"


# ─── D.fix-2: scanner persists consumed events to ledger ─────────


def test_scanner_writes_ledger_on_consumed(tmp_path, monkeypatch):
    """D.fix-2 · when scan builds consumed list · append_to_ledger fires once per id."""
    fake_ledger = tmp_path / "contract_ledger.jsonl"
    monkeypatch.setattr(contract_mod, "LEDGER", fake_ledger)

    close_file = tmp_path / "session_20260602_close.md"
    close_file.write_text(
        "---\n"
        "metadata:\n"
        "  contracts:\n"
        "    - id: cnt_ledger\n"
        "      giver: a\n"
        "      receiver: b\n"
        "      deadline: 2026-06-10\n"
        "      deliverable: ledger test\n"
        "      status: consumed\n"
        "      consumed_by: session_20260602_close.md\n"
        "      consumed_at: 2026-06-02T10:00+0800\n"
        "---\nbody\n",
        encoding="utf-8",
    )

    result = scan_sessions_for_contracts([tmp_path], within_hours=999_999.0)
    consumed_ids = [c.id for c in result["consumed"]]
    assert "cnt_ledger" in consumed_ids

    assert fake_ledger.exists(), "scanner did not create ledger sidecar"
    entries = [
        json.loads(line)
        for line in fake_ledger.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    consumed_entries = [
        e for e in entries
        if e.get("id") == "cnt_ledger" and e.get("action") == "consumed"
    ]
    assert len(consumed_entries) == 1, (
        f"expected 1 consumed ledger entry · got {len(consumed_entries)} · entries={entries}"
    )


def test_scanner_ledger_idempotent_on_rescan(tmp_path, monkeypatch):
    """D.fix-2 · re-running scanner does not double-append same consumption."""
    fake_ledger = tmp_path / "contract_ledger.jsonl"
    monkeypatch.setattr(contract_mod, "LEDGER", fake_ledger)

    close_file = tmp_path / "session_20260602_idem.md"
    close_file.write_text(
        "---\n"
        "metadata:\n"
        "  contracts:\n"
        "    - id: cnt_idem\n"
        "      giver: a\n"
        "      receiver: b\n"
        "      deadline: 2026-06-10\n"
        "      deliverable: idem test\n"
        "      status: consumed\n"
        "      consumed_by: session_20260602_idem.md\n"
        "      consumed_at: 2026-06-02T10:00+0800\n"
        "---\nbody\n",
        encoding="utf-8",
    )

    scan_sessions_for_contracts([tmp_path], within_hours=999_999.0)
    scan_sessions_for_contracts([tmp_path], within_hours=999_999.0)

    entries = [
        json.loads(line)
        for line in fake_ledger.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    consumed_for_idem = [
        e for e in entries
        if e.get("id") == "cnt_idem" and e.get("action") == "consumed"
    ]
    assert len(consumed_for_idem) == 1, (
        f"expected 1 entry after 2 scans · got {len(consumed_for_idem)}"
    )


# ─── D.fix-3: glob contract_close_*.md + default window 30d ─────


def test_scanner_globs_contract_close_files(tmp_path, monkeypatch):
    """D.fix-3 · scanner must also glob `contract_close_*.md` (not just `session_*.md`)."""
    fake_ledger = tmp_path / "contract_ledger.jsonl"
    monkeypatch.setattr(contract_mod, "LEDGER", fake_ledger)

    close_file = tmp_path / "contract_close_cnt_glob_CONSUMED_20260530.md"
    close_file.write_text(
        "---\n"
        "metadata:\n"
        "  contracts:\n"
        "    - id: cnt_glob\n"
        "      giver: a\n"
        "      receiver: b\n"
        "      deadline: 2026-06-10\n"
        "      deliverable: glob test\n"
        "      status: consumed\n"
        "      consumed_by: contract_close_cnt_glob_CONSUMED_20260530.md\n"
        "---\nbody\n",
        encoding="utf-8",
    )

    result = scan_sessions_for_contracts([tmp_path], within_hours=999_999.0)
    consumed_ids = [c.id for c in result["consumed"]]
    assert "cnt_glob" in consumed_ids, (
        f"scanner missed contract_close_*.md file · consumed_ids={consumed_ids}"
    )


def test_scanner_default_window_at_least_30d():
    """D.fix-3 · default `within_hours` bumped 168h (7d) → 720h (30d) to cover historic close."""
    import inspect

    sig = inspect.signature(scan_sessions_for_contracts)
    default = sig.parameters["within_hours"].default
    assert default >= 720.0, (
        f"expected default within_hours >= 720 (30d) · got {default}"
    )
