"""
Nautilus Agent Bootstrap - AutoResearch-inspired self-improvement system.

Core idea (from karpathy/autoresearch):
  1. Agent reads its own prompts/code (like train.py)
  2. Proposes improvements
  3. Runs evaluation under fixed constraints (like 5-min budget)
  4. Keeps improvements, reverts failures
  5. Loops

This module implements prompt optimization as the first bootstrap capability.
"""
