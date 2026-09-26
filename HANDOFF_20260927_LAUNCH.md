# HANDOFF — 9/27 BC1 发布日(新会话执行 · 用户批)

> 本会话(9/25-9/26 超长)按用户令退役,发布日由新会话执行本档。
> loop cron(:07)与 9/30 竞品终核(10:12)均 durable,新会话自动接管。

## 第一动作(09:00)

```bash
cd C:/Users/chunx/Projects/nautilus-compass
.venv/Scripts/python.exe scripts/bc1_launch_day.py all
```
判据不过即停(all 内置红灯止步);机械腿覆盖:链接检→README/墙页翻转
→push→scp 部署→外网回读→通报函(platform+vc_daily 已正名)。

## 人工两件(腿外)

1. **09:20 Discord 帖**:CDP 9224 Chrome 已开(P3 已验,勿关);用
   `python $LOCALAPPDATA/Temp/cdp_tool.py` 发 runtime/assay_bc1_20260927/
   DISCORD_LAUNCH_DRAFT.md 定稿;发后立即 `cdp_tool.py lastid` 存直链;
   坑:Slate Enter 必须带 text="\r"+发后查输入框残留循环重试
2. **09:30 中文稿(知乎,用户批)**:终稿=runtime/assay_bc1_20260927/
   BC1_LAUNCH_CN_DRAFT.md(P2 终核 GREEN+三臂对照段);知乎发布需用户
   账号——值班会话备好终稿+配图文末入口链接,交用户一键发;公众号
   做转载位(用户号)

## 值守(10:00-22:00)

Runbook docs/plans/BC1_LAUNCH_RUNBOOK_0927.md ⑥:Discord ≤2h 回复/
报名 issue ≤12h 发卷/首考生判分(verify_bc1+签名回执)。**首外部考生=
M1 级事件即刻通报**。

## 22:00 首日读数

`bc1_launch_day.py counters` 四计数器落 launch_day_report.md→
LOOP_STATE 记账。

## 已批未完成的用户侧件

投流开户(X+知乎知+,物料 docs/strategy/paid_promo_preregister_20260927.md
就绪,判据=可归因报名数,止损 ¥500/48h)。

## 今晚背景(9/26 定案)

命名=Assay(用户终裁);TypeSafe proof 复算立项档已立(9/28 开工);
τ-bench 判因勘误完毕(结果传达失败类);组织评测令 VB 死期 9/28
(深夜窗跑,接入包 v5 仓 customer-demo-ship-1 分支 docs/VB_ONBOARDING_
PACK_20260926.md)。
