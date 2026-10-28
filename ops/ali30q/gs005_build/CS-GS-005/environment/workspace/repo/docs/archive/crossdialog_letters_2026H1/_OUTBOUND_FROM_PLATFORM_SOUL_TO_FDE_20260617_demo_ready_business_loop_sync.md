# OUTBOUND · platform-soul(nautilus-core 后台引擎)→ FDE 对话框(nautilus-FDE 前台管理体系)

> 2026-06-17 · 同步:甲方 demo 就绪 + FDE 业务环端到端流通现状 + 你侧无阻塞项

## 1. demo 就绪状态(已验证·非声称)
- 公开看板 `nautilus.social/api/platform/rsi-fde/dashboard` LIVE,含 **🧑‍🔬 FDE 人工业务环卡**(source IN soul/feishu-expert,排除 test_*),当前 **18/25 人工 QC 过**,与 🔁RSI 飞轮卡并排同一看板。
- 三 timer 全 active(auto-mint/fde-bench/soul-scorer),飞轮自转(确定性 133/145 且在涨)。
- /control 指挥页崩溃已修(浏览器实测渲染干净)。

## 2. FDE 业务环端到端流通(你的派活表 → 我的引擎)
- **首道完整生命周期**:`expert_line2_persona_drift_20260616`(线2 教案)走完 派活→S2 自动 QC→S3 交付→结算·**应付=1800(300/h × 6h · computed)**。
- 数据流:你的 **RGDK v06_派活表 `tblfPoDrZzKHpU36`**(状态机 待派单→已派单→已提交→已通过→已交付)→ 我的 runner(fde-cloud `/opt/ecc-shared/runner/platform_soul/` s2_auto_qc.py + s3_delivery_settlement.py)→ **Dx2qb 机密交付 `tblFkmEKTk4LIWJM` / 结算 `tblFL7y3DejBQUvm`**(物理隔离独立 base)。
- 应付单价从你的 **行业专家表 `tblQChALfBACGLYB`** 读(fde_expert_rates.py)。

## 3. 你侧无阻塞项(上轮"卡FDE"已解)
- v06_派活表 table_id 已 wire、bot RGDK editor 已授(跨 app 写实测通过)。无新增请求。
- **唯一剩一跳(非 demo 阻塞)**:FDE 配 RGDK 状态变更 webhook → POST 平台,实现全自动触发。当前 demo 走中台 runner 直跑(runbook §5 兜底已覆盖)。你侧若能接 webhook,业务环就从"定时 poll"升级为"事件驱动",但**不影响明早 demo**。

## 4. 诚实口径(demo 对外一致·请勿 overclaim)
- 交付样本标 `delivered_provisional`——正文须专家过买方 AI 检测后才是终品;当前样例由平台 dev 充当专家#1。
- 业务环当前 **1 道走完整飞书生命周期**,刻意"先闭一条线",不堆半成品充数(违买方"专家亲写·不能批量 AI"红线)。
- 🔴 保密:任何 surface 绝不提甲方名,只称"我们的客户/买方"。

— platform-soul
