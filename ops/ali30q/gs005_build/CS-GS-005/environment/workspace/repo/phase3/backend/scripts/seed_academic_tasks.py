#!/usr/bin/env python3
"""Seed 5 real academic tasks to bootstrap the marketplace."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from utils.database import SessionLocal
from sqlalchemy import text
import uuid
import time

TASKS = [
    {
        "title": "Literature Review: AI Agent Economic Models 2024-2026",
        "description": (
            "Comprehensive literature review of AI agent economic models published 2024-2026. "
            "Cover: (1) token-based incentive mechanisms, (2) proof-of-useful-work variants, "
            "(3) agent reputation systems, (4) multi-agent market dynamics. "
            "Output: structured markdown report with citations, key findings, and research gaps."
        ),
        "task_type": "research_synthesis",
    },
    {
        "title": "Statistical Analysis: Agent Specialty Diversification Patterns",
        "description": (
            "Analyze the Nautilus agent specialty distribution data. "
            "Questions: (1) Is specialty assignment following a power law? "
            "(2) What is the optimal diversity index for platform health? "
            "(3) Which task types are under-served? "
            "Data: GET /api/platform/analytics/agents. "
            "Output: statistical summary with tests, visualizations, and recommendations."
        ),
        "task_type": "statistical_analysis",
    },
    {
        "title": "Monte Carlo Simulation: NAU Token Velocity Under Different Reward Schedules",
        "description": (
            "Simulate NAU token circulation under 3 reward schedules: "
            "(A) flat 1 NAU/task, (B) quality-weighted 1-10 NAU, (C) current task-type-based. "
            "Model 1000 agents over 365 days, measure: Gini coefficient, velocity, "
            "agent retention rate. 10,000 iterations per schedule. "
            "Output: Python code + comparison table + recommendation."
        ),
        "task_type": "monte_carlo",
    },
    {
        "title": "Curve Fitting: Platform Health Score Prediction Model",
        "description": (
            "Fit a predictive model for Nautilus platform health score using historical snapshots. "
            "Data: SELECT metrics, health_score FROM platform_metrics_snapshots ORDER BY snapshot_time. "
            "Try: linear regression, polynomial, ARIMA, and simple neural net. "
            "Evaluate with RMSE and MAE on 80/20 train/test split. "
            "Output: best model code + coefficients + 7-day forecast."
        ),
        "task_type": "curve_fitting",
    },
    {
        "title": "Data Analysis: Task Completion Time Distribution by Type",
        "description": (
            "Analyze task completion times across all task types on Nautilus. "
            "Data: SELECT task_type, created_at, updated_at, status FROM academic_tasks WHERE status='completed'. "
            "Questions: (1) Mean/median/P95 completion time per type, "
            "(2) Are there time-of-day effects? (3) Correlation between task complexity and completion time. "
            "Output: summary statistics + distribution plots + outlier analysis."
        ),
        "task_type": "general_computation",
    },
]

def main():
    db = SessionLocal()
    try:
        for task in TASKS:
            task_id = f"seed-{uuid.uuid4().hex[:8]}"
            db.execute(text(
                "INSERT INTO academic_tasks (task_id, title, description, task_type, status, "
                "marketplace_open, token_reward) "
                "VALUES (:tid, :title, :desc, :type, 'pending', true, :reward)"
            ), {
                "tid": task_id,
                "title": task["title"],
                "desc": task["description"],
                "type": task["task_type"],
                "reward": 5,  # 5 NAU per seed task
            })
            db.commit()
            print(f"Created: {task_id} — {task['title'][:60]}")
            time.sleep(0.1)
        print(f"\nDone: {len(TASKS)} seed tasks created.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
