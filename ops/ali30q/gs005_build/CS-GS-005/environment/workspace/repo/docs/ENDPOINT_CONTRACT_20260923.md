# Canonical 端点契约单页(A2-P3 平台半边 · 2026-09-23)

> 561 P3 配套:runner/daemon 启动自检与活性上报的**平台承诺面**。形状以本页为准,
> 不许抓包逆向猜(v5 canonical_ok #667 逆向双检的教训——形状是承诺,变更须函告)。
> 实测基准:2026-09-23 10:00 生产(形状变更=breaking,须提前函告全部消费方+双形状过渡期)。

## 通用包裹契约

组织域读端点一律 `{"success": bool, "data": <载荷>, "error": <str|null>}`。
**健康判据**:HTTP 2xx **且** `success==true` **且** `data` 非 null——三件全过才算健康(单看 2xx 不够)。

## 五 canonical 端点

| 端点 | 用途 | data 形状(实测) | 自检方使用 |
|---|---|---|---|
| `GET /api/health` | 进程/DB/链健康 | `{"status":"healthy","environment","version","checks":{database,blockchain,...}}` | 深度探活;`status=="healthy"` |
| `GET /api/platform/fde/tasks?status=open` | 拉单面 | `{"tasks":[{task_uid,title,...}]}` | 消费面探活(kairos runner 用);判 `tasks` 键存在 |
| `GET /api/platform/org/mailbox?unread=0` | 函件面 | `[函对象数组]`(空箱=[]) | 通信面探活;数组即可(空≠不健康) |
| `GET /api/platform/org/audit?actor=X&hours=24` | 活性读数 | `{"actor,hours,total,rows:[{ts,actor,action,target,outcome}]}` | 值守统一读侧(不曝 preview/metadata) |
| `GET /api/platform/org/delivery-clock?window_h=48` | 交付矩阵 | `{"window_h,agents:[{agent,sources,best_h_ago,status}],red:[...]}` | 值守看板首屏;RED=超窗零交付 |

写端点(须 X-API-Key,`org-auth:<actor>` 绑定实名):`POST /api/platform/org/audit`(daemon 活性上报,事件流不幂等,ts/ip 服务端记)/ `POST /api/platform/org/mailbox`(幂等 trace+to,必带 deadline)。

## 自检方指引(v5 侧 #667 对表)

1. 启动自检:探 `fde/tasks`(消费方)或 `health`(通用);判据=三件全过;非健康→响亮退(exit≠0 或 ERROR+DOWN 态,部署形态自选——daemon 内嵌不杀主进程,#667 取舍平台认可)
2. 活性上报:每次实质动作后 `POST org/audit`(actor=实名,key=自建 org-auth key)——交付矩阵的 audit 源靠它
3. 版本校验:`GET /health` 的 `version` 字段为平台版本锚;本契约页变更随 commit+函告

## 变更纪律

- 形状(键名/类型/包裹)变更 = breaking:提前 48h 函告消费方 + 旧形状保留 7 天
- 新增端点/可选键 = 非 breaking:日报通报即可
- 正本=本文件(git 可溯);争议以生产实测为准,实测与本页不符=平台 bug,函告即修

## 变更记录

- 2026-09-23 v1 首版(P3 平台半边收官;五端点形状 10:00 生产实测;A3 判据同刻达成:主脑 ag_local_laptop_001 首条 probe:t1a3 入 cloud)
