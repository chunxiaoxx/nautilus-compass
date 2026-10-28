# W-B 生产线归位 · 只读摸清发现 + canonical 决策(+ W-E 决策)

> 2026-06-06 · platform-soul-dialog · **只读调研**(SSH SELECT + git inspect · 未碰生产 · 部署=G-cloud 待授权)
> goal W-B:"Q2 生产线归位 · 只读摸清两线差异→定 canonical→reconcile→端点真部署 · ⚠️专门谨慎不盲 merge 889 分叉"。

## 0. 一句话结论
**平台后端跑在 8000(不是 goal 写的 8001),从 `~/nautilus-mvp` 的 `soul-audit-increment1` 分支,落后 canonical `origin/master` 889 commits,缺 W1/W2 全部代码** = "merged≠deployed" 的根。canonical = **origin/master**;归位 = 部署 origin/master 到 8000(非反向 merge);部署 = **G-cloud 待 SSH 授权**。

## 1. 两后端实况(只读 ps/netstat)
| 端口 | 进程 | cwd | 分支 | HEAD |
|---|---|---|---|---|
| **8000** | `main:app`(6/3 起) | `~/nautilus-mvp/phase3/backend` | **soul-audit-increment1** | `2d7bcdf63`(inc3 slice A) |
| 8001 | python(PID 3611775) | `~/nautilus-v5` | — | V5 turf · **不碰**(G-turf) |
| 8770 | compass_http_v09 | — | — | compass turf |

> **goal 端口纠正**:平台 API 后端在 **8000**,不是 8001。8001 是 nautilus-v5。

## 2. 两线差异(只读 git · 铁证)
- `origin/master ... soul-audit-increment1` = **889 / 90**(origin/master 多 889;部署线多 90)= goal 的"90/889"确认。
- **部署线 soul-audit-increment1 缺 W1/W2 全部文件**(`git cat-file -e` 全 ✗):
  - ✗ `api/fde_verdict.py`(W1 verdict-bus ingest)
  - ✗ `api/soul_activity.py`(W2 可感知)
  - ✗ `models/fde_verdict.py` + `alembic/.../a7f3c1d2e4b5_fde_verdicts.py`(W1 表)
- **origin/master 有这些 ✓**,且 `origin/master` HEAD `79d414032`(daily sync 6/5)= 本地 dev master 同源,含全部 W-work + 本 session 新写的 `control_plane.py`。
- 即:verdict-bus **表+数据生产存在**(cloud `fde_verdicts` 7 行,V5/compass 直写 DB),但**平台 8000 的 verdict/activity API 代码没部署**——跑 5/19 base 的 stale 分支。

## 3. 部署线独有 90 commit 分诊(决定 discard vs cherry-pick)
- **64 / 90 = `self-edit:` daemon 自改 commit**(main.py / cron_registry.py / sandbox.py / scheduler.py / agent_autonomy.py)= anchor #3 噪声,**不保留**。
- **inc2/inc3 特性 commit**(blessing / collaborative authorship / soul audit-generate)→ **origin/master 已全有**(确认文件在位:`e5c8b9a3d1f7_inc2_proposal_blessings.py` / `f6d9e2b8a4c1_inc2_proposal_authors.py` / `services/soul_self_audit.py` / `api/soul.py`)= **superseded**。
- **deploy/ops commit**(SOP/cron/systemd/APIKey hash)= 部署环境物料,reconcile 时单独评。
- **唯一可能独有**:`2d7bcdf63` inc3 slice A goal_stack 3-source sorter(symbol grep 在 origin/master 未命中)→ 归位前需 1 次内容核验,有价值则 cherry-pick。

## 4. canonical 决策
**canonical = `origin/master`**(= 本地 dev master)。理由:含全部 W-work(W1 verdict-bus / W2 soul-activity)+ inc2 特性 + soul audit-generate + 本 session 新 control_plane;领先部署线 889;是新工作落点。
部署线 `soul-audit-increment1` = **可弃**(64 自改噪声 + 26 多为 superseded)。

## 5. 归位 path(执行 = G-cloud 待授权 · 不盲 merge)
1. **不**反向 merge `soul-audit-increment1` → master(会拖 64 自改 + stale base 进 canonical)。
2. 对 `2d7bcdf63`(goal_stack sorter)做 1 次内容核验,有价值则 cherry-pick 进 master。
3. 8000 服务**切到 origin/master**(`git fetch && checkout origin/master` 或新 clone)。
4. ⚠️ **migration 归位风险**:`fde_verdicts` 等表生产已存在(有数据),889 commit 含大量 migration → **alembic version 必须先对账**,不能盲跑 `alembic upgrade head`(会撞已存在表)。这是 goal "不盲 merge" 的具体落点。
5. 重启 uvicorn(8000)。
- **3-5 全是 G-cloud**(生产 checkout/migration/restart)= **停报等用户 SSH 授权**。

## 6. W-E 决策落地(死投票门 + 新 gate)
**只读查实**(cloud `platform_improvement_proposals`,190 行):
- `voting` **106** + `pending` **63** = **169 (89%) 永久卡死**;历来 `executed_ok` 仅 5 / `executed_failed` 8 / `approved` 1。
- (goal 写"82 卡死"是 stale · 真实 = 106 voting / 169 卡死,更糟。)
**决策**:
1. **正式 deprecate 内部 code-PR 治理投票门**(停修 106 卡死 / auto_approve / executor)——它是死的自指环(anchor #3 反 D)。
2. **新 gate = V5 的 P3 沙箱门**(self_modify 改动→pytest pass 才 deploy · 6/6 已 ship)= 真测试验证门,已是现实,不用平台"协调建设",平台只在控制面**展示它当 live gate**。
3. **绝不删 soul checklist_scorer**(G-dead · 活的外部 fitness QC keystone · 评了 6 题)。

## 6.5 Pre-flight 部署评估(用户授权 G-cloud 后 · 只读 · 未动任何东西)
查实后发现 naive "checkout origin/master" **不安全**,3 个 blocker:
1. 🔴 **8000 工作树 47 个 uncommitted 修改文件**(main.py/platform.py/soul.py/auth.py/llm/client.py 等)= 未提交的生产 live 改动 → `git checkout origin/master` 冲突或丢弃,可能含生产关键 hotfix。
2. 🔴 **生产 DB 无 `alembic_version` baseline**(表存在但非 alembic 管)→ 盲 `alembic upgrade head` 从头跑 31 migration 撞已存在表崩。
3. ✅ 缓解:**8000 连 nautilus_production(表已存在·fde_verdicts 7 行同库)** → W1/W2 端点只缺代码不需 migration;origin/master main.py 已注册 W 路由(L82-83/628-629)。
- 回滚点:部署 HEAD `2d7bcdf63` · 服务 = systemd `nautilus-backend.service`。
- **两条安全路径**(全 G-cloud · 待用户选):
  - **A 外科式(低险·可逆)**:只把 3 个缺失 W 文件(`api/fde_verdict.py`/`api/soul_activity.py`/`models/fde_verdict.py`)从 origin/master 拷进 live 树 + main.py 加 4 行 include_router + 重启。表已存在→端点立即服务。不碰 47 脏文件。失败即删文件回滚。**不含 W-A control_plane(未 merge master)**。
  - **B 全归位(高险·专门 session)**:先 triage 47 脏文件(precious hotfix vs daemon 噪声)→ commit/stash → checkout origin/master → alembic `stamp`(非 upgrade·表已存在)→ 重启。需专门谨慎一轮,不 marathon 趟。
- **我未执行任何 mutation**——授权时按"clean checkout"理解,实况 47 脏文件 + 无 alembic baseline = 材料风险变了,叫停待用户选 A/B。

## 6.6 路径 A 外科式部署 · 执行 + 真生产验证(用户授权 · 2026-06-06)
**已执行**(每步 verification + 回滚 ready):
1. 回滚记录:3 文件部署前 absent;`main.py` 备份 `/tmp/main.py.bak.20260606`。
2. 从 origin/master 拷 3 W 文件入 live 树(`api/fde_verdict.py`/`api/soul_activity.py`/`models/fde_verdict.py`)→ 新模块 import clean(带 env)。
3. `main.py` line 628(`multimodal_router`)后插 2 import+2 include_router → **全量 `import main` 校验过**(329 routes · 3 W route 注册:`/api/platform/fde/verdict` `/{task_uid}` `/api/platform/soul/activity`)。
4. `systemctl restart nautilus-backend` → **active**。
5. **真生产 curl 验证(8000)**:`/api/platform/soul/activity`→200 真 cycle(gov-f3acef65/20260601_9680d136 success+git_sha);`/api/platform/fde/verdict/data_001`→200 真 verdict(`fde-data_001-1717545600`·source=fde-capsule-v5·pass·score=1.0·含 checklist items)。
- **W1 verdict-bus API + W2 soul-activity API 现 LIVE 生产 8000** = "merged≠deployed" 对 W1/W2 关闭。
- **未含**:W-A `control_plane.py`/`platform_rsi_fde.py`(未 merge master·在 worktree)→ 需后续 merge+部署。**未碰** 47 脏文件(外科式不触)。**未做** alembic stamp(端点只读·表已存在·不需)。
- 回滚:删 3 文件 + `cp /tmp/main.py.bak.20260606 main.py` + restart。

## 6.7 路径 B 全归位 · triage → 硬 HAZARD 即停(用户"全部推进"后 · 只读 triage)
**triage 铁证**(read-only):47 脏文件 = **11,139 行未提交发散代码**(30 files · +6167/-4912)· 仅 1 个 self-edit 标记 = **非 daemon 噪声**。关键差异 working-tree vs origin/master:`api/auth.py` 差 **2113 行**、`api/platform.py` 差 **737 行**、含前端(Login.tsx/PlatformDashboardPage.tsx)。
**判定:盲 checkout origin/master 不安全**——会丢弃 11k 行未提交生产状态(可能含关键 auth 行为)+ 用差 2113 行的 master auth.py 覆盖 live 生产 auth 流 = 极可能搞坏生产(= verification-mandatory.md 翻车模式)。
**且边际价值已低**:W1/W2/W-A/W-C/DMAS#3 全端点已外科式 LIVE 生产 · 全 checkout 仅为现代化其余代码 = 高险低值。
**HARD-STOP**:路径 B 需(a)查清生产为何有 11k 行未提交发散(刻意 fork?废弃 WIP?)(b)正式维护窗口(c)per-file reconcile 或 fresh-clone cutover + 并行测试。**不在本 session 盲做**。surgical-deploy 路线已达 goal 价值,full 归位另议。

## 6.8 本 session 生产上线汇总(全 curl 验证 · 外科式 · 回滚 ready)
1. W1 verdict-bus API(`/api/platform/fde/verdict`)+ W2 soul-activity(`/api/platform/soul/activity`)
2. W-A 看板(`/api/platform/rsi-fde` + `/dashboard`)
3. W-C dispatch(`/api/platform/dispatch` · gated 401/200 验证)
4. DMAS#3 FDE 派单 substrate(`/api/platform/fde/dispatch` gated + `/fde/tasks` 读)
- 鉴权:`require_platform_key`(`PLATFORM_DISPATCH_KEY` 在 cloud .env · 不回显/不入 git)
- main.py 备份:/tmp/main.py.bak{,2,3}.20260606
- canonical master:`041fe3733`(已 push origin)

## 7. W-B/W-E DONE 判定
- W-B:两线差异**摸清**(889/90 + W1/W2 missing 铁证)+ canonical **决策**(origin/master)+ 归位 path + migration 风险标注 ✓;**部署卡 G-cloud 如实标"待 SSH 授权"**。
- W-E:死投票门查实 + **决策落地**(deprecate / V5 沙箱门为新 gate / 守 soul scorer)✓。
- 顺带:`fde_outputs` 持久化(model_output · platform-soul 收工提醒)= 归位后端点真部署时一并补(脊柱 backlog #2)。
