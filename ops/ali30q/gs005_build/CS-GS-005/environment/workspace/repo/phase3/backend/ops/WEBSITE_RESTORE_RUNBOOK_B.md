# website SPA 全量恢复 runbook(B 档 · 用户拍 2026-10-09)

> 对账矩阵见台账 10/9 轮;本文=25 缺口端点建设+构建+部署的可执行规格。执行者:平台(前后端皆平台仓,无 turf 问题)。

## 现状

- 源码:`phase3/website/`(React18+TS+Vite,220 文件,git HEAD 9/5)=**完整基线,无缺失**(用户问备份:git 即备份;台式机若有 9/5 后新版,开机后对照)
- 权威路由面:生产 418 条(cloud introspection /tmp/live_routes.json)
- 对账:121 组 SPA 调用 = 96 可直连 / **25 真缺**

## R2(10/9)

1. `npm install`+`npm run build` 过编译(错逐个修,只修编译不改逻辑)
2. auth 接线核对:SPA auth.ts 调 /api/auth/login|register|verify ↔ auth.py 在役三端点字段对齐(login POST 200 行/wallet-login 285/me 355/web3auth 696);**钱包登录零新建**
3. API base URL:SPA 打向同源 `/api`(nginx 已代理)——核 services/api 配置

## R3(10/10-11)· 25 缺口建设

### A. users router(新建 phase3/backend/api/users.py,12 端点,数据源全现成)

| 端点 | 映射 |
|---|---|
| GET /api/users/profile | auth.get_current_user → user 行(=auth/me 薄壳) |
| GET /api/users/stats | bounty 完成数+NAU 累计(platform_bounties+ledger by user↔agent 映射) |
| GET /api/users/leaderboard | platform_agents ORDER BY nau_balance DESC LIMIT 50 |
| GET /api/users/history | platform_bounties claimed_by=me + assay_submissions contact=me email |
| GET /api/users/{user_id} | 公开档(用户名/钱包/注册时间/公开统计) |
| GET /api/users/{user_id}/stats | 同 stats 按参 |
| POST /api/users/avatar | URL 制存 users 表 avatar_url 列(ALTER TABLE IF NOT EXISTS;禁文件上传,开业期) |
| POST /api/users/change-password | auth.py 密码列 UPDATE(读 auth.py 用户存储实现,同 hash) |
| DELETE /api/users/delete-account | 软删(is_active=false) |
| GET /api/users/me/summary | (SPA UserCenter 聚合页用,组合 profile+stats) |

用户存储注意:**先读 auth.py 的 User 模型表名与字段**(models 定义在 auth.py 头部或 utils),users.py 复用同一 Session/get_db/get_current_user 依赖,勿另立用户体系。

### B. auth 补端点(5,加进 auth.py 或新 auth_session.py)

| 端点 | 实现 |
|---|---|
| POST /api/auth/logout | 无状态 JWT:返回 ok(客户端清 token);可选 token 黑名单 v2 |
| POST /api/auth/refresh | 校旧 JWT 签发新(同 SECRET/过期 7d,与 M1 一致) |
| GET /api/auth/profile | =/me 薄壳(SPA 旧字段名兼容) |
| POST /api/auth/password-reset/request | 发码=复用 M1 request-code 通道 |
| POST /api/auth/password-reset/confirm | 验码+改密(hash 同 auth.py) |

### C. 列表/映射(8)

| 端点 | 实现 |
|---|---|
| GET /api/tasks?params | tasks_router 补列表(筛选 status/lane;读 platform_bounties) |
| GET /api/tasks/available | status=open 清单 |
| GET /api/tasks/my | claimed_by=me |
| GET /api/agents/my | agents_router 补(me→agent 映射,复用 /api/platform/agents 逻辑) |
| GET /api/platform/control-plane | 映射 admin/overview 聚合+control-plane 现役端点(ControlCenter 舰桥读数) |
| GET /api/platform/proposals | 改进提案 P1 队列(improvement_proposals 表在) |
| GET /api/survival/leaderboard | survival 面现役端点加 sort 参数 |
| /api/academic-tasks/pdf + /api/agent-market/bounties | ①pdf 端点建(读 FDE 产物路径)或页面降级;②bounties=DMAS browse 映射 |

## R4(10/11-12)部署

1. `npm run build` → dist/ 推云 `/var/www/app/`(新目录)
2. nginx:`app.nautilus.social` server 块+证书(acme.sh)+SPA fallback try_files→index.html+`/api` 反代 8000
3. 三验:外网 200+登录真跑(邮箱码+钱包)+Dashboard 读数渲染
4. 静态根门面不动,双轨一周;验收后呈用户拍切换

## 红线

- 登录/权限端点必 rate limit(auth.py limiter 同款)
- users 域禁越权(只读自己;公开档只吐公开字段)
- 全部端点 curl 三验;SPA 页面渲染验证转浏览器截图坐标
