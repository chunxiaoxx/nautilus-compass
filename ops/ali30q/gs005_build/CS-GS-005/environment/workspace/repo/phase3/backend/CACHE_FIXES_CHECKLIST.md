# Redis Cache Implementation - Fix Checklist

**Date**: 2026-03-05
**Task**: Task 2.6 - Redis Cache Layer Fixes
**Review Score**: 7.5/10 → Target: 9.0/10

---

## Quick Summary

**Total Fixes**: 9 issues
**Time Required**: 6.5 hours
- P0 (Critical): 30 minutes ⚡
- P1 (High): 2 hours
- P2 (Medium): 4 hours

---

## CRITICAL Fixes (P0 - 30 minutes)

### Fix 1: Replace redis.keys() with SCAN ⚡
- **File**: cache.py:88-106
- **Time**: 15 minutes
- **Status**: ⬜ Not Started

Replace blocking operation with non-blocking SCAN.

### Fix 2: Replace print() with logger ⚡
- **File**: cache.py (5 locations)
- **Time**: 5 minutes
- **Status**: ⬜ Not Started

Replace all print() statements with logger.error().

### Fix 3: Add Cache Invalidation ⚡
- **File**: api/agents.py:189,210
- **Time**: 10 minutes
- **Status**: ⬜ Not Started

Add invalidate_agent_cache() after agent updates.

---

## HIGH Priority Fixes (P1 - 2 hours)

### Fix 4: Remove Duplicate Implementation
- **File**: utils/redis_cache.py
- **Time**: 1 hour
- **Status**: ⬜ Not Started

Delete unused utils/redis_cache.py (632 lines).

### Fix 5: Add Cache Warming
- **File**: main.py
- **Time**: 30 minutes
- **Status**: ⬜ Not Started

Warm cache on startup to prevent cold cache issues.

### Fix 6: Configure Memory Limits
- **File**: docker-compose.yml
- **Time**: 30 minutes
- **Status**: ⬜ Not Started

Set maxmemory 256mb and allkeys-lru policy.

---

## MEDIUM Priority Fixes (P2 - 4 hours)

### Fix 7: Improve Exception Handling
- **Time**: 1 hour
- **Status**: ⬜ Not Started

### Fix 8: Add Comprehensive Metrics
- **Time**: 1 hour
- **Status**: ⬜ Not Started

### Fix 9: Write Unit Tests
- **Time**: 2 hours
- **Status**: ⬜ Not Started

---

## Detailed Implementation

### Fix 1: Replace redis.keys() with SCAN

**Current Code** (cache.py:88-106):
```python
def invalidate_cache(pattern: str):
    try:
        keys = redis_client.keys(pattern)  # BLOCKS Redis!
        if keys:
            redis_client.delete(*keys)
          return len(keys)
        return 0
    except Exception as e:
        print(f"Cache invalidate error: {e}")
    return 0
```

**Fixed Code**:
```python
def invalidate_cache(pattern: str):
    """Clear cache keys using SCAN (non-blocking)."""
    try:
        cursor = 0
        keys_to_delete = []

    while True:
        cursor, keys = redis_client.scan(cursor, match=pattern, count=100)
          if keys:
         keys_to_delete.extend(keys)
       if cursor == 0:
       break

        deleted_count = 0
        if keys_to_delete:
      for i in range(0, len(keys_to_delete), 100):
         batch = keys_to_delete[i:i+100]
         deleted_count += redis_client.delete(*batch)

        if deleted_count > 0:
            logger.info(f"Invalidated {deleted_count} keys matching '{pattern}'")

        return deleted_count
    except Exception as e:
      from monitoring.metrics import cache_errors
        cache_errors.labels(operation='invalidate').inc()
        logger.error(f"Cache invalidate error: {e}")
        return 0
```

---

### Fix 2: Replace print() with logger

**5 Locations to Fix**:
```python
# Line 66
logger.error(f"Cache get error: {e}")

# Line 82
logger.error(f"Cache set error: {e}")

# Line 104
logger.error(f"Cache invalidate error: {e}")

# Line 128
logger.error(f"Get cache stats error: {e}")

# Line 142
logger.error(f"Redis health check failed: {e}")
```

---

### Fix 3: Add Cache Invalidation

**api/agents.py:189** (after agent creation):
```python
db.add(agent)
db.commit()
db.refresh(agent)

# ADD THIS:
invalidate_agent_cache(agent.agent_id)
logger.info(f"Invalidated cache for new agent {agent.agent_id}")
```

**api/agents.py:210** (after blockchain registration):
```python
if tx_hash:
  agent.blockchain_registered = True
    agent.blockchain_tx_hash = tx_hash
    db.commit()
    db.refresh(agent)

    # ADD THIS:
    invalidate_agent_cache(agent.agent_id)
```

---

### Fix 5: Add Cache Warming

**main.py** (add startup event):
```python
async def warm_cache():
    """Warm cache on startup."""
    logger.info("Starting cache warm-up...")
    try:
      db = next(get_db())
        await get_agents_list_cached(limit=100, offset=0, db=db)
        await get_tasks_cached(status=None, limit=100, db=db)
        logger.info("Cache warm-up completed")
    except Exception as e:
      logger.error(f"Cache warm-up failed: {e}")
    finally:
      db.close()

@app.on_event("startup")
async def startup_event():
    await warm_cache()
```

---

### Fix 6: Configure Memory Limits

**docker-compose.yml**:
```yaml
services:
  redis:
    image: redis:7-alpine
    command: >
      redis-server
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
```

---

## Progress Tracker

| Fix | Priority | Time | Status |
|-----|----------|------|--------|
| 1. SCAN instead of keys() | P0 🔴 | 15m | ⬜ |
| 2. logger instead of print() | P0 🔴 | 5m | ⬜ |
| 3. Cache invalidation | P0 🔴 | 10m | ⬜ |
| 4. Remove duplicate | P1 🟡 | 1h | ⬜ |
| 5. Cache warming | P1 🟡 | 30m | ⬜ |
| 6. Memory limits | P1 🟡 | 30m | ⬜ |
| 7. Exception handling | P2 ⚠️ | 1h | ⬜ |
| 8. Metrics | P2 ⚠️ | 1h | ⬜ |
| 9. Unit tests | P2 ⚠️ | 2h | ⬜ |

---

## Verification Commands

```bash
# Check for print statements
grep -rn "print(" cache.py services/*.py

# Check Redis memory
redis-cli INFO memory | grep used_memory_human

# Test cache invalidation
python3 -c "from cache import invalidate_cache; print(invalidate_cache('test:*'))"

# Run tests
pytest tests/test_cache*.py -v

# Check cache stats
curl http://localhost:8000/metrics | grep cache
```

---

## Re-Review Criteria

Request re-review when:
- ✅ All P0 fixes completed (30 min)
- ✅ All P1 fixes completed (2 hours)
- ✅ Tests passing
- ✅ Documentation updated

**Expected Score**: 9.0/10 ⭐⭐⭐⭐⭐

---

**Created**: 2026-03-05
**Next**: Implement P0 fixes (30 minutes)
