---
name: orgfuel-ORGM-hf-org-nautilus-compass--0daf9fa51a
description: "--- name: hf-org-nautilus-compass-20261007 description: "HF "
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGM-hf-org-nautilus-compass-
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

---
name: hf-org-nautilus-compass-20261007
description: "HF org 实际名=nautilus-compass(非 nautilus-org,404);全权限 token 双框各一份;10/8 死线件完成;org token 入库制式与 revoke 处置"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 44761907-86fe-49f8-b0ef-fc3ff9c0567b
  modified: 2026-10-06T16:39:32.264Z
fact_status: inferred
---

2026-10-07 凌晨(commit b7282eea):**HF org 授权(10/8 死线件)完成**。

- **org 实际名=nautilus-compass**(hf.co/nautilus-compass 200 实测;用户口语记的"nautilus-org"是 404 不存在——建 org 时 slug 自动落了 compass 尾)。后续所有 HF 引用/上传一律用 `nautilus-compass`,勿写成 nautilus-org。
- **token 双份制**:用户为 org 生成全权限 fineGrained token 两份,platform 对话框先同步一份,compass 一份;compass 侧入库=`~/.claude/.cache/compass_hf_org_token.env`(0600,变量 HF_TOKEN_ORG/HF_ORG);个人 token(chunxiaox)另存 `compass_hf_token.env`。凭据永不入仓不回显。
- **验证配方**:`curl 
