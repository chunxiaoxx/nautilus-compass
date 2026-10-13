---
name: orgfuel-ORGQ-R276-8b60255ff7
description: "### R276 · 2026-10-07 凌晨(HF org 授权落地:10/8 死线件完成) - **HF org "
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R276
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R276 · 2026-10-07 凌晨(HF org 授权落地:10/8 死线件完成)
- **HF org 实测定谳**:org 实际名=**nautilus-compass**(hf.co/nautilus-compass 200;nautilus-org 404 不存在——建 org 时 slug 落 compass 尾,如实记防后续误引);org token(全权限 fineGrained)双框各一份(platform 先同步,compass 侧已入库 ~/.claude/.cache/compass_hf_org_token.env 0600 并 whoami 验证)。个人 token(chunxiaox)另存。
- **台账判据⑥ HF org 授权(10/8)=完成**:org 建+双框授权+入库验证三步全落;10/12 开业件:判分器模型卡+caliber-bench 样例包挂 nautilus-compass org(综合判分器 README 上 org 面=对外 HF 门面)。
- 安全:两 token 永不入仓不回显;全权限 token 若泄漏处置=HF 设置页即时 revoke(记档)。
