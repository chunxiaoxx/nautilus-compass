# 金标答案

## 修复路径
1. `packages/nautilus_core/helix_chain.py` = 真实修复 defb148c6 原件(逐字,见
   `nautilus_core_helix_chain.py`),使桥接引用真实闭合(事故修复本体)。
2. `v5_bridge_golden/helix_bridge.py` = 降级显式化(GP-1..GP-4,见 change_points.yaml):
   结构化降级报告 / 消费侧前置防护 / 降级计数 / 后端标记如实。

## 三态自证(2026-10-29 实测,解释器 compass .venv python)
- 金标态(补件归位+金标 bridge):UT 3 passed,exit 0
- 坑版态(原样 repo):UT 3 failed,exit 1
- 反例双向成立(照 GS-001 selfcheck Golden=1/NOP=0 口径)

## 半边2 声明(如实)
env DSN 双错半边(密码旧值+库名错致 instrument 静默 skip)实物坐标候平台给精确坐标
(四仓考古零命中,定谳=环境层配置漂移无代码痕,R189 档);补齐前本卡坑面仅锚半边1
(soft fallback 静默),UT-3(骨架原计划配置校验条)未纳入 ut_index,不虚报覆盖。
