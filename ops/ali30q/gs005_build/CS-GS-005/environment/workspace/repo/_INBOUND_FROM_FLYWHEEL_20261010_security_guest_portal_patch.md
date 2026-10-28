# _INBOUND_FROM_FLYWHEEL_20261010_security_guest_portal_patch(泄密止血 nginx/app 变更知会+白窗合流)

**发件**:flywheel · 2026-10-10 · **优先级 P1(涉及 10/13 nginx systemd 交接防覆盖)**

## 事由

10/10 午 flywheel 侧处置一起泄密事件(完整审计件:flywheel 仓 `docs/evidence/2026-10-10-泄密事件审计-guest门户免登录暴露内部文档库.md`,commit 16e4c0de),处置中**手改了 cloud nginx `/etc/nginx/sites-enabled/fde.nautilus.social`**——正是贵框 10/13"根域白名单化专项+nginx systemd 交接"的标的文件,按"改 nginx 先对表"纪律与防覆盖需要,专函知会。

## 泄密事件摘要

- 外部 agent 经 `/console/g/evidence/` **免登录**读到 flywheel 内部审查报告(港区方案投资口径等);暴露窗约 37-40 天(research 口自 8/30、evidence 口自 9/3)。
- 根因三层:①`/console/g/` 注释写"独立口令"但 nginx **从未配 auth_basic**;②9/16 Phase1 auth 退役时 `/console/g/` 与 `/console/research/` 两 location 的 auth_basic 被注释**未补替代门**;③flywheel app 层 guest 白名单误含 `/evidence /research` 内部库。
- 暴露面:flywheel docs/evidence 37 篇+docs/research 45 篇(内部判断/商务口径类;无凭据无原始数据)。

## 已落变更(全部实测复验)

1. **nginx**(fde.nautilus.social,conf 备份 cloud:/tmp/fde.bak.leakfix):
   - `location /console/g/` 恢复 `auth_basic` + `auth_basic_user_file /etc/nginx/.htpasswd-flywheel`(htpasswd 9/10 存在,未轮换)
   - `location /console/research/` 同上恢复
   - `nginx -t` 过 + reload 生效;复测三口子 401,对外静态口(/embodied 等)200 不受影响
2. **flywheel app 层**(console_app.py `_GUEST_ALLOW`,已部署 /opt/flywheel 并重启 flywheel-console):
   - guest 白名单收窄到 `/demo /map /verify /api/demo-live /favicon.ico`,删除 `/evidence /research /roadmap /metrics` 及两前缀放行
   - data 域 `/console/g/evidence/` 复测 403 拒绝页(0 敏感串)

## 请贵框(平台)接手的三件

1. **10/13 nginx 交接时保留上述两处 auth_basic**(或将两 location 并入白名单专项时按"旧门关+新门开"二元实测迁移);`sites-enabled` 实体文件直改的坑已知,本变更即实体直改。
2. **10/11 白窗(ORG_AUTH_ROLLOUT_20261011.md)合流**:本次暴露与贵框"根域白名单化"同根(auth 分散退役无对账);建议白窗清单加一项"全站免登录 2xx 路径枚举扫描"作为常态轮检(flywheel 侧已在本框周检立项,跨框共享清单可免重复)。
3. **htpasswd 轮换**:口令 9/10 生成至今,事件窗内口令防护对象已被爬,建议随交接轮换(用户侧拍板)。

## 候用户知悉

- 搜索引擎若已索引 fde 域名历史路径,删除申请需 Search Console(用户动作);抓取方缓存不可撤回,如实呈报。

—— flywheel · 2026-10-10
