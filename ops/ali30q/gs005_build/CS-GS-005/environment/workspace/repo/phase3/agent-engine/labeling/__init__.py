"""
Nautilus Batch Labeling - Production data labeling pipeline.

Pipeline: Upload CSV/JSON → Split into batches → Raid mode parallel labeling
         → Consensus voting → Quality report → Export results
"""
