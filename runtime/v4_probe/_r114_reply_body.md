# 回函 · #2925 V4 效用闭环探针判读交卷(+具身 QC 工件问询)

**to**: flywheel · **re**: #2925 · **from**: compass
**判读件**: `runtime/v4_probe/v4_probe_verdict_v2.json`(schema v2.1 compliant)
**判据 lock**: v4_probe_criteria.lock.json(2026-10-04 冻结,预注册先于出数——程序要件齐,判读方认可)

## 复算结论(判官独立)

- **逐行复算零偏差**:detail.jsonl 60 行计数 native 52/60=0.8667、d128 47/60=0.7833、d96 37/60=0.6167,与 report 逐一相符;drop128=0.0833、drop96=0.25。
- **探针自检三重过**:盲探 3/3(log 实读坐实)、native replay delta=0.0≤0.03 过门、金标分布 47T/13F 与 eval_set 同池一致(R112 已交叉)。
- **材料缺口如实记**:函报 runtime/v4_probe/ 下 report.json/detail.jsonl/probe.log 三件在 commit 2e0af3e 树内 404(同 gen4_v2 B 轨缺席模式)——判官实例侧 /root/vdd3/gen4_v2/ 取证(sha16:report 52f9e72c9001f077/detail f5efce52d8e7c8d3/log 2d4b1af40b5c518f/.v4_done e1464b772bbbc048),复算未受阻。**升级建议:探针产物随材料落仓**(连续两案同缺口,入惯例即闭)。

## 请裁两件 · 裁决

**1. V4-J1:PARTIAL 口径成立(0.0833∈[0.05,0.15),判据零放宽)。CI 权重按保守口径计**——除函申报的 60 对 CI±~9pp 外,判官补测同帧配对 McNemar exact:native vs d128 对错 9 帧/错对 4 帧,**p=0.267 不显著**。即"128px 造成实质效用损害"在现样本下不足以单独宣称(连配对检验都未过)。补测检验法未预注册,只作 caveat 权重证据不进判定(零放宽)。
正面证据一并如实并陈:损害形态=判别力渐失而非多数类塌缩(d128 预测 True 42/60、d96 24/60 单调渐降),非阶跃崩坏。

**2. J2(25pp@96px):不随本判升格宣称。**lock 明文 gradient evidence only 无判定权,预注册纪律=判官不代赋权。但梯度证据本身坐实:配对 McNemar p=0.011 显著+单调性+与 resolution 检(franka 128/pusht 96 双 WARN)互证。**明示口径**:J2 可作"方向性发现"并入首报探索段,标注 PARTIAL/扩样中、附 p=0.011 与互证链,但不得入结论宣称;"低分辨率损害下游效用"作为结论宣称须等扩样≥200 对按同 lock 门复测。若拟升格 J2 为判定判据,走判据演进程序(用户批+预注册+止损三要件,承案 7)。

## gap_report(EGR)

gap_layer=data:60 对样本量卡住效用维终判(PARTIAL 已是现判据可达上限)。suggested_fuel:①eval 池扩≥200 对(与 J1b 扩集同池复用,一池两判)②探针产物落仓③J2 升格走演进程序。confidence=measured。

---

## 附:具身线 QC 工件问询(主动)

R113 盯守见 pipe_art 下新工件未随函送判:`aloha_ins_qc_v0/`、`xarm_qc_v0/`(10/4 14:15-16)。franka_diving_v1/v2 与 resolution_check_v1 已确认作为 V4 互证材料在链。请示 aloha/xarm 两件性质:是否属判分线材料(如需 QC 判读,请按惯例送判函+判据 lock+材料锚);若为采集线内部 QC 非判读对象,知会一声即可,判官不越权抓判。
