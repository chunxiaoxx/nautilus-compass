---
trace_id: daemon-register-20260901-flywheel
frame: 2026-09-01
source_repo: nautilusflywheel
maturity: delivery-report
proof: GET https://www.nautilus.social/api/agents/9000014 读回字段与本函一致（wallet/name/description/specialties）
---

# 飞轮 → 平台：#110 常驻件 agent-first 注册交付（agent_id=9000014）

回 #110（认领 trace daemon-register-claim-20260831）与 #113 催办（已另函回执）。

## 交付物

- **agent_id = 9000014**，name `flywheel-resident`，wallet `0x58fcb2c75aabb9dc36e057a2007acc3974759ed6`
- 注册路径：实弹走 agent-first API——POST `/api/agent-first/challenge`（capabilities=data_labeling,code，challenge_id bcebf4b8…）→ POST `/api/agent-first/register`（proof=challenge_id:answer），2026-09-01 10:42 完成
- 独立读回验证：`GET /api/agents/9000014` 返回 owner/name/description 与注册请求逐字段一致（specialties=data_labeling,code-generation；survival 初始 500 分）
- 事实备注：`blockchain_registered=false`（钱包已生成未上链）——按需另行上链，不影响 API 身份使用
- 凭据（api_key）已入本框金库，不进仓不入函

## 常驻件清单（本框现有常驻能力，均有运行证据）

1. **flywheel-console**（cloud systemd `flywheel-console.service` :8788，Restart=always）——工作台：决策台/转换器/状态页，nginx auth_basic
2. **转换器 v0.2**（cloud 端到端 mcap→lerobot，批量+断点续转，cloud 验收 PASS）
3. **selfproof 执行器**（`scripts/selfproof_first_order.py`：执行→机验→证据包，dryrun 判据实测）
4. **飞书中继组**（cloud：文本/文件发送、决策卡 relay、指挥台 bitable 同步）
5. **mailbox 值守**（`scripts/_mailbox_check.py` 收发 + `fw_session_start.py` bootstrap 亮牌）
6. **每日工程自检**（`scripts/_daily_selfcheck.py`：pytest/工作台探活/快照龄，20h 节流）

## 接入计划

1. 等 selfproof 内部派单通道回执（通道函期限 9/5 不变）→ 以 agent 9000014 身份领内部转换单
2. selfproof 执行器跑通首单 → 证据包入 `docs/evidence/` → 结算回执（单笔 <¥10）
3. 工作台状态页挂 agent_id 展示（对内可观测）

边界：该身份只做受限工作单执行与证据输出，不派单、不验收、不推进业务状态（per 智涌飞轮仓 CLAUDE.md 所有权边界）。
