# decoy_003B · CS-003 超档题诱饵层改造(2026-10-28)

> 母题: CS-003 ephem 时管精度(单 JD 越界·qwen 旧面曾 1.0 超档)。本打样=515B 模式复制到时域。
> 预注册判据: ①坑版 gating 挂 ②金标 27/27 det ③qwen 均值 ∈[0.25, 0.70)。判据只许更严。

## 改造内容
1. **新增第二层陷阱 `ephem/catalog.py`**: 批量均值历元/跨度/汇总落盘。坑=单 JD 浮点均值 + 空集 J2000 占位 + 落盘 `mean_jd`。policy §2/§3 枚举未覆盖聚合层,原则需模型自行贯穿。
2. **instruction.md 加半错断言草稿**(515B 配方): reviewer 结论补 catalog 段——"§3 枚举都在 ingest/predict/store 内,catalog 只是引擎内部统计;导出的是汇总不是原始观测,不算 §2 边界;空列表占位是标准 N/A"——每半句对,合起来错(空集≠有效历元、导出仍是持久化边界)。
3. **tests 追加 6 条 UT**,其中 3 条 gating=true(均值无损/空集拒绝/落盘禁裸 JD);task.toml **ut_index 27 条完整**(F-008 tomllib 解析门已过)。

## 双态验证 [实测·10-28 01:40]
- 坑版态: score=0.2593(7/27)·gating 恰挂 4 条(chain_full + catalog 三门) ✓
- 金标态: score=1.00(27/27)·gold_check GOLD-PASS deterministic=True ✓
- 官方工具: `gold_check.py` swap 5 文件(catalog/store/ingest/predict/format)

## qwen 快筛 [实测·10-28 02:03-02:31]
- 渠道指纹: `qwen3.8max` / `bl-qwen3.8-max` / 中转站 200 / 时段 02:03:50–02:31:39 CST / elapsed=**1667.9s** / applied=5 / raw_len=13607
- run0 score=**0.963**(26/27)。唯一挂=`test_catalog_missing_not_skipped`
- 落带口径: 均值须 ∈[0.25,0.70)。0.963=超档 → **FAILED 照标**,不硬凑,不开 run1(本轮已超时)
- 失败模式: qwen 用 jd1/jd2+ISO precision=9 修掉层1+层2 三门 gating;缺时间戳静默跳过未贯穿(非 gatin 功能条)

## 判定
双态闭合但诱饵未咬合。时域微秒+聚合层对本渠道=强域(与 509B 同构:第二层被看穿)。槽位换母题,本改造件库存不入带。

## 坐标
- scratch: `/tmp/cs_decoy_20261027/codesense/items/CS-003B`
- 持久快照: `ops/ali30q/decoy_003B/`
- v5 items 软链: `codesense/items/CS-003B` → scratch(不碰 CS-003 正本)
