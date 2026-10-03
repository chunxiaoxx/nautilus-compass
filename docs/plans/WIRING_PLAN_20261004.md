# 接线实施计划(2026-10-03 立档,准备推进)

> 性质:行动计划+接线计划(每线给接口/触发/步骤/验收,命令级可执行)。
> 背景:五框协同三线已闭环(数据→判读/燃料→训练/治理→执行),本计划把"待建协同"落成接线工程。
> 执行原则:每线独立可推进,完成即 commit;跨框线以函为接口,框内线以脚本为接口。

## L1 · errata 导入线(v5 → compass 语料池)【已发车,等回函】

- **接口**:函 2634(trace compass-errata-gold-request-20261003,死线 10/5 18:00)
- **触发**:v5 回函或 A100 落盘通知
- **步骤**:①收数据(信箱附件存 runtime/verdict_corpus/delta/inbox/,或 A100 落盘拉回)②字段映射(对方 qid/原判定/复算判定/判因 → 我方 artifact/judge_output/truth_label/label_origin;label_origin 按对方标注映射白名单四类)③投 inbox 交 p3_delta.py 吸收(指纹账去重+白名单门)④p3_ticket 看是否触发
- **验收**:delta_NNNN 入账,label_origin 白名单校验通过
- **依赖**:v5 响应;若 10/5 18:00 未回,reminder 一次(组织内数据请求,非外联催办)

## L2 · schema 会签线(flywheel case_spec × compass verdict_schema_v2)【本周】

- **接口**:flywheel `case_spec`(声明式验证案 schema,gen4_v1 校验 PASS)× compass `VERDICT_SCHEMA_V2.md`
- **步骤**:①读 flywheel case_spec 全文(仓 C:/Users/chunx/Projects/nautilusflywheel,找 gen4_v1 样例)②产出映射表:case_spec.判据版本 → verdict.criteria.version/ref;case_spec.验收判据 → verdict.criteria.ref;verdict.verdict.state → case_spec 状态机③会签函发 flywheel(双向引用:case_spec 引 verdict_schema_v2 作为结果格式,verdict 引 case_spec 作为案件定义)④各自 schema 加 `peer` 字段
- **验收**:两 schema 互引字段落地,gen4 案例用 v2 verdict 出一份样板
- **依赖**:无(单方面可先做映射表)

## L3 · E1 判读线(platform → compass 判读 → 语料)【死线 10/5 13:16】

- **接口**:platform 任务市场(席位已领 #2545,材料未发)
- **触发**:材料到(信箱/A100)
- **步骤**:①材料 sha16 锚定存档②按包判据独立盲判(不与 prime 互通)③判读器出 v2 verdict④死线前交付⑤判读判定转语料(verdict_to_samples 投 inbox)
- **验收**:死线前交付+65NAU 结算+语料增量
- **风险**:材料 10/4 仍未到→回函 platform 请发包(留痕)

## L4 · 判例集 v1 装订线(七演判例 → 对外可引用物)【本周】

- **内容**:G1 三锚定案+pusht 全弧(两版判据+终判)+判据演进程序化案(T1/T2→v2-final)+假说对撞案(2422)+口径裁定两案(#2553/#2572)
- **硬要求**:含"判据零放宽 vs 判据演进"张力段如实段;协议文档体(判据原文/sha 锚定链/复算命令/证据层标注);全部 verdict 过 schema v2 校验
- **步骤**:①判例清单定稿(8 案)②每案装订(模板:背景/判据/材料锚/判读/统计/claims/边界)③schema v2 批量校验④汇编 docs/cases/CASEBOOK_V1.md⑤发布位置(GitHub 仓+冷外联引用)
- **验收**:外部读者可按 sha 链独立复验任意判例
- **两线定价位**:装订线首物(收费 SKU 前的公开 demo 版免费)

## L5 · 外部破零线(判例集 → 冷外联)【判例集后】

- **目标**:首个组织外送判/复算请求(反剧场主尺破零)
- **顺序**:rsi-bench certification 兑现(等对方动)→ Letta Evals/Zep 协议互补函(附判例集链接+免费复算 offer)
- **验收**:首个外部请求进入测量线

## L6 · 首训练单线(P3 管道首转)【语料 ≥200 触发】

- **触发**:p3_ticket.py 报 ISSUED(pending ≥200;L1 errata+L3 E1+案源任一凑齐)
- **步骤**:①人工批准执行(ticket PENDING_APPROVAL→APPROVED)②4090 短租(1.65/h,API 层,守门 exit42)③train_judge_incremental.py(--ticket, epochs≤5)④双臂 preds 拉回⑤p3_gate --record⑥PASS→p3_promote 上岗;FAIL→rejected/ 冠军不动(重训限 2 次)
- **验收**:ledger 记 GATE/PROMOTE;组织 RSI 循环首次完整转一圈
- **成本上限**:ticket cost_cap ¥5

## L7 · 论文双线【本周并行】

- paper2:四件新素材织入 §卫生协议(判据演进程序化/证据三层实战/两法裁决/具身真空位)→tex 打包→arXiv 提交(用户操作,账号 Chunxiao Wang)
- paper3:《验证前置:因果倒置的验证机构》立项稿(§3 判据演进案例=10/3 活案例;novelty=具身验证闭环真空位,frontier_mapping 有据)

## 执行序(依赖图)

```
L3(E1材料到即判)──┐
L1(errata回函即吸)─┼→ L6(首训练单,语料≥200)
L4(判例集装订)────┼→ L5(外部破零)
L2(schema会签)────┘(独立)
L7(paper双线,独立并行)
```

## 沉淀纪律(每线完成时)

每线完成三件套:commit+ledger/queue 记账+memory 提炼(可复用经验)。组织 RSI 循环=判读→schema→转换器→P3→上岗,每转一格计一次。
