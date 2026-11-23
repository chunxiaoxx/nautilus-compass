# compass × assay 能力与发版事实清单(2026-11-23 审计席摸底)

> ⚠️ **本档已被用户否决并有四处错误,勿单独引用——以 `EVOLUTION_REVIEW_20261123.md` 为准。** 勘误:①"一命令验证成立"只在本机工作区成立,入库字节口径 15 张中 3 张 INVALID(EXAM5/RETAKE1/MEMORY_SYSTEMS_DIRECTORY);②把 NACRE 等同于"被撤回的判官"是错的——NACRE 是创新模型代号、判官 v1 在役、11/19–20 另有本地执行器训练路线;③"88.5% 不要讲"过头,应带适用域,且该字段是二值准确率;④漏掉了 HEAD 中 v14 两路由未鉴权。本档其余读数(PyPI 版本线、工具枚举、线上页面探活、发版断档)经复核无误,保留作存档。

> 起因:模真真专稿在即,用户令"先把自己的能力和发版摸清楚再行动"。
> 方法:不照抄 README——四个一手来源独立核对:仓库实物 / PyPI 发布记录 / 线上端点与页面 / 本机亲跑。
> 标注:`[实测]`=本席当场核得;`[仓内证据·未重跑]`=仓内有证据档但本席未复算;`[推断]`。
> 结论先行:**记忆层实物扎实、可对外;判读支柱的对外材料有三处与组织自己的勘误/线上实况不一致,发稿前须修。**

## 一、发版与迭代现状

| 项 | 事实 | 标注 |
|---|---|---|
| PyPI `nautilus-compass` | 共 20 个版本;最新 **3.3.0 @ 2026-10-04**,**七周未发版** | [实测] PyPI JSON |
| 版本时间线 | 2.2.0(06-03)→2.3.0(06-25)→3.0.0(08-24)→3.0.1(08-25)→3.1.0(09-01)→3.1.1(09-05)→3.1.2(09-06)→3.2.0(09-10)→3.3.0(10-04) | [实测] |
| 3.3.0 内容 | 新增 `nautilus_compass.assay` 子包(Verdict Schema v2 校验器+提交件),判分机构产品面首次 pip 可用;版本四处对齐 | [实测] CHANGELOG |
| 3.2.0 | 发布当日未留 CHANGELOG(10/04 补记,不臆补) | [实测] CHANGELOG |
| 主干自 v3.3.0 以来 | 1370 提交,**产品包体(assay/sdk/middleware/storage/proof/drift/recall_pkg/skills_pkg/judges/gep)零变更**;变更=tools/ 88 文件 + mcp_server.py + daemon.py + landing,共 90 文件 +10386/−80 | [实测] git diff |
| 未发版的实质迭代 | 双独立审查 worker+未验证记忆闸门(11/18)·蒸馏增量通道冻结与发布(11/05–18)·项目级 context capsule(11/19)·VerifyPack 相对路径修复(11/19)·rerank 上下文/输出限界(11/18–19)·a2a 只读结算完整性探针(11/22)·出口/订阅工具链(11/06) | [实测] git log |
| 关联包 | `jev-trust` 0.2.1(09-23);**assay 无独立 PyPI 包** | [实测] |

[推断] 迭代重心在"运行维护与证据工具",不在对外包体;主干上的加固用户拿不到(须发版)。

## 二、compass 能力(逐项核对)

**记忆层**(README"2026-08 state"):
- 本地优先的跨 agent 记忆:BGE-m3 语义召回+关键词混合、项目隔离、时间/项目范围;写入时零 LLM。
- 入口 6 个 console scripts:`nautilus-compass` CLI · `compass-mcp` · `compass-a2a` · `compass-drift-history` · `compass-session-search` · `compass-session-writer` [实测 pyproject]。
- MCP 线上工具 **17 个**[实测 tools/list 枚举]:recall / session_search / thread_recall / ingest_obs / drift_check / drift_history / feedback_log / profile / proof_of_impact / add_worker / governance_plan·dispatch·audit·lock_check / submit_platform_task / ingest_platform_task_result / long_task。注:公网 token 面自 3.1.1 起收敛为 8 个,17 为运维视角。
- Drift 检测(25+35 锚点)、Merkle 完整性审计日志、token 最小权限 scope(2.3.1)。
- 许可:Modified MIT(商标保护+托管 100 付费用户上限;自部署免费)。
- 跑分(LongMemEval-S 500q P@1 0.890/P@5 0.978/MRR 0.929;LOCOMO-10 P@1 0.644;e2e 75.4%;EverMemBench 44.4–47.3%;LongMemEval-V2 40.0/38.4;drift AUC 0.83)[仓内证据·未重跑]——均带证据档坐标,README 自述对比口径(我方复现/对方自报)。

**判读与验证支柱**(README"October 2026 new pillar"):
- 一命令验证:`scripts/verify_receipt.py` 验 `docs/wall/EXAM5_SCORECARD` → **[VALID] rc=0** [实测·本席亲跑]。docs/wall 共 32 件(成绩单+Ed25519 签名)。
- 线上页面 [实测 200]:leaderboard.html(L3 Harness 榜 Round 1)· intake.html · registry.html(挂勘误横幅)· errata.html · /api/judge_status(9 张卡:demo+nautilus-l1-0001..0008)· corpus_stats.json。
- 外链 [实测 200]:HF Space 演示 · HF 测试数据集 · IVP v1 gist · rsi-bench PR#3 · HF nacre-judge-v1 · HF caliber-bench-v0。
- 组织自评(11/19 `docs/assay/COMPASS_ASSAY_GAP_REVIEW_20261119.md`):`partial_ready`——"能力存在,组织闭环未完成":审查候选≠签名回执;蒸馏正式发布 0 条。

## 三、assay 是什么(厘清)

- **不是一个模型,也不是独立包**;是"独立判读"这件事的产品面与协议:
  - `assay/schema_v2.py`:Verdict Schema v2 校验器(L1 结构/L2 语义/L3 锚定/L4 一致四级+v1→v2 迁移+v2.1 EGR gap_report);
  - `assay/submit.py`:提交件制式(challenge 八件+errata 勘误件),纯 stdlib;
  - VerifyPack(`tools/verifypack`)· `scripts/verify_receipt.py` · Assay Protocol v0(`docs/protocol/ASSAY_PROTOCOL_V0.md`)· IVP v1(一页规范,已被 rsi-bench 等外部项目采用)· 判例集 Casebook v1.4 · 公开墙 registry/errata。
- 核心纪律:判据预注册(只许更严)· 三态判决 agree/disagree/not_computable · 证据三层 measured/inferred/unverifiable · 非实现者复算 · 负结果照发 · 判读免费/装订收费。

## 四、🔴 发专稿前必须处理的三处不一致

| # | 问题 | 证据 | 标注 |
|---|---|---|---|
| 1 | **README 仍对外宣传已被勘误的数字**:L53"Judgment-fuel corpus — 2,257 …"与 L37"NACRE judge v1 … 88.5% three-state";而 10/19 勘误档定谳"自产语料自举线从底层设计无效",处置表明写"**4002/3000 等语料量数字从一切对外叙事/进展展示中撤下**",且证据链第 2 条即"judge 1.7B 给自家记录开门,58/58 全 pass 化、28.9% 空输入判 pass"。2,257 是同一条棘轮(2257→2420→2553→3294→4002)的起点数。 | README.md L37-56;ERRATA_NACRE_SELFBOOT_20261019.md §一/§三 | [实测] 两处原文;[推断] 同一模型同一语料线,未加注=对外引用高风险 |
| 2 | **HF model card 无勘误字样**:`nautilus-compass/nacre-judge-v1` 页面检索 errata/勘误/invalid/retract 零命中。 | curl 实检 | [实测] |
| 3 | **`https://nautilus.social/assay/criteria` 返回 502**(判据机器可读包入口;10/4 记录为 sha16 ea20d6fd 在线)。 | curl 实检 | [实测] |

附:q50 真人卷页 404 = 10/19 主动下架,符合处置,非故障。

## 五、对外口径速查(给专稿/事实清单用)

**可以讲(有实测支撑)**:本地记忆层与 17 个 MCP 工具 · 一命令验证成绩单(可现场演示)· 线上榜单/受理/登记页 · 三态判决与证据三层纪律 · 负结果照发的做法 · 本周跨机器迁移+通道中断下记忆与验证记录完整保留(本席亲历)。

**不要讲**:NACRE judge 88.5% · 任何语料量数字(2,257/4,002 等)· "judge 模型可独立判分"。

**讲时须带口径**:所有跑分对比(我方复现 vs 对方自报)· "17 个工具"(公网面为 8)· "已认证"(组织自评为 partial_ready,候选≠签名回执)。

—— compass 审计席 · 2026-11-23
