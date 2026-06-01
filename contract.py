"""v1.7.0 · cross-agent contract schema + scanner

方向 2 · D1-D2 · sprint 5/17-5/30
North-star: cross-dialog handoff close_loop time 15h → <2h

Contract schema (添加到 session_*.md frontmatter):
    contracts:
      - id: cnt_a1b2c3
        giver: meme-dialog              # who promised
        receiver: v5-dialog             # who is owed
        deadline: 2026-05-17T22:00+0800 # ISO 8601
        deliverable: "terminate /loop + write final session"
        status: outstanding             # outstanding | consumed | expired | cancelled

Scanner reads outstanding contracts across all session files within window ·
checks deadline · cross-checks if a "consume" session exists fulfilling it ·
emits alert sidecar for unconsumed expired contracts.

Fail-soft: missing field / bad YAML doesn't crash. Just skipped.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

PLUGIN_DIR = Path(__file__).parent
ALERTS_SIDECAR = PLUGIN_DIR / ".cache" / "contract_alerts.jsonl"
LEDGER = PLUGIN_DIR / ".cache" / "contract_ledger.jsonl"


@dataclass
class Contract:
    """One promise between two agents · serialisable to YAML / JSON."""

    id: str
    giver: str
    receiver: str
    deadline: str  # ISO 8601 string · keep as-is for portability
    deliverable: str
    status: str = "outstanding"  # outstanding | consumed | expired | cancelled
    issued_at: str = ""
    source_session: str = ""  # session_*.md filename that issued
    consumed_by: str = ""  # session_*.md filename that consumed
    consumed_at: str = ""

    def to_yaml_dict(self) -> dict:
        d = {k: v for k, v in asdict(self).items() if v}
        return d

    def deadline_dt(self) -> Optional[datetime]:
        return _parse_iso(self.deadline)

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.now(timezone.utc)
        dl = self.deadline_dt()
        if not dl:
            return False
        return now > dl

    def matches_consume_hint(self, text: str) -> bool:
        """Loose match · does `text` look like it's fulfilling this contract?"""
        keywords = _extract_keywords(self.deliverable)
        if not keywords:
            return False
        t = text.lower()
        hits = sum(1 for k in keywords if k in t)
        return hits >= max(1, len(keywords) // 2)


def _parse_iso(s: str) -> Optional[datetime]:
    if not s:
        return None
    s = s.strip()
    # Common formats · pandas-free
    fmts = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M%z",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ]
    for fmt in fmts:
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    # Try +0800 → +08:00 normalisation
    if re.search(r"[+-]\d{4}$", s):
        normalized = s[:-4] + s[-4:-2] + ":" + s[-2:]
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def _extract_keywords(text: str) -> list[str]:
    """Crude keyword extraction · lowercase tokens of length >=4."""
    tokens = re.findall(r"[a-zA-Z_一-鿿]{2,}", (text or "").lower())
    stop = {"the", "and", "for", "with", "from", "into", "this", "that",
            "你", "我", "的", "了", "是", "在", "和"}
    seen, out = set(), []
    for t in tokens:
        if len(t) < 3:
            continue
        if t in stop or t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out[:10]


def generate_contract_id(giver: str, deliverable: str, ts: float) -> str:
    raw = f"{giver}|{deliverable}|{int(ts)}".encode()
    return "cnt_" + hashlib.blake2b(raw, digest_size=4).hexdigest()


# ─── frontmatter parsing ────────────────────────────────────────


_FM_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_contracts_from_frontmatter(md_text: str) -> list[Contract]:
    """Pull `contracts:` YAML list from session_*.md frontmatter.

    Returns [] if no frontmatter / no contracts field / malformed.
    Tolerant to compact and block YAML.
    """
    if not md_text:
        return []
    m = _FM_PATTERN.search(md_text)
    if not m:
        return []
    fm = m.group(1)
    # D.fix-4: also accept singular `contract_id:` protocol (V5 inbound convention).
    if "contracts:" not in fm and "contract_id:" not in fm:
        return []

    try:
        import yaml  # type: ignore
        try:
            data = yaml.safe_load(fm) or {}
        except yaml.YAMLError:
            # Frontmatter has un-quoted colons elsewhere (e.g. 决策: in description) ·
            # YAML chokes but contracts: block may still be parseable line-wise.
            return _parse_contracts_naive(fm)
    except ImportError:
        return _parse_contracts_naive(fm)

    # D.fix-1 (2026-05-30): read contracts from both top-level and metadata.contracts.
    # Real close_loop files (3/3 audited) nest contracts under metadata · earlier code
    # only saw top-level → close_loop status:consumed was never observed → contracts
    # stayed outstanding forever. Outbound files use top-level shape; both supported now.
    raw_lists: list[list] = []
    top_list = data.get("contracts")
    if isinstance(top_list, list):
        raw_lists.append(top_list)
    md = data.get("metadata")
    if isinstance(md, dict):
        nested_list = md.get("contracts")
        if isinstance(nested_list, list):
            raw_lists.append(nested_list)

    # D.fix-4 (2026-05-30): singular `metadata.contract_id: cnt_xxx` (string · not list).
    # V5 dialog 2026-05-19 inbound uses this shape (see
    # inbound_from_v5_dialog_20260519_compass_session_id_bug.md). Earlier parser missed
    # it → contract invisible to scanner for ~11 days → V5 dialog F4 close_loop request
    # could not be auto-tracked.
    singular: list = []
    if isinstance(md, dict):
        sid = md.get("contract_id")
        if isinstance(sid, str) and sid.strip():
            synth = {
                "id": sid.strip(),
                "giver": str(md.get("from") or md.get("giver") or ""),
                "receiver": str(md.get("to") or md.get("receiver") or ""),
                "deadline": str(md.get("due") or md.get("deadline") or ""),
                "deliverable": str(md.get("deliverable") or md.get("description") or ""),
                "issued_at": str(md.get("issued_at") or ""),
                "consumed_by": str(md.get("consumed_by") or ""),
                "consumed_at": str(md.get("consumed_at") or ""),
            }
            # Status inference: explicit `status` wins; else `close_loop: true` + consumed_by
            # implies consumed; otherwise outstanding.
            explicit_status = md.get("status")
            if isinstance(explicit_status, str) and explicit_status.strip():
                synth["status"] = explicit_status.strip()
            elif md.get("close_loop") is True and synth["consumed_by"]:
                synth["status"] = "consumed"
            else:
                synth["status"] = "outstanding"
            singular.append(synth)
    if singular:
        raw_lists.append(singular)

    if not raw_lists:
        return []

    out = []
    for raw_list in raw_lists:
        for item in raw_list:
            if not isinstance(item, dict):
                continue
            try:
                c = Contract(
                    id=str(item.get("id") or ""),
                    giver=str(item.get("giver") or ""),
                    receiver=str(item.get("receiver") or ""),
                    deadline=str(item.get("deadline") or ""),
                    deliverable=str(item.get("deliverable") or ""),
                    status=str(item.get("status") or "outstanding"),
                    issued_at=str(item.get("issued_at") or ""),
                    source_session=str(item.get("source_session") or ""),
                    consumed_by=str(item.get("consumed_by") or ""),
                    consumed_at=str(item.get("consumed_at") or ""),
                )
            except Exception:
                continue
            if not c.id or not c.giver or not c.receiver:
                continue
            out.append(c)
    return out


def _parse_contracts_naive(fm: str) -> list[Contract]:
    """Fallback when pyyaml absent · parses `contracts:` block by indent.

    Recognises one contract per dash list item with `key: value` lines below.
    """
    lines = fm.splitlines()
    out = []
    in_contracts = False
    cur: dict | None = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("contracts:"):
            in_contracts = True
            continue
        if not in_contracts:
            continue
        # Continue only while indented at least 2 spaces · else exit block
        if line and not line.startswith(" "):
            in_contracts = False
            if cur:
                out.append(cur); cur = None
            continue
        if stripped.startswith("- "):
            if cur:
                out.append(cur)
            cur = {}
            rest = stripped[2:]
            if ":" in rest:
                k, _, v = rest.partition(":")
                cur[k.strip()] = v.strip().strip('"').strip("'")
        elif ":" in stripped and cur is not None:
            k, _, v = stripped.partition(":")
            cur[k.strip()] = v.strip().strip('"').strip("'")
    if cur:
        out.append(cur)

    parsed = []
    for item in out:
        try:
            c = Contract(
                id=str(item.get("id") or ""),
                giver=str(item.get("giver") or ""),
                receiver=str(item.get("receiver") or ""),
                deadline=str(item.get("deadline") or ""),
                deliverable=str(item.get("deliverable") or ""),
                status=str(item.get("status") or "outstanding"),
                issued_at=str(item.get("issued_at") or ""),
                source_session=str(item.get("source_session") or ""),
                consumed_by=str(item.get("consumed_by") or ""),
                consumed_at=str(item.get("consumed_at") or ""),
            )
            if c.id and c.giver and c.receiver:
                parsed.append(c)
        except Exception:
            continue
    return parsed


# ─── ledger I/O ──────────────────────────────────────────────────


def append_to_ledger(c: Contract, action: str) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": int(time.time()),
        "action": action,
        **asdict(c),
    }
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def append_alert(c: Contract, reason: str) -> None:
    ALERTS_SIDECAR.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": int(time.time()),
        "reason": reason,
        "contract": asdict(c),
    }
    with open(ALERTS_SIDECAR, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def already_alerted(contract_id: str, reason: str) -> bool:
    if not ALERTS_SIDECAR.exists():
        return False
    try:
        for line in ALERTS_SIDECAR.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if obj.get("reason") == reason and obj.get("contract", {}).get("id") == contract_id:
                return True
    except Exception:
        pass
    return False


def _ledger_has_event(contract_id: str, action: str, consumed_at: str = "") -> bool:
    """Idempotency check for D.fix-2 · skip append_to_ledger if same event already logged.

    Match on (id, action). If consumed_at is provided, additionally require timestamp match
    so two genuine consume-events at different timestamps both log.
    """
    if not LEDGER.exists():
        return False
    try:
        for line in LEDGER.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if obj.get("action") != action or obj.get("id") != contract_id:
                continue
            if consumed_at and obj.get("consumed_at") and obj.get("consumed_at") != consumed_at:
                continue
            return True
    except Exception:
        pass
    return False


# ─── scanner ─────────────────────────────────────────────────────


def scan_sessions_for_contracts(memory_roots: list[Path], within_hours: float = 720.0) -> dict:
    """Walk recent session_*.md + contract_close_*.md files · build outstanding-contract index.

    D.fix-3 (2026-05-30): default window bumped 168h (7d) → 720h (30d) so historic close_loop
    files (e.g. 5/19 pypi clean ~11 days old) still resolve. Also globs `contract_close_*.md`
    in addition to `session_*.md` since some close-loop files use the `contract_close_` prefix.

    D.fix-2 (2026-05-30): each freshly observed consumed contract is also appended to
    `contract_ledger.jsonl` (idempotent · `_ledger_has_event` blocks dup on rescan).

    Returns {
        "outstanding": [Contract, ...],
        "consumed":    [Contract, ...],
        "expired":     [Contract, ...],   # outstanding + deadline passed
        "files_scanned": int,
    }
    """
    cutoff = time.time() - within_hours * 3600
    all_contracts: dict[str, Contract] = {}
    files_scanned = 0

    for root in memory_roots:
        if not root.exists():
            continue
        # D.fix-3 (2026-05-30): include contract_close_*.md (some close-loop files use this prefix)
        # D.fix-4 (2026-05-30): include inbound_*.md + outbound_*.md (cross-dialog naming
        # used by V5 inbound and similar conventions; otherwise V5 F4 contract was invisible)
        files = (
            list(root.glob("session_*.md"))
            + list(root.glob("contract_close_*.md"))
            + list(root.glob("inbound_*.md"))
            + list(root.glob("outbound_*.md"))
        )
        for f in files:
            try:
                if f.stat().st_mtime < cutoff:
                    continue
            except Exception:
                continue
            files_scanned += 1
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            for c in parse_contracts_from_frontmatter(text):
                if not c.source_session:
                    c.source_session = f.name
                # Last-write-wins on id collision (status updates win)
                prior = all_contracts.get(c.id)
                if prior is None:
                    all_contracts[c.id] = c
                else:
                    rank = {"outstanding": 0, "consumed": 1, "expired": 2, "cancelled": 3}
                    if rank.get(c.status, 0) > rank.get(prior.status, 0):
                        all_contracts[c.id] = c

    now = datetime.now(timezone.utc)
    outstanding, consumed, expired = [], [], []
    for c in all_contracts.values():
        if c.status == "consumed":
            consumed.append(c)
        elif c.status == "outstanding":
            if c.is_expired(now):
                expired.append(c)
            else:
                outstanding.append(c)
        # cancelled / expired status from file: just skip

    # D.fix-2 (2026-05-30): persist consumed events to ledger · idempotent on rescan.
    # `append_to_ledger` + `LEDGER` were defined since v1.7.0 but had zero callers
    # → contract_ledger.jsonl never materialised. Wire it now.
    for c in consumed:
        if not _ledger_has_event(c.id, "consumed", c.consumed_at):
            append_to_ledger(c, "consumed")

    return {
        "outstanding": outstanding,
        "consumed": consumed,
        "expired": expired,
        "files_scanned": files_scanned,
    }


def fire_alerts_for_expired(expired: list[Contract]) -> int:
    """For each expired contract not yet alerted · write to sidecar."""
    n = 0
    for c in expired:
        if already_alerted(c.id, "expired"):
            continue
        append_alert(c, "expired")
        n += 1
    return n


def format_for_prompt_injection(scan: dict, max_show: int = 5,
                                show_recent_consumed_hours: float = 24.0) -> str:
    """Render outstanding + expired + recent consumed into a prompt-prefix block.

    Use this in UserPromptSubmit hook to surface contracts.
    Always shows close_loop_mean across all consumed (north-star metric).
    """
    has_recent_consumed = False
    recent_consumed = []
    cl_times = []
    now = datetime.now(timezone.utc)
    for c in scan.get("consumed", []):
        iss = _parse_iso(c.issued_at)
        con = _parse_iso(c.consumed_at)
        if iss and con:
            hrs = (con - iss).total_seconds() / 3600.0
            cl_times.append(hrs)
            if (now - con).total_seconds() / 3600.0 <= show_recent_consumed_hours:
                recent_consumed.append((c, hrs))
                has_recent_consumed = True

    if not scan["outstanding"] and not scan["expired"] and not has_recent_consumed:
        return ""

    lines = []
    if scan.get("expired"):
        lines.append(f"⚠️  contracts · {len(scan['expired'])} EXPIRED unconsumed:")
        for c in scan["expired"][:max_show]:
            lines.append(f"  · {c.id} · {c.giver} → {c.receiver} · {c.deliverable[:60]} · due {c.deadline}")
    if scan.get("outstanding"):
        lines.append(f"📋 contracts · {len(scan['outstanding'])} outstanding:")
        for c in scan["outstanding"][:max_show]:
            lines.append(f"  · {c.id} · {c.giver} → {c.receiver} · {c.deliverable[:60]} · due {c.deadline}")
    if recent_consumed:
        cl_mean = sum(cl_times) / len(cl_times)
        lines.append(f"✅ contracts · {len(recent_consumed)} recently consumed · "
                     f"close_loop_mean {cl_mean:.2f}h (target <2h):")
        for c, hrs in recent_consumed[:max_show]:
            lines.append(f"  · {c.id} · {c.giver} → {c.receiver} · {hrs:.2f}h · {c.deliverable[:50]}")
    return "\n".join(lines)


# ─── CLI smoke ───────────────────────────────────────────────────


def _default_memory_roots() -> list[Path]:
    return list((Path.home() / ".claude" / "projects").glob("C--*/memory"))


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "scan":
        roots = _default_memory_roots()
        # D.fix-3 (2026-05-30): drop hardcoded within_hours=168 override · use function
        # default (720h = 30d) so historic close_loop files resolve. CLI accepts optional
        # `--hours N` to override (e.g. for tight diagnostic windows).
        within_hours = 720.0
        if "--hours" in sys.argv:
            try:
                within_hours = float(sys.argv[sys.argv.index("--hours") + 1])
            except (ValueError, IndexError):
                pass
        scan = scan_sessions_for_contracts(roots, within_hours=within_hours)
        print(f"scanned {scan['files_scanned']} files in {len(roots)} roots (window {within_hours}h)")
        print(f"  outstanding: {len(scan['outstanding'])}")
        print(f"  consumed:    {len(scan['consumed'])}")
        print(f"  expired:     {len(scan['expired'])}")
        for c in scan["outstanding"][:10]:
            print(f"    · OUT {c.id} {c.giver}→{c.receiver} · due {c.deadline} · {c.deliverable[:60]}")
        for c in scan["expired"][:10]:
            print(f"    · EXP {c.id} {c.giver}→{c.receiver} · due {c.deadline} · {c.deliverable[:60]}")
        n = fire_alerts_for_expired(scan["expired"])
        if n:
            print(f"  fired {n} new expired alert(s) · sidecar: {ALERTS_SIDECAR.name}")
    elif len(sys.argv) > 1 and sys.argv[1] == "parse":
        # parse a single file
        p = Path(sys.argv[2])
        cs = parse_contracts_from_frontmatter(p.read_text(encoding="utf-8"))
        print(f"file: {p.name}")
        for c in cs:
            print(json.dumps(asdict(c), ensure_ascii=False, indent=2))
    else:
        print("usage: contract.py scan|parse <path>")
