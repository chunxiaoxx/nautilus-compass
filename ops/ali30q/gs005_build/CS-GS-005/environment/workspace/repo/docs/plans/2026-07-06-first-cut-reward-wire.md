# 第一刀:接通 verdict→income 断线(reward wire)Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 让 external_verified 的 verdict 自动触发 record_income,使 agent_survival.total_income 第一次因外部验证产出而增长(SQL 可证)。

**Architecture:** 不新造服务。① FdeVerdict ORM 补 external_verified 2 列(DB 列 7/2 已 ALTER,模型没跟)② 新端点 `PATCH /api/platform/fde/verdict/{verdict_id}/external-verify` = 唯一置 True + 入账路径,带 4 防剧场护栏 ③ soul verify 脚本独立复现后 curl 该端点。

**Tech Stack:** FastAPI + SQLAlchemy(phase3/backend)· pytest sqlite fixture · cloud 部署(43.160.239.61:24860 → localhost:8000)。

**4 防剧场护栏(硬约束):**
1. 幂等:external_verified 已 True → no-op 返回,不重复入账
2. 只此转换入账:income 只在 False→True 时记,别处不入
3. 只整数 agent_id:从 artifacts.producer_agent_id 取,非 int → 拒
4. 验证器 ≠ 生产者:verifier_source == verdict.source → 400

---

### Task 1: FdeVerdict 模型补 2 列

**Files:**
- Modify: `phase3/backend/models/fde_verdict.py`(+2 Column,to_dict +2 键)

external_verified = Column(Boolean, nullable=False, default=False) · external_verified_at = Column(DateTime, nullable=True)。DB 生产列 7/2 已存在,此处只补 ORM 映射。

### Task 2: 失败测试(RED)

**Files:**
- Create: `phase3/backend/tests/test_fde_external_verify.py`

用例:① PATCH 未知 verdict → 404 ② 正常路径:ingest verdict(artifacts.producer_agent_id=9000009)→ PATCH external-verify(verifier_source="soul-verify")→ external_verified=True + AgentTransaction INCOME 行 + total_income == round(score)③ 幂等:重复 PATCH → 不再入账 ④ 护栏:verifier_source == source → 400 ⑤ 护栏:无 producer_agent_id → 400 ⑥ survival 行不存在 → 自动 create_agent_survival bootstrap。

Run: `python -m pytest tests/test_fde_external_verify.py -x -q` → 全 FAIL(端点不存在)。

### Task 3: 实现端点(GREEN)

**Files:**
- Modify: `phase3/backend/api/fde_verdict.py`(+PATCH 路由 ~45 行)

流程:查 verdict → 幂等检查 → 护栏④(source)→ 护栏③(int producer_agent_id)→ 置 True+at → survival 无则 create → `SurvivalService.record_income(db, agent_id, amount=round(score), category="fde_external_verified", task_id=task_uid)` → 返回 {verdict, income_recorded}。

Run 同上 → 全 PASS。再跑 `python -m pytest tests/test_fde_verdict*.py -q` 回归。

### Task 4: Commit

`git add phase3/backend/{models/fde_verdict.py,api/fde_verdict.py,tests/test_fde_external_verify.py} && git commit`

### Task 5: 部署 cloud + 真闭环

1. scp 2 个改动文件到 cloud backend 目录 → 重启 uvicorn(找到 systemd unit 或进程)
2. soul verify 脚本(cloud 端):独立重跑 JobShop verifier evaluate.py 对 producer 轨迹复现 score → 一致则 `curl -X PATCH .../verdict/verdict-genopt-...94df54d0/external-verify -d '{"verifier_source":"soul-canonical-verify"}'`
3. **binding-DONE 判据(3 SQL/API)**:
   - `GET /api/platform/fde/verdict/genopt_or_jobshop_orlib_v1_001_20260702` → external_verified=true
   - agent_survival WHERE agent_id=9000009 → total_income > 0
   - 幂等重跑 PATCH → income 不再涨
