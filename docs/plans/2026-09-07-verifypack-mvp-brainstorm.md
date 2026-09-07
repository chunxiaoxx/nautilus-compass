# VerifyPack MVP 跨框头脑风暴 · 正本草案(compass 起草 · 2026-09-07)

> trace: verifypack-mvp-brainstorm-20260907 · 性质:头脑风暴正本(各框对本文打靶)
> 上游:[2026-09-07-verifypack-v02.md](2026-09-07-verifypack-v02.md)(立项)·
> [2026-09-07-compass-roadmap.md](2026-09-07-compass-roadmap.md)(四层路线图)
> 参与框:flywheel(数据方)/V5(训练消费方)/platform(调度+计费基建)/compass(验证方+协议 owner)
> 用户=终拍。

## 1. MVP 一句话

**四命令闭环**:数据方 `build` 一命令生成自足验证包 → 验证方 `verify` 一命令复算 →
`receipt` 出 ed25519 签名回执 → 结算方 `check` 一命令验签采信。
**两个真实样本跑通即 MVP 成**:batch001(计量类 7 claims)+手几何(几何类 4 量)。

## 2. MVP 三角与角色

| 角色 | MVP 扮演者 | 命令 | 关心 |
|---|---|---|---|
| 数据方 | flywheel | build | 包便宜好生成,claims 不泄漏商业数据 |
| 验证方 | compass | verify / receipt | 复算可信,跑陌生脚本的隔离 |
| 结算方 | 暂=flywheel 自用→买方 | check | 验签快,不重算 |

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

## 4. 分工与回收规则

- 各框就 §3 六问回函(投 compass 仓根 `_INBOUND_FROM_<框名>_20260907_verifypack_mvp.md`),
  每问给立场+理由+反对意见,可只答主问;
- **deadline 2026-09-10 22:00 +0800**(发布后,与 #46 复算并行);
- **防剧场化判据**:每问 ≥2 框实质输入才进 spec 讨论,否则 compass 单方定稿并标注;
- compass 汇总→spec v0.2 定稿→用户终拍→#47 执行。

## 5. compass 首发立场(打靶用,可推翻)

- Q1:统一 claim schema 但 type 留扩展位,不追求一次穷尽;
- Q4:首版=声明式声明+只读脚本白名单(numpy/pandas 级),不上 docker(重);
- Q6:同源——VerifyPack=判分协议的数据版,T2 与验证飞轮合并叙事。
