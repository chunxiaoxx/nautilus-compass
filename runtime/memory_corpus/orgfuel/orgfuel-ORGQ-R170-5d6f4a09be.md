---
name: orgfuel-ORGQ-R170-5d6f4a09be
description: "### R170 追补 · 2026-10-05 10:2x-10:5x(用户拷问 Gmail 盲区+拍板 MVP 支点"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R170
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R170 追补 · 2026-10-05 10:2x-10:5x(用户拷问 Gmail 盲区+拍板 MVP 支点两件→SPEC+判例集全落地)
- **Gmail 盲区根因+修复(commit 2ecde644)**:根因=LOOP 指令清单从未含 Gmail,probe 四源不含它,严格执行清单=清单外盲区(9/10 后零覆盖);修复=probe.py 补第五源 probe_gmail(REST fallback 链 ~/.gmail-mcp token→oauth→API+基线增量防重报+营销过滤);坑两枚如实记——credentials.json 无 client_secret(在 client_secret.json installed 键下)/socks5h 形式 env 致 curl SSL rc35(显式 --proxy http://127.0.0.1:10808 修);首跑 10 封未读建基线+二跑 fresh=0 增量逻辑验过
- **Gmail 实查结论**:3 天内 9 封未读无外部待办(rsi-bench 通知=已回应那条+营销件);两处安全类提请用户自证(9/30 Windows 新登录+10/4 五仓 deploy key 13:56)
- **MVP 支点盘点**(用户拍"先找支点再固化放大"):系统化过筛=真支点两个(①验证协议=唯一外部实装资产 rsi-bench#3;②判例三单+勘误账=装订首物);诊断=**资源投放错位(最重投入在零消费判读器,被外部验证的协议层投入最轻)**
- **支点固化两件全落地(commit d0a73bb4)**:
  - **IVP 协议 SPEC v1**(docs/spec/VERIFICATION_PROTOCOL_SPEC_V1.md,sha16=`05e5d5b9ee532a60`):英
