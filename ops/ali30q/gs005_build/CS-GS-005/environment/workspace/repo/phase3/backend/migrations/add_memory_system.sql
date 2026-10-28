-- Agent Memory System Migration
-- This migration adds tables for agent memory, reflection, and skill tracking

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Agent memories table
CREATE TABLE IF NOT EXISTS agent_memories (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER NOT NULL,
    task_id INTEGER,
    memory_type VARCHAR(50) NOT NULL,
    content JSONB NOT NULL,
    embedding vector(384),
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB,
    CONSTRAINT fk_agent_memories_task FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- Indexes for agent_memories
CREATE INDEX IF NOT EXISTS idx_agent_memories_agent ON agent_memories(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_memories_task ON agent_memories(task_id);
CREATE INDEX IF NOT EXISTS idx_agent_memories_type ON agent_memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_agent_memories_created ON agent_memories(created_at DESC);

-- Vector similarity search index (IVFFlat for better performance)
CREATE INDEX IF NOT EXISTS idx_agent_memories_embedding
ON agent_memories USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Agent reflections table
CREATE TABLE IF NOT EXISTS agent_reflections (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER NOT NULL,
    task_id INTEGER,
    reflection_text TEXT NOT NULL,
    insights JSONB,
    importance_score FLOAT DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_agent_reflections_task FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- Indexes for agent_reflections
CREATE INDEX IF NOT EXISTS idx_agent_reflections_agent ON agent_reflections(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_reflections_task ON agent_reflections(task_id);
CREATE INDEX IF NOT EXISTS idx_agent_reflections_created ON agent_reflections(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_reflections_importance ON agent_reflections(importance_score DESC);

-- Agent skills table
CREATE TABLE IF NOT EXISTS agent_skills (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER NOT NULL,
    skill_name VARCHAR(100) NOT NULL,
    skill_level INTEGER DEFAULT 1 CHECK (skill_level >= 1 AND skill_level <= 10),
    experience INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(agent_id, skill_name)
);

-- Indexes for agent_skills
CREATE INDEX IF NOT EXISTS idx_agent_skills_agent ON agent_skills(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_skills_name ON agent_skills(skill_name);
CREATE INDEX IF NOT EXISTS idx_agent_skills_level ON agent_skills(skill_level DESC);
CREATE INDEX IF NOT EXISTS idx_agent_skills_last_used ON agent_skills(last_used DESC);

-- Comments for documentation
COMMENT ON TABLE agent_memories IS 'Stores agent task execution memories with vector embeddings for similarity search';
COMMENT ON TABLE agent_reflections IS 'Stores agent reflections and insights from task execution';
COMMENT ON TABLE agent_skills IS 'Tracks agent skill development and experience over time';

COMMENT ON COLUMN agent_memories.memory_type IS 'Type of memory: task_execution, observation, plan, error, success';
COMMENT ON COLUMN agent_memories.embedding IS '384-dimensional vector embedding for semantic similarity search';
COMMENT ON COLUMN agent_reflections.importance_score IS 'Importance score from 0.0 to 1.0 for memory consolidation';
COMMENT ON COLUMN agent_skills.skill_level IS 'Skill proficiency level from 1 (novice) to 10 (expert)';
