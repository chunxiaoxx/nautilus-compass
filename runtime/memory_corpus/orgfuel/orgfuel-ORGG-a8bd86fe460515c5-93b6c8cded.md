---
name: orgfuel-ORGG-a8bd86fe460515c5-93b6c8cded
description: "判读档判例 S6_RERUN_SCHEDULE_20261008 · 2. 资源缺口(如实列) ## 2. 资源缺口(如"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-a8bd86fe460515c5
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 S6_RERUN_SCHEDULE_20261008 · 2. 资源缺口(如实列)
## 2. 资源缺口(如实列)

- **磁盘为唯一硬约束**:30 题 swebench 评测镜像预计 40-70GB,cloud 余 62G——紧。预案:①按 repo 去重预拉(减 30-40%)②不足则临时清理非产容器镜像(espocrm/label-studio 等 6GB 级,清理前列单)③仍不足向平台申临时扩容(用户令背景优先响应);
- 判分算力:resolved 判定=测试套 exit code,**不依赖 LLM 判分器**;三态判读层复验(如需)A100 现役环境覆盖(bf16 部署纪律);
- 环境:cloud DOCKER_OK [实测];A100 无 docker [实测](判分器备用,非复跑瓶颈);
- 人工:compass 会话窗执行,零外部缺口。
