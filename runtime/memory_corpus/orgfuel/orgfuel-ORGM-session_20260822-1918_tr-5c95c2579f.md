---
name: orgfuel-ORGM-session_20260822-1918_tr-5c95c2579f
description: "--- name: tribal-utf8-explicit description:  type: discovery"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGM-session_20260822-1918_tr
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

---
name: tribal-utf8-explicit
description: 
type: discovery
concept: pattern
drift: green
drift_signals: []
agent_type: custom
user_id: u_local
ingested_via: mcp
proof_of_recall: not_attempted
declaration_type: none
tier: working
decay_rate: 0.5
promote_after: 1_access
reinforce_count: 0
---

# tribal-utf8-explicit

## 上下文


## 内容
Windows 上 Python open() 写文件必须显式 encoding='utf-8',否则默认 GBK 乱码。这是通用工程常识,glm-5.3 已知(Gate B c2e 实测 control 通过,delta=0,无 headroom)。
