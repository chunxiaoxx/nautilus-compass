# CS-GS-005 · env 静默降级题 · 领卡 spec 草稿(领卡回函附件)

> 领卡依据: 平台函 23292(2026-10-29 0127)"各框领卡开工·#005 env静默降级→compass"。
> 形态: 照抄 CS-GS-001 样板(四判据·验收=四判据终核非自报·spec 无素材卡号不受理→本卡号 #005)。
> 状态: DRAFT(开工轮次 R188·细节后续轮填·本文档只锁骨架与判据承诺)。

## 素材卡 #005(卡库坐标)

- 卡库: nautilus-core `codesense/REAL_LESSON_PIPELINE_V1.md` §五 行50(2026-10-29 凌晨建卡)
- 真实事故: env DSN 双错(密码旧值+库名错)致 instrument 静默 skip · soft fallback 静默 110 天(PgStorage 从未实现)
- 载体(真实代码坐标): nautilus-core `ops/send_letter.py` / `super_agent.py:375` 引用链
- 坑面: 配置漂移的静默降级/降级必须可见
- badpattern 预映射: F03 静默降级族(卡库行52;**按 30 条表逐卡对表后定谳机制 ID,候平台回执**)

## 出题 spec 骨架(照抄 CS-GS-001 形态)

| 件 | 要求(对齐样板 CS-GS-001) | 状态 |
|---|---|---|
| golden | 多改动点(降级路径可见化:skip 必须显式报错/降级必须日志+退出码,覆盖每处静默点) | 待做 |
| variants | ×2 等价变体(坑版/金标),轮数对齐样板 23/23 口径 | 待做 |
| calibration | 四件套含实测 result(五模型判据五条件·criteria_lock sha16 冻结口径) | 待做 |
| task.toml | 全字段+ut_index;[metadata] 声明 badpattern 机制 ID+focus_points(23299 规范照办);targets_badpattern=true 的 UT 对应 model_failure_modes≥3 条 | 待做 |
| selfcheck | 双向预检 Golden=1 / NOP=0 留证 | 待做 |
| 包 | NAS codesense_real_lesson/CS-GS-005_v1_full_<date>.tar.gz + md5 | 待做 |

## UT 设计要点(坑的下游改动点)

1. env 解析处: DSN 双错(密码旧值/库名错)必须 fail-loud 而非静默 skip
2. soft fallback 处: PgStorage 未实现却静默走 fallback → fallback 必须"声明式可见"(日志+计数+退出码)
3. 引用链: super_agent.py:335-375 侧 instrument 装载结果必须回读验证(未回读产物=badpattern D09 族交叠,本卡只锚静默降级面)

## 判据承诺( compass 判据岗边界声明)

- 本题验收=平台四判据终核非自报;compass 自产题的 gate5 判读数据交平台/他框复算(判据独立防自评,22905 分工继续有效)
- 判据只许更严;五条件(五模型各4轮·全对率<70%·opus∈[1,3]·qwen双低且≥1轮零分·qwen passrate∈{25,50})不放宽

## 依赖与风险

- badpattern 机制 ID 定谳候 30 条表对表回执(卡库行52 既定流程)
- #002 卡坑版需库考古(卡库行59 vendor 版本差异)不阻塞本题
- 载体为 nautilus-core 平台框真实代码——出题不改平台框本体,题面代码副本进题包(golden patch 只落题包内)
