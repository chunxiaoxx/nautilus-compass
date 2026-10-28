# 重算窗固化证据(2026-10-09 · soul #10809② 裁定落实)

## 快照锚

- 表:platform_nau_ledger_bak_20261009(重算前全量备份)
- 行数:9,225(id 1–9,333 跨度,含空洞=历史删除留白)
- **sha256(pg_dump):`0a0571bcf33f2b58`(前 16)**

## 重算差异说明(两类,依 soul 裁定区分)

**口径修正类(占绝对多数)**:balance_after 与流水累计的系统性偏离——根因=写入口径为派生链(接上一行)在并发下漂移累计误差,重算=按"资产台账=流水累计和"口径(#10377 裁)统一重写 4,108 行。**性质=口径统一,非个别错误**。

**数据错误类(2 行,标注影响范围)**:9315(nautilus-prime-001,-30 漂移)/9322(nautilus-prime-001,-20 漂移)——v5 预跑基线判定的真漂移单,重算后转 IDENTICAL(A5 门)。影响范围=prime-001 一户两行,已随全表重算修正。

## 纪律(soul 裁定采纳)

- 后续任何账本修正**只新增修正分录(reason 带 correction/backfill 标记),不改历史行**;
- 快照表保留至 10/31(开业首单后可归档);
- 修复分录先例:stake_release_backfill_20261009(+8 笔)/stake_slash_backfill_20261009+reversal(201+201 对消,append-only 审计链)。

—— platform · RECOMPUTE-EVIDENCE-SEALED · 2026-10-09
