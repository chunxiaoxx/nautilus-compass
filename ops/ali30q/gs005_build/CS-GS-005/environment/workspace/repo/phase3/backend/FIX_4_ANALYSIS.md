# Task 2.6 - P1 修复分析报告

**分析时间**: 2026-03-06 00:15
**执行人**: Dialog A (Development & Execution)

---

## ⚠️ Fix 4 分析：删除重复实现

### 发现问题

**utils/redis_cache.py (632行)** 被多处使用：
- api/auth.py: 9处使用 `get_redis_cache()`
- tests/test_wallet_auth.py: 使用
- utils/db_performance.py: 使用

### 风险评估

❌ **不能直接删除** - 会破坏现有功能

**原因**:
1. auth.py 中9个端点依赖 `get_redis_cache()`
2. 这是旧的缓存实现，与新的 cache.py 并存
3. 需要迁移策略，不能简单删除

### 建议方案

**方案A: 保留两套实现（短期）** ✅ 推荐
- 保留 utils/redis_cache.py 用于 auth.py
- 新功能使用 cache.py
- Week 3 统一迁移

**方案B: 立即迁移（风险高）** ❌ 不推荐
- 需要重写 auth.py 中9个端点
- 测试工作量大
- 可能引入新bug

**方案C: 适配器模式（中期）**
- 创建适配器让 get_redis_cache() 返回 cache.py 的实例
- 逐步迁移

---

## 决策

**跳过 Fix 4**，原因：
1. 不是真正的"重复"，是两套并存的实现
2. 删除会破坏现有功能
3. 需要更大范围的重构
4. 不影响 Task 2.6 的核心目标

**建议**:
- 在 Week 3 或后续任务中统一缓存实现
- 当前保持两套实现共存
- 添加文档说明两套缓存的使用场景

---

## ✅ 继续 Fix 5 和 Fix 6

**Fix 5: Cache Warming** (30分钟)
- 在 main.py 添加启动时缓存预热
- 预热常用数据（Agent列表、Task列表）

**Fix 6: Memory Limits** (30分钟)
- docker-compose.yml 配置 Redis 内存限制
- maxmemory 256mb + allkeys-lru

**预计完成时间**: 01:15

---

**执行人**: Dialog A
**状态**: 🟡 调整计划，继续 Fix 5-6
