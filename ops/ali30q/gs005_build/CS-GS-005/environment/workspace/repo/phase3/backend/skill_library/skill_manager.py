"""
Skill Library Manager — Voyager-inspired skill accumulation for Nautilus agents.

Core principle: skills are procedures (how-to), not knowledge (what).
A good skill = another LLM can reproduce the same quality output by following it.
"""
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

SKILL_DIR = Path(__file__).parent / "skills"
INDEX_DB = Path(__file__).parent / "index.db"

# Extraction prompt template — used after a bounty scores >= 7
EXTRACTION_PROMPT = """You just completed a task. Extract 1-3 reusable skills from your work.

Task: {task_title}
Task Description: {task_description}
Your Output (summary): {output_summary}
User Score: {score}/10
User Feedback: {feedback}

For each skill, provide:
1. name: Short name (e.g., "Analyze competitive moat")
2. description: One sentence — what problem does this skill solve?
3. procedure: Step-by-step instructions another agent could follow to reproduce this quality.
4. input: What information is needed to start?
5. output: What does the finished result look like?
6. tags: 2-5 relevant tags

Return as JSON array:
[{{"name": "...", "description": "...", "procedure": "...", "input": "...", "output": "...", "tags": ["..."]}}]
"""


def _init_db():
    """Create index database if it doesn't exist."""
    conn = sqlite3.connect(str(INDEX_DB))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            tags TEXT,
            quality_score REAL DEFAULT 0.0,
            usage_count INTEGER DEFAULT 0,
            success_rate REAL DEFAULT 1.0,
            version INTEGER DEFAULT 1,
            agent_id INTEGER,
            created_at TEXT,
            updated_at TEXT,
            file_path TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS skill_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_id TEXT NOT NULL,
            bounty_id TEXT,
            agent_id INTEGER,
            score_after REAL,
            used_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_skill(
    skill_id: str,
    name: str,
    description: str,
    procedure: str,
    input_schema: str = "",
    output_schema: str = "",
    tags: Optional[list[str]] = None,
    quality_score: float = 0.0,
    agent_id: Optional[int] = None,
    source_bounty: Optional[str] = None,
    depends_on: Optional[list[str]] = None,
) -> str:
    """Save a skill to YAML file and index it in SQLite."""
    _init_db()
    tags = tags or []
    depends_on = depends_on or []
    now = datetime.utcnow().isoformat()

    skill_data = {
        "id": skill_id,
        "name": name,
        "version": 1,
        "description": description,
        "tags": tags,
        "procedure": procedure,
        "input": input_schema,
        "output": output_schema,
        "quality_score": quality_score,
        "usage_count": 0,
        "success_rate": 1.0,
        "depends_on": depends_on,
        "source_bounty": source_bounty,
        "agent_id": agent_id,
        "created_at": now,
        "updated_at": now,
    }

    # Save YAML
    file_path = SKILL_DIR / f"{skill_id}.yaml"
    SKILL_DIR.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(skill_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    # Index in SQLite
    conn = sqlite3.connect(str(INDEX_DB))
    conn.execute("""
        INSERT OR REPLACE INTO skills
        (id, name, description, tags, quality_score, usage_count, success_rate, version, agent_id, created_at, updated_at, file_path)
        VALUES (?, ?, ?, ?, ?, 0, 1.0, 1, ?, ?, ?, ?)
    """, (skill_id, name, description, json.dumps(tags), quality_score, agent_id, now, now, str(file_path)))
    conn.commit()
    conn.close()

    return skill_id


def search_skills(query: str, min_quality: float = 5.0, limit: int = 5) -> list[dict]:
    """Search skills by keyword matching (FTS fallback — no embedding yet)."""
    _init_db()
    conn = sqlite3.connect(str(INDEX_DB))
    conn.row_factory = sqlite3.Row

    # Simple keyword search across name, description, tags
    words = query.lower().split()
    conditions = []
    params = []
    for word in words[:5]:  # max 5 keywords
        conditions.append("(LOWER(name) LIKE ? OR LOWER(description) LIKE ? OR LOWER(tags) LIKE ?)")
        params.extend([f"%{word}%", f"%{word}%", f"%{word}%"])

    where = " AND ".join(conditions) if conditions else "1=1"
    rows = conn.execute(f"""
        SELECT * FROM skills
        WHERE quality_score >= ? AND ({where})
        ORDER BY quality_score DESC, usage_count DESC
        LIMIT ?
    """, [min_quality, *params, limit]).fetchall()
    conn.close()

    results = []
    for row in rows:
        skill_file = Path(row["file_path"])
        procedure = ""
        if skill_file.exists():
            with open(skill_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                procedure = data.get("procedure", "")

        results.append({
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "procedure": procedure,
            "quality_score": row["quality_score"],
            "usage_count": row["usage_count"],
        })

    return results


def record_usage(skill_id: str, bounty_id: str, agent_id: int, score_after: Optional[float] = None):
    """Record that a skill was used and update its quality score."""
    _init_db()
    conn = sqlite3.connect(str(INDEX_DB))
    now = datetime.utcnow().isoformat()

    conn.execute("""
        INSERT INTO skill_usage (skill_id, bounty_id, agent_id, score_after, used_at)
        VALUES (?, ?, ?, ?, ?)
    """, (skill_id, bounty_id, agent_id, score_after, now))

    # Update usage count
    conn.execute("UPDATE skills SET usage_count = usage_count + 1, updated_at = ? WHERE id = ?", (now, skill_id))

    # Update quality score with EWA if we have a score
    if score_after is not None:
        row = conn.execute("SELECT quality_score FROM skills WHERE id = ?", (skill_id,)).fetchone()
        if row:
            old_score = row[0] or 0.0
            new_score = round(0.3 * score_after + 0.7 * old_score, 1)
            conn.execute("UPDATE skills SET quality_score = ?, updated_at = ? WHERE id = ?", (new_score, now, skill_id))

    conn.commit()
    conn.close()


def get_agent_skills_context(agent_id: int, task_description: str, limit: int = 3) -> str:
    """
    Generate a skills context string for injection into agent system prompt.
    Used when an agent picks up a new bounty.
    """
    skills = search_skills(task_description, min_quality=5.0, limit=limit)
    if not skills:
        return ""

    lines = ["You have the following reusable skills. Use them when relevant:\n"]
    for i, s in enumerate(skills, 1):
        lines.append(f"### Skill {i}: {s['name']}")
        lines.append(f"Quality: {s['quality_score']}/10 | Used {s['usage_count']} times")
        lines.append(f"{s['procedure']}\n")

    return "\n".join(lines)


def build_extraction_prompt(
    task_title: str,
    task_description: str,
    output_summary: str,
    score: int,
    feedback: str = "",
) -> str:
    """Build the skill extraction prompt for post-task processing."""
    return EXTRACTION_PROMPT.format(
        task_title=task_title,
        task_description=task_description,
        output_summary=output_summary[:2000],
        score=score,
        feedback=feedback or "None",
    )


def list_skills(min_quality: float = 0.0, limit: int = 50) -> list[dict]:
    """List all skills in the library."""
    _init_db()
    conn = sqlite3.connect(str(INDEX_DB))
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT id, name, description, quality_score, usage_count, version, created_at
        FROM skills
        WHERE quality_score >= ?
        ORDER BY quality_score DESC
        LIMIT ?
    """, (min_quality, limit)).fetchall()
    conn.close()
    return [dict(row) for row in rows]
