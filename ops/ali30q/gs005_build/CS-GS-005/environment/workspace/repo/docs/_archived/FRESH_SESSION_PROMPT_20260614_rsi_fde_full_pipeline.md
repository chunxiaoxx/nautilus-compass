# /goal — 闭第一份真实 FDE 交付物 = RSI 飞轮第一转(fresh session · 2026-06-14 收敛版)

> 复制本文当 /goal。你 = platform-soul(nautilus-core 对话框)。
> **Session-start 必读**:`FDE_BUSINESS_CHARTER.md` + 本文 + memory `feedback_close_one_real_loop_before_new_fronts_20260614`(防掰玉米)+ `design_20260614_rsi_distillation_flywheel_inference_ceiling`(RSI 转向)+ `session_20260612_s2_submission_qc_feedback_engine_done`。设计 doc 备查:`docs/plans/2026-06-14-rsi-distillation-flywheel-design.md` / `2026-06-11-fde-org-production-engine-design.md` / `2026-06-12-feishu-native-ops-console-design.md`。

## 🔴 唯一 P0(单一 forcing function · 别开第二条线)
**把第一份真实 FDE 交付物从头到尾闭一次**:
```
派活(S1 LIVE) → 专家亲笔(用户 RSI 教案 or 选一道 backlog 题) → QC 过(S2 LIVE)
  → S3:组装买方格式(16列/4段)入买方交付表 + settlement 最小记账(应付专家/token 成本)
  → ✅ 1 道交付物到买方载体 + 成本/应付账 = "≥5 道全程流完"的第 1 道
```
**为什么这是 RSI 飞轮第一转(不是两件事)**:这道交付物的 QC verdict + 买方验收 + 真$ 结算 = RSI 的外部 fitness 信号本身;而它过完后,对同一道题做"强模型先解→A/B/C 分拣"= 蒸馏飞轮的第一个真实输入。**FDE 业务流通 = RSI 链条转动·闭一份真东西就是喂 RSI 第一口。**

## 上轮自审(必须内化·防复发)
6/14 一天产了一堆 artifact(5 设计 doc/3 飞书表/6+ outbound)但**0 道真交付物流通**·S3 没建·"吞吐"=囤队列没流。**活动量 ≠ 价值。** 这轮**只认一个胜利条件:一份真东西交到买方载体 + 结算。** 其余全是 gated/parallel,不抢焦点。

## 已 binding-DONE(别重验)
- S1 派活+验收 LIVE(派活表 `EOVh/tbl69fankpoBhJfw`·timer 自驱)。
- S2 提交→QC反馈环 LIVE(教案 assembler·题目 checklist_scorer·第1类首验 GREEN)。
- 9 行真实 backlog 在派活表(纯待派单·可领)。
- 专家库 CRM `tblh5qmxF4Ebtdvi`+招募表单 `vewHeBPH04`+生产看板 `vewkm9UitR`(壳·分组列待 UI)。
- LIVE bug 治(空 task_uid 空键碰撞·commit 95ef1b739)。

## 这轮要建的(就 S3·最薄)
**S3 交付+财务最小记账**(我 turf·纯新模块·复用 `fde-row-assembler`/`knowledge-tutorial-assembler` 组装):
1. QC 过稿(状态=已通过)→ 组装买方格式:第1类=16列 → 第3类 L3表 同款 / 第2类=4段教案表。
2. settlement 最小记录:一张结算表(任务/专家/应付/token成本/状态)·先飞书表 + 公式,或引擎最小表。
3. 买方机密走**独立 base 物理隔离**(charter §E·别和运营 base 关联)。
4. 判据:1 道真稿 已通过 → 自动/半自动入交付表 + 一条 settlement 记录。**端到端实测(verification-before-completion)**。

## Gated / Parallel(captured·不抢 P0 焦点)
- **RSI 蒸馏(路1)**:gated 在 compass S-诊断分类表 ping + 强 completer(Claude 顶 or 百炼 key 修)+ A簇 T4。compass 回了我再接 verifier 聚合 + S-PoC。**不主动开**。
- **skill loop(路2)**:v5 自治修 L1·并行·不依赖我。
- **console UI / 招募真实专家**:用户侧 UI-config(看板分组/仪表盘/招募发链 ~10min)·放大吞吐的真瓶颈=人。
- **百炼 key**:用户取对的 `sk-`(现 401)·替代=Claude/开源 embedder。
- **出题-from-episode skill**:持续 supply 发动机·**第一份交付物闭环后**再做(别现在开)。

## 阻塞(开工先确认)
1. 用户那道 RSI 教案是否交稿(派活表 expert_t2_rsi_grounded_retrieval·骨架已给)→ 没有就选一道 backlog 题当第一份(如 expert_t2_drift_detection·我们真做过)。
2. compass 是否回 S-诊断分类表(回了=RSI 那条可并行接·但仍不抢 S3 焦点)。

## 纪律(anchor·硬执行)
- **#3 反D**:一个胜利条件=一份真交付物+结算·artifact 多 ≠ 闭环。
- **#4 反精分**:单一 forcing function·新想法进 parking lot·2 session 没闭→砍。
- **#2 RSI 闭环**:FDE 流通即 RSI 转·别把 RSI 当独立第二战线。
- **#5/#1**:复用现成 skill 栈·v5/compass 自治。
- 诚实负结果照实记(grounded 撞墙=成功的诚实)。

关联 [[feedback_close_one_real_loop_before_new_fronts_20260614]] · [[design_20260614_rsi_distillation_flywheel_inference_ceiling]] · [[session_20260612_s2_submission_qc_feedback_engine_done]] · [[FDE_BUSINESS_CHARTER]]
