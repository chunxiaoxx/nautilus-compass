---
name: orgfuel-ORGM-clawhub-glama-audit-2026-6b12b77ed0
description: "--- name: clawhub-glama-audit-20260916 description: ClawHub "
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGM-clawhub-glama-audit-2026
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

---
name: clawhub-glama-audit-20260916
description: ClawHub 安全审查(Review·T03 Error 未钉版本)+ Glama Docker build 根因(nautilus extra 内部轮子炸 uv universal lock)双双修复——技能卡 1.0.1 钉 v3.2.0 重发布;Glama 评分按钮=Admin→Request a re-sync
metadata: 
  node_type: memory
  type: project
  originSessionId: 5103bb42-025f-4754-adcf-4ff0f2b7218d
  modified: 2026-09-16T02:56:56.969Z
fact_status: inferred
---

# 双审查修复 9/16(commit 93519fc)

**Glama 构建失败根因**(用户贴 build log 定位):Glama 自动 Dockerfile 对
repo 跑 `uv sync`;uv 的 universal lock 解析**全部** extras,`nautilus` extra
依赖 nautilus-agent(内部轮子,PyPI 无包/无公开仓双 404)→ 外部解析必败。
修复=pyproject 移除该 extra(平台框直装内部轮,零破坏)+ 提交 uv.lock。
本地实证:`uv lock` 86 包 9.19s 成功(改前必炸)。

**Why:** 面向公开注册表的包,extras 里不能放私有依赖——pip 不炸(懒解析),
uv/Glama 这类 lock-first 工具必炸;自报"能装"≠外部能装。

**How to apply:** 以后新增 extra 前先跑 
