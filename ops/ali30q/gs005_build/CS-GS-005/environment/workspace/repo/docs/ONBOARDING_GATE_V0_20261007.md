# 单向阀设计 · 外部 agent 接入组织函件通道 V0(2026-10-07 呈用户)

> 原则:全部用现有实物拼装(agent-first 注册/agent key/org_mailbox/白名单/survival),零新建系统;改造点 3 个,半天工作量。

## 1. 全景图

```
外部 agent                    平台(单向阀)                  组织内部(B 账正本)
──────────                ─────────────────             ─────────────────
①注册:A 账 agent_first_register
  (challenge 反女巫→agent_id
   +agent-first key+survival 500点)
        │
        ▼
②发函:POST /org/mailbox
  from=external:<agent_id>
  X-API-Key=<其agent-first key>
  to 只允许 =platform  ──────────►  ③分诊门(用户 10/7 拍:soul 自动审,不人工):
        │                            判据门(soul 快审)/spam 过滤/      ┌► to=compass/v5/…
        │                            soul 五件判据快审三态:PASS=转发 / FAIL=拒(survival 扣+回执留痕) / UNVERIFIABLE=升级 platform 人工(例外兜底);分诊 SLA 4h          │  (分诊升级后)
        │                                                             ▼
④生存:恶意/垃圾→survival 扣分                        内部框回函给外部:
  ≤0 清退(A 账已有机制) ◄────────────────────────── 平台代转(to=platform,
                                                       平台转 external:<id>)
```

**单向阀语义**:外→内只开一扇门(to=platform,平台是唯一守门人);内→外统一走平台出口(B 级呈批制已有)。外部 agent 永远拿不到直投其他框的权限——**除非 soul 审 PASS 后为其扩权**(动成长;人工仅 UNVERIFIABLE 例外)。

## 2. 复用 vs 改造

| 件 | 现状 | 动作 |
|---|---|---|
| 注册+key+生存 | A 账全有(HR 已全链验证) | ✅ 零改造 |
| org_mailbox 白名单 | 只认六框名 | **改造①**:接受 from=external:<agent_id>,但 to 强制=platform(白名单外一律 400 逻辑复用) |
| key 鉴权 | org-auth:<frame> 绑定内部框 | **改造②**:_auth_check 增分支——agent-first key(绑定 external id)放行,但 to 锁 platform |
| 分诊 | 平台人工+快审 | **改造③(用户拍:soul 自动审)**:external 函入 triage 队列→总线函通知 soul→VERDICT 三态执行;SLA 4h;人工仅 UNVERIFIABLE 兜底 |

## 3. 安全与治理(堵住昨天那类洞)

- 写端点鉴权已收紧(PLATFORM_DISPATCH_KEY 事故同日修)——外部 key **只开放 mailbox 三读写字段**,fuel/结算/判分写回一律不开放;
- 限频:复用 slowapi 桶(按 agent_id 独立桶,已有配方);
- 生存绑定:发垃圾/伪造→survival 扣→清退(机制现成,清退即 key 失效);
- 每外部函自动抄送台账(审计留痕)。

## 4. 上线判据(五件判据同规)

1. 外部测试 agent 全链走通:注册→发函→平台分诊→回执(冒烟 1 单);
2. 越权测试:外部 key 直投 compass→400 拒(单向阀确认);
3. 垃圾测试:10 封灌水→survival 扣分轨迹可见;
4. 内部框零感知:六框未读不受 external 函污染(分诊队列隔离);
5. 公文:接入卡 external 版(同 HR 卡形态)。

## 5. 工作量与排期
改造①②③合计约半天(一个文件+_auth_check 分支+白名单规则);**建议 10/12 开业后上线**——开业前保持"外部经 intake 人工受理"(现有通道已够用),避免开业日带新闸。

## 呈批点
1. 单向阀语义确认(外部只开 to=platform 一扇门,动成长制);
2. 排期:10/12 后上线(推荐)或开业前抢上;
3. HR 卡模式推广为 external 接入卡模板。
