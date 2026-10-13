---
name: orgfuel-ORGM-assay-330-pypi-published-43cd1a6523
description: "--- name: assay-330-pypi-published-20261004 description: "Py"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGM-assay-330-pypi-published
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

---
name: assay-330-pypi-published-20261004
description: "PyPI 3.3.0 发布(10/4,发版五连全闭环)+nautilus_compass 根目录映射包布局坑(新增子包必走 package-dir 映射,tests/CLI 未安装环境用 importlib 文件加载)"
metadata: 
  node_type: memory
  type: project
  originSessionId: c62a754e-c031-437d-a37a-0d217fbf3144
  modified: 2026-10-04T11:42:02.388Z
fact_status: inferred
---

PyPI `nautilus-compass 3.3.0` 2026-10-04 发布定案(3.2.0 后 24 天空窗结束):

**内容**:nautilus_compass.assay 子包(verdict schema v2 校验正本+challenge 八件/errata 勘误提交侧 schema)+tools/verdict_schema_v2.py 薄壳化+版本五处对齐(修复 3.2.0 起版本同步测试就红的漂移)。

**🔴 布局坑(本次踩两次)**:`nautilus_compass` 是**根目录映射包**(pyproject package-dir `"nautilus_compass" = "."`,sdk/middleware/judges 等全是根目录映射子包)——repo 里**没有** nautilus_compass/ 目录。新增子包两要:①目录放根(如 assay/)+pyproject packages 加 `nautilus_compass.assay`+package-di
