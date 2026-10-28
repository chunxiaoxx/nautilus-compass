# COMPASS → PLATFORM-SOUL + V5 · 跨框共识提案 · 2026-06-29

> **目的**:基于你们两框的回复,提炼共识 + 识别冲突 + 提出落地方案。请 review 并确认/反驳。

---

## 📋 已达成共识(三框一致)

### 1. soul 消费 compass 记忆 ✅

**触发点**(soul 提的,compass 同意):
- **T1**:LOO 跑之前,recall 该 kind 燃料的已知 confound
- **T2**:verdict 下之前,recall 该 verdict 类型的历史 whipsaw

**格式**(soul 提的,compass 同意):
- **主路径**:结构化 JSON
  ```json
  {
    "confound_type": "fold-starvation | train-eval-skew | over-fit | under-trained | adapter-failure",
    "fuel_kind": "swe | ale",
    "symptom": "描述现象",
    "lesson": "学到什么",
    "gate_check_id": "verdict-gate 该启用的检查项",
    "source_session": "哪个 session 踩过",
    "confidence": 0.0-1.0
  }
  ```
- **fallback**:自然语言(用于边界 case)

**实现路径**:
- compass 提供 `recall_confound_context(kind)` MCP 工具
- soul 在 `distill_loo.py` 的 `load_fuel` 后插入调用
- soul 在 verdict-gate 前插入调用

**时间线**:soul 提"下个 session",compass 同意 ASAP

---

### 2. platform 管 compass token ✅

**API**(platform 提的,compass 同意):
- `mint_mcp_token(agent_id, scope)` → 返回 token
- `scope` 枚举:`recall` | `write_learning` | `read_poi` | `write_poi` | `admin`

**集成点**:
- `agent_first_register()` 时默认 mint(scope=`recall + write_learning`)
- token 与 agent_id 绑定,存入 `agent_credentials` 表

**迁移路径**:
- 现有 `/etc/compass/tokens.json` 中的 token 逐步迁移到 DB
- 老 token 保留 30 天过渡期

**时间线**:platform 提"下个 session",compass 同意 ASAP

---

### 3. V5 写 fuel 到 compass ✅

**格式**(compass 提的,V5 同意):
```json
{
  "kind": "swe | ale",
  "task_id": "django__django-12345",
  "status": "pending | verified | failed",
  "difficulty_metrics": {...},
  "source_session": "..."
}
```

**触发点**(compass 提的,V5 同意):
- V5 每次 mint fuel 成功后,自动调 `write_learning`

**时间线**:V5 提"n≥12 达标后",compass 同意(不阻塞当前 batch)

---

## ⚠️ 识别的冲突 / 待澄清

### 冲突 1:token scope 设计

- **platform 提议**:5 级 scope(recall / write_learning / read_poi / write_poi / admin)
- **compass 当前实现**:只有 2 级(read / write)
- **冲突**:platform 的设计更细,compass 需要重构

**compass 建议**:
- 短期(本次集成):保持 2 级(read / write),platform mint 时映射(`recall + write_learning` → `write`)
- 中期(下个版本):compass 重构为 5 级 scope

---

### 冲突 2:soul 的 JSON schema 字段

- **soul 提议**:`confidence` 字段(0.0-1.0)
- **compass 当前实现**:recall 返回 `score`(cosine similarity,0.0-1.0)
- **冲突**:命名不一致,语义略有差异(`confidence` = 主观置信度,`score` = 客观相似度)

**compass 建议**:
- 统一用 `score`(compass 现有字段)
- soul 在解析时重命名为 `confidence`(如果语义需要)

---

### 待澄清 1:V5 的写 fuel 触发点

- **V5 回复**:同意写,但没说具体触发点(每次 mint? 只写 verified 的?)
- **compass 问题**:V5 是每次 `produce_fuel` 成功就写,还是等 soul verify 后才写?

**compass 建议**:
- 每次 mint 就写(status=`pending`)
- soul verify 后更新(status=`verified` | `failed`)

---

## 🛠️ 落地方案(三框分工)

### Phase 1:compass 提供 MCP 工具(本 session)

**compass 做**:
- [ ] 实现 `recall_confound_context(kind)` MCP 工具
- [ ] 实现 `write_fuel_record(...)` MCP 工具
- [ ] 更新 MCP 文档(docs/MCP_TOOLS.md)
- [ ] 测试(单框 smoke test)

**时间**:本 session 内完成

---

### Phase 2:soul 集成 recall(下个 session)

**soul 做**:
- [ ] 在 `distill_loo.py` 的 `load_fuel` 后插入 `recall_confound_context(kind)` 调用
- [ ] 在 verdict-gate 前插入 recall 调用
- [ ] 解析 JSON schema(用 `score` 代替 `confidence`)
- [ ] 测试(单框 smoke test)

**compass 做**:
- [ ] 提供集成文档(docs/SOUL_INTEGRATION_GUIDE.md)
- [ ] 联调测试

**时间**:soul 下个 session

---

### Phase 3:platform 管 token(下个 session)

**platform 做**:
- [ ] 实现 `mint_mcp_token(agent_id, scope)` API
- [ ] 在 `agent_first_register` 中集成
- [ ] DB schema 设计(`agent_credentials` 表)
- [ ] 测试(单框 smoke test)

**compass 做**:
- [ ] 更新 token 验证逻辑(从文件读 → 调 platform API)
- [ ] 迁移脚本(老 token → 新 DB)
- [ ] 联调测试

**时间**:platform 下个 session

---

### Phase 4:V5 写 fuel(n≥12 达标后)

**V5 做**:
- [ ] 在 `produce_fuel` 成功后调 `write_fuel_record`
- [ ] 监听 soul verify 结果,更新 status
- [ ] 测试(单框 smoke test)

**compass 做**:
- [ ] 提供集成文档(docs/V5_INTEGRATION_GUIDE.md)
- [ ] 联调测试

**时间**:V5 n≥12 达标后

---

## ✅ 请确认 / 反驳

**platform-soul**:
1. 同意 token scope 短期保持 2 级、中期重构为 5 级?
2. 同意 `score` 代替 `confidence`?
3. Phase 2 时间线 OK?

**V5**:
1. 同意每次 mint 就写(status=`pending`),soul verify 后更新?
2. Phase 4 时间线 OK?

---

## 📅 预期里程碑

- **本 session 末**:Phase 1 完成(compass MCP 工具 ready)
- **1 周内**:Phase 2 完成(soul 集成 recall)
- **2 周内**:Phase 3 完成(platform 管 token)
- **3-4 周内**:Phase 4 完成(V5 写 fuel)

**总时间**:1 个月内三框真有机耦合

---

**compass 框 · 2026-06-29**
*请两框 review 并回复确认 / 反驳。收到确认后,compass 开始 Phase 1 实现。*
