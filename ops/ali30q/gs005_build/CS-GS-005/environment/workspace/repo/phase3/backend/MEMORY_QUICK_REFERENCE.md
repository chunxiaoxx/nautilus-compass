# Phase 1: Evomap.ai Memory System - Quick Reference

## 🚀 Quick Start

### Installation (3 steps)
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup database (Docker recommended)
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres ankane/pgvector

# 3. Run migration
alembic upgrade head
```

### Test
```bash
python test_memory_system.py
```

### Start Server
```bash
uvicorn main:app --reload
```

---

## 📚 API Quick Reference

### Authentication
All endpoints require API key:
```bash
-H "X-API-Key: naut_your_api_key"
```

### Endpoints

#### Get Recent Memories
```bash
GET /api/memory/memories?limit=10&memory_type=task_execution
```

#### Search Similar Memories
```bash
GET /api/memory/memories/search?query=code%20task&limit=5
```

#### Get Memory Stats
```bash
GET /api/memory/memories/stats
```

#### Get Reflections
```bash
GET /api/memory/reflections?limit=10&min_importance=0.5
```

#### Get Agent Skills
```bash
GET /api/memory/skills
```

---

## 💻 Code Examples

### Store Memory (Automatic)
```python
# Happens automatically when task completes
task = await complete_task(task_id=1, current_user=user, db=db)
# Memory and reflection created automatically!
```

### Manual Memory Storage
```python
from memory.agent_memory import get_memory_system
from utils.db_pool import get_db_pool

db_pool = await get_db_pool()
memory_system = await get_memory_system(db_pool)

memory_id = await memory_system.store_task_memory(
    agent_id=1,
    task_id=1,
    execution_data={
        "description": "Build REST API",
        "task_type": "CODE",
        "status": "COMPLETED",
        "result": "Success"
    }
)
```

### Search Similar Tasks
```python
similar = await memory_system.find_similar_memories(
    agent_id=1,
    query_text="API development",
    limit=5
)

for mem in similar:
    print(f"Similarity: {mem['similarity']:.2f}")
    print(f"Content: {mem['content']}")
```

### Get Agent Skills
```python
from memory.reflection_system import get_reflection_system

reflection_system = await get_reflection_system(db_pool, memory_system)
skills = await reflection_system.get_agent_skills(agent_id=1)

for skill in skills:
    print(f"{skill['skill_name']}: Level {skill['skill_level']}")
    print(f"Success rate: {skill['success_rate']:.1%}")
```

---

## 🗄️ Database Schema

### Tables Created
- `agent_memories` - Task memories with embeddings
- `agent_reflections` - Insights and learnings
- `agent_skills` - Skill progression tracking

### Key Indexes
- Vector similarity: `idx_agent_memories_embedding` (IVFFlat)
- Agent lookup: `idx_agent_memories_agent`
- Time-based: `idx_agent_memories_created`

---

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/nautilus

# Memory System (optional)
EMBEDDING_MODEL=all-MiniLM-L6-v2
MEMORY_POOL_SIZE=10
MEMORY_MAX_OVERFLOW=20
```

---

## 🐛 Troubleshooting

### pgvector not found
```bash
# Use Docker with pgvector pre-installed
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres ankane/pgvector
```

### Test fails
```bash
# Check database connection
psql -U postgres -d nautilus -c "\dt agent_*"

# Verify tables exist
psql -U postgres -d nautilus -c "SELECT COUNT(*) FROM agent_memories;"
```

### API returns 500
```bash
# Check logs
tail -f logs/app.log

# Verify database pool
python -c "from utils.db_pool import init_db_pool; import asyncio; asyncio.run(init_db_pool())"
```

---

## 📊 Memory Types

| Type | Description | Use Case |
|------|-------------|----------|
| `task_execution` | Completed tasks | Main memory type |
| `observation` | Environmental data | Context awareness |
| `plan` | Planning decisions | Strategy learning |
| `error` | Failures | Error prevention |
| `success` | Achievements | Best practices |

---

## 🎯 Skill Levels

| Level | Experience | Description |
|-------|------------|-------------|
| 1-2 | 0-100 | Novice |
| 3-4 | 100-300 | Beginner |
| 5-6 | 300-600 | Intermediate |
| 7-8 | 600-1000 | Advanced |
| 9-10 | 1000+ | Expert |

Experience gain:
- Success: +10 XP
- Failure: +5 XP
- Level up: Every 100 XP

---

## 📈 Performance Tips

### Vector Search Optimization
```sql
-- Adjust IVFFlat lists based on data size
-- Rule: lists = rows / 1000
CREATE INDEX idx_agent_memories_embedding
ON agent_memories USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

### PostgreSQL Tuning
```sql
-- Increase memory for vector operations
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET work_mem = '64MB';
SELECT pg_reload_conf();
```

---

## 📁 File Structure

```
backend/
├── memory/
│   ├── __init__.py
│   ├── embedding_service.py
│   ├── agent_memory.py
│   └── reflection_system.py
├── api/
│   └── memory.py
├── utils/
│   └── db_pool.py
├── migrations/
│   └── add_memory_system.sql
├── alembic/versions/
│   └── 002_add_memory_system.py
└── test_memory_system.py
```

---

## ✅ Verification Commands

```bash
# 1. Check dependencies
pip list | grep sentence-transformers

# 2. Check database
psql -U postgres -d nautilus -c "\dt agent_*"

# 3. Check pgvector
psql -U postgres -d nautilus -c "SELECT * FROM pg_extension WHERE extname='vector';"

# 4. Run tests
python test_memory_system.py

# 5. Test API
curl http://localhost:8000/api/memory/memories -H "X-API-Key: naut_test"
```

---

## 🔗 Related Documentation

- **Full Implementation**: `PHASE1_COMPLETE_REPORT.md`
- **Installation Guide**: `MEMORY_SYSTEM_INSTALL.md`
- **Technical Details**: `MEMORY_SYSTEM_IMPLEMENTATION.md`
- **Summary**: `PHASE1_SUMMARY.md`

---

## 🎉 Status

✅ **Phase 1 Complete** - Production Ready

**Next**: Phase 2 - Advanced Features (LLM reflections, memory consolidation, cross-agent learning)

---

*Last Updated: 2026-03-03*
