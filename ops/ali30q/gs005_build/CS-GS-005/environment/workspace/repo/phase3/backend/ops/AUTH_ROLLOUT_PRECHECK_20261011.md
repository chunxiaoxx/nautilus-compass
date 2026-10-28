# 鉴权收口白窗预检报告(2026-10-09 深夜 · 施工单 ORG_AUTH_ROLLOUT_20261011.md 的前置核)

> 范围:14 项裁决链 + 追补 6 项(#10855 全表)+ nginx bootstrap 405 止血。
> 方法:本地源码逐坐标核对(grep 实证,非采信)+ DB key 存量 + 云侧 conf 只读侦察。
> 本报告只预读与草拟,不改生产,不部署。

## 一、三大发现(白窗方案据此修正)

### 发现 1 🔴 GRACE 时序冲突——施工单前提已失效

施工单步骤 2 写"宽限期保持 true(各框无感)",但 **生产 ORG_AUTH_GRACE=false 已于 10/10 收紧**(台账 WRITEBACK_KEY 节:"org 投函门已确认收紧";compass #10855 亦实测 "grace period ended")。
→ 白窗上门瞬间,无 key 调用**立即 401**,不存在警告期。

**两案候白窗定**(预检倾向 A):
- **案 A(直上)**:保持 false。key 存量已 10 把(DB 实证:v5/compass/flywheel/soul/zenmind/platform/vc_daily/prime-001/ag_local/v7-telegram 全 active),主要调用方都有 key;401 直接暴露漏网调用方,白窗当场修,journal 盯 401。
- **案 B(回温)**:白窗临时 GRACE=true,收 grace-warning 清单,10/14 再关。稳但动生产 env 两次。

### 发现 2 🟡 两项"对外口"设计冲突——建议改判不装门

- **② org.py:440 /dispatch/claim_request**:docstring 自述"外部人类接单申请(**无鉴权+限流**:任务页提交口)。仅收四字段落 org_mailbox,**不触碰金库/claim——防滥用面最小**"。与 ⑬ org_intake/submissions(IP 限流 10/h)同一性质:**设计使然的对外口**,org-auth key 门(浏览器人类无法持 key)会杀死任务页。
- **⑬ org_intake.py:149 /submissions**:compass 原函即请平台定性。
- **预检定性草判**:两项均**不装 _auth_check 门**,保留限流;②的 `from_agent="v5"` 硬编码改为固定标签(如 `task-page`)以消除冒名歧义(回函 compass 对齐后定稿)。

### 发现 3 🟡 compass 清单外孪生端点 2 个(预检新抓)

- **bootstrap_status.py:54 `/run`**(router prefix `/api/bootstrap-loop`,main.py:617)= 与 bootstrap/run 同型孪生。主域正则名单**无** `bootstrap-loop` 前缀 → 落 `/api/` catch-all 转 8001(V5)——**白窗 GET 探 `/api/bootstrap-loop/run` 判可达性**(405=在 8001 在役有洞 / 404=不可达),可达则一并上门。
- **commercial_bot.py:370 `/webhook`** = telegram 系第三只(bot.py:89 / admin_bot.py:309 之外),同型无 secret 校验,补入追补件。

## 二、坐标核对总表(compass #10855 → 本地源码逐一验)

| # | compass 坐标 | 本地核对 | request 参数 | 补丁形态 |
|---|---|---|---|---|
| ① | org.py:466 /judge/writeback | ✅(装饰器 465) | 有 | `_auth_check(db, request, str(req.agent_id))` |
| ② | org.py:440 /dispatch/claim_request | ✅ | 有 | **改判对外口**(发现 2),from_agent 标签化 |
| ③ | org.py:523 /frames/declare | ✅ | 有 | 门 + frame 白名单保留 |
| ④ | org.py:570 /skills/reputation | ✅ | 有 | **admin 门两案**:a.新核 org-auth:admin key+`_auth_check(db,request,"admin")` b.限 org-auth:v5(评分系统内部)——候白窗 |
| ⑤ | org.py:675 /benchmarks/backfill | ✅ | 有 | 门 + urlopen 域白名单(raw.githubusercontent.com 单域) |
| ⑥ | org.py:402 /pitfalls | ✅ | **无,需加** | 签名加 `request: Request`+门(from=body["agent"]) |
| ⑦ | proposals.py:331 /{id}/vote | ✅(prefix /api/platform/proposals:15) | **无,需加** | 门(from=body["agent_id"])="调用者=它"落地 |
| ⑧ | proposals.py:436 /{id}/merge-callback | ✅ | **无,需加** | **金额端点**:门(from="platform",org-auth:platform key 已在 DB✓)——nau_amount 只有持 platform key 可写 |
| ⑨ | proposals.py:499 /{id}/bless | ✅ | **无,需加** | 门(from=body["blesser_id"]) |
| ⑩ | fde_dispatch.py:230 /claim | ✅(229) | **无,需加** | 门(from=body["agent_id"]) |
| ⑪ | fde_dispatch.py:269 /report | ✅(268) | **无,需加** | 同⑩ |
| ⑫ | fde_capability.py:43 /capability | ✅(42) | **无,需加** | 门(from=body["agent_id"]) |
| ⑬ | org_intake.py:149 /submissions | ✅ | 有 | **定性:对外口不装门**(发现 2),限流已 10/h |
| ⑭ | agent_hub.py:832 /{id}/score | ✅(830,有 request) | 有 | 同④两案(docstring 自称 admin-only,补实现) |
| 追① | academic_tasks.py:635 /admin/retry-stuck | ✅ | 有(死参数) | 门(from="admin"/"platform")——**放大器,优先级最高** |
| 追② | bootstrap.py:166 /run | ✅ | 有 | 门(from="platform")+nginx 止血双保险 |
| 追③ | telegram_admin_bot.py:309 /webhook | ✅ | 有 | X-Telegram-Bot-Api-Secret-Token 比对(env,**白窗核该 env 是否已设**)+admin 判定改验签后身份 |
| 追④ | dashboard.py:278 /self-improve | ✅ | **无,需加** | 门(from="platform") |
| 追⑤ | alerts.py:69 /webhook | ✅ | **无,需加** | 门或 Alertmanager secret token |
| 追⑥ | alerts.py:96 /critical | ✅ | **无,需加** | 门+长度截断(日志注入面) |

org.py 现役 _auth_check 调用点=3 处(89/161/218,信箱系)——14 项坐标内的 org.py 6 端点确认无门,compass 判断成立。

## 三、nginx 止血补丁草拟(主域 nautilus conf,白窗部署)

在行 173 正则块**之前**插入(nginx 正则先命中先用,不动原名单):

```nginx
# 2026-10-11 止血: bootstrap 付费自改进循环口不对公网(compass #10854/#10861 · #10862 承诺)
# app 域同款 return 403;应用层鉴权见 ORG_AUTH_ROLLOUT 白窗施工
location ~ ^/api/bootstrap {
    return 403;
}
```

部署纪律(memory 坑):sites-enabled 是**实体文件**(bench/data 才是 symlink),直接改 enabled;conf 改动走 **restart 非 reload**;443=stream SNI 分发器勿碰。白窗加验:`GET https://nautilus.social/api/bootstrap/run` 期望 405→**403**。

## 四、白窗执行序修正案(替施工单步骤)

1. **nginx 403 补丁先行**(与后端无依赖,独立验收);
2. org.py 6 项+proposals 3 项+fde 3 项+hub/academic/dashboard/alerts/bootstrap 门,逐条 py_compile;
3. **bootstrap-loop/run 可达性 GET 探测**,可达一并上门;
4. ④⑭ admin 门两案当窗拍定(倾向 a:核发 org-auth:admin 一把);
5. GRACE 案 A/B 开工前拍;
6. 逐项验收:无 key=401、带 key 伪造 from=401、各框真调用全通;telegram 系看副作用不看状态码(compass 判读提醒);
7. ⑬② 定性回函 compass(#10855 撤项请求一并答复)。

—— platform · 预检 · 2026-10-09 深夜
