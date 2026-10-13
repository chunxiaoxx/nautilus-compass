---
name: orgfuel-ORGG-da79de46749d7aa6-28c19708fc
description: "判读档判例 2026-06-22-compass-v2.3.0-release · Task 5: 块 5 — 给 V5"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-da79de46749d7aa6
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-22-compass-v2.3.0-release · Task 5: 块 5 — 给 V5/soul 的写端契约文档
## Task 5: 块 5 — 给 V5/soul 的写端契约文档

**Files:**
- Create: `docs/contracts/2026-06-22-v5-soul-writeside-contract.md`

**内容**(compass 侧定义·V5/soul 后接·不阻塞发版):
- W1 写端:`write_learning(agent_id, task_family, reason, reward, bucket, score, source)` 已上线·请 V5 传全 verdict 元数据(当前只传 reason+reward)。
- P1 预备:结构化字段契约(triggers / env_fingerprint / confidence / when_not_to_use)——V5 产结构化经验的字段定义(见 Task 6 schema)。
- P2 预备:report 回流契约——B 用完回写 reward 到胶囊的端点形态。
- soul:verdict(reward/bucket/overall_pass)已成体系·只需被 W1 带上(已支持)。

**Step: Commit** — `git commit -m "docs(contract): V5/soul 写端契约(W1 元数据+P1/P2 预备字段)"`

**验收**:契约可被 V5/soul 直接 ACK,字段定义与 compass_fleet_memory 现有签名一致。

---
