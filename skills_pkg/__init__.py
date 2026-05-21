"""nautilus_compass.skills_pkg · v2.0 Layer 5 · GBrain skillpack subsystem.

Python clean-room rewrite of GBrain 5-step skill cycle (concept→prototype→evaluate→codify→cron).
NO fork of GBrain TypeScript source (MIT but TS not idiomatic for compass).

Storage layout (under repo root or user-provided base):
  skills/concepts/    · step 1 · markdown proposals
  skills/prototypes/  · step 2 · code in progress
  skills/codified/    · step 3-4 · evaluated · production
  skills/retired/     · step 5 (rare) · archived
  skills/_skill_registry.json · lookup for codified skills

NO LLM. Pure schema + dynamic import + subprocess.
Reference: paper/SPEC_GBRAIN_SKILLPACK_REWRITE.md.
"""
