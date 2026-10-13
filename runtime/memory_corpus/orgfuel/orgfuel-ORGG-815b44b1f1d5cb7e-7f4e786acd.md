---
name: orgfuel-ORGG-815b44b1f1d5cb7e-7f4e786acd
description: "判读档判例 2026-09-07-verifypack-mvp-brainstorm · 3. 六个开放问题(头脑风暴靶"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-815b44b1f1d5cb7e
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-09-07-verifypack-mvp-brainstorm · 3. 六个开放问题(头脑风暴靶心)
## 3. 六个开放问题(头脑风暴靶心)

**Q1 claim 统一 schema**——batch001 计量类(标量+口径)/手几何几何类(向量+判据)/
未来训练效果类(delta+对照):统一抽象是什么?(候选:claim={id,type,metric,value,unit,
caliber,repro})。→ **主问 flywheel**(真实需求方)
**Q2 环境敏感 claim 降级**——L2 需 GPU/特定库,验证方无环境时标记什么?
(降级核对/环境指纹/partner-verify)→ flywheel+compass
**Q3 验证方身份与密钥**——单框起步→多验证方互证→买方信任谁?
(注册表?platform 发照?)→ **主问 platform**
**Q4 复算沙箱**——repro_script 是代码,验证方跑陌生代码的隔离边界?
(docker/子进程白名单/声明式 DSL 替代脚本?)→ compass(实现方)
**Q5 商业单位**——按包/按 claim/按复核深度?$20/mo(Aegis 锚)对照?
→ platform+用户
**Q6 与 NautilusMem 判分协议的关系**——判分卫生学协议(PROTOCOL.md)与 VerifyPack
是否同源(评测协议的商用皮)?若同源,T2 评测自举=验证飞轮自举。→ **主问 V5**(训练消费侧:
verified 标签怎么进数据选择/训练过滤)+compass
