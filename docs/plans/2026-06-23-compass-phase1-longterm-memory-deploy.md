# compass Phase 1 · 真正长期记忆上线 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: 用 superpowers:executing-plans 逐 task 执行。**fresh session 执行**(本设计 session 极长·R3·deploy=ship 留新 session)。

**Goal:** 把已有但没跑的长期记忆生命周期机器(tier 晋升 driver + L2 nightly 蒸馏 + reinforce-on-recall)**接通 + 部署 + 验证**,让 compass 记忆从扁平召回库变成活的分层长期记忆(LLM-WIKI2 fuse 实运行)。

**Architecture:** 代码几乎全在(`scripts/tier_promotion_driver.py` CLI-ready·`storage/l2_distiller.py` nightly·`recall.promote_lifecycle_tier` 逻辑+8测·均在 `feat/v2.3.0-release` 分支)。Phase 1 = 部署 2 个 systemd timer(模板=已证的 `compass-fleet-capsule.timer`)+ wire reinforce-on-recall-hit + 实测验证。**不写新核心逻辑,接通已有件。**

**Tech Stack:** Python3 · systemd timer · 记忆文件在 T4(daemon 读处·参 ⑤桥 cloud→T4 rsync 拓扑)。

**前置铁律:**
- anchor#5 不重造:所有核心逻辑已存+已测,只 deploy+wire。
- measurement-first:每 timer 部署后实测真 mutation,不靠"应该会跑"。
- 拓扑:记忆文件 canonical 在 T4(`compass-t4-tunnel`)。tier driver 改写文件 → 必须跑在文件所在盒(T4)或改写后 rsync。先确认(Task 0)。
- 代码在 `feat/v2.3.0-release`·先确认部署源分支。

---

### Task 0: reconcile 两套 tier 逻辑 + 确认部署拓扑(设计决策·先做)

**问题:** 存在两套 tier 晋升逻辑,必须先定主从,否则互相打架:
- `scripts/tier_promotion_driver.py` → `proof.tier_promotion.calculate_new_tier(tier, delta)`,delta 来自 **`cumulative_impact`**(PoI 影响力)。
- `recall.promote_lifecycle_tier(entry)` → 用 **`reinforce_count` + `promote_after` + `forget_at`**(LLM-WIKI2 fuse · access-driven)。

**Step 1:** 读两者 + `proof/tier_promotion.py` + `paper/LLM_WIKI2_FUSE_DESIGN.md`,判定。

**✅ DECISION(2026-06-23 · grounded·读码实证):两轴互补合一,无需定主从。**
- 关键证据:`proof/tier_promotion.py` 顶部 docstring 自述 *"Companion to the access-based promote_after schema"* —— 两套是**设计时就规划好的 companion**,不是冲突的两实现。
- impact 轴(`tier_promotion_driver` + `calculate_new_tier`·daily cron):读 `cumulative_impact`(PoI 价值),delta = `cumulative_impact - tier_last_changed_at_impact`,>1.0 升 / <-0.5 降。有升有降。
- access 轴(`recall.promote_lifecycle_tier`·LLM-WIKI2 fuse·recall-hit 即时):读 `reinforce_count` vs `promote_after`(`N_access`/`Nd`),只升不降,带 `forget_at` 归档 + decay reset。
- **不打架的证明**:access 升级不写 `cumulative_impact` → driver 下次看到 delta=0,不会回撤 access 的晋升;driver 降级只在 PoI 转负(`cumulative_impact < -0.5`)时触发,与访问轴正交。两者都只把同一 `tier:` 字段沿同一 `TIERS` ladder 移动。
- **落地**:两轴都跑。Task 1 的 reinforce-on-recall 复用 driver 的 `_rewrite_tier_in_frontmatter` 同款 frontmatter 改写(DRY),只多写 `reinforce_count`/`tier`(经 fuse 算)。driver 保持 daily 跑 impact 轴。**无核心逻辑改动。**

**Step 2 拓扑(2026-06-23 部分确认):** 一次只读 SSH 双跳确认失败 —— cloud 上 `ssh -i id_ed25519_qb ...` key 相对路径未解析(回落密码被拒),**未重试(fail2ban)**。
- 决策规则(不阻塞 Task 0):tier driver 原地改写 `session_*.md` → 必须跑在 **daemon 索引的文件所在盒**。canonical 拓扑(`canonical_memory_capsule...`):bge-m3 file 语义库在 **T4 43.166.8.20**(经 `compass-t4-tunnel`),serving sqlite 在 cloud。→ **driver 部署在 T4**(文件原地),或 cloud 跑后 rsync 到 T4(成本更高,不选)。
- 🔴 fresh session 部署第一步:在 cloud 解析正确 key 路径(试 `~/id_ed25519_qb` / `~/.ssh/id_ed25519_qb`),`ls -d ~/.claude/projects/*/memory` 确认 T4 上记忆文件真在,再挂 timer。**一次成功,不在 fail2ban 下盲试。**

**产出:** Task 0 决策已落本 plan(上 DECISION 块)。无代码改动。fresh session 从 Task 1 起步。

---

### Task 1: wire reinforce_count +1 on recall hit(access event 闭合)

**Files:** Modify `recall.py`(recall 命中路径)· Test `tests/test_lifecycle_fuse.py`(扩)

**Step 1: 失败测试** —— recall 命中一条胶囊后,其 `reinforce_count` +1 且 decay timer reset(`promote_lifecycle_tier` 的输入随之变)。
**Step 2:** 跑确认失败(当前 recall 不回写 reinforce)。
**Step 3:** 实现:recall 返回 top-k 后,对命中文件 frontmatter `reinforce_count += 1`(复用 `tier_promotion_driver._rewrite_*` frontmatter 改写模式·DRY)。⚠️ 性能:批量/异步写不阻塞 recall 热路径(参 v1.7.2 recall <1s 约束)。
**Step 4:** 跑全测(`test_lifecycle_fuse` + `test_recall_semantic` 无回归)。
**Step 5:** commit `feat(lifecycle): reinforce_count +1 on recall hit (access-driven promotion)`。

---

### Task 2: 部署 tier_promotion_driver timer(批量晋升运行)

**Files:** Create `compass-tier-promotion.service` + `.timer`(模板=`compass-fleet-capsule.{service,timer}`)

**Step 1:** 同步 `scripts/tier_promotion_driver.py` + `proof/tier_promotion.py` 到部署盒(T4 或 cloud·按 Task 0 决策)。
**Step 2:** 写 systemd unit(User=ubuntu·ExecStart=`python3 .../tier_promotion_driver.py`·OnCalendar daily·参 fleet-capsule timer 格式)。
**Step 3:** `systemctl daemon-reload && enable --now compass-tier-promotion.timer`。
**Step 4: 实测验证(measurement-first·不信"应该跑"):** 手动 `systemctl start compass-tier-promotion.service` → 读 `tier_promotion_log.jsonl` 确认有真 mutation 记录(old_tier→new_tier)→ 抽查一个 session_*.md 确认 `tier:` 字段真改了。Expected: ≥1 条 promotion(若全 0 = cumulative_impact 全空,回 Task 0 看是否该用 reinforce 轴)。
**Step 5:** commit unit 文件 + 部署记录。

---

### Task 3: 部署 L2 dream-layer 蒸馏 nightly timer

**Files:** Create `compass-l2-distill.{service,timer}` · 同步 `storage/l2_distiller.py` + `storage/l1_*.py`

**Step 1:** 确认 L1 overview 文件存在(l2_distiller 读 L1 输入)——若 L1 没生成,先确认 l1_grouper/l1_renderer 是否在跑(可能 Phase 1 还要部署 L1 层)。⚠️ 这是依赖,Task 3 Step 1 先查。
**Step 2:** Ollama 可选:查部署盒有无 ollama(`curl 127.0.0.1:11434/api/tags`)·有则用 qwen2.5:7b·无则确定性 extractive fallback(l2_distiller 已支持)。
**Step 3:** 写 nightly timer(OnCalendar=*-*-* 03:00)·ExecStart l2_distiller。
**Step 4: 实测:** 手动 start → 确认 `_l2/` 目录产出蒸馏摘要文件 + recall 能召回 L2 摘要。
**Step 5:** commit。

---

### Task 4: 端到端验证 + recall tier 加权

**Step 1:** recall 排序加 tier 权重(procedural/semantic 优先于 working)——改 `recall.py` ranking·测试 tier 高的同分胶囊排前。
**Step 2: 端到端实测(verification-before-completion):** ① 写一条胶囊 → 多次 recall 命中 → reinforce_count 累积 → tier driver 跑 → tier 真晋升 → recall 优先返它。② 跑全仓测试无回归。③ live recall ok:true。
**Step 3:** commit + 更新 CHANGELOG。

---

## 验证总判据(Phase 1 done 定义)
- tier driver timer LIVE + 实测真有胶囊 working→episodic→... 晋升(log + 文件双证)。
- L2 nightly timer LIVE + 产出 `_l2` 蒸馏摘要 + 可召回。
- recall 命中回写 reinforce_count(access→promote 回路闭合)。
- recall 排序 tier 加权生效。
- 全仓测试绿 + live recall 无回归。
**= 记忆从扁平召回库变活的分层长期记忆(LLM-WIKI2 fuse 实运行)。**

## 后续(Phase 2/3·本 plan 范围外)
Phase 2 = OKF 接通(找真消费者)+ GEP 全面(技能图依赖边/复用复利难度门/治理门 quarantine/负样本)。Phase 3 = 耦合主助推 RSI(W2 高 tier 优先 + forbidden_pattern 注入 + L2 喂 soul 蒸馏)。见 `2026-06-23-compass-longterm-memory-gep-capability-design.md`。
