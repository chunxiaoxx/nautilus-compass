---
name: orgfuel-ORGD-bf6c602a4a7da2ee-8507e71650
description: "[## 三 · V 算子的七判据分类学(checks.py 实物)] | kind | 判据内容 | 纯度 | |---"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-bf6c602a4a7da2ee
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 三 · V 算子的七判据分类学(checks.py 实物)] | kind | 判据内容 | 纯度 |
|---|---|---|
| aggregate | ratio_eq/exact:filtered rows 上 num/den(expr.eval) | 纯 |
| file_hash | sha256/sha256_16 | 纯 |
| file_hash_map | 名字→哈希映射(rows/claim 驱动,支持 input dir) | 纯 |
| group_count | 分组计数+min_group/expect_groups | 纯 |
| json_map_equal | 容差映射比较 | 纯 |
| text_contains | needles(可引用前序 claim **计算结果**) | 纯 |
| script | 子进程跑 repro 脚本,timeout+env_caps 声明 | **拟纯**(环境依赖) |
