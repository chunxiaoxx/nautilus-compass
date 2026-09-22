# DCR 支付链路+全网安全审查报告(2026-09-22)

> 范围:微信支付接入/密钥管理/公网暴露/GPU 实例/签名体系/官网页面。
> 方法:15 项逐条实测(非自报),每项给出判定与修复建议。

## 发现清单

### 🔴 高危(需修复)

| # | 问题 | 影响 | 修复建议 | 优先级 |
|---|---|---|---|---|
| H1 | **accounts 服务零鉴权**:CORS `Access-Control-Allow-Origin: *`,所有 API 无 token/无频率限制 | 任何人可:(a) 注册任意邮箱→占用 user_id;(b) 无限创建订单→垃圾订单/恶意占坑;(c) 轮询 `/api/orders` 列出所有用户的订单(含邮箱/金额);(d) 调用 `/api/usage` 注入假用量 | nginx 层加 API key 验证(如 `if ($http_x_api_key != $secret) { return 403; }`)或服务层加 Bearer token;CORS 限定 origin 为 compass.nautilus.social | **P0 立即** |
| H2 | **DCR 共享账号硬编码**:dcr_zh.html 中 user_id=550a91f6 公开可见 | 所有人共用同一账号下单,无法区分客户;恶意者可替他人下单 | 每次下单前为访客生成临时 user_id(session token)或引导 GitHub 下单为主通道 | P1 今天 |
| H3 | **/api/users 公网暴露**:GET /api/users 返回用户列表(含邮箱、手机号) | 信息泄露:任何人可拉取全量用户数据 | 加 admin_key 或移出公网;nginx deny /api/users | **P0 立即** |

### 🟡 中危(应修)

| # | 问题 | 影响 | 修复 |
|---|---|---|---|
| M1 | **/api/orders 可匿名查询**:任何 order_id 可查状态与金额 | 商业信息泄露(谁买了什么) | 加 admin_key 或限制为「仅查自己的订单」 |
| M2 | **微信回调无 IP 白名单**:依赖签名验证(正确),但无额外防护 | 回调端点可被探测(签名保护了实际操作) | 加 nginx allow/deny 微信支付回调 IP 段 |
| M3 | **GPU 实例 SSH 暴露公网**(端口 21232/26422,root 密码弱) | 暴力破解风险 | 改用密钥登录+fail2ban;密码已给过(写在聊天里),应视为已泄露 |

### 🟢 已确认安全(通过审查)

| # | 检查项 | 结果 |
|---|---|---|
| S1 | 微信支付证书/MCHID/APIv3 key 不在 git 仓内 | ✅ 仅在 cloud ~/nautilus-accounts/.env |
| S2 | .verifypack/compass.key(签名私钥)未被 git 追踪 | ✅ git ls-files = 0 |
| S3 | TypeSafe API key 未泄漏到仓内 | ✅ 仅在 ~/.claude/.cache/ |
| S4 | PyPI token 未泄漏 | ✅ 仅在 cache |
| S5 | 支付金额不可前端篡改 | ✅ 前端只传 plan 名,金额由服务端套餐表决定 |
| S6 | 订单确认需 admin_key | ✅ confirm_order_admin 验证 ADMIN_KEY |
| S7 | 微信回调验签实现 | ✅ decrypt_notify 用 APIv3 key 解密+验签 |
| S8 | 官网 5 个页面全部 200,无死链 | ✅ wall/trust_report/dcr/dcr_zh/playbook |
| S9 | CRLF 签名风险 | ✅ git 内 blob 为 LF,本地 verify 不受影响;但 CRLF=true 是已知坑(之前 NanoJev 案) |

## 立即修复清单(P0)

1. **nginx 限制 /api/users**:deny all(或 admin only)
2. **nginx 限制 /api/orders**:deny all(或 admin only)
3. **CORS 收窄**:仅允许 compass.nautilus.social
4. **DCR 下单改用 GitHub issue 为主通道**(微信支付按钮保留,但引导先开 issue 获取专属 user_id)

## 建议修复(P1 本周)

5. API key 中间件(nginx 或服务层)
6. 频率限制(至少 create_order 每 IP 5 次/分钟)
7. GPU 实例改密钥登录
