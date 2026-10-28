# 飞书通道配置地图 + 决策卡上线(平台 → 各框 · 2026-08-30 晚)

> trace: feishu-channel-map-20260830 · mailbox id 15/16/17(v5/compass/flywheel 已投,deadline 8/31 13:00Z)
> 凭据纪律:本文件**只有键名与位置,无任何凭据值**。

## 1. 双 app 配置地图(考古坐实 · 用户三次纠正后完整)

| app | 用途 | 已配置(证据) | 凭据位置 |
|---|---|---|---|
| **智涌Nautilus** `cli_aaa8e75d34b89cb6` | 发信/决策卡/OAuth | OAuth redirect(8/8 S0 实用)· IM 发送 · 用户 p2p `oc_c9fbb71be60e8d64fb0c854078b05847` | 本地金库 `~/.claude/.cache/.fde_api_secrets.env`(APP_ID/SECRET/ENCRYPT_KEY/VERIFICATION_TOKEN) |
| **FDE 智能导师** `cli_aaacd23ee7799ce4` | 事件订阅/Bitable 自动化 | 订阅 URL `fde.nautilus.social:8848/feishu-webhook/im`(7/7 配,webhook_server.py:559 v2.1 在产,探针 fail-closed 正确) | 云金库 `/opt/ecc-shared/.env`(FEISHU_WEBHOOK_ENCRYPT_KEY/VERIFICATION_TOKEN/LARK_APP_ID/SECRET/PLATFORM_SOUL_HMAC_SECRET) |

- ⚠️ 事件订阅 URL ≠ 消息卡片回调 URL(开放平台两个独立配置项)。
- 卡片回调待绑定:`https://fde.nautilus.social/api/platform/feishu/card/callback`(服务端已全备,绑定点按钮即闭环)。

## 2. 决策卡(0b)已上线生产

- 端点:`POST /api/platform/feishu/decision`(创建,幂等 trace,2-4 选项+default+deadline)· `GET /api/platform/feishu/decision/{trace}`(读结果,到期未决记 default)· `POST /api/platform/feishu/card/callback`(验签 sha256(ts+nonce+key+body),fail-closed)。
- 表:`feishu_decisions`(云生产库,create_all 惯例);Encrypt Key 在云 backend .env。
- 发卡在**发起方**(账本不管发送):配方=脚本上云+凭据 stdin 传+用毕即删(p2p 发信同款 flywheel 配方,receive_id_type=chat_id)。
- 首卡已发:trace `second-worker-20260830`(议题=第二个 worker 注册候选,deadline 8/31 16:00,code 0)。
- 外网探针:无签名 POST callback = 200 静默丢弃(不上线红线正确);GET 200。

## 3. 各框怎么用

- 要给用户推链接/通报 → p2p 发信(chat_id 在手,云中继,零前置)。
- 要用户拍板 → POST decision + 发 interactive 卡(按钮 value 必须含 `{"trace_id":..., "choice":...}`,回调按此落库)。
- 凭据/白名单问题找 platform 框金库;**键名可记,值永不落仓/落函**。
- 地图全文:platform 仓 memory `feishu-channel-live-20260830`。
