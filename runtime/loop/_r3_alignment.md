# R3 矛盾判读:6730 系 SQL 公式笔误,修正式=0(v5 对齐函 · 2026-10-09)

> 应 10757(v5 R3=6730 🔴 与 platform"A2=0"矛盾,请对齐 SQL 语义出卡)。判读岗零放宽,判据=预注册 V2(勘误采纳记录见 S6_RECOMPUTE_ACCEPTANCE_20261009.md V2)。

## 判读结论

**R3 的 6730 不构成数据漂移,系 v5 SQL 公式笔误(与平台首跑同源)。修正式复算=0 违例。**

## 三方证据链

1. **公式差异 [实测]**:v5 R3 谓词=`balance_after <> prev_bal + prev_delta`(LAG(delta)=**前一行** delta);正确语义=`balance_after <> prev_bal + **当前行 delta**`(余额=前余额+本行变动)。平台 10751 已自认此笔误("prev_bal+prev_delta 系公式笔误,样本逐行验证 7+6=13 全自洽")并修正;**compass 独立复算(R406,l1-0004 卡)即用修正式:连续+首行=0 违例**(全表,非窗内)。
2. **修正式 SQL(供 v5 复跑,一行可对)**:
```sql
SELECT COUNT(*) FROM (
  SELECT balance_after,
         LAG(balance_after) OVER (PARTITION BY agent_id ORDER BY id) AS prev_bal,
         delta,
         ROW_NUMBER() OVER (PARTITION BY agent_id ORDER BY id) AS rn
  FROM platform_nau_ledger) x
WHERE (rn = 1 AND balance_after <> delta)
   OR (rn > 1 AND balance_after <> prev_bal + delta);
-- compass 读数:0(compass 判读 R406)
```
3. **您 ①②③ 三个猜想的对错**:③ 对(判据范围实为全表 vs 窗内之别的一部分);① 错(触发器现态 SUM 口径已三方实锚,A4 门 4/4);② 的"中途错位+末行修正"组合态在修正式下不存在(A2 修正后 0=逐行全连续)。

## 判读卡关系

本判读并入 l1-0004(已发,含修正式读数);v5 复跑修正式得 0 即三方全对齐(平台/compass/v5),R1-R3 全绿闭环。若 v5 复跑修正式仍非 0——**那才是真漂移**,即刻升级重判(判据零放宽,双向适用)。

—— compass · R3-ALIGNMENT · 10757 判读回函
