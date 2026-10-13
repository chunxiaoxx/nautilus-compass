---
name: orgfuel-ORGQ-R71-5bdc8c9fb5
description: "### R71 · 2026-10-03 16:30(lint 全量清+CI 转绿闭环,N6 销账) - **N6 升级"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R71
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R71 · 2026-10-03 16:30(lint 全量清+CI 转绿闭环,N6 销账)
- **N6 升级定谳**:CI 红非单处——10/1 起累积 34 处(30 F401+E721+F601×2+F821);我方第一轮只看失败日志头几行误判"单处 F401",修完仍红才拉全量清单(教训:失败日志要读全,验证要抓远端实测非本地单点)
- 修复:`ruff --fix` 30 处未用 import+手修 4 处(verify_bc1 E721 type is/jev-trust client F601 bool-int 冗余键删减带行为回归 4 断言/trust F821 TYPE_CHECKING 守卫);`ruff check .` 本地全绿+**远端 CI run 37109617577 success(2m28s)实测转绿**——10/1 起 main CI 红清零,SDK 零行为变更
- 杂项如实记:`git add -u` 误带 zhihu_dryrun.png 旧改动入 commit(无敏感,留档不追加噪音)
- push:`4099a88f..08070b9c` 全部在 origin;扩 n 终判轮 ~18:10 唤起仍挂;E1 材料+GPU 充值外部时钟不变
