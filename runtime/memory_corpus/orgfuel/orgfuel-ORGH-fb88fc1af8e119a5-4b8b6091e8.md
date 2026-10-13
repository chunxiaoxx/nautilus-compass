---
name: orgfuel-ORGH-fb88fc1af8e119a5-4b8b6091e8
description: "commit 12a4a58aee52 2026-09-05 fix(security): 自助 token 缺省 pr"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-fb88fc1af8e119a5
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 12a4a58aee52 2026-09-05
fix(security): 自助 token 缺省 project 双洞修复——读写全断+跨租户读,已上线验证
9/5 新人全流程复测抓到:9/4 workers2 重启后 scope 门禁把无 project 参数
判 read:''(403),且 403 包在 HTTP 200 body 里(9/4 实测'200'=假绿);
首修检查侧兜底后复测暴露执行侧落 daemon 默认内部用户 cycle-N-auto 空间
(跨租户读,修复前 forbidden 反而挡着它)。终修:_call_tool 缺省 project
显式注入持有者 uid(检查/执行同源 resolve,immutable args copy);
新增回归测试(缺省→自己空间+uid 在响应+显式他 project 仍 fail-closed);
22 测试绿,scp+restart,公网复验读写落自己空间+probes.py FOUR-GREEN
