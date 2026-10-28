# decoy_005B · CS-005 诱饵层改造(2026-10-28 bait)

> 母题: CS-005(抽样审计可复算·qwen 旧 16K 0.529 / 32K 超档约 0.91)。
> 本改造=515B 模式: policy 枚举外语义(联审聚合层)+半错草稿。

## 层2 定位
- policy §4 写了「切分清单后合并审计,敞口结论必须一致」,但**未枚举**联审入口对短分片的处置。
- 草稿可辩护:「campaign 只循环调 sample_ledger;短分片 N/A 跳过;空 all()=无失败;§4 只约束单份合计」。每半句对,合起来错(空集≠审过、未并入≠切分合并、k×分片≠一次抽样)。

## 双态 [实测]
- 坑版: score=0.5(4/8)·gating 三门全挂(短分片敞口/空联审/样本长度=k)
- 金标: score=1.0(8/8)·pytest 8 passed

## 红线
不动 v5 items 正本;scratch=/tmp/csCS-005B;同步 /tmp/cs_decoy_20261027/codesense/items/CS-005B 与 ops/ali30q/decoy_005B。
