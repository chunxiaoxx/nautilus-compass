# rsi-bench 四件套样例包(RSI 环 #1 完整闭环 · 2026-10-03 组装中)

> 对方要求(rsi-bench Issue #1 follow-up):公开机读四件套+完整观察窗含失败+逐观察标注可独立复算 vs 自报。
> 本包=RSI 环 #1(记忆门三件套 #48 进生产)全链:预注册→实现自报绿→**非实现者复算抓 2 处 FAIL**→当日修复→重测全绿闭环。

## 进度(组装中)

- [x] 1_ticket/criteria_prereg_extract.md——J1-J4 判据正本(fact_status 覆盖/查重零误合并/沿链一跳/回归门,各含门槛+验证法)
- [x] 2_fix/01_recompute_FAIL_receipt.diff——0210f49d 复算回执(J1 0/30 覆盖+J3 截断,环不闭环)
- [x] 2_fix/02_fix_and_retest_GREEN.diff——a12c08c8 修复重测(J3 全文扫描+J1 写入门 hook,四条全绿)
- [x] 4_timestamps/commit_chain.txt——时间链 12:30 FAIL 回执→13:52 修复重测(同日闭环)
- [ ] 3_trajectory/——复算轨迹细节(下轮:从预注册档「复算 FAIL 后修复与重测」段+judged_requests 抽)
- [ ] 英文索引 README(对方是英文仓)
- [ ] 可复算 vs 自报标注表(MANIFEST 末)

## 可复算 vs 自报标注(草案,随包完善)

| 观察 | 类型 | 复算方式 |
|---|---|---|
| J1 覆盖 0/30(FAIL)| 可独立复算 | git show 复算回执时点的 mem 目录 frontmatter 扫描 |
| J3 chain_extra 截断(FAIL)| 可独立复算 | 归档请求件全文重放 |
| J2/J4 PASS | 可独立复算 | 单测+regression_gate.py 重跑 |
| 修复后 J1-J4 全绿 | 可独立复算 | 同脚本对 9/14 修复后时点重跑 |
| 复算会话独立性 | 自报(过程事实) | 复算在新会话执行,回执 commit 时间戳佐证 |

## 发布坐标(填完后)

目标:rsi-bench Issue #1 评论链接(本包将挂 gist 或 org 仓路径)
