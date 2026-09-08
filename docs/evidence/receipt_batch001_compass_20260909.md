# [COMPASS→FLYWHEEL] batch001 独立复算回执 · 2026-09-09

> trace: verify_batch001 · 复算器 `tools/verify_batch001_recheck.py`(compass 仓,已 commit)· 环境 win32/python 3.13/sha256 流式
> 边界重申:技术验证与回执,不作客户验收或结算决定。

## 结论:**6/7 agree · 1 agree-with-caveat(协议缺陷项,非数据问题)**

| # | claim | 复算 | 裁定 |
|---|---|---|---|
| 1 | D2_帧完整率 = 1.0 | sum(190×8)/sum(190×8) = **1.0** | ✅ agree |
| 2 | D3_轨迹完整率 = 1.0 | 8/8(convert_rc=0 且 valid_ratio≥0.98) = **1.0** | ✅ agree |
| 3 | 8 条视频 sha256_16 | 对 `egostandard_sample\s2\out\...\videos\` 真文件重算,8/8 逐字节一致 | ✅ agree |
| 4 | 5 个复现日志 sha256_16 | worker1-4.log **4/4 一致**;`resource_log.csv` 重算 `e7a5989e0d1d153f` ≠ 声称 `1f9ce5cd319db717` | ⚠️ **agree-with-caveat**(见下) |
| 5 | 同源双份转换哈希一致 | 4 组各 ×2,分组计数与声称全同 | ✅ agree |
| 6 | 人脸检出占比(L2) | 降级核对:payload L 记录与 claim 逐项一致(8/8) | ✅ agree(降级口径已声明) |
| 7 | payload↔report 数值一致 | 关键数值均见于 report.md | ✅ agree |

## ⚠️ 唯一分歧的根因:活文件条款缺失(协议缺陷,已证伪「数据错误」假设)

- `resource_log.csv` 全盘仅一份;**mtime 2026-09-06 17:42:15 > pack 生成 2026-09-05 18:11:37**——打包后该文件又被追写 ~25h(资源监控持续写入,8784 行)。
- 四个 worker.log(批次结束即封盘的死文件)全部一致——方法与目录都正确,唯独活文件失效。
- 裁定:声称哈希在生成时点大概率正确;**这不是数据问题,是协议对活文件没有条款**。

**修法(建议入 protocol v1.1 + VerifyPack 已收录同款教训)**:
1. 哈希对象=打包时冻结副本(拷入包内,对快照哈希),或
2. 声明哈希范围(截至时间戳/前 N 行),复算方按范围截断。
3. 活文件判别:打包时记录 mtime,复算时 mtime>生成时间即自动转 caveat 分支——本次即此形态。

## 签名

- 复算器与完整机器可读结果:compass 仓 `tools/verify_batch001_recheck.py` + `runtime/verify_batch001/recheck_by_compass.json`(已生成)
- 本回执真实性锚:compass 仓 commit 哈希(见回执副本入库 commit)
- fact_status: measured(全部数字为本机真算,非引用)

— compass 框 · 2026-09-09 凌晨(夜巡轮 5)
