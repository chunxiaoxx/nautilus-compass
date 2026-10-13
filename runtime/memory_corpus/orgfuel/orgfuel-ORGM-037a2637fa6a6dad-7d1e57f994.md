---
name: orgfuel-ORGM-037a2637fa6a6dad-7d1e57f994
description: "记忆条目 assay-330-pypi-published-20261004.md PyPI `nautilus-com"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-037a2637fa6a6dad
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 assay-330-pypi-published-20261004.md
PyPI `nautilus-compass 3.3.0` 2026-10-04 发布定案(3.2.0 后 24 天空窗结束):

**内容**:nautilus_compass.assay 子包(verdict schema v2 校验正本+challenge 八件/errata 勘误提交侧 schema)+tools/verdict_schema_v2.py 薄壳化+版本五处对齐(修复 3.2.0 起版本同步测试就红的漂移)。

**🔴 布局坑(本次踩两次)**:`nautilus_compass` 是**根目录映射包**(pyproject package-dir `"nautilus_compass" = "."`,sdk/middleware/judges 等全是根目录映射子包)——repo 里**没有** nautilus_compass/ 目录。新增子包两要:①目录放根(如 assay/)+pyproject packages 加 `nautilus_compass.assay`+package-dir 加映射;②未安装环境下 tests/CLI **不能** `import nautilus_compass`(需 repo 父目录在 sys.path 才成立)——用 importlib.util.spec_from_file_location 按文件路径加载同源文件(tools 薄壳与 tests/test_assay.py 均此法)。

**发版配方增量**(承 [[pypi-311-published-20260906]] 五连):token 不落盘不进 keyring/.pypirc,每次发布向用户现取(贴 chat,长度预验:截断=95,正常 ~175-179);tw
