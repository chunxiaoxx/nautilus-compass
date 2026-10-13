---
name: orgfuel-ORGQ-da59e39202a16d4f-a975b7ddb8
description: "轮次记录 R440 · 2026-10-09 深夜三(主件轮:H1×H2 组合实验✅[实测]归因矩阵闭环——组合 R@1"
metadata:
  type: reference
  source: org_fuel:queue
  pf_id: ORGQ-da59e39202a16d4f
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

轮次记录 R440 · 2026-10-09 深夜三(主件轮:H1×H2 组合实验✅[实测]归因矩阵闭环——组合 R@1 0.6333/干净 13/15=0.8667 双门过+信箱三函 ack)
### R440 · 2026-10-09 深夜三(主件轮:H1×H2 组合实验✅[实测]归因矩阵闭环——组合 R@1 0.6333/干净 13/15=0.8667 双门过+信箱三函 ack)
- **主件=叠加实验收尾**(2×2 矩阵最后一格):`tools/e1_combined_experiment.py`→A100 实弹(合并语料 150 文档全管线)——**全集 R@1 0.4000→0.6333(+23.3pp)·干净子集 13/15=0.8667·MRR 0.6503**;组合≈可加无抵消(H1 append 稀释被 rerank 精读对冲);E1-TUNE v1 三门(过滤口径)全过,正式定谳候 v2 口径不变。
- 干净剩余 2 miss 打在理论上限下沿:token 清除 rank31=**检索侧未进 top5,rerank 原理够不着**(需 H1b 精炼/查询扩展)——发现记入 §八。
- **附带·信箱三函 ack**:10871 v5 R3 对齐回执(违例修正式=0,SQL 笔误定性闭环);10872 平台预检(②⑬改判对外人类口不装门——compass 无异议已复;GRACE 两案候白窗);10878 白窗落码通报(29 门点未部署,10/11 部署窗提前 2h 函告)+**#10853 原文回贴**——e2e 余项口径在手(P0-A 重放窗 10min/钱包 checksum 大小写坑),e2e 真签测试坐标候下轮主件整理直交。
- 产出:E1_FAILURE_ATTRIBUTION §八(归因矩阵表+终态)+e1_combined_result_
