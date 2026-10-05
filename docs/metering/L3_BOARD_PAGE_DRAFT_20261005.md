# L3 Harness 榜 Round 1 页面稿 v1(10/12 挂墙目标;Round 1 读数定版 10/6 02:1x——EOF 双臂补跑折入+抽查完成)

> 判据正本:L3_HARNESS_BOARD_ROUND1_PREREG_20261005.md(冻结+披露附录 A)。本稿=对外呈现层,读数以 report 实测为准,占位符一律 `[R1-A-*]`/`[R1-B-*]`。

## 主表:同模型双臂 harness 对比(30 题,SWE-bench Verified 分层抽样 seed=20261005)

| 臂 | harness | 模型 | max_steps | resolved | 全量率 | completed 内率 | patch 合规率 | 空 patch |
|---|---|---|---|---|---|---|---|---|
| A | v5-harness@4e14a898 | MiniMax-M3 | 50 | 8 | **26.7%** | 61.5%(8/13) | 50.0%(15/30 可 apply)¹ | 2 |
| B | mini-swe-agent@2.4.6 | MiniMax-M3 | 50 | 5 | **16.7%** | 50.0%(5/10) | 63.3%(19/30 可 apply)² | 9 |

配对矩阵(30 题,镜像 EOF 补跑折入后终版):A 独解 4 / B 独解 1 / 双臂皆解 4 / 双臂皆未解 21;差分 A−B=**+10.0pp**。

¹ A 臂 error 15=patch 格式 15/环境 0 [实测:补跑折入,sphinx-8475 补跑后 resolved(+1),sympy-13974 补跑后仍 apply fail 归格式;malformed hunk 是致命特征]。
² B 臂 error 11=patch 格式 11/环境 0 [实测:sphinx-8475 原判环境 EOF,补跑实机跑通后 apply fail(malformed at line 64)改判格式;sympy-13974 patch 本为 0ch,原批即 empty,补跑复核一致,empty 9 净不变];空 patch 9=mini-swe-agent@50 步打满无产出为主因(与 smoke 信号一致)——编排产出质量差是对比读数的一部分,照报不剔除。
**归因勘误(判绩账)**:此前归因简报(函 9842)称"缺尾换行=apply 失败确定性成因"——抽查 12 题(含全部 resolved 题)patch **全部缺尾换行**,其中 4 题 resolved 通过 apply → 缺尾换行降级为伴随特征非充分条件;真正阻断=malformed hunk 结构(hunk 行数/新增文件路径)。修正不改变 16→25 题格式层归因结论,只修正机制表述。

## 读数注记(判分纪律呈现)

- **口径**:resolved=官方 swebench harness(FAIL_TO_PASS+PASS_TO_PASS 全过);判分环境=独立 A100(非实现者隔离);抽查 ≥6 题/臂复核一致(12/12 零不符);2 题镜像 EOF 已双臂补跑折入,终版环境层归零;
- **污染 caveat(附录 A)**:SWE-bench Verified 已被 OpenAI(2026/2)停引(污染证据链);本榜读数=**同模型双臂 harness 编排差分**,非模型能力绝对值;
- **双臂归因(终版)**:格式层 A 15/B 11 全定性 [实测](malformed hunk 结构;v5 管线病灶=repo 外新增文件入 diff+尾换行,mini-swe-agent 亦有 malformed);归因简报(9838/9842)已送 v5,尾换行"确定性成因"表述勘误见上;Round 2 前修复三件(尾换行补齐/路径过滤/smoke 门),25 题格式 error 作回归集;
- 抽查读数(含"解在题面"标注):分层抽 6 题/臂(12 题,含 4 题双臂同题对照),状态↔preds 逐题一致零不符;"解在题面"污染扫描(30 题全量,gold patch 新增行子串检测 [推断]):弱命中 2 题(django-14855 两行/matplotlib-26291 一行,均为常见惯用代码行,不构成污染证据,如实披露;升级路径=人工 hunk 上下文比对)。

## Round 1 结论位

**Round 1 定版 [实测]**:同模型(MiniMax-M3)双臂 harness 编排差分——v5-harness resolved **26.7%** vs mini-swe-agent **16.7%**(+10.0pp;配对 A 独解 4/B 独解 1/双解 4/皆未解 21)。三层归因:①模型层=同模型受控,差分非模型差;②编排层=A 臂 completed 内转化 61.5%>B 50.0%,B 空 patch 9(50 步打满无产出)——产出纪律差是主差分来源;③格式层=双臂合规率 50.0%/63.3% 均未过工程合格线(malformed hunk 双臂皆有)——Round 2 前修复窗口。负结果与格式缺陷照报;n=30 达名次区门槛,扩样滚动。

## 服务区(挂墙四件)

- **价目**:首检收录免费/深度报告 $199(launch)/企业定制 $999 起(正本 JUDGING_PRICE_LIST_V1);
- **SLA**:交付 ≤5 工作日/返工 ≤2/判据 sha 预注册(只许更严);
- **样例报告**:G1 差分终判脱敏版+UMI V4 判读实物+本 Round 归因简报(判例集 v1 摘录);
- **入口**:CTA mailto + 7 日内响应承诺。

## 复现区

- 判据档+双臂 preds+六 report+合并/抽查件 sha16(10/6 02:1x 定版):
  判据档 b81eca8436887785 · preds_a f2b34552f6c0d4de · preds_b 39cb1bb39f58c3a6
  A:rest 8e9da206a0f3f5c6 · django 7dc1efbb710ffcab · eof 3f6f200a22073787
  B:rest ca194dde7551b959 · django 5fea45df7beb6181 · eof 1d59a024f8509962
  合并件 36f3f38665419f3a · 抽查件 056267e179a3845e
