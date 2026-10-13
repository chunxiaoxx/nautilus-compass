---
name: orgfuel-ORGQ-R128-6a4d547e96
description: "### R128 · 2026-10-04 19:2x-19:5x(用户拍三件连排轮·3.3.0打版+J8发出+assa"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R128
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R128 · 2026-10-04 19:2x-19:5x(用户拍三件连排轮·3.3.0打版+J8发出+assay API)
- **用户拍板**"三件都排:3.3.0 打版→J8 发出→assay API 最小件"——三件全动:
- **3.3.0 打版 [三重验证绿,待 token]**:nautilus_compass.assay 子包(schema_v2 校验正本自 tools 迁入+submit 提交侧 schema=challenge 八件制式/errata 勘误件);tools CLI 薄壳化(importlib 同源直载——首版 sys.path 引导踩根目录映射包布局坑两次,importlib 文件加载定案);版本**五处**一次对齐 3.3.0(pyproject/package.json/plugin.json/mcp_server.SERVER_VERSION/CHANGELOG——发现 3.2.0 起版本测试就红(3.1.2 漂移),本次修复 2 绿);单测新增 tests/test_assay.py 14 绿;wheel 内 assay 三件+twine check 双 PASSED+干净 venv 装轮 import OK;**CHANGELOG 补 3.2.0 段时臆写两条 bullet 即删(未验证不落档)**;待 PyPI 上传(token 不落盘=用户侧唯一阻塞)
- **J8 发出 [3037]**:verdict-judge 装载热路径三步申报+P4 判据预注册正本发 platform,deadline 10/11;档头状态更新"已用户明示";动工=申报回执后
- **assay API 最小件**:随 3.3.0 交付(challenge/errata 纯 stdlib 校验,枚举与 verdict schema v2.1
