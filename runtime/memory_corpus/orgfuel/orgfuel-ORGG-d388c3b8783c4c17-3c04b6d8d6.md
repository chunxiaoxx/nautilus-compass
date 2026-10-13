---
name: orgfuel-ORGG-d388c3b8783c4c17-3c04b6d8d6
description: "判读档判例 S6_RECHECK_FIX_20261008 · 实锤②:judge_status 无参返 demo → "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-d388c3b8783c4c17
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 S6_RECHECK_FIX_20261008 · 实锤②:judge_status 无参返 demo → 已修
## 实锤②:judge_status 无参返 demo → 已修

- **根因 [实测]**:API 无 `?id` 参数时默认返回 demo 演示卡——平台无参探测得到 demo 属实;带参 `?id=nautilus-l1-0001` 一直返回真卡(平台探测口径与真卡查询口径不一致,但默认返 demo 确实易误读=compass 修)。
- **修复 [实测外网]**:无参现返回**可查询卡清单+用法说明**(`{"ok":true,"cards":["demo","nautilus-l1-0001"],"note":"pass ?id=<card_id> to query; live cards carry criteria_sha16"}`);带参回归绿(id=nautilus-l1-0001,criteria_sha16=b81eca8436887785)。

**criteria_sha16 live 时点**:即日 live——`GET /api/judge_status?id=nautilus-l1-0001` 外网即返 b81eca8436887785(与 GitHub 判据档同源,可逐件对)。
