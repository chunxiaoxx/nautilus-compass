---
name: orgfuel-ORGQ-R267-1f33257726
description: "### R267 · 2026-10-06 深夜(主动推进:criteria 死链修复+daemon 重启上岗+榜页真身"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R267
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R267 · 2026-10-06 深夜(主动推进:criteria 死链修复+daemon 重启上岗+榜页真身确认)
- **🔴开业级死链修复[实测闭环]**:终检预跑抓到 https://nautilus.social/criteria 裸路径 301→`:8443/criteria/`(外网 000 不可达)——nginx 目录加斜杠隐式重定向用 listen 端口。修复=sites-enabled/nautilus 8443 块定点 `location = /criteria` → 301 https://nautilus.social/criteria/(同块 phase3 先例同款);备份 nautilus.bak_20261006_criteria;nginx -t 过+reload;**外网跟随 200+页面判据内容在**。报备函已发(trace NGINX-CRITERIA-FIX-1006)。教训:nginx 隐式 301 端口坑=凡"目录自动加斜杠"必查 Location 端口。
- **daemon 重启(补丁 A/C 上岗)**:低峰重启完成;随后 ping 超时 → py-spy 取证=**非故障**,4 worker 全在 get_memory_entries 856/867 真算=重启后 embed 债高峰(缓存空一次性重算)。明早值守首查三件:①ping 恢复 ②fusion fail 零新增(补丁 C 验证)③liveness skip 行出现(补丁 A 验证)。
- **榜页真身确认**:26.7%/16.7% 榜面=文档草稿 L3_BOARD_PAGE_DRAFT_20261005.md 定版(f9df9f01),**10/12 才挂墙**,unipat.html 现无数字属正常;终检预跑发现 intake/unipat 20
