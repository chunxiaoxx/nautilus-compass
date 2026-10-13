---
name: orgfuel-ORGF-4f02f58d643e6160-a12b09bc61
description: "flywheel 档案 2026-10-02-LeRobot首件数据集候选清单-v0.md # LeRobot 首件数据"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-4f02f58d643e6160
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 2026-10-02-LeRobot首件数据集候选清单-v0.md
# LeRobot 首件数据集候选清单 v0(2026-10-02 深夜筹备 · 明晨 HF 实查校准)

> 用法:明晨用 huggingface_hub API 按 downloads 排序逐 embodiment 校准取 top 2-3;
> 本文候选凭现有知识预列,repo_id 以实查为准(不冒充已确认)。

## 校准方法(一条命令)

```bash
python -c "from huggingface_hub import HfApi; api=HfApi();
[print(d.id, d.downloads) for d in api.list_datasets(author='lerobot', sort='downloads', direction=-1, limit=30)]"
```
逐 embodiment: `api.list_datasets(search='<关键词>', sort='downloads', ...)`。

## 候选(5 embodiment × 2-3)

| embodiment | 候选 repo_id(待校准) | 备注 |
|---|---|---|
| agibot_g1 | agibot-world org 系列(AgiBot World 官方) | 智元官方;我们 G1 链同源,QC 读数可直接对照 G1 探针 |
| bridge | lerobot org 的 bridge 官方转换版 | bridge_orig/rrk 变体;32 维动作注意转 14 对齐读数不转数据 |
| franka_droid | physical-intelligence/droid(π0 官方转换) | 100K 级大库;首件抽
