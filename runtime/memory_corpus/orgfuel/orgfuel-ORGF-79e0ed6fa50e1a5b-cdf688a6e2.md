---
name: orgfuel-ORGF-79e0ed6fa50e1a5b-cdf688a6e2
description: "flywheel 档案 ADR-0002-brand-and-repository-name.md # ADR-0002"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-79e0ed6fa50e1a5b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 ADR-0002-brand-and-repository-name.md
# ADR-0002：智涌飞轮品牌与工程仓命名

状态：已接受

日期：2026-08-10

## 背景

组织 AI 品牌已确定为“智涌 / Nautilus”。具身智能数据业务需要在该品牌下形成清晰产品线，
并避免 `guoshu-embodied-data` 这类过长、组织归属不准确的工程名称。

## 决定

- 中文产品品牌：**智涌飞轮**。
- 英文产品品牌：**Nautilus Flywheel**。
- 本地工作目录：`C:\Users\chunx\Projects\nautilusflywheel`。
- GitHub 私有仓库：`chunxiaoxx/nautilusflywheel`。
- 工程名、Python 包名和未来契约命名统一使用 `nautilusflywheel`；不使用连字符。
- “循数 / Xunshu”保留为数据闭环方法论的候选名称，不作为当前主品牌或仓库名。

## 后果

这是一项产品标识与工程命名决定，不改变本仓的业务边界、数据保护规则、适配器边界、
离线优先计划或任何 FDE 事实。所有原始数据、客户材料、凭据与外部业务状态仍禁止进入 Git。

## 未验证项

本决定未验证商标、域名或社交媒体可用性。GitHub 可用性仅在创建私有仓库时核验；若名称冲突，
停止并由产品所有者选择新的命名，不使用自动替代名称。
