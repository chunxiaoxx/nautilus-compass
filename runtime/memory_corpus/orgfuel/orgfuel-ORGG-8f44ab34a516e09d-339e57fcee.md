---
name: orgfuel-ORGG-8f44ab34a516e09d-339e57fcee
description: "判读档判例 LAUNCH_KIT_V1_20261009 · 一、判分 API 公告文(主站口径,中文) ## 一、判分"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-8f44ab34a516e09d
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 LAUNCH_KIT_V1_20261009 · 一、判分 API 公告文(主站口径,中文)
## 一、判分 API 公告文(主站口径,中文)

---

**Nautilus Compass 判分 API 开放 · 判读永久免费**

AI 评测结果谁说了算?我们给出第三种答案:不问厂商,不问社群,问**可复算的证据链**。

自 2026-10-12 起,Nautilus Compass 独立判卷机构面向公众开放:

**已上线能力(全部免费):**
- **判读状态 API**:`GET https://nautilus.social/api/judge_status?id=<card_id>`——每张判读卡的判定/证据链/流程时间线/判据 sha16,机器可读;
- **免费判读入口**:提交评测产物走 [intake](https://nautilus.social/intake.html)(L1 机器判读/L2 深度报告/L3 定制,SLA 明示);
- **判据预注册披露**:所有判据先冻结后判读([criteria](https://nautilus.social/criteria/)),sha 锚定不可事后改;
- **公开榜单**:首榜 Round1 已定版(A 26.7% / B 16.7%,判据+复算全锚);
- **判分模型**:NACRE judge v1 权重公开([HF nautilus-compass/nacre-judge-v1],三态 88.51%,fp16 部署纪律在档);
- **独立复算**:任何判定可请求第三方复算,复算免费。

**定价边界(一句话):判读永久免费;装订收费**——深度报告/判例集/协议植入,只做判后事。

**已走通的首例链路**:intake → 判据预注册 → 三态判读 → delivered
