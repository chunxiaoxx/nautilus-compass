---
name: orgfuel-ORGM-2752b9d1a72fcc90-bae0b73606
description: "记忆条目 clawhub-glama-audit-20260916.md # 双审查修复 9/16(commit 935"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-2752b9d1a72fcc90
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 clawhub-glama-audit-20260916.md
# 双审查修复 9/16(commit 93519fc)

**Glama 构建失败根因**(用户贴 build log 定位):Glama 自动 Dockerfile 对
repo 跑 `uv sync`;uv 的 universal lock 解析**全部** extras,`nautilus` extra
依赖 nautilus-agent(内部轮子,PyPI 无包/无公开仓双 404)→ 外部解析必败。
修复=pyproject 移除该 extra(平台框直装内部轮,零破坏)+ 提交 uv.lock。
本地实证:`uv lock` 86 包 9.19s 成功(改前必炸)。

**Why:** 面向公开注册表的包,extras 里不能放私有依赖——pip 不炸(懒解析),
uv/Glama 这类 lock-first 工具必炸;自报"能装"≠外部能装。

**How to apply:** 以后新增 extra 前先跑 `uv lock` 实证可解析;对外安装命令
一律钉 tag/SHA+pip ==版本(ClawHub A.I.G T03 Error 就是抓未钉版本)。

**Glama 知识**:无独立"评分按钮";Admin 标签(需 GitHub owner 登录认领)→
Repository syncs → "Request a re-sync"=触发重评;每个新 commit 也自动触发
全管线重跑;"cannot be deployed"=Docker 构建没过,认领后 Docker builds 面板
可看失败日志。

**ClawHub 1.0.1**(2026-09-16):双语卡钉 v3.2.0(commit a24563a)+脚本行为/
备份/卸载说明+云托管出域提示;p
