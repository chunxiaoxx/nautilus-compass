# L3 Harness 榜 Round 1 页面稿 v0(10/12 挂墙目标;读数位占位待 B 臂收官填充)

> 判据正本:L3_HARNESS_BOARD_ROUND1_PREREG_20261005.md(冻结+披露附录 A)。本稿=对外呈现层,读数以 report 实测为准,占位符一律 `[R1-A-*]`/`[R1-B-*]`。

## 主表:同模型双臂 harness 对比(30 题,SWE-bench Verified 分层抽样 seed=20261005)

| 臂 | harness | 模型 | max_steps | resolved | 全量率 | completed 内率 | patch 合规率 | 空 patch |
|---|---|---|---|---|---|---|---|---|
| A | v5-harness@4e14a898 | MiniMax-M3 | 50 | 7 | **23.3%** | 58.3%(7/12) | 53.3%(16/30 可 apply)¹ | 2 |
| B | mini-swe-agent@2.4.6 | MiniMax-M3 | 50 | 5 | **16.7%** | 50.0%(5/10) | 66.7%(20/30 可 apply)² | 9 |

配对矩阵(30 题):A 独解 3 / B 独解 1 / 双臂皆解 4 / 双臂皆未解 22;差分 A−B=+6.7pp(双解交叠低=编排路径差异大,非同题扎堆)。

¹ A 臂 error 16=patch 格式 14 [实测:14/14 缺尾换行,12/14 含 repo 外新增文件]+评测环境 2(镜像 EOF,双臂补跑中)。
² B 臂 error 11=patch 格式 10 [推断:patch-apply 型,抽查轮逐题定性]+评测环境 1;空 patch 9=mini-swe-agent@50 步打满无产出(与 smoke 信号一致)——编排产出质量差是对比读数的一部分,照报不剔除。

## 读数注记(判分纪律呈现)

- **口径**:resolved=官方 swebench harness(FAIL_TO_PASS+PASS_TO_PASS 全过);判分环境=独立 A100(非实现者隔离);抽查 ≥6 题/臂复核一致;2 题评测环境侧镜像拉取失败不计入臂差异(补跑对齐后更新);
- **污染 caveat(附录 A)**:SWE-bench Verified 已被 OpenAI(2026/2)停引(污染证据链);本榜读数=**同模型双臂 harness 编排差分**,非模型能力绝对值;
- **A 臂归因**:16 error 中 14 题=patch 格式合规层(缺尾换行+新增文件入 diff,归因简报已送 v5,Round 2 前修复)——格式合规本身是 harness 编排能力的一部分,计 0 分照报;
- 抽查读数(含"解在题面"标注):`[R1-SPOT]`。

## Round 1 结论位

`[R1-VERDICT]`:双臂差分 + 三层归因(模型/编排/格式)——B 臂收官后填。

## 服务区(挂墙四件)

- **价目**:首检收录免费/深度报告 $199(launch)/企业定制 $999 起(正本 JUDGING_PRICE_LIST_V1);
- **SLA**:交付 ≤5 工作日/返工 ≤2/判据 sha 预注册(只许更严);
- **样例报告**:G1 差分终判脱敏版+UMI V4 判读实物+本 Round 归因简报(判例集 v1 摘录);
- **入口**:CTA mailto + 7 日内响应承诺。

## 复现区

- 判据档+双臂 preds+双 report sha16 全挂;`[R1-SHA]` 收官时定版。
