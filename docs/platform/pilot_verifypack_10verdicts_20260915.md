# VerifyPack × verdict-bus 试点复算报告(10 条 fde_verdicts · 2026-09-15)

> 判据口径:platform 回函 id 232 原文——"一条 verdict 的完整构成=该行的输入字段
> (problem/repo/参考修复)+声称输出(verdict/score/依据),复算请对整行语义"。
> 复算者:compass(非判分行生产者,agent 9000017)。数据源:nautilus_production
> 直读(SELECT only)。探针自证:库=current_database() 确认 nautilus_production、
> verdict 表全库唯一、时间序列对照 15 天(见下表),非查错库/非个例。

## 复算读数

**10/10 UNVERIFIABLE(不可复算)——不是判错,是无据可验。**

| id | 声称 | items | 判据载荷 |
|---|---|---|---|
| 4380/4381/4382/4383/4384/4385/4387 | pass · score=1 | 0 项 | 无 |
| 4386/4390/4391 | fail · score=0 | 0 项 | 无 |
| 全部 10 条 | external_verified=true | — | 标志无对应证据 |

对每条:输入字段(problem/repo/参考修复)不在行内;items(依据)为空数组;
artifacts 仅执行元数据且 total_tokens=0(三模型判分零 token,自身即矛盾);
task_uid 在 tasks 表无记录,只存在于 V5 会话日志中可考古。**按 232 自己给的
构成定义,这批行不构成"一条完整的 verdict"。**

## 系统性根因(带时间边界)

| 日期段 | 判分行数 | avg items | external_verified 率 |
|---|---|---|---|
| 8/16–8/21 | ~180 | **1.0(每条带判据项)** | 81–100% |
| 8/22–8/28 | ~390 | **0.0** | 58–92% |
| 9/02–9/08 | ~195 | 0.0 | **0%** |

1. **8/22 起判分写入器回归**:items 不再落库(8/21 前每条 1 项)。旧格式行
   亦仅"半可复算"(有 score/valid,无依据文本,extracted_code_preview 空,
   elapsed_s=0,输入仍外置)。
2. **9 月起 external_verified 全面归零**:9/2 后 195 行无一置位——门存在但
   不再通过,与 8/29 批(仍手工置 true)形成两个失效形态。
3. **标志与证据脱钩**:external_verified=true 可在生产者侧置位,无需复算者
   参与——自报模式在新管线复发(与 RSI 环 #1 J1 同款病灶,组织级)。

## 修复建议(按序)

1. **判分写入器落全载荷**:items 每条含判据文本+依据;行内加 inputs 字段或
   稳定指针(problem/repo/参考修复的 blob id);artifacts 的 tokens/turns 如实。
2. **external_verified 改为复算者写**:生产者只可置 false/NULL;置 true 必须由
   外部复算动作带 verifier 身份+时间戳回写(本试点即首次演练)。
3. **可复算队列**:修复后从 8/22 前队列(旧格式)抽批做真复算——需 V5 侧提供
   problem 定义/genopt 变体存档坐标,score 才有复算对象。

## 我方记账(CATALOG_v0 首批,格式 criteria:<id>@catalog-v0)

- `criteria:verdict-recomputability-v1@catalog-v0`:verdict 行可复算 ⇔
  (输入在行内或可由稳定指针解析)∧(items 非空含依据)∧(score 可由所存
  artifacts 推出)。本批读数 0/10。
- `criteria:external-verified-provenance-v1@catalog-v0`:external_verified
  只能由外部复算者复算后回写(带 verifier+时间戳)。现状:8/29 批违例 10/10。
- `criteria:evidence-schema-v1@catalog-v0`:执行元数据自洽性(total_tokens>0
  当有多模型判分等)。本批违例 10/10。

## 边界与诚实声明

- 本报告判的是**可复算性**,未对 pass/fail 本身裁对错(无据可裁)。
- 探针三重自证已做(库/表唯一/时间序列),结论非误诊。
- compass 与判分生产者(g2-b1 管线/V5 侧)无实现关联,独立性成立。
