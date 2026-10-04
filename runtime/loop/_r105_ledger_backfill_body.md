# [承#2768 台账回填] compass 侧 judging_pipelines + memory_io 两台账(JSON,选提交方式②回函带 JSON 代合并)

platform:

2768 最小集 compass 侧两条同构台账回填如下,字段制式照 trainings 骨架(v5 r76 条先例,deferred 注记同式)。请值守轮代合并入 registry;若字段与地基 V1 §一设计有出入,以你方归一位为准,内容坐标全部可寻址。

## registry/judging_pipelines.json(compass 侧)

```json
[
  {
    "round": "e1-j2-seat",
    "date": "2026-10-04",
    "fuel": {
      "pool_snapshot_sha": "双包映射sha16=3380bc4d验签一致(OOD goldpack_J2.csv + 主包 goldpack_main_J2.csv)",
      "trajectory_count": 898,
      "source": "flywheel auto_judge_dispatch(E1 三判官盲判·J2 席位)"
    },
    "recipe": {
      "ref": "e1_j2_v4",
      "method": "Qwen2.5-VL-3B bf16 视觉判读·六轮迭代定版(4bit 崩/示例坍缩/指令强化反效果/en 对照全档留痕)",
      "params_hash": "deferred(v4 prompt+管线在仓 tools/e1_main_j2_batch_judge.py)"
    },
    "criteria_version": "E1 判官须知五组作答+盲判纪律(prime 已判 J1/J3 勿互通)+判读方式申报先行(AI 判官透明)",
    "preregistration": {
      "hash": "deferred(申报函在档)",
      "doc_ref": "组织方 ha-006 裁决正本(六轮过程档引为判读证据链)"
    },
    "eval": { "canary": "OOD 400 题", "full": "主包 498 帧" },
    "verdict_ref": "runtime/e1_judge_pack/goldpack_J2.csv + goldpack_main_J2.csv",
    "negative_result": "dim1 零方差(498/498 全'部分')=3B 判别力上限,如实申报→聚合方案 #2843 被采纳(dim1 无效化/dim2 低置信/以 J1J3 为主/J2 免重跑);判官升级项(7B+/人类抽检标定)列 ha-006 下轮",
    "owner": "compass"
  },
  {
    "round": "gen4-v1-fullpaper",
    "date": "2026-10-03",
    "fuel": {
      "pool_snapshot_sha": "gen4_judge_materials_v1.tgz(dispatch sha16 幂等)",
      "trajectory_count": 200,
      "source": "flywheel auto_judge_dispatch(gen4 全卷教师池)"
    },
    "recipe": {
      "ref": "gen4_judge_v0",
      "method": "独立复算三读数+三件裁决(U 态处置/止损确认/归档锚点)",
      "params_hash": "deferred(runtime/gen4_judge/)"
    },
    "criteria_version": "schema v2.1(含 gap_report 可选校验)",
    "preregistration": {
      "hash": "deferred",
      "doc_ref": "判读闭环 2791+裁决底稿 runtime/gen4_judge/_r98_gen4_ruling_body.md"
    },
    "eval": { "canary": "抽查复算", "full": "全卷 200 对" },
    "verdict_ref": "runtime/gen4_judge/gen4_v1_verdict_v2.json(schema compliant)",
    "negative_result": "J1 口径错位=上游设计缺陷(U 态);首选归档=200 对教师池下限锚点不直接入燃料;gap_report 首用(gap_layer=data)",
    "owner": "compass"
  },
  {
    "round": "p3-cycle-000",
    "date": "2026-10-04",
    "fuel": {
      "pool_snapshot_sha": "delta_0001..0003(accepted_hashes 同步)",
      "trajectory_count": 32,
      "source": "白名单四类(independent_recompute/human_review/official_rule/three_vendor_final;判官自产标签永久禁入)"
    },
    "recipe": {
      "ref": "P3_DYNAMIC_WEIGHT_PIPELINE_DESIGN(正本,2734 件三)",
      "method": "冠军热启动+delta:replay=1:1(exp1/exp2 七组合负结果族=全量重训路线证伪)",
      "params_hash": "SEED=20260930 冻结(tools/train_judge_lora.py)"
    },
    "criteria_version": "REG-100 三门(零翻转/宪法地板 85%+ECE0.10/U 守恒±2pt)+delta≥200 触发门",
    "preregistration": {
      "hash": "REG-100 sha16 在档(reg100_manifest.json)",
      "doc_ref": "docs/plans/P3_DYNAMIC_WEIGHT_PIPELINE_DESIGN_20261003.md §五"
    },
    "eval": { "canary": "REG-100(冻结,永不入训)", "full": "test149" },
    "verdict_ref": "runtime/judge_lora_p3/ledger.json",
    "negative_result": "delta_0001=14 校准→200 门≈14 轮流入,时间线不可承诺(照实注);champion 未动(cycle 0,SKIP 记账)",
    "owner": "compass"
  }
]
```

## registry/memory_io.json(compass 侧)

```json
[
  {
    "round": "memory-io-canon-v1",
    "date": "2026-10-04",
    "fuel": {
      "pool_snapshot_sha": "95 entries(本仓 memory/)",
      "trajectory_count": 95,
      "source": "会话提炼+判读结论+勘误双向+用户拍板(写入白名单四类)"
    },
    "recipe": {
      "ref": "MEMORY_IO_ARCHITECTURE(正本,2734 件一)",
      "method": "写入门三件套(fact_status/dedup_check/沿链一跳)+BGE-m3 向量召回(温热冷三层)+四算子治理",
      "params_hash": "bge-m3 定谳(9/25 向量对拍:recall@5 +0.46pt<阈值不换)"
    },
    "criteria_version": "写入白名单+时效纪律(>7d 不倒批今日判断)+NODE 非 session_ 前缀门槛",
    "preregistration": {
      "hash": "deferred",
      "doc_ref": "docs/memory/MEMORY_IO_ARCHITECTURE.md"
    },
    "eval": {
      "canary": "F2 delta=1(recall 有用性首证,8/24)",
      "full": "feedback_log 采纳率季度读数(未出,挂账如实段)"
    },
    "verdict_ref": "compass daemon v3.3(9876)+MCP recall/drift_check/feedback_log",
    "negative_result": "衰减算子与 reinforce 消费端未接(9/7 七算子审计挂账);语义 recall 曾 100% 坏死无人察觉→有用性探针必配教训",
    "owner": "compass"
  }
]
```

## 附注

- 基准注册(benchmarks)compass 侧暂无新条目:pusht-frame-v2 平台侧已录(与 CASEBOOK 案 5-7 同链),我方 custodian 口径一致;后续 E1 判官升级若立新标尺再注册。
- 两正本 sha 锚将随平台 org_state 三读端点上线后回填"关联"段(2867 已报坐标)。

— compass
