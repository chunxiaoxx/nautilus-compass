# 全框协同对齐报告(2026-10-25 · 涡轮增压出题体系)

## 一、正本对齐(五框同一原文)
| 文档 | 载体 | 位置 |
|---|---|---|
| 甲方需求 1012 全文(20972字/45870B) | v5 仓 BUYER_SPEC_1012_FULL.txt + compass 仓 ALI_REQUIREMENTS_DOC_1012_FULL.md | 双仓同源 ✓ |
| 产线手册(PIPELINE_30Q) | v5 仓 codesense/docs/ | 单点正本 |
| 出厂门 13 门 V1 | platform 21367 + compass ops/ali30q/factory_gate.py | 双源 ✓ |
| R1-R7 需求正本 | compass 仓 ALI_REQUIREMENTS_SPEC_V1 | 单点正本 |
| 涡轮素材池 69 条 | compass 仓 s0_v2_turbo_pool.json | 单点正本 |

## 二、各框当前状态(2h 内实测)
| 框 | 做什么 | 产出 |
|---|---|---|
| v5 Mac | 判分七门+九类交付件+UT七律+退回清单+GAP分析 | 交付格式最终真相入仓 |
| v5 笔记本 | 晨报+CS-008R 重产(quota_gate 域) | 封包冲刺输入件 |
| core | 1012 正本入仓 | 文档同步 |
| flywheel | 点位校准配方v1 + D13/D14 施工 | 工装+施工件 |
| compass | 涡轮池 69 条+资格战判读门+适配器+出厂门脚本 | 判读层全线 |

## 三、避免重复造轮子(分工边界确认)
- 产线手册/scaffold/判分脚本 = v5 单点(compass 不重复造)
- 判读签名/出厂门/金标自检/审计 = compass 单点(v5 不重复造)
- 施工 = flywheel/core 按领题
- 素材通鉴/涡轮池/适配器 = compass 出,全框共用

## 四、无重复造轮子验证 [实测]
- compass 没有再造 PIPELINE_30Q(用 v5 的)
- v5 没有再造 factory_gate(用 compass 的)
- 笔记本晨报与 compass 晨报互补不重复
