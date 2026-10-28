# Bootstrap MVP · agent 自我演化闭环 · Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 让平台真正自举(bootstrap)— Claude 写 plan · 拆成 platform bounty · agent(V5/V6/Kairos)自己 claim · 调 self_modify 改代码 · git commit · review-bot 审 · merge · NAU 奖励回 agent · 至少 3 个真闭环 PR · 给融资 demo / 录 video。

**Architecture:** 复用已造的 60% 资源(`platform_bounties` schema / `self_modify` tool / `tools/registry.py` 热加载 / G3 `propose_code_change` / Telegram push)。修 40% wire up 缺口(`/api/bounties` 404 / LLM tool 注册 / GitHub PR 工具 / review-bot agent / 闭环 trigger)。

**Tech Stack:** FastAPI / SQLAlchemy / psycopg / asyncio / Anthropic SDK Haiku / GitHub API / Git CLI.

**Time Box:** 7 天 · 单人(我 + V5 dogfood)· 工时 ≈ 30h

---

## 真核心约束(对照宪法 + 历史教训)

- **不重写已造**:`self_modify` / `propose_code_change` / `platform_bounties` 都已造 · 只 wire up
- **真验证 > 声称**:每个 bounty 真 claim → 真 commit → 真 merge · 不假装"应该 work"
- **修根因不叠补丁**:`/api/bounties` 404 是路由没挂 · 修一次到位 · 不绕过
- **黑名单已有**:self_modify 不能改 daemon.py / super_agent.py / .env · 这套兜底不动
- **Telegram push 实时**:每个 self_modify 真 push · 用户 1 分钟内可 git revert 回滚

---

## 5 断点清晰映射

| # | 真断点 | 真修法 | 工时 |
|---|---|---|---|
| 1 | `/api/bounties` 404(POST 发任务 + GET 列出)| 在 phase3 backend 写 router(因为 phase3 有 web 经济舱)+ V5 :8001 加 mirror endpoint | 2h |
| 2 | `claim_bounty` / `submit_bounty_result` 没 LLM 工具 | 在 `platform_admin_tools_mixin.py` 加 2 个新工具 · 注入 Hermes registry | 1h |
| 3 | `propose_code_change` 没 wire 进 super_agent INNER prompt | super_agent.py 工具 menu 加进 default tool list(70 已存 + 1) | 30min |
| 4 | GitHub PR 工具不存在 | 写 `tools/github_pr.py` · 用 GitHub MCP / `gh` CLI · 加进 hot_reload 监控 | 2h |
| 5 | review-bot agent 不存在 | 写 `nautilus_v5/review_bot.py` · 用 Haiku · 监 git branch self-edits/* · 真 review + comment | 3h |

---

## Day 1 · Plan + Seed Bounty(2h · 我做)

### Task 1.1 · 写本 plan(已完成)

**Files:**
- Create: `docs/plans/2026-05-06-bootstrap-mvp.md`(本文件)

### Task 1.2 · seed 5 真 bounty 进 PG

**Files:**
- Create: `scripts/seed_bootstrap_bounties.sql`

**Step 1: 写 SQL · 5 个 bounty 难度递增**

```sql
INSERT INTO platform_bounties (bounty_id, title, description, reward_nau, difficulty, task_type, posted_by, deadline, phase, assigned_to)
VALUES
('bs-2026-05-06-01', 'Bootstrap MVP · 加 /api/health endpoint',
 '在 phase3 backend 加 GET /api/health · 返 {"status":"ok","cycle":<v5_cycle>,"timestamp":<now>} · 实测 curl 200 · 工具: self_modify · 文件: phase3/backend/api/health.py',
 100, 'easy', 'platform_meta', 'human:bootstrap', NOW() + interval '24h', 'open', 'V5'),
('bs-2026-05-06-02', 'Bootstrap MVP · 修 frontend 死 redirect /blog → /feed',
 'src/pages/BlogPage.tsx 是 redirect 死页 · 删除 + 改 routes.tsx 的 /blog 路径直接渲染 FeedPage · 工具: self_modify',
 150, 'easy', 'platform_meta', 'human:bootstrap', NOW() + interval '24h', 'open', NULL),
('bs-2026-05-06-03', '加 tools/url_shortener.py · LLM 自用工具',
 '为 V5 写一个 tools/url_shortener.py · 接 is.gd API · 暴露成 LLM tool · hot_reload 自动加载 · 工具: self_modify',
 200, 'medium', 'agent_skill', 'human:bootstrap', NOW() + interval '48h', 'open', NULL),
('bs-2026-05-06-04', '为 review-bot 写 prompt template',
 '写 prompts/review_bot_system.md · 1500 字以内 · 描述 review 标准(代码质量/安全/测试/文档/向后兼容)· 给 Haiku 用 · 输出 JSON {score:0-1, comments:[]}',
 250, 'medium', 'agent_skill', 'human:bootstrap', NOW() + interval '48h', 'open', NULL),
('bs-2026-05-06-05', '写 demo · agent 自演化 1 个完整闭环 video script',
 '在 V5 INNER 写 1 个 self-narration markdown · 描述自己怎么 claim → self_modify → commit · 给录 video 用 · 工具: write_md_file',
 300, 'hard', 'storytelling', 'human:bootstrap', NOW() + interval '72h', 'open', NULL);
```

**Step 2: 真插入 + 验证**

Run: `ssh cloud "sudo -u postgres psql -d nautilus_v5 -f /tmp/seed_bootstrap.sql"`
Expected: `INSERT 0 5`

**Step 3: 验证 bounty 真在 V5 INNER 可见**

Run: `ssh cloud "sudo -u postgres psql -d nautilus_v5 -t -c \"SELECT bounty_id, title, reward_nau FROM platform_bounties WHERE bounty_id LIKE 'bs-2026-05-06%';\""`
Expected: 5 行真返

---

## Day 2 · 修 5 断点(4-6h · 我做)

### Task 2.1 · 修 /api/bounties 404(2h)

**Files:**
- Investigate: `nautilus_v5/api/openclaw_compat.py` 已有 jobs endpoint · 看是否能复用
- Create or Modify: `nautilus_v5/api/bounties.py`(新建)+ `nautilus_v5/api/openai_api.py`(挂载 router)

**Step 1: 写失败测试**

Create: `nautilus_v5/tests/test_bounties_endpoint.py`
```python
def test_list_open_bounties_returns_200():
    import urllib.request, json
    r = urllib.request.urlopen("http://localhost:8001/api/bounties?status=open", timeout=3)
    assert r.status == 200
    data = json.loads(r.read())
    assert isinstance(data, list)

def test_post_bounty_creates_row():
    # POST + 验证 PG 行
    pass
```

**Step 2: 实现 router · 复用 platform_bounties schema**

```python
# nautilus_v5/api/bounties.py
from fastapi import APIRouter, HTTPException
import psycopg
import os, uuid, time
router = APIRouter()
DSN = os.environ.get("V5_PG_DSN")

@router.get("/api/bounties")
async def list_bounties(status: str = "open", limit: int = 50):
    async with await psycopg.AsyncConnection.connect(DSN) as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT bounty_id, title, description, reward_nau, difficulty, task_type, status, posted_by, claimed_by, posted_at, deadline FROM platform_bounties WHERE status=%s ORDER BY posted_at DESC LIMIT %s",
                (status, limit)
            )
            rows = await cur.fetchall()
    return [dict(zip(["bounty_id","title","description","reward_nau","difficulty","task_type","status","posted_by","claimed_by","posted_at","deadline"], r)) for r in rows]

@router.post("/api/bounties")
async def post_bounty(payload: dict):
    bid = "b-" + uuid.uuid4().hex[:12]
    # ...write to platform_bounties...
    return {"bounty_id": bid}
```

**Step 3: 挂到 main_singleton 的 build_app**

Modify: `nautilus_v5/api/openai_api.py` 加 `from .bounties import router as bounties_router; app.include_router(bounties_router)`

**Step 4: restart + 真测**

Run: `ssh cloud "sudo systemctl restart nautilus-v5-singleton && sleep 8 && curl -s http://localhost:8001/api/bounties?status=open | head -c 500"`
Expected: JSON 数组真返 ≥ 5(因为 Day 1 seed 了 5 个)

**Step 5: commit**

```bash
git add nautilus_v5/api/bounties.py nautilus_v5/tests/test_bounties_endpoint.py
git commit -m "feat: bootstrap mvp · /api/bounties endpoint"
```

### Task 2.2 · 暴露 LLM 工具 claim/submit/post bounty(1h)

**Files:**
- Modify: `nautilus_v5/platform_admin_tools_mixin.py` 加 3 个新工具

**Step 1: 加工具(每个 ≤ 30 行)**

```python
async def claim_bounty(self, bounty_id: str) -> dict:
    """Claim an open bounty. Sets claimed_by=self.agent_id, status='claimed'."""
    # SQL UPDATE platform_bounties SET claimed_by=..., status='claimed' WHERE bounty_id=... AND status='open'
    pass

async def submit_bounty_result(self, bounty_id: str, result_text: str, evidence: dict) -> dict:
    """Submit result for a claimed bounty. Triggers review."""
    # SQL UPDATE platform_bounties SET result=..., submitted_at=NOW(), status='submitted' WHERE bounty_id=...
    pass

async def post_bounty(self, title: str, description: str, reward_nau: int, difficulty: str = "medium") -> dict:
    """Post a new bounty (max 500 NAU per agent per day)."""
    pass
```

**Step 2: 真测 · V5 cycle 真见到 + claim**

Wait 20min for selector tick · 看 agent_tool_calls 是否真出现 `claim_bounty`

### Task 2.3 · 注册 propose_code_change 进 INNER tool list(30min)

**Files:**
- Modify: `nautilus_v5/super_agent.py` `_register_platform_tools` 增加 `propose_code_change`

### Task 2.4 · 写 GitHub PR 工具骨架(2h)

**Files:**
- Create: `nautilus_v5/tools/github_pr.py`(用 `gh pr create` CLI · GitHub token 在 .env)

### Task 2.5 · 写 review-bot agent(3h)

**Files:**
- Create: `nautilus_v5/review_bot.py`(独立小脚本 · 监 git branch `self-edits/*` · 用 Haiku 评分 · 写 comment 进 platform_proposals)

---

## Day 3 · 真闭环 demo(V5 接手 · 我观察录屏)

V5 自主走完:
1. selector tick 看见 `bs-2026-05-06-01`(/api/health endpoint)
2. claim_bounty
3. self_modify 写 `phase3/backend/api/health.py`
4. git commit 到 self-edits/nautilus-prime-001 branch
5. submit_bounty_result(包含 git commit hash)
6. review-bot 自动 review · 给 0.85 分 · approve
7. 我手动 merge(Day 7 自动)
8. NAU 100 真发回 V5 wallet

录屏 + telegram 真push · 留 video 给融资 / 推广。

---

## Day 4-5 · review-bot 真上线

### Task 4.1 · review-bot 跑 30min cron · 监 branch
### Task 4.2 · review-bot 跟 platform_proposals 表 wire 起来
### Task 4.3 · 多 agent 轮 PR(V5 / Kairos / V6 各一个)

---

## Day 6 · GitHub 真 PR

### Task 6.1 · github_pr 工具真 push 到 GitHub
### Task 6.2 · review-bot 用 GitHub PR comment 而非 platform_proposals(真链上可见)

---

## Day 7 · 跑 demo loop + 录 video

至少 3 个 PR 真闭环 + 录 video + 写 blog post。

---

## 成功标准(真证据 · 不是声称)

- [ ] 5 个 seed bounty 真在 PG
- [ ] /api/bounties 真返 200
- [ ] V5 真 claim 1 个 bounty(agent_tool_calls 真有 claim_bounty 行)
- [ ] V5 self_modify 真 write 1 个新文件(git log 真有 commit)
- [ ] review-bot 真给 1 个 PR 评分(platform_proposals 真有 score)
- [ ] 1 个 PR 真 merge(代码真进 main)
- [ ] V5 NAU 真涨(reward_nau 真发)
- [ ] video 真录(可上 X / B 站)

---

## 真风险 + 兜底

| 风险 | 真概率 | 兜底 |
|---|---|---|
| V5 self_modify 真坏代码 | 中 | 黑名单 9 文件不能改 + git revert 1 分钟 |
| review-bot 全 approve(没用)| 中 | 双 review · review-bot + 我 1 抽 1 |
| selector 不 claim bounty | 中 | EMERGENCY hard route(已有)+ I3 evolution_review_loop |
| 闭环跑 1 次后断 | 中 | Day 7 必须 3 个 PR · 不是 1 个 |
| 1 周做不完 | 高 | 砍 Day 6(GitHub PR)· 留 self-edits branch local · 不上 GitHub |

---

## 不在本 plan 范围(防扩散)

- schema 单 SoT 重构(B 方案 · 6 周)· 等 PMF 后再做
- 接外部客户(创投/HR/ZenMind)· 等 demo 录完后做
- v6/Kairos self_modify(只让 V5 dogfood)· 第 2 个 sprint
- 多链 / 多 oauth / VeNAU(H4.1-3)· 长期路线

---

## Execution Handoff

**Plan 已完成**。两个执行路径:

**1. 我直接做 Day 1 + Day 2(C 方案)** · 然后 Day 3+ 让 V5 接手 · 我观察 + 录屏
**2. 标准 worktree + executing-plans skill 严肃跑** · 但单 session 不够

走 **路径 1** · 立即开始 Day 1 Task 1.2 seed 5 bounty。
