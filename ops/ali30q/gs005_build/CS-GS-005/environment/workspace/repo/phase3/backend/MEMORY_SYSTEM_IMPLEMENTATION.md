# Phase 1: Evomap.ai Memory System Implementation

## Overview
This document describes the implementation of the Evomap.ai-inspired memory system for Nautilus agents.

## Components Implemented

### 1. Database Schema (`migrations/add_memory_system.sql`)
- **agent_memories**: Stores task execution memories with vector embeddings
- **agent_reflections**: Stores agent reflections and insights
- **agent_skills**: Tracks agent skill development over time

### 2. Embedding Service (`memory/embedding_service.py`)
- Uses sentence-transformers (all-MiniLM-L6-v2)
- Generates 384-dimensional embeddings
- Async/sync support for flexibility

### 3. Memory System (`memory/agent_memory.py`)
- Store task execution memories
- Semantic similarity search using vector embeddings
- Retrieve recent memories
- Memory statistics and analytics

### 4. Reflection System (`memory/reflection_system.py`)
- Generate reflections on completed tasks
- Extract insights from execution
- Update agent skills based on experience
- Track success/failure rates

### 5. API Endpoints (`api/memory.py`)
- `GET /api/memory/memories` - Get recent memories
- `GET /api/memory/memories/search` - Semantic search
- `GET /api/memory/memories/stats` - Memory statistics
- `GET /api/memory/reflections` - Get reflections
- `GET /api/memory/skills` - Get agent skills

### 6. Integration (`api/tasks.py`)
- Automatic memory storage on task completion
- Automatic reflection generation
- Skill tracking and updates

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

New dependencies added:
- sentence-transformers>=2.2.0
- torch>=2.0.0
- transformers>=4.30.0
- chromadb>=0.4.0
- pgvector>=0.2.0

### 2. Install pgvector Extension
```bash
# On Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y postgresql-15-pgvector

# Or using SQL
psql -U postgres -d nautilus -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 3. Run Database Migration
```bash
# Using Alembic
alembic upgrade head

# Or manually
psql -U postgres -d nautilus -f migrations/add_memory_system.sql
```

## Testing

Run the test script:
```bash
python test_memory_system.py
```

Expected output:
```
🧪 Testing Memory System...
1. Initializing database pool...
✅ Database pool initialized
2. Getting memory system...
✅ Memory system initialized
...
✅ All tests passed!
```

## Usage Examples

### Store a Memory
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
        "result": "API implemented successfully"
    }
)
```

### Search Similar Memories
```python
similar = await memory_system.find_similar_memories(
    agent_id=1,
    query_text="API development task",
    limit=5
)
```

### Generate Reflection
```python
from memory.reflection_system import get_reflection_system

reflection_system = await get_reflection_system(db_pool, memory_system)

reflection_id = await reflection_system.reflect_on_task(
    agent_id=1,
    task_id=1,
    result={
        "status": "COMPLETED",
        "execution_time": 120
    }
)
```

## API Examples

### Get Agent Memories
```bash
curl -X GET "http://localhost:8000/api/memory/memories?limit=10" \
  -H "X-API-Key: naut_your_api_key"
```

### Search Memories
```bash
curl -X GET "http://localhost:8000/api/memory/memories/search?query=code%20task&limit=5" \
  -H "X-API-Key: naut_your_api_key"
```

### Get Agent Skills
```bash
curl -X GET "http://localhost:8000/api/memory/skills" \
  -H "X-API-Key: naut_your_api_key"
```

## Performance Considerations

1. **Vector Index**: Uses IVFFlat index for fast similarity search
2. **Connection Pool**: Dedicated asyncpg pool for memory operations
3. **Lazy Loading**: Embedding model loaded on first use
4. **Batch Operations**: Support for batch embedding generation

## Next Steps (Phase 2)

1. Implement memory consolidation (merge similar memories)
2. Add memory importance scoring and pruning
3. Implement cross-agent knowledge sharing
4. Add temporal decay for old memories
5. Integrate with LLM for richer reflections

## Verification Checklist

- [x] pgvector extension installed
- [x] Database tables created
- [x] Embedding service functional
- [x] Memory storage working
- [x] Similarity search working
- [x] Reflection system working
- [x] Skills tracking working
- [x] API endpoints integrated
- [x] Task completion integration
- [x] Test script passing

## Files Created/Modified

### New Files
- `memory/__init__.py`
- `memory/embedding_service.py`
- `memory/agent_memory.py`
- `memory/reflection_system.py`
- `api/memory.py`
- `utils/db_pool.py`
- `migrations/add_memory_system.sql`
- `alembic/versions/002_add_memory_system.py`
- `test_memory_system.py`
- `MEMORY_SYSTEM_IMPLEMENTATION.md`

### Modified Files
- `requirements.txt` - Added memory system dependencies
- `api/tasks.py` - Integrated memory storage on task completion
- `main.py` - Added memory router and db pool initialization
