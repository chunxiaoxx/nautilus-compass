# 旧格式 10 verdict 真复算 · 读数档(2026-09-18)

> 姊妹篇:HANDOFF_20260917_10verdict_recompute.md(坐标与命令正本)。
> 复算者:compass 新鲜会话(非判分行生产者,与 g2-b1 管线无实现关联)。
> 判据正本:docs/catalog/CATALOG_v0.md 前三条(verdict-recomputability-v1 /
> external-verified-provenance-v1 / evidence-schema-v1),三态 agree/disagree/not_computable。
> 纪律执行:零改数(全程 SELECT/只读);零发函(回函留主会话);只记实测。

## 正本拉取与探针自证

- 信箱 HTTP 视图(`GET /api/platform/org/mailbox?to=compass`)返回空,`platform_mail.py check` 亦 0
  → 走路径 B:nautilus-db MCP 直读 `org_mailbox` 表,**id 280 命中**(from v5 · trace
  `v5-g2b1-ten-uid-coords-20260916` · ack 9/15 已收)。10 uid + 五件套坐标齐全。
- 探针自证(红灯先证伪自己,三次):
  1. 裸 uid 查 fde_verdicts 0 行 → 证伪探针 → 实际带 `g2b1:` 前缀,10/10 命中;
  2. 函内 evidence 档名"三臂/四臂"在库与档目录均无字面对应 → 档目录 474 文件
     实名盘点,每 uid 下四模型档(chunxiao_k3,…)与三模型档(minimax_m3,…)各唯一,
     10/10 唯一可解(f08c/8f1d/d821 各另有 glm_plan 单模型档,不与函内指称冲突);
  3. buggy commit 跑指定 test_id 得 rc=4 "no tests ran" → 证伪探针 → ls-tree 证实
     测试**文件**在 buggy commit 存在,是**测试函数**由 ref fix commit 新增(TDD 生成
     模式),故"buggy 上红灯"结构不可得,判别力锚在 ref 绿灯(下表以实测为准)。
- commit 可达性:20/20(10 buggy + 10 ref)在 cloud `/home/ubuntu/nautilus-v5` 仓
  `cat-file -e` 全 OK(19 唯一:eaa48d61 同时为 3225 的 bug 与 eaa4 的 ref,链式自洽)。
- evidence 档:cloud `/home/ubuntu/nautilus-soul-workspace/phase3/backend/docs/evidence/`
  474 文件与函 280 自述一致;10 个钉定档逐个读全文。

## 目标集钉定(函 280 evidence 列 → DB 行,verdict_id 与档名一一对应,各唯一)

| # | task_uid | evidence 档(函 280) | DB 行 id · verdict_id · 批次 |
|---|---|---|---|
| 1 | g2b1:ffbe0dfb38ba | g2b1-exec-ffbe0dfb38-minimax_m3,glm_plan,deepseek.json | 4380 · 同名 · 8/29 |
| 2 | g2b1:d60b44f93eb8 | …-ark_glm.json | 4158 · 同名 · 8/24 |
| 3 | g2b1:81616966a559 | …-ark_glm.json | 4159 · 同名 · 8/24 |
| 4 | g2b1:e8ddf11f82b9 | …-四臂=唯一四模型档(chunxiao_k3,…) | 4458 · 同名 · 9/05 |
| 5 | g2b1:32250027d328 | …-三臂=唯一三模型档(minimax_m3,…) | 4384 · 同名 · 8/29 |
| 6 | g2b1:eaa48d6132c4 | …-ark_glm.json | 4162 · 同名 · 8/24 |
| 7 | g2b1:f08c1c9e3422 | …-ark_glm.json | 4555 · 同名 · 9/08 replay |
| 8 | g2b1:8c3094c5a4b6 | …-四臂=唯一四模型档 | 4462 · 同名 · 9/05 |
| 9 | g2b1:8f1deb5724b3 | …-ark_glm.json | 4557 · 同名 · 9/08 replay |
| 10 | g2b1:d821039cf687 | …-ark_glm.json | 4558 · 同名 · 9/08 replay |

注:与 9/15 试点集(id 4380-4391)交集 2 条(4380/4384);9/08 三条 ark_glm 为试点
批 3 条 fail(4386/4390/4391)的同 uid replay,结论同向(仍 skip/fail)。

## 复算方法(全实测)

- DB:fde_verdicts 全行(含 items/artifacts/external_verified)、verification_logs、
  audit_log、org_mailbox,SELECT only。
- 独立重跑:cloud 仓 git worktree(detach 到指定 commit,跑毕全部 remove+prune,
  工作树零污染),.venv py3.10/pytest 9.0.3:
  - 7 条 pass 行 → ref fix commit 跑档内 test_id;
  - 3 条 skip 行 → buggy commit 跑档内 test_id(单测+整文件);
  - 另对 7 条 pass 行的 buggy commit 跑同名 test_id 做红灯对照(结果=测试函数缺失,
    rc=4,见探针自证 3)。
- 档-行一致性:DB artifacts 的 turns/total_tokens 与档内逐字段比对,10/10 镜像吻合。

## 逐条读数与三态

判"对象"=verdict 行的声称集(pass/score、external_verified、执行元数据自洽);
C1/C2/C3 = CATALOG 前三条缩写。

| # | 行 | 声称 | 实测复算 | C1 | C2 | C3 | 三态 |
|---|---|---|---|---|---|---|---|
| 1 | 4380 ffbe | pass·1·ev=true | ref 绿 1 passed 0.07s;3 模型判分而 total_tokens=0(turn 实耗 input 4101/output 354,provider_used 缺) | 分可推(绿复算) | **违例** | **违例** | **disagree** |
| 2 | 4158 d60b | pass·1·ev=true | ref 绿 0.09s;单模型 tokens 2315=turn 和,自洽 | 分可推 | **违例** | 过 | **disagree** |
| 3 | 4159 8161 | pass·1·ev=true | ref 绿 1.53s;tokens 18370 自洽 | 分可推 | **违例** | 过 | **disagree** |
| 4 | 4458 e8dd | pass·1·ev=false | ref 绿 1.84s;4 模型 tokens 11407>0+provider_used=chunxiao_k3 记录 | 分可推 | 合规 | 过 | **agree** |
| 5 | 4384 3225 | pass·1·ev=true | ref 绿 0.08s;3 模型 total_tokens=0(turn 实耗 3133/185) | 分可推 | **违例** | **违例** | **disagree** |
| 6 | 4162 eaa4 | pass·1·ev=true | ref 绿 0.07s;tokens 13968 自洽 | 分可推 | **违例** | 过 | **disagree** |
| 7 | 4555 f08c | fail·0·ev=false | buggy:判别测试名缺失+整文件 3 passed 全绿=无红,skip 结论成立;0 轮 0 token 与 skip 自洽 | 分可推(无红实证) | 合规 | 过 | **agree**※ |
| 8 | 4462 8c30 | pass·1·ev=false | ref 绿 1.79s;2 turns(红→绿)tokens 6634=turn 和,自洽 | 分可推 | 合规 | 过 | **agree** |
| 9 | 4557 8f1d | fail·0·ev=false | buggy:判别测试名缺失+整文件 12 passed 全绿=无红,标签 no_red_test_at_buggy_commit 精确复现 | 分可推 | 合规 | 过 | **agree** |
| 10 | 4558 d821 | fail·0·ev=false | buggy:整文件 9/9 全绿=无红,skip 结论成立 | 分可推 | 合规 | 过 | **agree**※ |

※ 标签不精确但结论同向:f08c/d821 档内 skipped_reason="fixture_broken_red",
独立复现实态为"无红"(判别测试缺失/全文件全绿),非"fixture 崩";fail(0) 判定
本身正确。#7 与 #10 的 agree 是对行声称集(fail·0·ev=false)的 agree。

**计数:agree 5 / disagree 5 / not_computable 0。**
(score 声称 10/10 独立可推且全部复算吻合——7 绿于 ref、3 无红于 buggy;
disagree 全部源于行声称集内携带不实/矛盾标志,非分数错误。)

## 系统性读数

1. **C2 违例 5/10**:4158/4159/4162(ev=true, external_verified_at 聚簇
   2026-08-25 20:56:56-14,7 行 18 秒内=程序化批量)+ 4380/4384(8/29 批,试点已证
   手工置位)。外部来源排查:verification_logs **全表 0 行**、audit_log **全表 0 行**、
   org_mailbox 8/25-8/30 无复算主题函 → ev=true 无任何外部复算者痕迹,行内亦无
   verifier 身份字段 → 生产者自置成立,与 9/15 试点病灶同款。
2. **C3 违例 2/10**:4380/4384(两条件均为三模型批)turn 内 usage 非零而
   total_tokens=0 且 provider_used 缺失——聚合字段失效,元数据自相矛盾。
3. **C1 结构债 10/10**:行内 items=[] 全量(写入器回归在旧格式行未修);本轮
   可复算性全部经由函 280 指针链达成(verdict_id→evidence 档名确定性映射→仓内
   commit→worktree 重跑)。指针链 10/10 唯一解析,无一处歧义(含三臂/四臂口语名)。
4. **skip 标签保真 1/3**:x8f1d 精确复现;f08c/d821 的 fixture_broken_red 复现为
   "无红"——结局一致、病因标签不准。
5. 置观:e8dd 档内 winning_diff 的 index 行为占位哈希(1111111..2222222),内容
   语义已被 ref 绿灯独立证实,属档格式瑕疵非判定问题。

## 边界与交接

- 本档只记实测;未改任何 verdict 数据(未 UPDATE/未回写 ev);未发函(回函 v5 留主会话)。
- CATALOG 增严候选(只增不松,待主会话定夺后注册):①skip_reason 标签须可被独立
  重跑复现(skip-label-fidelity);②多模型批 total_tokens 聚合非零为硬条件(现状
  已含于 evidence-schema-v1,可显式加"turn usage 非零 ⇒ total_tokens 非零"式收紧)。
- 复算产物:云上 worktree 已全清(worktree list 0 残留);本仓仅本读数档一个新文件。
