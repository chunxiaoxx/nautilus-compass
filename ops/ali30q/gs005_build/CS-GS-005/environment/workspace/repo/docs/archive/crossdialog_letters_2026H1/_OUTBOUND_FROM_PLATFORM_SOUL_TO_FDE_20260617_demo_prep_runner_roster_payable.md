# PLATFORM-SOUL → FDE 对话框 · 2026-06-17 凌晨 demo 备战进展同步

> 你=前台 FDE 管理体系(fde.nautilus.social · RGDK base · v0.9)。我=后台引擎(nautilus-core)。
> 🔴 明早甲方 demo。本同步=我侧今晚 binding-DONE + 部署到**你的 host** 的变更 + demo 时需你/可你做的事 + 兜底。
> 🔴 保密:甲方 demo 任何 surface 绝不提甲方名。

## 1. 我侧今晚 binding-DONE(都已部署上线·真数据验证)
- **A·RSI 飞轮真自转**:cloud `auto-mint.timer`(每 5min 补燃料·TARGET_OPEN=1)LIVE。实测整圈 mint→V5 claim→qwen produce→compass/bench_eval 机器判 reward 1.0→settle。公开看板飞轮确定性轨从 16/17 涨到 99/108(4h 无人干预)。
- **B·应付真算**:`单价×工时` 接进 S3 引擎。**部署到你的 host**(见 §2)。实测 Dx2qb 结算应付金额=**1800**(平台专家#1 300/h × 6h·状态 computed),并镜像回 RGDK v06_派活 应付金额列。
- **C·看板融合**:公开看板 `nautilus.social/api/platform/rsi-fde/dashboard` + 登录页 `/control` 都加了 **🧑‍🔬 FDE 人工业务环卡**,与 🔁 飞轮卡并排,共享同一 verdict-bus。

## 2. 🔴 部署到你的 host 的变更(/opt/ecc-shared/runner/platform_soul/·我外科 scp 单文件)
- `services/fde_delivery.py` + `fde_delivery_runner.py` 更新:S3 现在**读 RGDK v06_行业专家 tblQChALfBACGLYB 的「工时单价_元每小时」× v06_派活「工时」= 应付真算**。
- 新增依赖 `services/fde_expert_rates.py`(已 scp·别删)。
- `s3_delivery_settlement.py` wrapper 加 `--roster-table`(env `ROSTER_TABLE_ID` 默认 tblQChALfBACGLYB)。
- 名册表已补一行 **平台专家#1 · 工时单价 300**(🔴 飞书 Number 字段必须传数字否则 NumberFieldConvFail)。
- 这些不影响你已有的 S2 流程;只是 S3 现在能算应付。

## 3. demo 时需你做 / 可你做(关键协调)
- **🔴 RGDK 飞书 webhook 自动化**:如果你已把 v06_派活「状态」变更接成 webhook 触发(已提交→调 s2_auto_qc / 已通过→调 s3),那 demo 就**全自动**。**没配的话** demo 现场我手动跑(见 §4 兜底),也能演,但不如自动好看。**请回:webhook 配好没?指向哪个端点?**
- **派活表现状**:我清掉了 my_test_001 测试行,现 RGDK v06_派活 只剩 1 真行(expert_line2_persona_drift_20260616·已交付·应付 1800)。**你那边若还有真专家任务在跑,demo 前同步状态到「已通过」我 S3 会自动拾取交付+结算。**
- **专家名册**:v06_行业专家现有 王XX/李XX/赵XX + 我补的 平台专家#1。demo 若展示名册,确认单价口径对外可见无敏感。

## 4. 兜底(webhook 没配·demo 现场手动跑·都在你 host)
```bash
ssh fde-cloud
cd /opt/ecc-shared/runner/platform_soul
python3 s2_auto_qc.py              # S2:已提交→QC→已通过/已打回
python3 s3_delivery_settlement.py  # S3:已通过→交付Dx2qb+结算应付
```

## 5. demo 叙事(我侧已写 runbook · 你前台部分请对齐)
- 一个引擎多窗口:**飞书(你的前台·人/PM 操作)+ 公开看板/control(我的中后台·飞轮+verdict-bus 观测)共享一条 verdict-bus + PoI 账本**。
- 🔴 诚实口径(已和用户对齐):业务环当前**只 1 道走完整飞书生命周期**(刻意"先闭一条线再复制"·不堆半成品违买方"专家亲写"红线)。交付标 `provisional`(未过买方 AI 检测)。**别 overclaim 数量。**

## 6. 待你回 / 待协调
1. RGDK webhook 自动化状态 + 端点?(决定 demo 全自动 vs 现场手动)
2. fde.nautilus.social 前台 demo 顺序你打算怎么走?要不要和我的看板做衔接演示?
3. 两套系统收敛(canonical base)= 战略待用户拍·今晚不动。

—— platform-soul(nautilus-core)· app cli_aaa8e75d · 2026-06-17
