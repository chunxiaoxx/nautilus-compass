# PoI 中央表 Phase 1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把 PoI 信用从 memory 文件 frontmatter(主机绑死)迁到云端单表 `compass.poi_credit`,reconciler 累加、本地 daemon 读快照 boost,跨主机可累积。

**Architecture:** 单表 `compass.poi_credit(memory_key, cumulative_impact, event_count, last_impact_at)`,`memory_key=project/filename`。reconciler settle 时 UPSERT 累加(替代 frontmatter 写入)并顺手导出快照 dict;`boost_top_k` 读快照内存 dict(~0ms),miss 回退 frontmatter(过渡双读)。Phase 1 不动 live 云端端点;幂等靠本地 `settled_keys`。

**Tech Stack:** Python 3.11 · psycopg2(云端 pg via SSH 隧道)· pytest · sqlite(单测用,ON CONFLICT 兼容)。

**设计依据:** `docs/plans/2026-06-03-poi-central-ledger-design.md`(6 决策 + 三方审查横切 P0)。

**前置:** 工作分支 `feat/poi-central-ledger`(已基于 origin/main 6ab5c9b 建)。每个 Task 末尾 commit。

---

## Task 1: `derive_memory_key` 单一来源(纯函数 + 契约)

横切 P0-1。三处(本地 emit / 云端 inline / boost / 迁移)必须用同一 key 派生,否则 join 不上。

**Files:**
- Create: `proof/poi_memory_key.py`
- Test: `tests/test_poi_memory_key.py`

**Step 1: 写失败测试**

```python
# tests/test_poi_memory_key.py
from pathlib import Path
from proof.poi_memory_key import derive_memory_key, memory_key_from_path

def test_derive_basic():
    assert derive_memory_key("C--Users-chunx", "session_x.md") == "C--Users-chunx/session_x.md"

def test_derive_normalizes_raw_windows_project():
    # 防御 V5 传未编码路径 C:\Users\chunx
    assert derive_memory_key("C:\\Users\\chunx", "x.md") == "C--Users-chunx/x.md"

def test_derive_strips_filename_dir():
    # filename 只取 basename,防上游误传路径
    assert derive_memory_key("proj", "memory/x.md") == "proj/x.md"

def test_memory_key_from_full_path():
    p = Path.home() / ".claude" / "projects" / "C--Users-chunx" / "memory" / "session_x.md"
    assert memory_key_from_path(p) == "C--Users-chunx/session_x.md"

def test_memory_key_from_path_filename_only_returns_none():
    # 纯文件名无法定位 project → None(boost 侧据此回退 frontmatter)
    assert memory_key_from_path("session_x.md") is None
```

**Step 2: 跑测试确认失败**

Run: `cd /c/Users/chunx/Projects/nautilus-compass && python -m pytest tests/test_poi_memory_key.py -q`
Expected: FAIL（ModuleNotFoundError: proof.poi_memory_key）

**Step 3: 最小实现**

```python
# proof/poi_memory_key.py
"""Single source of truth for PoI memory_key = project/filename.
Used by emission (local + cloud inline copy), reconcile, boost, migration.
Pure · no I/O on the derive path. Reference: docs/plans/2026-06-03-poi-central-ledger-design.md §5.
"""
from __future__ import annotations
from pathlib import PurePosixPath, PureWindowsPath
from typing import Optional


def _normalize_project(project: str) -> str:
    """Match recall.py encoded_cwd form: C:\\Users\\chunx -> C--Users-chunx."""
    p = (project or "").strip()
    if ":" in p or "\\" in p:
        p = p.replace(":\\", "--").replace(":/", "--").replace("\\", "-").replace("/", "-")
    return p


def _basename(filename: str) -> str:
    name = (filename or "").strip().replace("\\", "/")
    return name.rsplit("/", 1)[-1]


def derive_memory_key(project: str, filename: str) -> str:
    return f"{_normalize_project(project)}/{_basename(filename)}"


def memory_key_from_path(path) -> Optional[str]:
    """Derive key from a memory file path .../projects/<project>/memory/<file>.
    Returns None if path is just a filename (project undeterminable)."""
    s = str(path).replace("\\", "/")
    parts = s.split("/")
    if len(parts) < 3:
        return None  # filename only or too shallow
    # <project>/memory/<file>  → project = parts[-3]
    return derive_memory_key(parts[-3], parts[-1])
```

**Step 4: 跑测试确认通过**

Run: `python -m pytest tests/test_poi_memory_key.py -q`
Expected: PASS (5 passed)

**Step 5: Commit**

```bash
git add proof/poi_memory_key.py tests/test_poi_memory_key.py
git commit -m "feat(poi): derive_memory_key single source (P0-1)"
```

---

## Task 2: `poi_credit_store` — UPSERT 累加 + 快照原子读写

横切 P0-3(原子写)。可用 sqlite 单测(ON CONFLICT 与 pg 兼容),生产传 psycopg2 连接。

**Files:**
- Create: `proof/poi_credit_store.py`
- Test: `tests/test_poi_credit_store.py`

**Step 1: 写失败测试**

```python
# tests/test_poi_credit_store.py
import json, sqlite3
from pathlib import Path
from proof.poi_credit_store import (
    upsert_credit, fetch_all_credits, write_snapshot_atomic, load_snapshot,
)

CREATE_SQLITE = (
    "CREATE TABLE poi_credit (memory_key TEXT PRIMARY KEY, "
    "cumulative_impact REAL NOT NULL DEFAULT 0, event_count INTEGER NOT NULL DEFAULT 0, "
    "last_impact_at TEXT)"
)

def _conn():
    c = sqlite3.connect(":memory:")
    c.execute(CREATE_SQLITE)
    return c

def test_upsert_accumulates():
    c = _conn()
    upsert_credit(c, "proj/a.md", 0.5, "2026-06-03T00:00:00+00:00", placeholder="?")
    upsert_credit(c, "proj/a.md", 0.3, "2026-06-03T01:00:00+00:00", placeholder="?")
    row = c.execute("SELECT cumulative_impact, event_count FROM poi_credit WHERE memory_key='proj/a.md'").fetchone()
    assert round(row[0], 4) == 0.8 and row[1] == 2

def test_fetch_all_credits_dict():
    c = _conn()
    upsert_credit(c, "proj/a.md", 0.5, "t", placeholder="?")
    upsert_credit(c, "proj/b.md", -0.2, "t", placeholder="?")
    d = fetch_all_credits(c)
    assert d == {"proj/a.md": 0.5, "proj/b.md": -0.2}

def test_snapshot_atomic_roundtrip(tmp_path):
    snap = tmp_path / "poi_credit_cache.json"
    write_snapshot_atomic(snap, {"proj/a.md": 0.8})
    # 原子:无 .tmp 残留
    assert not list(tmp_path.glob("*.tmp"))
    assert load_snapshot(snap) == {"proj/a.md": 0.8}

def test_load_snapshot_missing_returns_empty(tmp_path):
    assert load_snapshot(tmp_path / "nope.json") == {}

def test_load_snapshot_corrupt_returns_empty(tmp_path):
    p = tmp_path / "bad.json"; p.write_text("{not json", encoding="utf-8")
    assert load_snapshot(p) == {}
```

**Step 2: 确认失败** — Run `python -m pytest tests/test_poi_credit_store.py -q` → FAIL（模块缺失）

**Step 3: 最小实现**

```python
# proof/poi_credit_store.py
"""Central PoI credit table I/O + atomic snapshot. Replaces frontmatter as the
credit source of truth. Reference: design §4.1/§4.3. NO LLM."""
from __future__ import annotations
import json, os, tempfile
from pathlib import Path
from typing import Dict

UPSERT_SQL = (
    "INSERT INTO poi_credit (memory_key, cumulative_impact, event_count, last_impact_at) "
    "VALUES ({p}, {p}, 1, {p}) "
    "ON CONFLICT (memory_key) DO UPDATE SET "
    "cumulative_impact = poi_credit.cumulative_impact + EXCLUDED.cumulative_impact, "
    "event_count = poi_credit.event_count + 1, "
    "last_impact_at = EXCLUDED.last_impact_at"
)


def upsert_credit(conn, memory_key: str, delta: float, now_iso: str, placeholder: str = "%s") -> None:
    """Accumulate delta onto memory_key. placeholder='%s' for psycopg2, '?' for sqlite."""
    sql = UPSERT_SQL.format(p=placeholder)
    cur = conn.cursor()
    cur.execute(sql, (memory_key, float(delta), now_iso))
    conn.commit()


def fetch_all_credits(conn) -> Dict[str, float]:
    cur = conn.cursor()
    cur.execute("SELECT memory_key, cumulative_impact FROM poi_credit")
    return {k: float(v) for k, v in cur.fetchall()}


def write_snapshot_atomic(path, credit: Dict[str, float]) -> None:
    """tmp -> fsync -> os.replace · daemon never reads a half-written file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(credit, f, ensure_ascii=False)
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def load_snapshot(path) -> Dict[str, float]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
```

**Step 4: 确认通过** — `python -m pytest tests/test_poi_credit_store.py -q` → PASS

**Step 5: Commit**

```bash
git add proof/poi_credit_store.py tests/test_poi_credit_store.py
git commit -m "feat(poi): credit store UPSERT + atomic snapshot (P0-3)"
```

---

## Task 3: `boost_top_k` 读快照 + NaN/clamp 兜底

横切 P0-2。boost 改成先查快照 dict(key 由 entry 路径派生),miss 回退 frontmatter,NaN/inf 兜底裸 cosine。

**Files:**
- Modify: `recall_pkg/poi_weighting.py`
- Test: `tests/test_poi_weighting_snapshot.py`

**Step 1: 写失败测试**

```python
# tests/test_poi_weighting_snapshot.py
import math
from recall_pkg.poi_weighting import apply_poi_boost_value, boost_top_k_with_snapshot

def test_apply_value_basic():
    # cumulative=5 → boost=clamp(0.5)=0.5 → 0.8*1.5=1.2
    assert round(apply_poi_boost_value(0.8, 5.0), 4) == 1.2

def test_apply_value_clamp_cap():
    # cumulative=100 → boost capped at +1.0 → 0.5*2.0=1.0
    assert round(apply_poi_boost_value(0.5, 100.0), 4) == 1.0

def test_apply_value_clamp_floor():
    assert round(apply_poi_boost_value(0.5, -100.0), 4) == 0.25  # *0.5

def test_apply_value_nan_returns_base():
    assert apply_poi_boost_value(0.7, float("nan")) == 0.7
    assert apply_poi_boost_value(0.7, float("inf")) == 0.7

def test_boost_with_snapshot_reranks():
    snap = {"proj/hi.md": 5.0}
    top = [
        (0.50, {"path": "x", "fullpath": "/h/.claude/projects/proj/memory/lo.md"}),
        (0.45, {"path": "y", "fullpath": "/h/.claude/projects/proj/memory/hi.md"}),
    ]
    out = boost_top_k_with_snapshot(top, snap)
    # hi.md boosted 0.45*1.5=0.675 > lo.md 0.50 → reranked to top
    assert "hi.md" in out[0][1]["fullpath"]
```

**Step 2: 确认失败** — `python -m pytest tests/test_poi_weighting_snapshot.py -q` → FAIL

**Step 3: 实现**（在 `recall_pkg/poi_weighting.py` 追加,保留现有 `apply_poi_boost`/`boost_top_k` 作回退）

```python
import math
from .._compat_noop import noop  # if no such, skip; just add below to poi_weighting.py
from proof.poi_memory_key import memory_key_from_path

def apply_poi_boost_value(cosine_score: float, cumulative: float,
                          boost_factor: float = BOOST_FACTOR_DEFAULT) -> float:
    """Boost from a raw cumulative value (snapshot path). NaN/inf-safe."""
    if not math.isfinite(cumulative):
        return cosine_score
    boost = max(BOOST_FLOOR, min(BOOST_CAP, cumulative * boost_factor))
    out = cosine_score * (1.0 + boost)
    return out if math.isfinite(out) else cosine_score

def boost_top_k_with_snapshot(top_entries: list, snapshot: dict,
                              boost_factor: float = BOOST_FACTOR_DEFAULT) -> list:
    """Re-rank using central-credit snapshot dict (memory_key -> cumulative).
    Miss → fall back to frontmatter read (transition). Never raises."""
    boosted = []
    for score, entry in top_entries:
        if not isinstance(entry, dict):
            boosted.append((score, entry)); continue
        path = entry.get("fullpath") or entry.get("path") or ""
        mk = memory_key_from_path(path) if path else None
        if mk is not None and mk in snapshot:
            new_score = apply_poi_boost_value(score, snapshot[mk], boost_factor)
        else:
            front = parse_session_frontmatter_safe(path) if path else {}
            new_score = apply_poi_boost(score, front, boost_factor=boost_factor)
        boosted.append((new_score, entry))
    boosted.sort(key=lambda x: x[0], reverse=True)
    return boosted
```

> 注意:删掉示例里不存在的 `from .._compat_noop import noop` 行,只保留 `import math` 与 `from proof.poi_memory_key import memory_key_from_path`(放文件顶部 import 区)。

**Step 4: 确认通过** — `python -m pytest tests/test_poi_weighting_snapshot.py -q` → PASS

**Step 5: Commit**

```bash
git add recall_pkg/poi_weighting.py tests/test_poi_weighting_snapshot.py
git commit -m "feat(poi): boost reads credit snapshot + NaN/clamp guard (P0-2)"
```

---

## Task 4: candidate emission 加 `project` + `creator`(本地)

横切 P0-1 / P0-5。本地 `emit_poi_candidate` 写 candidate 时带 project(从路径派生)与 creator(frontmatter,已读)。

**Files:**
- Modify: `proof/poi_emitter.py:151-203`（`emit_poi_candidate`）
- Test: `tests/test_poi_candidate_project.py`

**Step 1: 写失败测试**

```python
# tests/test_poi_candidate_project.py
import json
from pathlib import Path
from proof.poi_emitter import emit_poi_candidate

def test_candidate_carries_project_and_creator(tmp_path):
    mem = tmp_path / "projects" / "C--Users-chunx" / "memory" / "m.md"
    mem.parent.mkdir(parents=True)
    mem.write_text("---\nagent_type: other-agent\n---\nbody", encoding="utf-8")
    top = [(0.9, {"fullpath": str(mem), "path": "m.md"})]
    n = emit_poi_candidate(top, query="q", agent_id="me", cache_dir=tmp_path)
    line = json.loads((tmp_path / "poi_candidates.jsonl").read_text().splitlines()[0])
    assert n == 1
    assert line["project"] == "C--Users-chunx"
    assert line["memory"] == "m.md"
    assert line["creator"] == "other-agent"
```

**Step 2: 确认失败** → FAIL（无 project 字段）

**Step 3: 实现** — 在 `emit_poi_candidate` 写 JSONL 处加字段。当前 line 193-201 的 dict 改为:

```python
            front = parse_session_frontmatter_safe(path)
            creator = front.get("agent_type", "") or front.get("agent_id", "")
            if SUPPRESS_SELFCITE and agent_id and creator == agent_id:
                continue
            from proof.poi_memory_key import memory_key_from_path, derive_memory_key
            mk = memory_key_from_path(path)
            project = mk.split("/", 1)[0] if mk else os.environ.get("COMPASS_PROJECT_NS", "")
            f.write(json.dumps({
                "ts": ts, "kind": "candidate", "actor": actor,
                "project": project, "memory": path.name, "creator": creator,
                "query_hash": q_hash, "rank": rank, "score": round(float(score), 4),
            }, ensure_ascii=False) + "\n")
```

> 把原先单独的 self-cite 块(line 186-192)合并进上面(避免重复读 frontmatter)。

**Step 4: 确认通过** + 回归 `python -m pytest tests/test_poi_emitter.py -q`（确认旧测试不破）

**Step 5: Commit**

```bash
git add proof/poi_emitter.py tests/test_poi_candidate_project.py
git commit -m "feat(poi): local candidate carries project+creator (P0-1/P0-5)"
```

---

## Task 5: 云端 inline helper 加 `project` 参数(patch)

横切 P0-1 契约另一端。云端 `_v14_emit_poi_candidate` 从 v14 recall 的 `project` query 参数取(V5 已传)。沿用现有 exec 契约测试模式。

**Files:**
- Modify: `ops/patch_v14_recall_poi_candidate.py`（`EMIT_HELPER` 常量 + 注入点传 project）
- Test: `tests/test_v14_poi_emission_patch.py`（已存在 · 加断言)

**Step 1: 加失败断言** — 在现有 exec 测试里断言输出行含 `"project"`,且 helper 签名为 `_v14_emit_poi_candidate(hits, query, agent_id, project)`。

**Step 2: 确认失败**

**Step 3: 实现** — `EMIT_HELPER` 签名加 `project`,写入 dict 加 `"project": project`(helper 内对 project 做同样规范化:`if ":" in project or "\\\\" in project` 则 replace);注入到 v14_recall 的调用点把 `project` 实参传进去(recall 路由已有 project 变量)。

**Step 4: 确认通过** — `python -m pytest tests/test_v14_poi_emission_patch.py -q`

**Step 5: Commit**

```bash
git add ops/patch_v14_recall_poi_candidate.py tests/test_v14_poi_emission_patch.py
git commit -m "feat(poi): cloud inline emit carries project (P0-1 contract)"
```

> ⚠️ 本 Task 只改 patch 脚本 + 测试 · **不部署到云端**(Phase 1 不动 live)。部署在 Phase 2。

---

## Task 6: reconciler 改用 memory_key + 中央表 credit + 松绑 M1

横切 P0-4。`reconcile` 用 memory_key 做 key,credit 写中央表(替代 frontmatter),M1 不再以本地文件存在为 settle 前置,self-cite 用 candidate 的 creator DB 侧过滤。

**Files:**
- Modify: `proof/poi_reconciler.py:62-67`（candidate_key）, `:126-174`（reconcile）
- Test: `tests/test_poi_reconciler_central.py`

**Step 1: 写失败测试**

```python
# tests/test_poi_reconciler_central.py
import sqlite3
from proof.poi_reconciler import reconcile_central

CREATE = ("CREATE TABLE poi_credit (memory_key TEXT PRIMARY KEY, cumulative_impact REAL "
          "NOT NULL DEFAULT 0, event_count INTEGER NOT NULL DEFAULT 0, last_impact_at TEXT)")

def _conn():
    c = sqlite3.connect(":memory:"); c.execute(CREATE); return c

def _cand(actor="a1", project="proj", memory="m.md", creator="other", ts="2026-06-03T00:00:00+00:00", qh="q"):
    return {"kind": "candidate", "actor": actor, "project": project, "memory": memory,
            "creator": creator, "query_hash": qh, "ts": ts, "rank": 0, "score": 0.9}

def test_settle_writes_central_no_file_needed():
    # 云端 memory · 本地无文件 · 仍 settle(M1 松绑)
    conn = _conn(); settled = set()
    outcomes = [{"agent_id": "a1", "success": True, "ts": "2026-06-03T00:10:00+00:00"}]
    r = reconcile_central([_cand()], outcomes, conn=conn, settled_keys=settled, placeholder="?")
    assert r["settled"] == 1
    row = conn.execute("SELECT cumulative_impact FROM poi_credit WHERE memory_key='proj/m.md'").fetchone()
    assert row and row[0] > 0

def test_rerun_idempotent_no_double_count():
    conn = _conn(); settled = set()
    outcomes = [{"agent_id": "a1", "success": True, "ts": "2026-06-03T00:10:00+00:00"}]
    reconcile_central([_cand()], outcomes, conn=conn, settled_keys=settled, placeholder="?")
    reconcile_central([_cand()], outcomes, conn=conn, settled_keys=settled, placeholder="?")
    row = conn.execute("SELECT event_count FROM poi_credit WHERE memory_key='proj/m.md'").fetchone()
    assert row[0] == 1  # 第二次被 settled_keys 挡住

def test_selfcite_dropped():
    conn = _conn(); settled = set()
    outcomes = [{"agent_id": "a1", "success": True, "ts": "2026-06-03T00:10:00+00:00"}]
    r = reconcile_central([_cand(creator="a1")], outcomes, conn=conn, settled_keys=settled, placeholder="?")
    assert r["settled"] == 0 and r.get("skipped_selfcite") == 1
```

**Step 2: 确认失败** → FAIL（`reconcile_central` 缺失）

**Step 3: 实现** — 新增 `reconcile_central`(不删旧 `reconcile`,保留兼容)。key 用 `derive_memory_key(cand["project"], cand["memory"])`;credit 走 `upsert_credit`;不查文件存在;creator==actor 跳过并计 `skipped_selfcite`。impact 用现有 `compute_with_drift`(memory_root 可为 None → drift_penalty 默认 1.0)。

```python
from .poi_memory_key import derive_memory_key
from .poi_credit_store import upsert_credit
from datetime import datetime, timezone

def reconcile_central(candidates, outcomes, *, conn, settled_keys=None,
                      window_seconds=DEFAULT_WINDOW_S, placeholder="%s"):
    if settled_keys is None:
        settled_keys = set()
    settled = skipped_no_match = skipped_already = skipped_selfcite = 0
    for cand in candidates:
        mk = derive_memory_key(cand.get("project", ""), cand.get("memory", ""))
        key = candidate_key({**cand, "memory": mk})  # key now includes project
        if key in settled_keys:
            skipped_already += 1; continue
        if cand.get("creator") and cand.get("creator") == cand.get("actor"):
            skipped_selfcite += 1; continue
        outcome = match_outcome(cand, outcomes, window_seconds=window_seconds)
        if outcome is None:
            skipped_no_match += 1; continue
        poi = ProofOfImpact(
            action_id=f"recon-{key}", agent_id=cand["actor"], cited_memory_paths=[cand["memory"]],
            action_outcome=outcome_to_action_outcome(outcome),
            timestamp_action=str(cand.get("ts", "")), timestamp_outcome=str(outcome.get("ts", "")),
            notes=f"central reconcile {cand['actor']}")
        compute_with_drift(poi, memory_root=None)
        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
        upsert_credit(conn, mk, poi.impact_score, now_iso, placeholder=placeholder)
        settled_keys.add(key); settled += 1
    return {"settled": settled, "skipped_no_match": skipped_no_match,
            "skipped_already": skipped_already, "skipped_selfcite": skipped_selfcite}
```

> `candidate_key` 现用 `cand["memory"]`;此处传入已是 memory_key,三元组 `(actor, memory_key, query_hash)` 与未来 DB 约束口径一致(P1-3)。

**Step 4: 确认通过** — `python -m pytest tests/test_poi_reconciler_central.py -q`(3 passed)+ 回归 `tests/test_poi_reconciler.py`(旧 reconcile 不破)

**Step 5: Commit**

```bash
git add proof/poi_reconciler.py tests/test_poi_reconciler_central.py
git commit -m "feat(poi): reconcile_central → poi_credit, relax M1, DB self-cite (P0-4/5)"
```

---

## Task 7: SQL 004 建表 + grant

**Files:**
- Create: `sql/004_poi_credit.sql`
- Test: `tests/test_sql_004_applies.py`(用 sqlite 跑 schema 段,验证语法可建表)

**Step 1: 写失败测试** — 加载 `sql/004_poi_credit.sql` 里 `CREATE TABLE` 段在 sqlite 跑通(grant 段单独标记跳过 sqlite)。

**Step 2: 确认失败**

**Step 3: 实现**

```sql
-- sql/004_poi_credit.sql · PoI central credit table (Option C · MVP single-table)
-- Reference: docs/plans/2026-06-03-poi-central-ledger-design.md §4.1
CREATE TABLE IF NOT EXISTS compass.poi_credit (
    memory_key        text PRIMARY KEY,
    cumulative_impact double precision NOT NULL DEFAULT 0,
    event_count       int NOT NULL DEFAULT 0,
    last_impact_at    timestamptz
);
-- Phase 1: reuse existing writable account (the schema-owner used for deploys).
-- Phase 2 will introduce a dedicated poi_writer role and tighten this grant.
GRANT SELECT, INSERT, UPDATE ON compass.poi_credit TO compass_sub;  -- TODO Phase 2: move to poi_writer
```

> ⚠️ grant 给 compass_sub 写权是 Phase 1 简化(决策 6)· Phase 2 收紧到 poi_writer。应用到云端 DB 需用户/部署账户跑(本 Task 只入库 SQL 文件,不连云改库)。

**Step 4: 确认通过**

**Step 5: Commit**

```bash
git add sql/004_poi_credit.sql tests/test_sql_004_applies.py
git commit -m "feat(poi): sql 004 poi_credit table + phase1 grant"
```

---

## Task 8: cron 接线 — UPSERT + 快照导出(连接复用)

把 `reconcile_central` 接进 `ops/poi_reconcile_cron.py`:复用现有 DB 连接(读 outcome 那条),settle 后 `fetch_all_credits` → `write_snapshot_atomic`。

**Files:**
- Modify: `ops/poi_reconcile_cron.py`
- Test: `tests/test_poi_reconcile_cron_wire.py`(mock DB 连接 + tmp 快照,验证流程:load candidates → reconcile_central → 导快照文件存在且含 settle 的 key)

**Step 1: 写失败测试** — 用 sqlite 连接 + 假 candidates/outcomes 跑 cron 的 `run_once(conn, ...)` 入口,断言快照文件落地且 boost 能读。

**Step 2-4:** 实现 `run_once`:`load_candidates` → `load_settled` → `reconcile_central(conn=...)` → `save_settled` → `fetch_all_credits` → `write_snapshot_atomic(snapshot_path, credits)`。snapshot_path 默认 `DEFAULT_CACHE_DIR / "poi_credit_cache.json"`(env `COMPASS_POI_CREDIT_SNAPSHOT` 覆盖)。生产 placeholder='%s'。

**Step 5: Commit**

```bash
git add ops/poi_reconcile_cron.py tests/test_poi_reconcile_cron_wire.py
git commit -m "feat(poi): cron wires reconcile_central + atomic snapshot export"
```

---

## Task 9: daemon boost 接快照(读端接线)+ 全量回归

把 daemon 召回路径(`recall.py:1010` 的 `boost_top_k(top)`)换成读快照的 `boost_top_k_with_snapshot`,快照用 mtime 缓存懒加载。

**Files:**
- Modify: `recall.py:1006-1014`（boost 调用点)
- Create: `recall_pkg/poi_snapshot_cache.py`（mtime 懒加载单例:`get_credit_snapshot()`）
- Test: `tests/test_poi_snapshot_cache.py`(mtime 变 → reload;损坏 → 保留旧)

**Step 1: 写失败测试** — `get_credit_snapshot()` 首次读文件;文件 mtime 不变时不重读;mtime 变重读;损坏时返回上次好的 dict。

**Step 2-4:** 实现懒加载缓存,recall.py 调用点改:
```python
if os.environ.get("COMPASS_NO_POI_BOOST") != "1":
    try:
        from recall_pkg.poi_weighting import boost_top_k_with_snapshot
        from recall_pkg.poi_snapshot_cache import get_credit_snapshot
        top = boost_top_k_with_snapshot(top, get_credit_snapshot())
    except Exception:
        pass  # boost is enhancement · never fail recall (design §8)
```

**Step 5: Commit + 全量回归**

```bash
python -m pytest -q   # 全绿
git add recall.py recall_pkg/poi_snapshot_cache.py tests/test_poi_snapshot_cache.py
git commit -m "feat(poi): daemon boost reads credit snapshot (mtime lazy cache)"
```

---

## Task 10: 端到端验证(verification-before-completion)

REQUIRED SUB-SKILL: superpowers:verification-before-completion。**不实测不宣告完成。**

1. **本地全绿**:`python -m pytest -q` → 0 fail(记录数字)。
2. **DB 建表**:在云端 pg 应用 `sql/004_poi_credit.sql`(用户/部署账户;隧道连 `nautilus_production`)→ `\dt compass.poi_credit` 确认存在。
3. **reconcile 真跑**:`python ops/poi_reconcile_cron.py`(或 scheduled task `compass-poi-reconcile`)→ 拉云 candidate + 隧道连 DB → 断言 `settled > 0`(用真 nautilus-prime-001 流量)→ `SELECT * FROM compass.poi_credit ORDER BY cumulative_impact DESC LIMIT 5` 看真值落库。
4. **快照落地**:`poi_credit_cache.json` 存在 + 含 settle 的 memory_key。
5. **boost 生效**:本地 daemon 重启 → 召回一个高 credit memory 的 query → 确认排名被提升(对比 `COMPASS_NO_POI_BOOST=1` 基线)。
6. **重跑不双计**:再跑一次 reconcile → `event_count` 不重复增长。

全部通过才标 Phase 1 done。**诚实边界**:V5 云端召回 Phase 1 仍未 boost(Phase 2),如实告知 V5(`cnt_compass_v5_recall_demand_c1`)。

---

## Phase 1 完成后 → finishing-a-development-branch

REQUIRED SUB-SKILL: superpowers:finishing-a-development-branch(决定 merge/PR)。Phase 2(快照上云 + 云端 daemon boost + poi_writer + 多主机幂等)另起 session,见 design §6 Phase 2。
