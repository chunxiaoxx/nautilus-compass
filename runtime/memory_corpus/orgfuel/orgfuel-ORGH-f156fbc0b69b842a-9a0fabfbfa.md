---
name: orgfuel-ORGH-f156fbc0b69b842a-9a0fabfbfa
description: "commit 440713d6a11c 2026-06-23 fix(v2.3.0 收口): 补 bump 漏掉的 2 "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-f156fbc0b69b842a
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 440713d6a11c 2026-06-23
fix(v2.3.0 收口): 补 bump 漏掉的 2 处 manifest 版本(plugin.json + npm/package.json)
全套终验抓出 test_plugin_manifest_version_matches_pyproject 失败 = 我首轮只 bump 6 处、
漏 .claude-plugin/plugin.json(grep 非递归漏 dotdir)+ npm/package.json。递归 grep 确认
现 8 处版本声明全 2.3.0、无残留。test_version_sync + test_plugin_manifest 8 测绿。
