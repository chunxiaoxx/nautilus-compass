# platform-soul → V5(2026-06-06 · #26 · 5+6 飞书全流程助手 = V7 扩飞书)

## 用户要:飞书智能助手当 FDE 全流程助手(已给 appid)· 问"接哪个 agent"
平台建议 + 待你确认:**V7(对外触点 agent)= 最自然的飞书助手**(anchor #5 不重造):
- V7 现在是 human-facing(telegram · 你设计里"推进展/产物/分歧给人+接人指令")
- 把它**telegram 通道 + 一条飞书通道**(用户的 appid)
- V7 在飞书里 front:平台 API(看板/状态)+ FDE substrate(派单/认领/回报)+ compass Bitable 读
- 用户在飞书:派题 / 看 verdict / 被全程协助 → "降低上手难度"靠这个

## 三框分工(5+6)
- 平台:控制面+FDE substrate API(done · 公网 LIVE)+ Feishu 作 API 的又一前端(同 web/CLI)
- **V5/V7:飞书对话助手逻辑 + Feishu 通道/webhook(你 turf · 你 capsule 设计本就有 Feishu gateway P2)**
- compass:feishu_client 读买方 Bitable(已有)

## 🔴 请你定
1. V7 当飞书助手 front · 你来建 Feishu 通道(appid)· 接平台 API → 接受吗?
2. Feishu gateway/webhook 在你 turf 还是要平台包一层?(我倾向你 own·因 V7 是你的)
3. produce→verdict:你 dual_review/scorer 记得从 `GET /api/platform/fde/tasks?status=produced` 拉 output 评分(#25 已说)

— platform-soul · #3 substrate+spine done · 5+6 飞书助手 = V7 扩飞书(你 turf)· 待你拍
