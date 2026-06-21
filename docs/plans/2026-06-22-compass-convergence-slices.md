# Compass 收敛切片 实施计划(2026-06-22)

> **For Claude:** 执行用 superpowers:executing-plans。北极星=`docs/plans/2026-06-22-flywheel-convergence-design.md`。
> 🔴 红线:改 live DB 先 SELECT + backup-first;共享 repo nautilus-core 最小化 git(outbound 写文件不 commit);ssh 单次 heredoc(fail2ban·别循环重试)。

**Goal:** 把 compass 在飞轮右半圈的切片落地——先让验证(齿轮③)可信、recall 干净,为 uplift 见证扫清下游噪声。

**实测坐实的范围修正(写计划前已 grounding)**:
- compass 对 `fde_verdicts` **只读**(`proof/fde_verdict_bus_reader.py`·GRANT SELECT TO compass_sub)。14 行 source=compass 是**手工 ingest**(items=[]·note "batch1")·**无 compass 写入器可改**。→ A = 数据订正 + 口径,不是代码特性。
- verdict 真 bug 实测**仅 1 条** `compass_autolab_bvh_001`(score=0 但 overall_pass=t·passk_reproduced=0.0 但 passk_threshold_met=true·note 是 batch1 非难倒门=漏标)。
- 6 条阈值复核候选:`aes128_ctr`(0.8)/`hash_join`(1.0)/`fft_rust`(1.0)三条 threshold_met=false 却 pass·`levenshtein`(0.2)/`regex_engine`(0.4)/`stack_machine_golf`(0.4)三条难倒门 pass。

---

## 切片 A · verdict 数据订正 + 口径解耦(齿轮③·先做·关键路径)

**为什么先做**:uplift 见证(胜负手)依赖验证可信。score=0 盖通过章会污染"提升信号"。

**A.1 作废 bvh_001(数据·backup-first)**
- 凭据:`psql 'postgresql://nautilus_user:nautilus2024@127.0.0.1:5432/nautilus_production'`(经 ssh cloud·fail2ban 清后)。
- Step 1 — SELECT 确认:`SELECT task_uid,score,overall_pass,artifacts->'qc'->>'passk_reproduced',artifacts->>'note' FROM fde_verdicts WHERE task_uid='compass_autolab_bvh_001';` 期望 score=0/overall_pass=t/passk_reproduced=0.0。
- Step 2 — backup:`\copy (SELECT * FROM fde_verdicts WHERE task_uid='compass_autolab_bvh_001') TO '/tmp/bvh_001_verdict_backup_20260622.tsv'`(+ 已有 `/tmp/autolab_bogus_verdicts_backup_20260621.tsv`)。
- Step 3 — UPDATE:`UPDATE fde_verdicts SET overall_pass=false WHERE task_uid='compass_autolab_bvh_001' AND score=0;`(带 score=0 守卫·防误伤)。
- Step 4 — 验证:重跑 Step 1 SELECT·期望 overall_pass=f。

**A.2 口径决策:6 条阈值复核(compass turf·先判后动)**
- 判据=分两类:① 难倒门 pass(buyer stump 验收·pass@5≤0.6=合格)≠ ② 解对 pass(solver correctness)。这两套语义当前混用同一 overall_pass。
- `levenshtein/regex/golf`:note 明写难倒门→若作买方难倒题,overall_pass=t 合理,**保留**(标注 verdict_kind='stump_gate')。
- `aes128_ctr/hash_join/fft_rust`:threshold_met=false 却 pass·note 仅 batch1·**来源不明 → 与 bvh 同批订正**(SELECT 确认后,若非难倒门语义则 overall_pass=f)。
- 产物:不改代码(无写入器),而是**在 verdict 上加 `verdict_kind` 标注口径**(若 schema 允许)或写一份口径备忘 `docs/verdict_semantics_stump_vs_correctness.md`,供未来 ingest 分流。

**A.3 未来 ingest 守卫(若有标准 ingest 路径)**
- 实测:compass 无标准 verdict 写入器(手工 ingest)。→ 守卫归属 = soul 的 `is_substantive_output`(已部署)+ 难倒门/解对口径备忘。**compass 不重造写入器**(anchor#5)。outbound 给 soul:ingest 时按 verdict_kind 分流,solver-correctness 路径 score=0 强制 pass=f。

**Commit**:A 主要是 DB 数据 + 口径备忘文档;DB 改动无 git;若产口径备忘 → `git add docs/verdict_semantics_*.md && commit`。

---

## 切片 C · recall 清污(删 dummy.md·一步·安全)

- 实测:`~/.claude/projects/default/memory/dummy.md`(12 字节 "test memory"·2026-05-01 冒烟遗留)是 `default` 项目唯一文件→任何 project=default 的 v14 recall 必 rank-1(候选池只它一个),score 0.72 霸榜。
- 文件在 T4 daemon 侧(经 cloud 跳板)。
- Step 1 — 确认:`ssh cloud "ssh -i ~/.ssh/id_ed25519_qb ubuntu@43.166.8.20 'cat ~/.claude/projects/default/memory/dummy.md; ls ~/.claude/projects/default/memory/'"`(T4 跳板·fail2ban 清后)。
- Step 2 — 删:`rm ~/.claude/projects/default/memory/dummy.md`(或删整个 default/memory/·确认无他文件后)。inotify 标脏自动重索引。
- Step 3 — 验证:`curl -s "http://127.0.0.1:8770/v1/v14/recall?q=memory+capsule&scope=user&top_k=3"`·期望 dummy.md 不再 rank-1。

---

## 切片 B · 记忆并库 + 沉淀(齿轮⑤主线·延后到独立 session)

**为什么延后**:① 是架构级改动(合并两套记忆 store),不是 bite-sized 任务,值得自己的 brainstorm→plan;② 在 uplift 见证(soul/V5 turf·胜负手#1)下游——见证未成前,沉淀层优先级低于让验证可信(A);③ 需先定几个未决设计问题(下列)。

**已坐实的约束(给下个 session 起点·别重挖)**:
- Store A=sqlite(`/var/lib/compass/compass.db` observations·飞轮 W1 写 /v1/observations·W2 读 /v1/recall·475 条 ob_fw·自洽闭合)。
- Store B=文件语义库(`~/.claude/projects/*/memory/*.md`·33386 目录·/v1/v14/recall·daemon get_memory_entries+inotify+mtime cache)。
- **无桥接代码**(全库 grep consolidation/reindex/sync 仅 perf TODO 注释·file:line 在设计文档 §4)。
- 方向:**往 Store B(文件库)并**(别往 sqlite·会丢真语义召回+人类可读沉淀)。

**B 的未决设计问题(下个 session brainstorm 先答)**:
1. 桥接点:飞轮 write_learning 改/加调 `/v1/v14/ingest_obs`(learning→session_*.md 带 frontmatter family/reward/verdict),还是另起 consolidation 周期任务?
2. 晋升门/revoke 在文件侧怎么等价(frontmatter reward/revoked 字段 + recall 端过滤)?
3. user 级隔离:文件库按 project/scope 分·无 JWT user 强隔离·并库怎么补租户隔离?
4. consolidation 胶囊化:33386 碎片如何蒸馏成少量高密度胶囊(顺带解 37k 冷扫 perf·45s timeout 是急救非根治)?OKF/GEP 概念如何落进 frontmatter schema?

---

## 执行次序
1. **A**(verdict 可信·关键路径·gated on ssh/fail2ban 清 + DB access)
2. **C**(recall 清污·gated on T4 跳板)
3. **B**(独立 session·brainstorm 先答 4 问·下游)

🔴 当前 blocker:本 session ssh 调用多·fail2ban 已触发(连续 reset)→ A/C 的 live DB/T4 步骤**等 ssh 恢复**再执行,不循环重试。
