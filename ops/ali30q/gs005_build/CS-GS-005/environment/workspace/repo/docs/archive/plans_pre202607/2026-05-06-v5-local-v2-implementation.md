# V5 Local v2 · daemon.py 重写 + 5 补强 · Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 重写 `daemon.py:_action_selector_tick` (line 2963) + `fulfill_directive` 路径 · 加 A1+A2+A4+A5 4 大补强(A3 已做)· 修 LLM 不 tool calling 死循环 · agent 真 self_modify / 真 ask_kairos / 真 PR 闭环。

**Architecture:** worktree 隔离 / Python file patcher(不再 shell heredoc) / TDD 单元测 + smoke test → atomic cutover · 留 90% 资产(memory / learning / mixins / tools / integrations / PG schema 全不动)。

**Tech Stack:** Python 3.10 / psycopg-pool / asyncio / pytest / nautilus_v5 framework / git worktree

**Time:** 5 day 单人专注(buffer 1 day)= 6 day · 失败回滚 0 影响 production

---

## Pre-flight · Day 0(0.5h)

### Task 0.1: cloud worktree 隔离

**Files:**
- N/A · 目录操作

**Step 1: 真 ssh + git worktree 隔离**

```bash
ssh cloud "cd /home/ubuntu/nautilus-v5 && git status --short | head -10"
# 真有 untracked 但都 ignore · 不污染 worktree
ssh cloud "cd /home/ubuntu/nautilus-v5 && git worktree add /tmp/v5-local-v2 -b daemon-v2 master 2>&1 | tail -5"
# 真验证
ssh cloud "ls /tmp/v5-local-v2/nautilus_v5/runtime/daemon.py | head"
```
Expected: `/tmp/v5-local-v2/nautilus_v5/runtime/daemon.py` 真存在

**Step 2: 复制 .venv link**

```bash
ssh cloud "cd /tmp/v5-local-v2 && ln -s /home/ubuntu/nautilus-v5/.venv .venv && ls -la .venv"
```
Expected: symlink 真存在

**Step 3: 验真 worktree 跑 syntax check**

```bash
ssh cloud "cd /tmp/v5-local-v2 && /tmp/v5-local-v2/.venv/bin/python -c 'import ast; ast.parse(open(\"nautilus_v5/runtime/daemon.py\").read()); print(\"daemon.py ast OK\")'"
```
Expected: `daemon.py ast OK`

---

## Day 1 · A4 instrument 缺工具 + A5 LoopBreaker (1 day)

### Task 1.1: A4 · agent_tool_calls instrument 真补 4 工具

**Files:**
- Modify: `nautilus_v5/platform_tools_mixin.py` 真加 audit insert · 真 4 处:
  - propose_code_change(line ~822)
  - register_dynamic_tool(line ~958)
- Modify: `nautilus_v5/tools/self_modify.py` make_self_modify_tool 内加 audit insert
- Modify: `nautilus_v5/integrations/compass_client.py` acompass_drift_prehook 调用真 audit

**Step 1: 写真 instrument helper · 真复用**

Create: `nautilus_v5/learning/tool_audit.py` (新文件 · ≤80 行)
```python
"""真 audit helper · 给 agent_tool_calls 表写真行 · 4 工具复用."""
import logging
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)


async def audit_tool_call(
    pool,
    agent_id: str,
    tool_name: str,
    args_summary: str,
    output_summary: str,
    success: bool,
    elapsed_ms: int = 0,
) -> Optional[int]:
    """真 INSERT agent_tool_calls · 1 行 · 真 1s timeout · 真不阻塞主路径."""
    if pool is None:
        return None
    try:
        async with pool.connection(timeout=2.0) as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """INSERT INTO agent_tool_calls
                       (agent_id, tool_name, args_summary, output_summary, success, elapsed_ms)
                       VALUES (%s, %s, %s, %s, %s, %s)
                       RETURNING id""",
                    (agent_id, tool_name, args_summary[:1000], output_summary[:1000], success, elapsed_ms),
                )
                r = await cur.fetchone()
            await conn.commit()
            return int(r[0]) if r else None
    except Exception as e:
        logger.debug(f"audit_tool_call fail · {tool_name}: {e}")
        return None
```

**Step 2: 写失败测试**

Create: `nautilus_v5/tests/test_tool_audit.py`
```python
import pytest, asyncio
from nautilus_v5.learning.tool_audit import audit_tool_call


@pytest.mark.asyncio
async def test_audit_with_pool_writes_row(real_pg_pool):
    """真测:audit_tool_call 真 INSERT 1 行."""
    rid = await audit_tool_call(
        real_pg_pool, "test-agent", "test_tool",
        "args", "output", True, 100,
    )
    assert rid is not None and rid > 0


@pytest.mark.asyncio
async def test_audit_with_none_pool_returns_none():
    """真测:pool=None 真 return None · 不 crash."""
    rid = await audit_tool_call(None, "x", "y", "", "", True, 0)
    assert rid is None
```

**Step 3: 跑真测验证 fail**
```bash
ssh cloud "cd /tmp/v5-local-v2 && /tmp/v5-local-v2/.venv/bin/python -m pytest nautilus_v5/tests/test_tool_audit.py -v 2>&1 | tail -10"
```
Expected: `import error · audit_tool_call not found`

**Step 4: 真接 4 工具**

Create patcher: `_tmp_patch/audit_4_tools.py`(本地 · scp 上去)
```python
"""4 处真插 audit_tool_call · 不再 shell heredoc."""
import pathlib

V5 = pathlib.Path("/home/ubuntu/nautilus-v5")
patches = [
    # propose_code_change · 在 logger.info 后真插
    (V5 / "nautilus_v5/platform_tools_mixin.py",
     'logger.info(f"Self-awareness tools registered',
     None,  # surgical patch 用 anchor · 略具体
    ),
    # ... 其他 3 处
]
# 真 ast 验证 + 真 write
```

(此处真完整 patcher 代码在 `_tmp_patch/audit_4_tools.py` · ~150 行)

**Step 5: 跑测真过**
```bash
ssh cloud "cd /tmp/v5-local-v2 && /tmp/v5-local-v2/.venv/bin/python -m pytest nautilus_v5/tests/test_tool_audit.py -v"
```
Expected: 2 passed

**Step 6: commit**
```bash
cd /tmp/v5-local-v2 && git add nautilus_v5/learning/tool_audit.py nautilus_v5/tests/test_tool_audit.py nautilus_v5/platform_tools_mixin.py nautilus_v5/tools/self_modify.py nautilus_v5/integrations/compass_client.py
git commit -m "feat(A4): tool_audit helper + 4 tools instrumented"
```

### Task 1.2: A5 · LoopBreaker 识别 fulfill 死循环

**Files:**
- Modify: `nautilus_v5/runtime/daemon.py:~3840` (fulfill_directive char_count fail 路径)

**Step 1: 写失败测试** Create: `nautilus_v5/tests/test_loop_breaker.py`
```python
def test_3_fails_in_24h_unstakes():
    """同 stake 24h 3 fail · 真 unstaked + audit."""
    # mock 2 historical fails · 1 new fail → trigger
    pass
```

**Step 2-5: 实现 + commit**
- 真新方法 `_check_directive_loop_breaker(stake_id) → bool`
- 真 query platform_audit `action='fulfill_directive_fail' AND target=stake_id AND ts > NOW()-24h`
- count >= 3 → UPDATE platform_agent_stakes SET status='unstaked' + INSERT audit `directive_loop_breaker`
- 在 fulfill_directive char_count fail 那行加调用

```bash
cd /tmp/v5-local-v2 && git commit -m "feat(A5): LoopBreaker auto-unstake on 3 fails/24h"
```

---

## Day 2 · A1 fulfill_directive 系统兜底(1 day)

### Task 2.1: 真重写 fulfill_directive dispatch 路径

**Files:**
- Modify: `nautilus_v5/runtime/daemon.py:fulfill_directive 路径`(已 patch · 真完善)

**Step 1: 写真测试**
```python
@pytest.mark.asyncio
async def test_metadata_requires_tool_systems_dispatch_after_5min():
    """LLM 不调 → 5min 等 → 系统真代调 required_tools[0]."""
    # mock stake metadata.requires_tools=["ask_kairos"]
    # mock LLM respond 返空(0 tool calls)
    # 真 wait 5min(test 用 1s)
    # 真 query agent_tool_calls · 验真有 ask_kairos 系统代调记录
    pass
```

**Step 2-4: 实现真兜底**

在已 patch 的 dispatch 后加:
```python
# 5min wait · 真查 agent_tool_calls
await asyncio.sleep(int(os.environ.get("FULFILL_LLM_WAIT_S", "300")))
async with ag.platform_admin._pool.connection(timeout=3.0) as _c:
    async with _c.cursor() as _cu:
        await _cu.execute(
            "SELECT count(*) FROM agent_tool_calls WHERE agent_id=%s AND tool_name=ANY(%s) AND ts > %s AND success=true",
            (ag.agent_id, _required_tools, _stake_ts),
        )
        _cnt = (await _cu.fetchone() or [0])[0]
if _cnt == 0:
    # 系统兜底:真代调 required_tools[0]
    logger.info(f"[fulfill_directive] {sid} · system fallback · dispatch {_required_tools[0]}")
    _tool0 = _required_tools[0]
    # 用 directive 当 prompt · 默认参数
    _tool_args = {"prompt": directive[:2000]} if _tool0 == "ask_kairos" else {"text": directive[:2000]}
    try:
        _tool_res = await ag.tool_registry.dispatch(_tool0, _tool_args)
        from nautilus_v5.learning.tool_audit import audit_tool_call
        await audit_tool_call(
            ag.platform_admin._pool, ag.agent_id, _tool0,
            f"system_fallback:{sid}", str(_tool_res)[:1000], True, 0,
        )
        res = {"ok": True, "body": str(_tool_res)[:5000], "system_fallback": True}
        res_json = __import__("json").dumps(res)
    except Exception as _te:
        logger.warning(f"system fallback fail: {_te}")
```

**Step 5: 真 commit**
```bash
git commit -m "feat(A1): fulfill_directive system fallback · auto-dispatch required_tool[0] after 5min"
```

---

## Day 3 · A2 selector menu 升级 (1.5 day)

### Task 3.1: 真给 LLM 看 70+ tools schema

**Files:**
- Modify: `nautilus_v5/runtime/daemon.py:_action_selector_tick` action_menu 那段(line ~2877)

**Step 1: 真测试**

Create: `nautilus_v5/tests/test_selector_tools_menu.py`
```python
def test_selector_prompt_has_real_tool_schemas():
    """selector prompt 真 include tool_registry 全 schemas · 不 hardcoded 22 actions."""
    pass

def test_llm_picks_real_tool_not_action():
    """LLM output 真选 tool name from registry · 不选 action keyword."""
    pass
```

**Step 2-4: 真重写 prompt**

把 hardcoded:
```python
action_menu = ["fulfill_directive — ...", "scan_bounty — ...", ...]
```

改成动态:
```python
all_tools = ag.tool_registry.list_schemas()  # 70+ tools
tool_section = json.dumps([
    {"name": t["name"], "description": t["description"][:200]}
    for t in all_tools
], ensure_ascii=False, indent=2)
# 注入 prompt
```

LLM 输出格式改成 `{"tool": "xxx", "args": {...}, "reason": "..."}` 而非 action name。

dispatch 改:
```python
if "tool" in llm_choice:
    res = await ag.tool_registry.dispatch(llm_choice["tool"], llm_choice["args"])
else:
    # backward compat · 老 action 路径
    ...
```

**Step 5: smoke test**
```bash
ssh cloud "cd /tmp/v5-local-v2 && CHANNELS_DAEMON=0 CHANNELS_TELEGRAM=0 CHANNELS_HTTP=0 timeout 60 /tmp/v5-local-v2/.venv/bin/python -c 'import asyncio; from nautilus_v5.runtime.config import Config; from nautilus_v5.super_agent import SuperAgent; ...'"
```

**Step 6: commit**
```bash
git commit -m "feat(A2): selector LLM sees full tool schemas · picks tool not action"
```

---

## Day 4 · daemon.py 真拆 _action_selector_tick(1.5 day)

### Task 4.1: 真拆 god method 5 函数

**Files:**
- Modify: `nautilus_v5/runtime/daemon.py:_action_selector_tick`

**真拆**:
- `_collect_state` (~150 行)
- `_compute_action_masks` (~200 行)
- `_build_tool_menu` (新 · ~100 行)
- `_run_llm_selector` (~150 行)
- `_dispatch_and_persist` (~200 行)
- `_action_selector_tick` 主函数 ≤ 100 行

**Step 1-N**: 一个一个抽 · 每抽一个 commit · TDD

**Step N+1: smoke test 真 cycle**
```bash
ssh cloud "cd /tmp/v5-local-v2 && CHANNELS_DAEMON=1 CHANNELS_TELEGRAM=0 CHANNELS_HTTP=0 nohup /tmp/v5-local-v2/.venv/bin/python -m nautilus_v5.main_singleton > /tmp/v5-v2.log 2>&1 &"
sleep 60
ssh cloud "grep '_action_selector_tick' /tmp/v5-v2.log | tail -5"
```
Expected: cycle 真推进 · 0 crash

---

## Day 5 · cutover + 24h 监控(0.5 day)

### Task 5.1: atomic cutover

**Step 1: 备份 production daemon.py**
```bash
ssh cloud "cp /home/ubuntu/nautilus-v5/nautilus_v5/runtime/daemon.py /home/ubuntu/nautilus-v5/nautilus_v5/runtime/daemon.py.pre-v2-cutover.$(date +%s)"
```

**Step 2: 真 copy worktree → production**
```bash
ssh cloud "cp /tmp/v5-local-v2/nautilus_v5/runtime/daemon.py /home/ubuntu/nautilus-v5/nautilus_v5/runtime/daemon.py"
ssh cloud "cp /tmp/v5-local-v2/nautilus_v5/learning/tool_audit.py /home/ubuntu/nautilus-v5/nautilus_v5/learning/"
# ... 其他改动文件
ssh cloud "/home/ubuntu/nautilus-v5/.venv/bin/python -c 'import ast; ast.parse(open(\"/home/ubuntu/nautilus-v5/nautilus_v5/runtime/daemon.py\").read()); print(\"OK\")'"
```

**Step 3: restart V5**
```bash
ssh cloud "sudo systemctl restart nautilus-v5-singleton && sleep 12 && systemctl is-active nautilus-v5-singleton"
ssh cloud "tail -20 /home/ubuntu/nautilus-v5/logs/v5_singleton.err.log"
```
Expected: active + breath cycle 真推进

**Step 4: 真注 minimal directive(测 A1 兜底)**

```bash
ssh cloud "set -a; source /home/ubuntu/nautilus-v5/.env; set +a; sudo -u postgres psql -d nautilus_v5 -f /tmp/test_postpatch_directive.sql"
# requires_tools=['ask_kairos'] · 400 NAU
```

**Step 5: 等 30min 真观察**
```bash
ssh cloud "sleep 1800 && sudo -u postgres psql -d nautilus_v5 -t -c \"SELECT count(*) FROM agent_tool_calls WHERE tool_name='ask_kairos' AND ts > NOW() - interval '30 min';\""
```
Expected: count >= 1 · 真证 D=1

**Step 6: 24h 监控 + 失败回滚预案**
```bash
# 真观察 24h
ssh cloud "sudo -u postgres psql -d nautilus_v5 -t -c \"SELECT tool_name, count(*) FROM agent_tool_calls WHERE ts > NOW()-interval '24h' GROUP BY tool_name;\""

# fail 真 rollback
ssh cloud "cp /home/ubuntu/nautilus-v5/nautilus_v5/runtime/daemon.py.pre-v2-cutover.* /home/ubuntu/nautilus-v5/nautilus_v5/runtime/daemon.py"
ssh cloud "sudo systemctl restart nautilus-v5-singleton"
```

---

## Success Criteria(全 ✓ 才算 Day 5 完成)

- [ ] daemon.py 行数 4377 → ~2500 (减 40%+)
- [ ] _action_selector_tick 拆 5 函数 · 主 ≤ 100 行
- [ ] minimal directive 真 fulfilled · agent_tool_calls 真有 ask_kairos 1+ 行
- [ ] LoopBreaker 真识别死循环 · 24h 自动撤 stake
- [ ] V5 24h+ 0 crash · breath cycle 真推进
- [ ] 单元测 ≥ 5 个真过

---

## Out of Scope

- super_agent.py 重写
- 11 mixins 拆 platform_tools_mixin
- compass v1.0 接入
- phase3 schema 桥
- 全新 V7

---

Plan complete and saved to `docs/plans/2026-05-06-v5-local-v2-implementation.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session in worktree with executing-plans, batch execution with checkpoints

**Which approach?**
