# compass → ALL · 2026-06-29 · 对话框同步 · verify 进行中 · MCP 共识已确认

> 用户要求同步各对话框最新进展。本文件汇总当前状态。

---

## 🎯 compass 当前工作(北极星)

**verify V5 候选 · 官方 harness 双 arm**
- 脚本: `/home/ubuntu/compass_verify_v5_candidates.py`(我写的)
- 候选: 5 道(swe_passk_glm_nondjango 3 + swe_passk_glm_noneasy 2)
- **STRONG arm 完成**: 2 resolved ✓, 3 unresolved ✗, 0 error
- **DOUBAO arm 进行中**: 20% (1/5), 1 error
- 预计: 10-15 分钟完成 DOUBAO arm
- 输出: `/home/ubuntu/swe_aclass_fuel_verified_<timestamp>.jsonl`(A-class = strong✓ doubao✗)

**下一步**: DOUBAO arm 完成 → 读 A-class 输出 → ping soul 跑 LOO

---

## 📡 V5 状态(从 outbound 读)

**✅ MCP 共识确认**
- 写 fuel 触发点: 每次 mint 就写(status=pending) · soul verify 后更新(verified/failed)
- Phase 4 时间线: n≥12 达标 + soul LOO 出 verdict 后启动 write_fuel_record 集成
- 理由: verdict 出前集成新机制 = 分叉(anchor #3 反 D 维护)

**球在 V5**:
- 候选产完就停(反 D · 别无限产)
- 等 compass verify 完成 ping

---

## 📡 platform-soul 状态(从 outbound 读)

**✅ MCP 共识确认 + 关键补充**
- 三确认点: token scope / score vs confidence / Phase 2 时间线
- 🔴 **关键补充**: Phase 1 缺"种子数据" · 否则 recall 是空架子
- 提议: platform-soul 提供 5 条结构化 confound JSON 作为初始 recall 语料

**5 条种子 confound**:
1. fold-starvation(ale): 4-fold 每折 9 道饿死 → valid0 · 误当能力缺失
2. train-eval-skew(ale): train 用 A instruction · eval 用 B → KILLED 假象
3. over-fit(swe): 易 django 套路化 · distilled 可能背模板假迁移
4. under-trained(ale): 3B train_loss 只到 0.22 · valid0 · 非模型大小没用
5. adapter-failure(ale): 4 次 KILLED 全 confound(adapter 没存/seq 截断/进程死)

**球在 platform-soul**:
- 等 compass Phase 1 MCP 工具完成 → 做种子 ingest
- 接 settlement 探针(已 ship · 你 refine)

---

## 📡 compass 状态(我)

**已完成**:
- ✅ Ship settlement probes to platform-soul(2 probe + 9 TDD + commit 17f165f)
- ✅ Verify V5 候选(STRONG arm 完成 · DOUBAO arm 进行中)

**进行中**:
- 🔄 Verify V5 候选(DOUBAO arm · 预计 10-15 分钟完成)

**待做**:
- ⏳ Output A-class and ping soul for LOO(等 verify 完成)
- ⏳ MCP tools Phase 0 design document(等 verdict 出)
- ⏳ Autodata mechanism design document(等 verdict 出)

**球在 compass**:
- 等 DOUBAO arm 完成 → 输出 A-class → ping soul

---

## 🎯 SSOT 护栏(守教训 · 6/29 用户拍)

1. n≥12 才跑 LOO(verdict-gate 拦 n<12 · 防 whipsaw)
2. 易 django PROVEN → 须非易料复证(排 over-fit 假迁移)
3. confound 先核再下结论
4. SSOT 钉死+广播四框(治精神分裂)
5. ship 了必验活

---

## 🔄 下一步协调

1. **compass**: 等 DOUBAO arm 完成 → 输出 A-class → ping soul
2. **soul**: 接 A-class · canonical 复核 · 归一化 · 借 GPU 跑 distill_loo --kind swe
3. **V5**: 候选产完就停 · 等 verdict
4. **platform-soul**: 等 compass Phase 1 MCP 工具完成 → 做种子 ingest

---

## 🅿️ Parking Lot(冻结 · 等 verdict 出)

- MCP tools Phase 1-4(等 verdict)
- Autodata 机制借鉴(等 verdict)
- 维②经济环(credit 口径/结算腿 liveness)
- FDE 切飞书多维表格

---

— compass · 2026-06-29(对话框同步 · verify 进行中 · 等 DOUBAO arm 完成 → ping soul)
