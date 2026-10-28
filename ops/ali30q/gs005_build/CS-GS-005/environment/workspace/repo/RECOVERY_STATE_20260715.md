# 🛟 底座抢救工程 · 交接锚(2026-07-15 · 7/16 更新审计结果)

> 本文 = 2026-07-15 一次底座体检+抢救的单一交接记录。下个 session 接手先读本文,别重复诊断。
> 不放 .claude memory(该目录当日正被记忆蒸馏会话占用)。变更走本文件。

---

## 一、当前安全状态(可独立复核)

**生产处于:安全 + 干净 + 三层备份。所有有"归零风险"的事已做完。**

- 生产 backend 活着在涨:`GET http://<cloud>:8000/api/platform/convergence` → income 703 / verdict 61 / 自治率 88.5%(7/15 实测)。
- 生产工作区已入库,0 改动,仅剩 21 个 `.bak/.env` 垃圾未跟踪。
- 无活雷:soul 服务的 `git reset --hard origin/master` 实测只作用于独立的 `nautilus-soul-workspace`,物理隔离,碰不到生产 backend(已用 reflog 证)。

## 二、关键坐标(不可逆操作留痕 · 下个 session 必读)

| 项 | 值 |
|---|---|
| 生产环境 SSH | `ssh cloud`(VM-0-8-ubuntu · 端口 24860)|
| 生产 repo | `/home/ubuntu/nautilus-mvp` · 分支 `soul-audit-increment1` |
| 生产 backend WorkingDir | `/home/ubuntu/nautilus-mvp/phase3/backend`(systemd `nautilus-backend`)|
| **静雷入库 commit** | **`1eaeba565`** "固化生产在跑的 FDE 引擎入库"(35 真代码 + 12 改动)|
| **生产真相 GitHub 分支** | **`prod-truth-20260715`** = `1eaeba565`(第三层备份 · 融合基准锚)|
| **三处 bundle 备份** | `C:\Users\chunx\nautilus-rescue-20260715\`(prod 187M / canonical 189M / mastercopy 190M · 全 `git bundle verify` OK)|
| 生产未提交快照 | 同目录 `prod-untracked-code.tar.gz`(35 真代码)+ `prod-tracked.patch`(12 改动)|
| GitHub token | 本地 `gh` 已登录 chunxiaoxx · 对 repo `push:true`(实测可用 · 非旧 revoke 的)|

## 三、根问题:4 个平行世界(分裂 4.5 个月)

| 真相源 | 分支 | 状态 |
|---|---|---|
| `Projects/nautilus-core` | soul-distill-deploy | canonical 开发,领先生产 1241 commit,从没上生产 |
| cloud `/home/ubuntu/nautilus-mvp` | soul-audit-increment1 | **生产在跑**(已入库 `1eaeba565`)|
| GitHub origin | master(停 6/29)+ 废分支 + **新增 `prod-truth-20260715`** | 僵尸远程 → 现有生产真相锚 |
| `/c/Users/chunx/nautilus-core` | master | 另一本地副本(Claude Local)|

分裂点 = `2c1941771`(2026-03-03)。根因 = **无 git 纪律**:部署走 scp 不走 git + 生产 VM 直接改工作区 + PAT 曾断 + 野分支扩散 + 多副本无主 + 无 CI。

## 四、融合进度("以生产为准 · 向前重建" · 用户 7/15 拍)

- [x] 生产真代码入库(`1eaeba565`)
- [x] 生产真相 push 上 GitHub(`prod-truth-20260715`)= 事实基准锚
- [x] **canonical 1242 commit 价值审计已完成(7/16 · 3 subagent 并行扫 · 结果见 §四.1)**
- [x] **main 候选分支已建:`main-rebuild-20260716`**(7/16 · worktree `C:\Users\chunx\Projects\nautilus-main-rebuild`)= prod-truth + 捞入资产(genopt_factory 整目录 + 根锚 SSOT 三件 + 运维脚本 + 买方规格书 + 12 活文档)+ 部署纪律草案 `ops/DEPLOY_DISCIPLINE.md`
- [x] cherry-pick 核验完(7/16 · 重要发现):**6 条捞清单里 3 条(conductor 容错/path-escape/A2A 鉴权)早已经 scp 部署、随 `1eaeba565` 在 prod-truth 里**(cherry-pick 判空);另 4 条(verdict-gate/confound/strong-gate/triage)落点文件 prod 不存在,属 distill 子系统,归入存疑#1 连带冻结。**canonical 与生产的实质代码分歧比 commit 数显示的小得多。**
- [x] **用户四项拍板(7/16)**:① main 已立(分支改名 main + push,GitHub 默认分支已切,旧 origin/main `e9cedf1f9` 是祖先 fast-forward 无丢失)② 存疑 5 项**全部维持冻结**(含 genopt 未跟踪变体题——只活在本地磁盘的丢失风险已知晓,用户选择接受)③ 部署纪律 **v1 生效**(`ops/DEPLOY_DISCIPLINE.md`,SSOT 护栏#4 已换轨)④ 减法走"先证据清单再删"
- [x] **减法(7/16 执行)**:`.bak/.env` 垃圾已被清零(7/15 后,非本轮);证据清单产出(`ops/SUBTRACTION_EVIDENCE_20260716.md` @ main:31 活 / 5 存疑 / 38 判死);**平台 turf 25 个死 unit 已物理删除**(50 文件 tar 备份 `/root/dead_units_20260716.tar.gz`,残留 0,记分牌复验无倒退);跨框 13 死 + 5 存疑已发 outbound 等 compass/V5/V7 确认。
- [ ] 收尾余项:跨框 unit 确认核销 · 生产 VM remote/分支切到 main(按 DEPLOY_DISCIPLINE 择机)· nezha-agent ×2(enabled 但 inactive 一个月,外部监控,用户定去留)

### 四.3 六点收敛(7/16 用户拍板"开始推动闭环" · 每点一格实步)

| # | 乱点 | 7/16 实步 | 状态 |
|---|---|---|---|
| 1 | 425 封散落信件 | 根目录 480 md → **12**(448 份归档 docs/archive/,只留 SSOT/常规件/待回信) | ✅ 闭 |
| 2 | 93 plans + 5 SSOT | plans 93 → **13**(80 份归档);5 SSOT 合一挂后续 | 🟡 大头闭 |
| 3 | DB split-brain | 只读采证固化 `ops/DB_SPLITBRAIN_EVIDENCE_20260716.md`:**库级**(活库旁 3 陈旧库)+ **表级**(agents 342 int vs platform_agents 250 varchar);fde_verdicts 无 producer 外键 → 分裂不污染经济账本,**冻结安全**;收敛三步路线已写(收口新增→迁存量复用 agent_identity_map→删陈旧库) | ✅ 采证闭 · 迁移冻结 |
| 4 | 前端两套 | **决定并记录**:生产 frontend 现役;website/ 冻结留 canonical 历史,不进 main,等真需求再评 | ✅ 闭(冻结即决定) |
| 5 | FDE 人侧减法 | 催收信 `_OUTBOUND_..._subtraction_list_due.md` + compass 语义通道 ingest(thread_platform_compass_subtraction_20260716),附平台格式参照 | 🟡 球在 compass |
| 6 | 身份两套 | 平台侧核验:`/api/agent-first/register` 生产**活**(422=挂载+校验);V5 outbound 已追加注册 ask(prime-001 → 整数 agent_id) | 🟡 球在 V5 |

### 四.1 审计结论(7/16 · grounded,分歧面 52k 文件收敛到以下)

**必须整目录进新 main(不是 cherry-pick,是缺了就丢生产端源码)**:
- `genopt_factory/` 全部 163 文件 — **prod-truth 零覆盖**,是 income 生产端(出题/runner/verifier/入账脚本)唯一源码所在地。管线跑在本地/H800,cloud 只是入账门。接缝已验:它依赖的两个平台 API(`/api/fde/verdicts`、external-verify)在 prod-truth 后端**存在**(`api/fde_verdict.py`/`fde_auto_verify_runner.py`),无融合风险。5 个遗留未提交 bug 修复已入库(`10ed0ac45`)。

**「捞」清单 = 6 个自包含 bug/安全 fix commit(blast radius 小,可干净 cherry-pick 到新 main)**:
| commit | 内容 | 为什么捞 |
|---|---|---|
| `210e0fd24` + `feddcac4b` | verdict-gate 硬门 + confound_check | 直接护 FDE verdict 质量 = 收入正确性 |
| `1c15731a4` + `5b79680b6` | fde_strong_gate 三态语义修 facade bug + fde_triage 双门 | 修 FDE 门假阳性,收入质量 |
| `03e58d27c` | soul peek-and-claim 防双 ship 竞态 | 真并发 bug |
| `93ca9b834` | fuel_summary 逐行容错防 V5 非原子写漏数 | 数据正确性 |
| `3d5236f41` | soul generate path-escape 防护 | 安全加固 |
| `8c0d734f6` | A2A 鉴权+信任层 | 安全:无鉴权 A2A 是暴露面 |

**零散捞(少量)**:`scripts/cloud_health_check.sh`、`scripts/deploy.sh`(对"立部署纪律"有用)、`ops/fde_dispatch_timeout_reap.py`(活 cron)、`vtf/BUYER_SPEC_GenOpt_RL_20260702.md`+PDF 页(买方交付物)、docs 里 11 个 2026-07 活文档(LOOP_STATE_ARCHIVE_20260707 + 7 月 plans/reviews,prod 侧全缺失)。

**判丢/归档(大头)**:`.claude`(27k)、`_dead_code_backup`(20k)、`frontend/node_modules`(prod 误提交的 11k 依赖,canonical 已 ignore)、旧 `frontend/`(被 website/ 取代)、soul selfimprove daemon 本体、benchmarks 实验产物、backend/scripts 一次性实验、docs 顶层 ~270 个 HANDOFF/OUTBOUND/session 类、research/ 调研 md、`.bak/.broken`、contracts 编译产物。**`.github` 两分支都没有 workflows——CI 需从零建,无可捞。**

### 四.2 「存疑」四项(整包或不碰 · 等用户拍板)
1. **SWE 正确性 RSI 流水线**(swe_runner/swe_verify/distill_train/rsi_swe_* 一整套)— 真代码有测试,但高耦合只能整港,且需 docker/held-out 基础设施,prod 侧未验证。
2. **`backend/models/database.py` 重写 + alembic 新迁移** — **风险最高**:prod 是活库且已有等价表(自己的迁移史),盲港会砸活库;除非逐字段比对,否则不动。
3. **website/ 前端重写**(控制面板强于旧 frontend)— 非收入关键,整迁或不迁。
4. **多租户隔离**(tenants.py,269 行)— 未来商用能力,prod 当前单租户无此需求,引入=纯增面。
5. genopt ~40 个未跟踪变体题目录(含 trajectory JSON)— income 库存,入库 vs .gitignore 待定(可能刻意靠 H800/S3 留存)。

## 五、防再分叉 = 三脊柱(架构重建 · 不推倒重来)

1. **单一主干 + git 部署纪律**:一 repo 一 main 一生产;部署 = CI 从 main 拉;**禁 VM 直接改 · 禁 scp**;soul 自我 reset 对齐新 main。
2. **能读 cloud 真值的单一盘**:先修「本地/CI 能起真后端读 cloud」(master/fork 分歧),否则再建盘仍是 mock。
3. **物理删除纪律**:死代码/死服务/垃圾 bak 标记后删,不留 `.disabled`。
次序:脊柱1 → 脊柱3 → 脊柱2。

## 六、与三条业务的关系(战略结论 · 7/15)

- **具身数采**(有钱有需求 · 组队落地):**另起干净地基 + Day1 带三脊柱**,不继承老平台债、不等和解。复用教训不复用烂代码。
- **① LLM 后训练(题目工厂/飞轮)**:老平台在跑的东西,income 在涨、数据质量干净(genopt 坏账仅 JobShop 一个孤儿 metrics,详见给 V5 的 outbound `_OUTBOUND_FROM_PLATFORM_TO_V5_20260714_*`)。
- **② FDE**:轻,主靠人 + 飞书表。
- 底座和解**不阻塞任何业务**;用具身团队 onboarding 当"底座够用了"的验收线。

## 七、遗留不紧急项(择日/外包 · 不停业务)

canonical 价值审计 · 定 main + 部署纪律 · 减法清 bak/死服务 · 修 fine-grained token 收敛权限面 · JobShop 孤儿 metrics(等 V5 定口径)· 5 份 SSOT 合一 · 437 散落 md 归档。

---
*维护:本工程有进展 → 更新本文件。关联 `LOOP_STATE_SSOT.md`(业务闭环状态)· `FDE_BUSINESS_CHARTER.md`(业务宪章)。*
