# 10/8 晨部署窗 runbook(v4 单一版本 · SUPERSEDES v1/v2/v3 全部旧段)

> v4(06:0x,承 compass #10521 diff 三处全改):旧版三套批次序并存已删净,本文=唯一执行正本。
> 执行窗:08:00-09:00(compass 验收 09:00 就位)。全部批件已齐,窗内零裁定纯执行。
> 窗前状态(DB 01:00 实测):注资行 0 · dedup 负行 0 · 索引不存在 · ledger 8,165 行——①②③均未动,一切在动手前改净。

## 前置:云仓同步(批次①前)
- 云=nautilus-mvp 主仓(禁 soul-workspace);云工作树脏(main.py M+2 未跟踪)→`git stash -u → [同步] → git stash pop`(冲突即停)
- **[同步]双模式**:A 正常=`git pull origin soul-distill-deploy`(GitHub 已恢复,远端=c975e21b7+);**B 故障模式=**`git merge --ff-only eb0f5a872`**(对象已在云对象库,零网络依赖)
- 验证:云 HEAD=eb0f5a872+;fuel_settle.py 82-84 行=去重放全;reconcile_dedup.py 存在;两个 migration SQL 存在

## 六批次序(每步验证过才进下一步)

### ① 止血部署(fuel_settle 修复)
- 云拉后 timer 下轮 dry-run pending 降;回滚=git checkout 旧版 -- ops/fuel_settle.py

### ② 注资对平(批甲 v2)
- **口径甲(用户 10-08 裁定):`nau_balance := SUM(ledger)`,不插 ledger 行。金额 kairos +9,997 / nautilus-prime-001 +13 / platform +199 = 10,209**
- psql -f migrations_manual/20261008_capital_injection_batch_a.sql(v2 纯函数幂等,重跑同结果)
- 验证:三行 gap=0(kairos 10,057/prime-001 54,955/platform 224)+**capital_injection 行数=0**(>0=跑了旧 v1 口径,FAIL 勿手改)
- 回滚:反向 UPDATE 余额(资金写,须用户批)

### ③ 冲正 dry-run 验门 → apply(用户裁 C)
- 门=974/1,039/−30,613 三数精确命中(漂移按 apply 时点实数报,增量一并冲禁挑行);拒负闸在(reconcile_dedup.py:80+,冲后<0 即 ABORT)
- apply(a+ 双腿标记:负行+被冲正行重命名 .dedup+余额扣减,事务内)
- 验证:dry-run 复跑=0;逐 agent 余额回读(**kairos 5,237/v5 88/prime-001 30,022/9000018 601/caishen 22**,#10516/#10518 v2 终值);compass 验收 SQL 三道
- 回滚:.dedup 行定位 DELETE+正行重命名还原+反向 UPDATE 余额(资金写,须用户批)

### ④ 唯一索引 v5.1(用户批随窗)
- psql 执行 20261008_ledger_settle_unique_gate.sql(四排谓词;**未用 CONCURRENTLY**——1.8MB/8,165 行锁窗亚毫秒;文件无 BEGIN,psql -f 直跑;勿包外层事务)
- 验证:CREATE 成功+**V3d 查 indisvalid**(防 INVALID 假绿)+compass 验收 SELECT(分组同谓词 HAVING>1)期望 0(**索引谓词口径残留=71 组,a+ 后归 0**,#10514 更正,非 153)
- 回滚:DROP INDEX ledger_settle_unique_gate

### ⑤ bench nginx/TLS(DNS 已配,flywheel HTTPS 基线已修 #10511——执行前先核现状防双修)
- bash ops/deploy_bench_nginx_20261008.sh(80→acme.sh→443→三验);通后函 v5 挂 V2.2
- 回滚:sites-enabled 删配置(禁 .bak)

### ⑥ 9000024 DELETE(compass-evidence-auditor,HR 原批)
- 验证:agents 表无 9000024 行

## 收口
全窗回执(逐件读数)→函 compass 复读→台账+08:47 晨报(注资金额 10,209 vs 裁甲时呈数 30,735 显著披露:现 gap 实测口径)

## 纪律
- 资金写(②③apply/回滚)=门判据+用户批双前置;(c) 删行销毁凭证永不;(b) 不需要(a+ 已并入③)
- 部署类 push+restart+curl 三验
