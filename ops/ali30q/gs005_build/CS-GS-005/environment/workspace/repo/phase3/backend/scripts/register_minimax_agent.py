#!/usr/bin/env python3
"""Register MiniMax multimodal agent on Nautilus platform.

This agent leverages MiniMax's Token Plan (4500 calls/5h):
- M2.7 Highspeed (100 TPS) — text generation
- Speech 2.8 HD — Chinese/English TTS
- image-01 — image generation (200/day)
- Hailuo-2.3-Fast — video generation
- Mu-2.5 — music generation
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from utils.database import SessionLocal
from sqlalchemy import text
import json

AGENT_NAME = "MiniMax-Multimodal"
DESCRIPTION = (
    "MiniMax-powered multimodal agent with text (M2.7 100TPS), "
    "image generation (image-01), TTS (Speech 2.8 HD), "
    "video generation (Hailuo), and music generation (Mu-2.5). "
    "4500 API calls per 5 hours. First multimodal-native agent on Nautilus."
)
SPECIALTIES = json.dumps([
    "image_generation", "tts_generation", "video_generation",
    "music_generation", "general_computation", "research_synthesis",
    "content_creation", "multimodal_analysis",
])
SYSTEM_CONTEXT = """You are MiniMax-Multimodal, a creative AI agent on the Nautilus platform.

Your unique capabilities:
1. TEXT: M2.7 Highspeed at 100 TPS — fast text generation and analysis
2. IMAGE: image-01 — generate images from text descriptions (200/day)
3. TTS: Speech 2.8 HD — high-quality Chinese/English text-to-speech (100K chars/day)
4. VIDEO: Hailuo-2.3-Fast — generate short videos from prompts
5. MUSIC: Mu-2.5 — generate music from text descriptions

When executing tasks:
- For image tasks: call POST /api/multimodal/minimax-image
- For TTS tasks: call POST /api/multimodal/minimax-tts
- For video tasks: call POST /api/multimodal/minimax-video
- For music tasks: call POST /api/multimodal/minimax-music
- For text/analysis tasks: use your M2.7 LLM capabilities directly

Rate limit: 4500 calls per 5 hours = ~15 calls/min. Pace yourself.
Prioritize tasks that leverage your multimodal capabilities.
"""


def register():
    db = SessionLocal()
    try:
        # Check if already exists
        existing = db.execute(
            text("SELECT agent_id FROM agents WHERE name = :name"),
            {"name": AGENT_NAME}
        ).fetchone()

        if existing:
            print(f"Agent '{AGENT_NAME}' already exists with id={existing[0]}")
            return existing[0]

        # Get next agent_id
        max_id = db.execute(text("SELECT COALESCE(MAX(agent_id), 0) FROM agents")).scalar()
        new_id = max_id + 1

        db.execute(text("""
            INSERT INTO agents (
                agent_id, owner, name, description, reputation,
                specialties, current_tasks, completed_tasks, failed_tasks,
                total_earnings, created_at, blockchain_registered,
                agent_status, autonomy_enabled, system_context
            ) VALUES (
                :aid, :owner, :name, :desc, 85,
                :specs, 0, 0, 0,
                0, NOW(), false,
                'alive', true, :ctx
            )
        """), {
            "aid": new_id,
            "owner": "0x0000000000000000000000000000000000000000",
            "name": AGENT_NAME,
            "desc": DESCRIPTION,
            "specs": SPECIALTIES,
            "ctx": SYSTEM_CONTEXT,
        })
        db.commit()
        print(f"Registered agent '{AGENT_NAME}' with id={new_id}")

        # Also create agent_survival record
        try:
            db.execute(text("""
                INSERT INTO agent_survival (agent_id, survival_tier, credit_balance, tasks_completed, quality_score)
                VALUES (:aid, 'GROWING', 500, 0, 0.8)
                ON CONFLICT DO NOTHING
            """), {"aid": new_id})
            db.commit()
            print(f"Created survival record for agent {new_id}")
        except Exception as e:
            print(f"Survival record skipped: {e}")

        return new_id
    finally:
        db.close()


if __name__ == "__main__":
    agent_id = register()
    print(f"\nMiniMax Agent ID: {agent_id}")
    print(f"Capabilities: text/image/tts/video/music")
    print(f"Rate limit: 4500 calls/5h")
