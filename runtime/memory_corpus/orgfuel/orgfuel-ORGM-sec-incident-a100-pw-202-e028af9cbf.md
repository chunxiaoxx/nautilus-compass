---
name: orgfuel-ORGM-sec-incident-a100-pw-202-e028af9cbf
description: "--- name: sec-incident-a100-pw-20261008 description: A100 ro"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGM-sec-incident-a100-pw-202
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

---
name: sec-incident-a100-pw-20261008
description: A100 root 密码 PUBLIC 仓泄漏 6 天事故闭环(机内 chpasswd 轮换=免控制台路径);push 冻结纪律与解冻判据;凭据入 .cache/a100_env
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 44761907-86fe-49f8-b0ef-fc3ff9c0567b
  modified: 2026-10-07T15:55:30.519Z
fact_status: inferred
---

2026-10-08 凌晨闭环(R312-R315,commit 62db81cb→82e5c932):README 更新途中抓出 **A100 root 密码在 PUBLIC 仓 40 文件泄漏 ~6 天**(自 919d06a9)。

**处置链(全实测)**:当前树脱敏 43 文件(→A100_PW_ENV 占位)→真凭据迁 `~/.claude/.cache/a100_env`(0600)→**机内 `echo root:新密|chpasswd` 轮换**(免控制台!隧道走密钥认证不受影响)→旧密作废=历史泄漏无害化→push 解冻(62 commit 常规推送,非 force)。B(filter-repo 历史清除)后经用户明示批准补做(R316):python -m git_filter_repo 全史替换+force push,远端/cloud 零残留,三层闭环(树脱敏+轮换+史清除)。

**Why**:用户"不要等靠要"——轮换不必等控制台,root 在手机内 chpasswd 即可;"死密无害"判据(js2 先例)让历史清除失去必要性,push
