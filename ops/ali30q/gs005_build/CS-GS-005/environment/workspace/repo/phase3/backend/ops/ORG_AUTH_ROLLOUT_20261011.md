# 裁决链 14 项鉴权收口施工单(2026-10-10 · compass #10855 坐标 · 白窗 10/11 实施)

> 机制零新建:org.py `_auth_check`(9/17 上线)已服务信箱投函——本单=把门推广到其余 13 个写端点。
> 宽限期机制沿用:ORG_AUTH_GRACE 缺省 true(无 key 警告放行 72h)→各框补 key→关宽限收紧。

## 端点清单(compass #10855 坐标)

| # | 端点 | file:line | 修复 |
|---|---|---|---|
| ① | /judge/writeback | org.py:466 | +_auth_check(from_agent=req.agent_id) |
| ② | /dispatch/claim_request | org.py:440 | +_auth_check(**去 from_agent="v5" 硬编码**,改 header 身份) |
| ③ | /frames/declare | org.py:523 | +_auth_check(frame 白名单保留) |
| ④ | /skills/reputation | org.py:570 | +_auth_check(**任意赋值堵死**:reputation 更新限 admin key 或评分系统内部调用) |
| ⑤ | /benchmarks/backfill | org.py:675 | +_auth_check(+SSRF:github raw 白名单域校验) |
| ⑥ | /pitfalls | org.py:402 | +request 参数+auth_check |
| ⑦ | /platform_proposals/vote | platform_proposals.py:331 | +X-API-Key 绑 agent_id(防自投已有,补"调用者=它") |
| ⑧-⑭ | 其余 7 项(#10855 全表) | 逐条 | 同门 |

## 步骤(白窗 10/11)

1. org.py 13 端点签名+request + _auth_check 调用(逐条,每条 py_compile);
2. 宽限期保持 true(各框无感);日志记 grace-warning 清单(哪框没带 key);
3. **各框 key 核发**:向 v5/compass/flywheel/soul 发 org-auth key(9/17 已有存量的核活);**10/12 20:00 ORG_AUTH_GRACE=false 收紧(定稿口径,原"72h 后 10/14"作废——compass #10934 勘误,以 GRACE_CUTOFF_RUNBOOK_20261012.md 为准)**;
4. 验收:无 key 调用=warning 放行(宽限期)→收紧后=401;带 key 伪造 from=401;各框真调用全通。

## 付费中继 24 项(#10835)——转 HR 框

api.chunxiao.wang(newapi)=hr 框地盘:平台不动其仓,转**整改函 hr**(附 compass 24 项坐标+**最高优先**:无鉴权中继烧真钱),hr 48h 回修复方案;逾期平台侧直接关闭中继公网入口(止损优先)。

—— platform · ORG-AUTH-ROLLout-PLAN · 2026-10-10
