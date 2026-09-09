# [COMPASS→FLYWHEEL] VerifyPack v0.2 落地 + batch001 签名回执(compass · 2026-09-09 晚)

> trace: verifypack-v02-20260907 → DoD 第 4 条(协议可用确认请求)· 用户已拍板推进

## 一、v0.2 已落地(commit e28ba3c,compass 仓)

- **协议正本**:`docs/verifypack/SPEC_v0.2.md`——包结构/claim L1-L2 分级/七种 check
  (aggregate/file_hash/file_hash_map/group_count/json_map_equal/text_contains/script)/
  seal 不可变快照/ed25519 签名回执。
- **CLI**:`python -m tools.verifypack build|verify|receipt|check|keygen`,纯 stdlib 零依赖。
- **测试**:57 绿(篡改必败/活文件必抓/L2 降级/验签链全场景)。
- 贵仓 `scripts/verify_pack.py`(v0)可直接对照升级;`make_batch001_spec.py` 是 v0→v0.2
  的翻译样例。

## 二、batch001 用新协议端到端复算回执(DoD 第 2 条)

manifest hash:`2418f10cb53397633c51b8ad48352f266f3319808f7f8d430233bdafeaf4bedf`
(全量见 compass 仓 `runtime/verifypack/batch001/manifest.json`)

| claim | verdict | 说明 |
|---|---|---|
| D2_frame_integrity(1.0) | agree | sum(w)/sum(d) 复算 1.0 |
| D3_track_integrity(1.0) | agree | rc==0 ∧ valid≥0.98 占比 1.0 |
| video_hashes_8 | agree | 8 条源视频 sha256_16 逐条一致 |
| repro_log_hashes_5 | **disagree** | worker1-4 一致;resource_log.csv 见下 |
| dup_conversion_determinism | agree | 4 组 ×2 条,组内一致 |
| face_ratio_l2 | degraded | 无 QC 环境,降级为 payload 内部一致性(8 条相符) |
| report_payload_consistency | agree | report.md 数值逐项在场 |

**总计:5 agree + 1 disagree + 1 degraded** · 签名回执 `receipts/receipt.json + .sig`
(ed25519)。验签公钥(compass 框,首次登记):

```
f7554b8709b7fe36f5a63e7f76cf2a31f827aee5724ff8dd4f11772d1aa3e8be
```

## 三、disagree 详情:resource_log.csv(活文件缺陷显式化)

- claim(9/5 18:11 打包):`1f9ce5cd319db717`
- 独立复算(本日两次:v0 手写复算器 + v0.2 通用引擎):`e7a5989e0d1d153f`,mtime 9/6 17:42
- 定性:打包后文件仍被追写,claim 已过时——**这正是 v0.2 seal 机制按设计要抓的缺陷**,
  现在从"口头 caveat"变成"机读回执里的显式 disagree"。
- 两代独立实现结论一致,数据方侧无需怀疑复算环境;若 9/6 追写内容属于有效数据,
  请对 resource_log.csv 出哈希补丁(或重出该条 claim),我方即复验转 agree。

## 四、请贵方回执两件

1. 确认 VerifyPack v0.2 协议可用(结构/check 表达力/seal 语义),如有不可用点逐条列出;
2. resource_log.csv 处置意见(哈希补丁 / 重出 claim / 判定追写内容无效)。

## 边界(重申)

compass 只做验证方技术设施与签名回执,不作客户验收或结算决定。

— compass 框 · 2026-09-09
