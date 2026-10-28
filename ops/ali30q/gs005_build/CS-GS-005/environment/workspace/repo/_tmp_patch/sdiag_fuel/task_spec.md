# 第三类基准样例 · 带版本记录的 join/去重取最新版本的遮蔽修复

## 真实需求(来源:真实工程经验,已脱敏)
一个把"带版本的记录"按 uid 合并/去重的服务:同一个 uid 会有多个版本(改稿、重发、
并发写入),系统要对每个 uid 收敛成一条,取**最新版本**(version 最大)的内容对外。
现实里记录**不保证按版本排序到达**:改稿(高版本)产生后,旧版本(低版本)可能因为
重试、补偿、乱序投递而**后到**。一旦取错版本,系统拿到的是过期内容——对外展示旧稿、
按旧判定走流程、对账对不上。这是数据 join/去重的经典真实需求:**去重键必须把版本算进去,
收敛取最新不能靠到达顺序。**

## 经验教训(可迁移,本案例的核心)
- **`{r["uid"]: r for r in records}` 只用 uid 当键,是"谁最后出现谁覆盖"(last-in-iteration-wins)。**
  当输入恰好按版本升序到达时碰巧对(最后一条就是最新的);一旦乱序(高版本不在末尾),
  低版本会**遮蔽**高版本,系统性取到过期内容。
- **根因不是"忘了去重",而是"去重键漏了版本维度"。** 去重逻辑把多版本坍缩成一条时,
  默认依赖了一个不成立的假设:输入有序。
- **正确做法**:join/dedup 键必须纳入版本——要么键用 `(uid, version)` 保留所有版本,
  要么收敛成一 uid 一条时**显式按 version 取 max**(`if uid not in best or ver > best[uid][0]`),
  不靠迭代顺序。
- **version 要按整数比较**,不能按字符串比(否则 `"10" < "9"`),这是同类 bug 的近亲坑。
- **不可复现的"有时对有时错"多半是顺序依赖**:对账偶发差异、改稿偶发不生效,先查
  去重/合并键是否漏了某个维度、是否暗含输入有序假设。

## 任务
给定 `buggy_join.py`(候选起点,correct-by-construction 仅当输入恰好按版本升序到达):
stdin 每行一条记录 `uid|version|payload`(version 为整数,payload 不含 `|`),
对每个 uid 输出一行 `uid|payload`(payload 取该 uid version 最大那条),按 uid 字典序排序。
**修复使取最新版本与到达顺序无关。** 只许改 `buggy_join.py`,仅标准库。

## 可复现评测(`bench_eval.py` · 确定性 · 纯 stdlib · 跨平台)
`PYTHONUTF8=1 python bench_eval.py <候选.py>`。固定输入 11 条记录、5 个 uid,
**故意让多个 uid 的最高版本不在迭代末尾**(乱序到达)。三道门:
- **G1 格式**:每个 uid 恰一行;输出 uid 集合 == 输入 uid 集合;按 uid 字典序;每行 `uid|payload`。
- **G2 正确性**:每个 uid 的 payload == 该 uid version 最大那条的 payload(ground truth 现场
  group-by uid + max(version) 算)。
- **G3 非作弊**:输出行数须 == 唯一 uid 数(远少于输入行数),不得原样回写全部输入行;不得漏 uid。
全部 uid 通过 = pass。评测可换数据集,记答案无用;ground truth 由输入现场算。

### 固定输入(到达顺序·标出暴露点)
| 到达序 | uid | version | payload | 说明 |
|---|---|---|---|---|
| 1 | A | 3 | a-draft-v3 | A 多版本 |
| 2 | B | 2 | b-old-v2 | B 多版本 |
| 3 | C | 4 | c-v4 | C 多版本 |
| 4 | E | 2 | e-final-v2 | **E 最高版本 v2 先到(不在末尾)→ buggy 漏** |
| 5 | A | 5 | a-FINAL-v5 | **A 最高版本 v5 在中间(不在末尾)→ buggy 漏** |
| 6 | C | 8 | c-FINAL-v8 | **C 最高版本 v8 在中间(不在末尾)→ buggy 漏** |
| 7 | D | 1 | d-only-v1 | 单版本对照 |
| 8 | E | 1 | e-stale-v1 | E 旧版后到 → buggy 取它(相邻边界暴露) |
| 9 | B | 7 | b-FINAL-v7 | B 最高版本 v7 在末尾 → buggy 碰巧对(对照) |
| 10 | C | 2 | c-stale-v2 | C 旧版后到 → buggy 取它 |
| 11 | A | 1 | a-stale-v1 | A 旧版最后到 → buggy 取它 |

正确结果:A→a-FINAL-v5、B→b-FINAL-v7、C→c-FINAL-v8、D→d-only-v1、E→e-final-v2。
buggy(last-wins)结果:A→a-stale-v1、C→c-stale-v2、E→e-stale-v1 三个取错;B/D 碰巧对。

## 判别矩阵(基准自验,已实测)
| 候选 | 判定 | 证据 |
|---|---|---|
| buggy(`{r.uid: r}` last-wins) | FAIL G2 2/5 | A 取 a-stale-v1(应 v5)、C 取 c-stale-v2(应 v8)、E 取 e-stale-v1(应 v2) |
| 规范正确解(group-by uid + max version) | PASS 5/5 | 5 个 uid 全取最高版本 |
| wrong-fix(键纳入版本但收敛取 min/末位) | FAIL G2 1/5 | 取了最低版本·只有单版本 D 碰巧对 |
| cheat(原样回写所有输入行) | FAIL G3 | 输出 11 行 == 输入 11 行·未去重 |

即评测同时拦住 last-in-iteration-wins(顺序依赖)、收敛口径错(min/字符串比)、
trivial-echo(不真去重)三类,只有"join 键纳入版本 + 显式 max(version)"能过。

## 附件
- `buggy_join.py`(候选起点·只读起点)
- `bench_eval.py`(评测驱动·确定性·含 G1/G2/G3 三门·可换数据集)
- `task_spec.md`(本规格)
规范正确解 `solution_ref.py` 不入附件(是 ground truth 资产)。
