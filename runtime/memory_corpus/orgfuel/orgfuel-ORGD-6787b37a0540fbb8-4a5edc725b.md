---
name: orgfuel-ORGD-6787b37a0540fbb8-4a5edc725b
description: "[### 7.1 三层身份模型] - 隔离边界 = project 命名空间(`u_<id>_memory`);head"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-6787b37a0540fbb8
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[### 7.1 三层身份模型] - 隔离边界 = project 命名空间(`u_<id>_memory`);header-only 身份(X-User-ID 类)永久禁止——v0.9 曾有 X-User-ID 冒充洞(公网可冒充任意用户读写),已改 JWT-only 并五项矩阵验证;
- 自助 token 由 signup→console 自助签发,scopes 只含持有者自己的空间;缺省 project 显式注入持有者 uid(读写落自己空间,而非进程默认空间)——9/5 曾抓到"自助 token 读写全断+跨租户读"双洞,根因是检查侧与执行侧不同源 resolve,终修后公网复验 own-space 通过;
- ops token(tokens.json,`tools.*` 旧格式标志)为内部调度凭证,可见全量工具面;公网自助 token 只见 8 个用户工具(tools/list 17→8,内部工具知名字直调也 forbidden)。
