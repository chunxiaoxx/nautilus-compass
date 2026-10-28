# 全站身份标准 V1(UNIFY 阶段 1 · 2026-10-10 · 各框接入规范)

> 目标:一个账号管全站。账号源=app users/identity(M1 两步码),唯一登录入口=app.nautilus.social/login。

## 一、登录流(标准)

1. 各站登录入口统一为跳转:
   `https://app.nautilus.social/login?redirect=<原站URL编码>`
2. 用户在 app 登录成功(邮箱两步码/钱包)→ app 写父域 cookie → `location.href = redirect`
3. 原站各受保护页/接口:读父域 cookie 中 JWT → 调 `GET https://nautilus.social/api/users/me`(带 Authorization: Bearer)验身份 → 200=已登录(返回身份 JSON);401=未登录→重走第 1 步

## 二、技术规范

| 项 | 值 |
|---|---|
| cookie 名 | `nt_token` |
| 域 | `.nautilus.social`(父域,全子域可见) |
| 内容 | JWT(issuer=app users M1) |
| 验证端点 | `GET /api/users/me`(Bearer)——200=有效,401=无效 |
| 登出 | `POST /api/users/logout` + 清 cookie |
| 回跳参数 | `?redirect=<encodeURIComponent(原站URL)>`;无 redirect 默认回 app |
| 安全 | HttpOnly 由 app 登录侧决定(SPA 需读则 document.cookie;推荐 addTokenIfExists 双轨);sameSite=Lax |

## 三、各框改造清单

| 框 | 对象 | 改造 |
|---|---|---|
| v5 | bench.nautilus.social/admin.html | 独立两步码页→重定向 app 登录;admin API 加 Bearer 验证 |
| flywheel | data.nautilus.social/console/login | 同上;console 后端验 JWT |
| compass | compass.nautilus.social | 定性:公开部分不加,需登录部分接同链 |
| 平台 | app 登录页 | 支持 ?redirect= 回跳(本标准发布即改) |

## 四、验收(阶段 1 里程碑,10/11 晚)

playwright:在 bench 登录→开 data console 刷新→已登录→开 compass 同态;登出全站同态退出。

—— platform · AUTH_STANDARD_V1 · 2026-10-10
