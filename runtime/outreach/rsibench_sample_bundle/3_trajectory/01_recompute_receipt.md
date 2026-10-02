### 非实现者复算回执(2026-09-14 午 · 独立会话 · 只信本档判据与自测)

> 复算者:与实现无涉的新会话,开工前未读实现方会话结论(档内 9/14 回填段在读判据时一并入眼,
> 但以下所有判定均以本会话独立实测为准;两处不一致处已如实标注)。
> 环境:生产 worktree `feat/memory-gate-trio` @ 9cb9e7e 核实 · daemon 9876 复算期间死过一次
> (watchdog 12:16:56 拉起,12:21 listening;J4 在热身后跑)· 探针材料全部自选,不复用实现方样本。

| # | 判定 | 读数 |
|---|---|---|
| J1 fact_status 覆盖 | **FAIL** | 9/9 落档后新写入 30 条(v5/compass/core 三项目合计)带 fact_status **0 条(0%)**;9/14 合入后新写 2 条同样 0/2;实现方合入后自己写的 rsi-loop1-merged-20260914.md 亦无。探针已排除 CRLF/格式误判(frontmatter 完好,纯缺字段) |
| J2 查重零误合并 | **PASS** | 5 条无关对照全 unique(hits 空);2 条同主题改写 gray(0.809 / 0.767,均在 0.75-0.9);2 条原文前 600 字 merge(0.9184 / 0.9107,均 ≥0.9)。三档行为全对,对照组 0 误合并 |
| J3 沿链一跳 | **FAIL** | 带链查询命中 arm-a-summary-layer-pass-20260903.md(body 含 3 条 `[[...]]`,首链偏移 814)→ **chain_extra=[]**(判据要求被引条目 100% 出现)。无链查询 chain_extra 恒空 ✓;延迟 p50=356ms / p95=397ms(n=12 热 recall)✓ |
| J4 全局回归门 | **PASS** | 三 fact hit@3 全对,hits 与 ops/regression_gate_baseline.json 逐条一致;延迟 12248ms(重启后 embed 冷)/824 / 905ms |
| 15 单测 | **PASS** | tests/test_memgate.py 15 passed(3.31s) |

**J1 根因**:fact_status 门只落在 daemon 读出路径(parse_memory_file)+session_writer 蒸馏;
而 9/9 以来全部实际新写入走 Claude Code 直写路径(auto-memory frontmatter 模板无此字段,
hooks/ 与 scripts/ grep `fact_status` 零命中)——「人工写入走纪律」无任何机制或模板支撑,纪律未被执行。

**J3 根因**:parse_memory_file 的 `body[:500]` + `description[:120]` 截断;expand_chain_links
只扫截断窗口。链接在 body 偏移 <500 时可正常展开(本复算期间 recall hook 偶然实证 2 例,偏移 342/214),
链接在文件尾部(「关联 [[…]]」惯例位置)时**永不展开**。实现方 9/14 读数的 aegis 例
(链接偏移 1272,窗口外)在本复算中不可复现,疑为误记或误测。

**结论**:RSI 环 #1 第四段(非实现者复算)不通过(J1、J3 FAIL),环不闭环,不发闭环通报函。
按预注册纪律:不改代码、不放宽判据。修复与判据处置留用户裁决(判据只许更严,任何放宽须用户拍板并记录)。

### 复算 FAIL 后修复与重测(2026-09-14 午后 · 用户拍板「先修 J1/J3 → 重测闭环 → 发通报函」)
