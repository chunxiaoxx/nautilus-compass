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
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
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
    consume_method: str = ""  # "" = 显式 frontmatter · "auto_keyword" = scanner 自动检测(v1.7.1)

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
            "你", "我", "的", "了", "是", "在", "和",
            # v1.7.1 · 领域 boilerplate(几乎每个 session 都有 · 不过滤会造假闭环 · cnt_ncore FP 实证)
            "session", "session_", "compass", "mcp", "claude", "json", "nautilus",
            "dialog", "memory", "agent", "ship", "md", "py"}
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
    if "contracts:" not in fm:
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

    raw_list = data.get("contracts")
    if not isinstance(raw_list, list):
        return []

    out = []
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


# ─── implicit contracts from inbound_/outbound_ files (v1.7.1) ────
# 解 adoption:dialogs 一直在写 inbound_/outbound_ session 文件(就是交接)· 只是没带 contract
# frontmatter。教 scanner 把它们当隐式合约 → 不要求行为改变,立刻从 2 个变 ~N 个。

_PARTY_NORM = {"nautilus_core": "nautilus-core", "core": "nautilus-core",
               "nautiluscore": "nautilus-core"}


def _norm_party(name: str) -> str:
    """归一化 party 名:剥 -dialog/_dialog 后缀 + 别名映射。
    'compass-dialog'→'compass' · 'nautilus-core-dialog'→'nautilus-core' · 'nautilus_core'→'nautilus-core'。"""
    p = (name or "").strip().lower()
    p = re.sub(r"[-_]dialog$", "", p)
    return _PARTY_NORM.get(p, p)


def _owner_from_root(root: Path) -> str:
    """memory root → 拥有该 root 的 dialog 名(用于隐式合约方向)。"""
    n = root.parent.name  # e.g. C--Users-chunx-Projects-nautilus-core
    for suf, name in (("nautilus-core", "nautilus-core"), ("nautilus-v5", "v5"),
                      ("nautilus-compass", "compass")):
        if n.endswith(suf):
            return name
    if n == "C--Users-chunx":
        return "main"
    return n


def _parse_handoff_filename(fname: str, owner: str):
    """inbound_from_<X>/inbound_to_<X>/outbound_to_<X> → (giver, receiver) or None。"""
    base = fname[:-3] if fname.endswith(".md") else fname
    m = re.match(r"(inbound|outbound)_(from|to)_(.+)", base)
    if not m:
        return None
    _, direction, rest = m.groups()
    if "_dialog" in rest:
        party = rest.split("_dialog")[0]
    else:
        dm = re.search(r"_(\d{8})", rest)
        party = rest[:dm.start()] if dm else rest
    party = party.strip("_")
    party = _PARTY_NORM.get(party, party)
    if direction == "from":
        return party, owner   # X 发给 owner
    return owner, party       # owner 发/留给 X


def derive_implicit_contracts(memory_roots: list[Path], within_hours: float = 720.0) -> list[Contract]:
    """v1.7.1 · 从 inbound_/outbound_ session 文件派生隐式合约。
    deliverable=description frontmatter · issued_at=file mtime · id 前缀 imp_ · status outstanding。
    """
    cutoff = time.time() - within_hours * 3600
    out = []
    for root in memory_roots:
        if not root.exists():
            continue
        owner = _owner_from_root(root)
        for f in list(root.glob("inbound_*.md")) + list(root.glob("outbound_*.md")):
            try:
                mt = f.stat().st_mtime
            except Exception:
                continue
            if mt < cutoff:
                continue
            gr = _parse_handoff_filename(f.name, owner)
            if not gr:
                continue
            giver, receiver = gr
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except Exception:
                text = ""
            dm = re.search(r"^description:\s*(.+)$", text, re.M)
            deliverable = (dm.group(1).strip() if dm else "")[:200] or f.name
            issued = datetime.fromtimestamp(mt, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
            cid = "imp_" + hashlib.blake2b(f.name.encode(), digest_size=4).hexdigest()
            out.append(Contract(
                id=cid, giver=giver, receiver=receiver, deadline="",
                deliverable=deliverable, status="outstanding",
                issued_at=issued, source_session=f.name,
            ))
    return out


# ─── auto consume detection (v1.7.1) ─────────────────────────────


def auto_detect_consumption(contracts: list[Contract], memory_roots: list[Path],
                            within_hours: float = 168.0,
                            receiver_authorship: bool = False) -> int:
    """v1.7.1 · 自动闭环检测 · 把死代码 matches_consume_hint 接入 scanner。

    consumed=0 根因:消费只认下游显式写的 `status: consumed`,dialogs 不可靠这么做。
    兜底:对每个 outstanding 合约,扫 issued_at 之后的 session(非 source_session),
    deliverable 关键词松匹配 → auto-mark consumed(consume_method=auto_keyword · 可审计)。
    返回 auto-consumed 数。显式 status:consumed 优先(本函数只补 outstanding 的)。

    caveat:matches_consume_hint 是关键词松匹配(≥半数命中)· 有 FP 风险 · 故标 auto +
    记 consumed_by 供人工核 · close_loop 时间是 consumed_at(匹配文件 mtime)− issued_at 的代理。
    """
    pend = [c for c in contracts if c.status == "outstanding"]
    if not pend:
        return 0
    cutoff = time.time() - within_hours * 3600
    best: dict[str, tuple[float, str]] = {}  # contract_id → (earliest mtime, filename)
    known_parties = {"nautilus-core", "v5", "v7", "compass", "main"}
    for root in memory_roots:
        if not root.exists():
            continue
        owner = _owner_from_root(root)
        for f in root.glob("session_*.md"):
            try:
                mt = f.stat().st_mtime
            except Exception:
                continue
            if mt < cutoff:
                continue
            text = None
            for c in pend:
                if f.name == c.source_session:
                    continue
                # v1.7.1 · receiver-authorship:消费须在 receiver 自己的 root(杀跨 context FP)
                _rcv = _norm_party(c.receiver)
                if receiver_authorship and _rcv in known_parties and owner != _rcv:
                    continue
                iss = _parse_iso(c.issued_at)
                if iss and mt < iss.timestamp():  # 消费必须在发起之后
                    continue
                if text is None:
                    try:
                        text = f.read_text(encoding="utf-8", errors="replace")
                    except Exception:
                        text = ""
                if c.matches_consume_hint(text):
                    prev = best.get(c.id)
                    if prev is None or mt < prev[0]:
                        best[c.id] = (mt, f.name)
    n = 0
    for c in pend:
        if c.id in best:
            mt, fname = best[c.id]
            c.status = "consumed"
            c.consumed_by = fname
            c.consumed_at = datetime.fromtimestamp(mt, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
            c.consume_method = "auto_keyword"
            n += 1
    return n


# ─── scanner ─────────────────────────────────────────────────────


def scan_sessions_for_contracts(memory_roots: list[Path], within_hours: float = 168.0,
                                auto_detect: bool = False, include_implicit: bool = False,
                                receiver_authorship: bool = False) -> dict:
    # v1.7.1 · auto_detect 默认 False:keyword 匹配仍有 FP(cnt_ncore 实证 · 生成假闭环比 consumed=0 更糟)。
    # 显式 status:consumed 始终生效。auto_detect=True 是 opt-in 实验工具(标 consume_method=auto_keyword 供审计)。
    # 可信自动闭环需更强 matcher:receiver-authorship 约束 + 语义/LLM 验证(见 design_cross_agent_handoff.md)。
    """Walk recent session_*.md files · build outstanding-contract index.

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
        for f in root.glob("session_*.md"):
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

    # v1.7.1 · 隐式合约:从 inbound_/outbound_ 文件派生(解 adoption · 不覆盖已有显式合约)
    if include_implicit:
        for c in derive_implicit_contracts(memory_roots, within_hours):
            all_contracts.setdefault(c.id, c)

    # v1.7.1 · 自动闭环检测(补显式 status:consumed 之外的)· consume_method=auto_keyword
    if auto_detect:
        auto_detect_consumption(list(all_contracts.values()), memory_roots, within_hours,
                                receiver_authorship=receiver_authorship)

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
        scan = scan_sessions_for_contracts(roots, within_hours=168)
        print(f"scanned {scan['files_scanned']} files in {len(roots)} roots")
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
