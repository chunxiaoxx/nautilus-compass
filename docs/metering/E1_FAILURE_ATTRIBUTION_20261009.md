# E1 检索调优第一刀:A+ 查询失败样例归因(2026-10-09 · R437)

> 判据档:EMB_BAKEOFF_PREREG_20261009.md(基线 0.40 出处)· 工作集:/root/vdf/emb_bakeoff/A_plus_queries.json(30 条,Qwen3-1.7B 情境改写 seed42)
> 复跑:`tools/e1_failure_attribution.py`(口径与 eval.py 逐行一致:bge-m3 CLS 池化+normalize+MAXLEN 512)· 明细:同目录 e1_attribution_20261009.json

## 一、基线复现 [实测]

| 指标 | 预注册基线 | 本轮复跑 | 判 |
|---|---|---|---|
| R@1 | 0.4000 | 0.4000 (12/30) | 逐位一致 |
| R@5 | 0.6667 | 0.6667 | 逐位一致 |
| MRR | 0.4994 | 0.4994 | 逐位一致 |

口径自证通过——归因结论建立在同一把尺子上。

## 二、三个发现

### 发现一:工作集 50% 污染 [实测]

30 条查询中 **15 条**带生成器指令泄漏(「如果 agent 再次遇到完全相同的情况…」SYS prompt 原文/「查询:」模板前缀),其中 9 条 FAR_MISS(rank 55-122)。**18 个 miss 中一半来自无效查询**——emb_gen_a_plus.py 的 resp 清洗(splitlines()[0])未剥指令回显,且无空泛查询拒绝门。

### 发现二:干净集失败结构=near-miss 邻域干扰 [实测]

剔除污染后 15 条干净查询:R@1 仍 6/15=0.4000,但失败结构质变——**9 个失败中 8 个 NEAR_MISS(gold 在 rank 2-4),FAR_MISS 仅 1**。

干净集失败明细(全部 gold∈top5):

| 查询(截断) | gold rank | top1(抢走者) |
|---|---|---|
| fast path 环境差虚警: inotify_simple… | 4 | memgate-m5-deploy-lessons |
| nginx 生产陷阱: 非 systemd 管理… | 4 | memgate-m5-deploy-lessons |
| 判官升级项列下轮,我方备料档已出 | 2 | day-log-20261006-round1-fi |
| T0 发布版(9/12) | 4 | bc1-launch-eve-20260926 |
| 域 3(同日):embodied-qc-labeling… | 7(唯一 far) | compass-roadmap-20260907 |
| query: 为什么 token 被清除 before forwarding? | 4 | p1-host-migration-http-2 |
| R0 有4种 intervention+5种 selector… | 4 | session_20260718-1142_差异 |
| 这轮用户的实质诉求推进了吗 | 4 | launch-sprint-status-202 |
| "标准远程MCP已实现,但当前/мcp/*…" | 2 | session_20260822-1918_tr |

### 发现三:干扰根因在库结构而非 embedder [实测→推断]

决定性例证:库内存在**同主题双文档**(`memgate-m5-deploy-lessons-20261009.md` 与 `m5-memgate-deploy-lessons-20261008.md` 两份 M5 部署教训并存),两者互抢 top1、把真 gold 挤到 rank 4——出现 2 次。8 个 near-miss 中至少 3 个的 top1 是同主题邻居文档(day-log 与专题档并存是常态)。
**推断**:0.40 的主要瓶颈是记忆库的分档结构(同主题多版本/专题档与流水档并存),不是向量模型本身;bge-m3 留任判据与此互证。

## 三、调优假设分级(候预注册)

| 假设 | 动作 | 成本 | 预期收益 |
|---|---|---|---|
| **H1 库侧去重/合并** | 同主题双文档合并(M5 lessons 先例)+专题/流水分档标记 | 零模型成本 | 直接消除互抢,保守估计 +2~3 hit |
| **H2 rerank 层** | top5 内 cross-encoder/启发式重排 | 中(需模型或规则) | near-miss 8 条吃 3 条 → R@1 0.60 |
| **H3 工作集 v2** | 生成器剥指令前缀+空泛查询拒绝门+重生成 30 条 | 低 | 判据口径干净化(必做前置) |

## 四、E1-TUNE v1 预注册判据(建议稿,判据只许更严)

- **口径**:干净工作集(生成器 v2 重生成,人工抽检零污染)
- **基线**:R@1=0.4000(本轮干净集实测同值)
- **过门**:R@1 ≥ 0.60 **且** R@5 ≥ 0.80 **且** bge-m3 底座不动(换模型另走对拍)
- **负结果照报**:任一假设单独归因(H1/H2 分开测),不做混合归因

## 五、证据层

- 基线复现/失败明细/污染计数:[实测](A100 远程复跑,JSON 明细 18KB 在档)
- 发现三的根因指向:[推断](2 例决定性+3 例旁证,未穷举全部 8 例)
- 过门预期收益数字:[推断](保守估计,upgrade_path=H1/H2 单独归因实验)

—— compass · E1 调优第一刀 · R437 · 2026-10-09
