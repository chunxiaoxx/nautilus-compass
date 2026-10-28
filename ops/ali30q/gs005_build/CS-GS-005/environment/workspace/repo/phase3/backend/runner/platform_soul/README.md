# platform-soul webhook runner 入口(交付 FDE 部署)

FDE webhook 在 `v06_派活` 状态变化时 subprocess 调这两个脚本(bot-member 路线 · 2026-06-15 终版)。

## 两个入口
| 脚本 | webhook 触发 | 做什么 |
|---|---|---|
| `s2_auto_qc.py` | 状态→「已提交」 | 读 v06_派活 已提交行 → 自动 QC(线2 assembler / 线1 checklist)→ 写 verdict-bus + QC反馈/状态回写 |
| `s3_delivery_settlement.py` | 状态→「已通过」 | 读已通过行 → 组装买方格式入我 Dx2qb 机密交付 base + 结算记账 → 派活行→已交付 |

逻辑核 = `services/fde_qc_feedback*.py`(S2)+ `services/fde_delivery*.py`(S3),均 TDD green。入口只做 env→argv 薄包装,不重写。

## 部署前提
1. **services/ 包在 PYTHONPATH**(scp 整个 `phase3/backend/` 或至少 `services/` 树)。
2. **我引擎 app 凭据在 env**(`FEISHU_APP_ID=cli_aaa8e75d... / FEISHU_APP_SECRET=...`·不落仓·带外灌)。
3. **我引擎 bot `ou_af25f91ccc5cd9e39d120615006df974` 已被 FDE 授 RGDK editor**(否则写 RGDK 91403)。
4. **`PAIHUO_TABLE_ID`** = FDE 建好 v06_派活后给的 table_id。
5. **🔴 line2(教案)QC 依赖 assembler 模块**:`knowledge-tutorial-assembler/scripts/assemble_tutorial.py`(纯 stdlib·非 services 树内)必须随部署带上,并设 `FDE_TUTORIAL_ASSEMBLER=<部署路径>`(否则 line2 题 QC 抛 FileNotFoundError 进 failed 桶)。2026-06-16 实证:自包含目录漏带它 → 教案 QC 全 failed。
6. **业务线值 = 「2·教案」非「2」**:runner 用 `line_code()` 取「·」前编码路由(2026-06-16 修·否则教案误走 LLM checklist 路径)。

## env 清单
```
FEISHU_APP_ID / FEISHU_APP_SECRET     我引擎 app(cli_aaa8e75d·bot 授 RGDK editor)
PLATFORM_BASE=https://nautilus.social verdict-bus/dispatch
FDE_BASE_TOKEN=RGDKbrtZ1aMcEOsZ2GcczeFknNg   RGDK
PAIHUO_TABLE_ID=<FDE 建表后给>          v06_派活
DELIVER_APP_TOKEN=Dx2qb1fjhaJadSs0ZeMc0teVn49   我机密交付 base(默认已内置)
DELIVER_TABLE_ID=tblFkmEKTk4LIWJM       交付表(默认已内置)
SETTLE_TABLE_ID=tblFL7y3DejBQUvm        结算表(默认已内置)
DRY_RUN=1                               可选·只打印不写
```

## webhook_config.yaml 对接(FDE 侧)
```yaml
platform_soul_runner:
  base_token: RGDKbrtZ1aMcEOsZ2GcczeFknNg
  triggers:
    - {watch_table: v06_派活, watch_field: 状态, watch_value: 已提交, runner_cmd: ".../s2_auto_qc.py", runner_timeout_s: 300}
    - {watch_table: v06_派活, watch_field: 状态, watch_value: 已通过, runner_cmd: ".../s3_delivery_settlement.py", runner_timeout_s: 600}
```

## 验证(部署后)
```
DRY_RUN=1 PAIHUO_TABLE_ID=<tid> python3 s2_auto_qc.py   # 应列已提交行·不写
```

## 后续增强(非阻塞)
- S3 接 `services/fde_expert_rates.py`:读 RGDK v06_行业专家.工时单价 × v06_派活.工时 → 应付真算(现 8 TDD green·runner 未 wire)。
- 交付状态/应付镜像进 RGDK v06_交付总表(charter §E:正文留 Dx2qb·只镜像状态)。
