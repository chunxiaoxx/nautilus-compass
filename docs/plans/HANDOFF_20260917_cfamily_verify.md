# HANDOFF 2026-09-17 · C 族首批校准 verify + 旧格式 10 verdict 真复算(新鲜会话执行)

> 本档只给坐标与命令,**零预期读数**(占位句也不写)。
> 判据正本:docs/plans/2026-09-16-c-family-calib-preregistered.md(V1-V4 已冻)。
> 纪律:验证端不改 build 产物一字;发现数据问题走 disagree 不走改数;
> FAIL 处置见预注册档;复算红灯先证伪自己探针。

## 任务一 · C 族首批校准(V1-V4)

- **pack**:`C:\Users\chunx\Projects\nautilusflywheel\runtime\verifypack\c_family_calib_b1`
  (sealed,manifest 在;build 方=flywheel,验证方=compass)
- **claims 清单与 C 族定义**:入站函 `_INBOUND_FROM_FLYWHEEL_20260916_c_family_b1_built.md`
  (仓根;6 条 C0-C4b)
- **verify**:`python -m tools.verifypack verify <pack 路径> --verifier compass`
- **check / receipt**:`python -m tools.verifypack check|receipt`(密钥 `.verifypack/`,
  公钥 f7554b8709b7fe36f5a63e7f76cf2a31f827aee5724ff8dd4f11772d1aa3e8be)
- V1 逐条核对 pack.json 锚引用(只指向历史合格批,不引用未验证剩余池)
- 读数回填预注册档空白区 → 签名回执 → 函告 flywheel
  (POST 信箱,trace=`flywheel-c-family-b1-built-20260916`)

## 任务二 · 旧格式 10 verdict 真复算

- **坐标正本**:v5 函 id 280(10 task_uid + 五件套 ref/bug/test/src/evidence)
- **拉函**:`curl -s "https://nautilus.social/api/platform/org/mailbox?to=compass"`
  (按 id=280 找;DB 凭证运行时读 ~/.claude.json mcpServers.nautilus-db.env)
- 口径照 CATALOG_v0 三判据 + 三态(agree/disagree/not_computable);回函 v5 记账

## 同日背景(9/16 已完成,勿重做)

- 291 回函已发(id 298):评估器位接,四问逐答(工单级判据注册姿势/
  重测放 v5 侧/接口兼容确认/LEDGER 入库守 fact_status)
- CATALOG_v0 第 5 条 judge-systematic-inconsistency-v1 已注册(X1-v2 活例)
- ClawHub 1.0.1 审查状态待查(9/16 02:50 UTC 提交,约 9-12h 出);
  Glama 等用户 re-claim 后看构建是否吃到 4772a10

## 空白区(运行时回填,现在一个字不写)

- V1-V4 各条读数:______
- 10 verdict 逐条读数:______
- 两函回执 id:______
