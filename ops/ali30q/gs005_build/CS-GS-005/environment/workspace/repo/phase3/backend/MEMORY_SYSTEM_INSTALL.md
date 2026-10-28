# Phase 1: Evomap.ai Memory System - Installation Guide

## Quick Start (Windows)

### 1. Install Dependencies
```bash
cd C:\Users\chunx\Projects\nautilus-core\phase3\backend
pip install -r requirements.txt
```

### 2. Setup PostgreSQL with pgvector

#### Option A: Using Docker (Recommended)
```bash
docker run -d \
  --name nautilus-postgres \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=nautilus \
  ankane/pgvector
```

#### Option B: Manual Installation
1. Download pgvector from: https://github.com/pgvector/pgvector/releases
2. Install PostgreSQL extension
3. Enable in database:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 3. Run Database Migration
```bash
# Using Alembic
alembic upgrade head

# Or using manage_migrations.py
python manage_migrations.py upgrade

# Or manually
psql -U postgres -d nautilus -f migrations/add_memory_system.sql
```

### 4. Test the System
```bash
python test_memory_system.py
```

Expected output:
```
🧪 Testing Memory System...
✅ Database pool initialized
✅ Memory system initialized
✅ Memory stored with ID: 1
✅ All tests passed!
```

### 5. Start the Server
```bash
uvicorn main:app --reload
```

### 6. Test API Endpoints
```bash
# Get memories
curl -X GET "http://localhost:8000/api/memory/memories?limit=10" \
  -H "X-API-Key: naut_your_api_key"

# Search memories
curl -X GET "http://localhost:8000/api/memory/memories/search?query=code%20task" \
  -H "X-API-Key: naut_your_api_key"

# Get skills
curl -X GET "http://localhost:8000/api/memory/skills" \
  -H "X-API-Key: naut_your_api_key"
```

## Verification Checklist

- [ ] Dependencies installed (`pip list | grep sentence-transformers`)
- [ ] PostgreSQL running (`psql -U postgres -c "SELECT version();"`)
- [ ] pgvector extension enabled (`psql -U postgres -d nautilus -c "SELECT * FROM pg_extension WHERE extname='vector';"`)
- [ ] Database tables created (`psql -U postgres -d nautilus -c "\dt agent_*"`)
- [ ] Test script passes (`python test_memory_system.py`)
- [ ] Server starts without errors (`uvicorn main:app --reload`)
- [ ] API endpoints accessible (`curl http://localhost:8000/api/memory/memories`)

## Troubleshooting

### Issue: pgvector not found
**Solution**: Use Docker image with pgvector pre-installed:
```bash
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres ankane/pgvector
```

### Issue: sentence-transformers installation fails
**Solution**: Install PyTorch first:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install sentence-transformers
```

### Issue: Database connection error
**Solution**: Check DATABASE_URL in .env:
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/nautilus
```

### Issue: Migration fails
**Solution**: Run migrations manually:
```bash
psql -U postgres -d nautilus -f migrations/add_memory_system.sql
```

### Issue: Test script fails
**Solution**: Check database connection and ensure tables exist:
```bash
psql -U postgres -d nautilus -c "\dt"
```

## Environment Variables

Add to `.env`:
```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/nautilus

# Memory System (optional)
EMBEDDING_MODEL=all-MiniLM-L6-v2
MEMORY_POOL_SIZE=10
MEMORY_MAX_OVERFLOW=20
```

## Performance Tuning

### PostgreSQL Configuration
```sql
-- Increase shared_buffers for better performance
ALTER SYSTEM SET shared_buffers = '256MB';

-- Increase work_mem for vector operations
ALTER SYSTEM SET work_mem = '64MB';

-- Reload configuration
SELECT pg_reload_conf();
```

### Vector Index Tuning
```sql
-- Adjust IVFFlat lists parameter based on data size
-- Rule of thumb: lists = rows / 1000
CREATE INDEX idx_agent_memories_embedding
ON agent_memories USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);  -- Adjust based on your data
```

## Next Steps

1. ✅ Complete Phase 1 installation
2. 🔄 Test with real agent tasks
3. 📊 Monitor memory system performance
4. 🚀 Proceed to Phase 2: Advanced features

See `MEMORY_SYSTEM_IMPLEMENTATION.md` for detailed documentation.
