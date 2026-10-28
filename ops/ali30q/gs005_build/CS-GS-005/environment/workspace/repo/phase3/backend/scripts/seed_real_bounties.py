#!/usr/bin/env python3
"""
Seed REAL bounty/challenge tasks from actual platforms.
Every task links to a real competition with real prize money.
"""
import os, sys, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from utils.database import SessionLocal
from sqlalchemy import text

REAL_BOUNTIES = [
    # ── Kaggle: ARC Prize 2026 ($2M) ───────────────────────────────────────
    {
        "title": "[Kaggle $2M] ARC Prize 2026 — ARC-AGI-3: Build system scoring >85% on abstract reasoning",
        "description": (
            "SOURCE: https://arcprize.org/competitions/2026 | Kaggle: https://kaggle.com/competitions/arc-prize-2026-arc-agi-2\n\n"
            "PRIZE: $2M total across 3 tracks. Milestone #1 (June 30 2026): 1st $25K, 2nd $10K, 3rd $2.5K.\n\n"
            "TASK: The ARC-AGI benchmark tests general intelligence via abstract visual reasoning puzzles. "
            "Each puzzle shows input→output grid transformations; the system must infer the rule and apply it to new inputs. "
            "Current SOTA is ~55%. Target: >85% to claim grand prize.\n\n"
            "APPROACH FOR NAUTILUS AGENTS:\n"
            "1. Download ARC-AGI-3 dataset from Kaggle\n"
            "2. Analyze pattern types: symmetry, rotation, color mapping, counting, object manipulation\n"
            "3. Design a program synthesis approach (DSL + search) vs neural approach (GPT-4V + chain-of-thought)\n"
            "4. Use RAID-3 consensus: 3 agents try different approaches, vote on best answer\n"
            "5. Submit to Kaggle leaderboard\n\n"
            "DEADLINE: September 30, 2026"
        ),
        "task_type": "general_computation",
        "reward": 25,
    },

    # ── Kaggle: Konwinski Prize ($1M) ───────────────────────────────────────
    {
        "title": "[Kaggle $1M] Konwinski Prize — AI that closes 90% of real GitHub issues automatically",
        "description": (
            "SOURCE: https://kaggle.com/competitions/konwinski-prize\n\n"
            "PRIZE: $1,000,000 grand prize for first team to close 90% of new GitHub issues.\n\n"
            "TASK: Build an autonomous coding agent that can:\n"
            "1. Read a GitHub issue (bug report or feature request)\n"
            "2. Understand the codebase context\n"
            "3. Write the fix/implementation\n"
            "4. Submit a working pull request\n"
            "5. Pass the repo's test suite\n\n"
            "APPROACH FOR NAUTILUS AGENTS:\n"
            "1. Study SWE-bench dataset (the evaluation benchmark)\n"
            "2. Build repo understanding pipeline: clone → index → dependency graph\n"
            "3. Design fix generation: issue→localization→patch→test\n"
            "4. Use RAID-3: Agent 1 generates fix, Agent 2 reviews, Agent 3 tests\n"
            "5. Iterate on SWE-bench-lite first, then full benchmark\n\n"
            "This directly validates Nautilus's multi-agent architecture."
        ),
        "task_type": "research_synthesis",
        "reward": 25,
    },

    # ── Kaggle: Hull Tactical ($100K) ───────────────────────────────────────
    {
        "title": "[Kaggle $100K] Hull Tactical Market Prediction — Challenge the Efficient Market Hypothesis",
        "description": (
            "SOURCE: https://kaggle.com/competitions (Hull Tactical)\n\n"
            "PRIZE: $100,000 total. 1st place: $50,000.\n\n"
            "TASK: Predict stock market returns using quantitative methods. "
            "Hull Tactical challenges participants to build models that outperform "
            "buy-and-hold strategy, directly testing the Efficient Market Hypothesis.\n\n"
            "APPROACH FOR NAUTILUS AGENTS:\n"
            "1. Agent 1 (Quant): Traditional factor models — momentum, value, volatility\n"
            "2. Agent 2 (ML): XGBoost/LightGBM on alternative data features\n"
            "3. Agent 3 (DL): Transformer time-series model (temporal fusion transformer)\n"
            "4. Ensemble via RAID-3 consensus weighted by Sharpe ratio\n"
            "5. Backtest on out-of-sample data before submission\n\n"
            "DEADLINE: June 16, 2026"
        ),
        "task_type": "statistical_analysis",
        "reward": 20,
    },

    # ── XPRIZE Quantum ($5M+$4M) ───────────────────────────────────────────
    {
        "title": "[XPRIZE $9M] Quantum Applications — Propose quantum algorithms solving real-world problems",
        "description": (
            "SOURCE: https://xprize.org/competitions/qc-apps\n\n"
            "PRIZE: $5M Phase I + $4M Phase II (grand prize $3M, awarded March 2027). "
            "Backed by Google Quantum AI, Google.org, GESDA.\n\n"
            "TASK: Propose and analyze quantum algorithms that solve pressing real-world problems "
            "in areas like healthcare, climate, energy, materials science, or finance.\n\n"
            "APPROACH FOR NAUTILUS AGENTS:\n"
            "1. Survey current NISQ-era quantum algorithms: VQE, QAOA, quantum ML\n"
            "2. Identify 3 high-impact applications where quantum advantage is provable\n"
            "3. Design hybrid classical-quantum pipeline for each\n"
            "4. Estimate resource requirements: qubit count, circuit depth, error rates\n"
            "5. Compare with best classical algorithms — quantify speedup\n"
            "6. Write competition-ready proposal document\n\n"
            "Phase II Wild Card Registration closed March 4, 2026 — prepare for next round."
        ),
        "task_type": "research_synthesis",
        "reward": 20,
    },

    # ── HeroX: Evolution 2.0 ($10M) ────────────────────────────────────────
    {
        "title": "[HeroX $10M] Evolution 2.0 — Discover the origin of genetic code and information",
        "description": (
            "SOURCE: https://herox.com/evolution2.0\n\n"
            "PRIZE: $10,000,000 — one of the largest science prizes ever offered.\n\n"
            "TASK: Discover a process by which a naturally occurring, non-biological system "
            "can generate a functional coding system (like DNA/RNA) from scratch. "
            "Must demonstrate: (1) a code that maps symbols to functions, "
            "(2) the code emerged without intelligent design, "
            "(3) the process is reproducible.\n\n"
            "APPROACH FOR NAUTILUS AGENTS:\n"
            "1. Survey origin-of-life research: RNA world, metabolism-first, autocatalytic sets\n"
            "2. Analyze recent breakthroughs: self-replicating RNA, protocells, ribozyme evolution\n"
            "3. Design computational model of code emergence using cellular automata or ALife\n"
            "4. Simulate chemical evolution: random polymers → functional replicators\n"
            "5. Identify most promising experimental directions\n"
            "6. Generate research proposal for lab verification\n\n"
            "OPEN INDEFINITELY — $10M on the table."
        ),
        "task_type": "research_synthesis",
        "reward": 25,
    },

    # ── InnoCentive: Agentic AI Coding ─────────────────────────────────────
    {
        "title": "[InnoCentive $3K] Agentic AI Coding Challenge — Build autonomous coding agent",
        "description": (
            "SOURCE: https://innocentive.com/challenges/agentic-ai-coding-challenge/\n\n"
            "PRIZE: $3,000 award pool.\n\n"
            "TASK: Build an AI agent that can autonomously write, debug, and test code "
            "based on natural language specifications. Evaluated on code quality, "
            "test coverage, and ability to handle edge cases.\n\n"
            "APPROACH FOR NAUTILUS AGENTS:\n"
            "1. This is META — Nautilus agents building an agent that codes\n"
            "2. Use MiniMax M2.7 for fast code generation (100 TPS)\n"
            "3. RAID-3 review: generate → review → test in parallel\n"
            "4. Benchmark against HumanEval and MBPP\n"
            "5. Submit working solution to InnoCentive\n\n"
            "LOW BARRIER — good first bounty to win and prove Nautilus works."
        ),
        "task_type": "general_computation",
        "reward": 10,
    },

    # ── Clay Millennium: Riemann Hypothesis ($1M) ──────────────────────────
    {
        "title": "[Clay $1M] Riemann Hypothesis — Computational verification and zero-free region survey",
        "description": (
            "SOURCE: https://claymath.org/millennium-problems/riemann-hypothesis\n\n"
            "PRIZE: $1,000,000 from Clay Mathematics Institute.\n\n"
            "TASK: Prove that all non-trivial zeros of the Riemann zeta function ζ(s) "
            "have real part equal to 1/2.\n\n"
            "REALISTIC SUBTASKS FOR AGENTS:\n"
            "1. Verify zeros: confirm first 10^13 non-trivial zeros lie on critical line\n"
            "2. Survey zero-free regions: compile state-of-the-art results\n"
            "3. Analyze connection: quantify how RH would improve prime number theorem bounds\n"
            "4. Test GUE hypothesis: compare zero spacing to random matrix theory predictions\n"
            "5. Literature review: classify proof attempts by approach and assess viability\n\n"
            "Any verifiable computational result is valuable and publishable."
        ),
        "task_type": "statistical_analysis",
        "reward": 20,
    },

    # ── Clay Millennium: P vs NP ($1M) ─────────────────────────────────────
    {
        "title": "[Clay $1M] P vs NP — Map proof landscape and identify viable attack vectors",
        "description": (
            "SOURCE: https://claymath.org/millennium-problems/p-vs-np-problem\n\n"
            "PRIZE: $1,000,000 from Clay Mathematics Institute.\n\n"
            "TASK: Determine whether every problem whose solution can be quickly verified "
            "can also be quickly solved (P = NP or P ≠ NP).\n\n"
            "REALISTIC SUBTASKS FOR AGENTS:\n"
            "1. Classify all known barrier results: relativization, natural proofs, algebrization\n"
            "2. Survey circuit complexity lower bounds: what's the best we can prove?\n"
            "3. Analyze geometric complexity theory (Mulmuley-Sohoni) — current state\n"
            "4. Study proof complexity: connections between proof systems and P vs NP\n"
            "5. Generate structured roadmap of what sub-results would constitute progress\n"
            "6. Cite all relevant papers with arXiv IDs\n\n"
            "A comprehensive survey paper would be publishable and valuable."
        ),
        "task_type": "research_synthesis",
        "reward": 20,
    },

    # ── XPRIZE Wildfire ($11M) ─────────────────────────────────────────────
    {
        "title": "[XPRIZE $11M] Wildfire — AI-driven rapid wildfire detection and response system",
        "description": (
            "SOURCE: https://xprize.org/competitions (XPRIZE Wildfire)\n\n"
            "PRIZE: $11,000,000 grand prize, awarded 2026.\n\n"
            "TASK: Develop autonomous wildfire detection and suppression technologies that can "
            "detect and extinguish wildfires within 10 minutes of ignition.\n\n"
            "RESEARCH SUBTASKS FOR AGENTS:\n"
            "1. Survey satellite-based fire detection: MODIS, VIIRS, Sentinel-2 capabilities and latency\n"
            "2. Analyze drone swarm architectures for coordinated fire response\n"
            "3. Design ML model: satellite imagery → fire probability → alert pipeline\n"
            "4. Compare detection methods: IR sensors, smoke detection, weather prediction\n"
            "5. Economic analysis: cost of early detection vs. cost of late response\n"
            "6. Generate technical proposal for autonomous detection-to-suppression pipeline\n\n"
            "Multi-agent coordination directly applies — this is Nautilus's strength."
        ),
        "task_type": "research_synthesis",
        "reward": 20,
    },

    # ── OpenAI First Proof ─────────────────────────────────────────────────
    {
        "title": "[OpenAI] First Proof Challenge — Attempt formal proofs of 10 expert-level math problems",
        "description": (
            "SOURCE: https://openai.com/index/first-proof-submissions/\n\n"
            "CONTEXT: OpenAI's First Proof challenge tests AI on expert-level mathematics. "
            "Their model achieved ~5/10 correct proofs (Feb 2026). Can Nautilus agents do better?\n\n"
            "TASK: Attempt formal proofs for the 10 First Proof challenge problems. "
            "Problems span algebra, analysis, number theory, and combinatorics.\n\n"
            "APPROACH FOR NAUTILUS AGENTS:\n"
            "1. Retrieve the 10 problem statements from OpenAI's publication\n"
            "2. For each problem: decompose into lemmas, identify proof strategy\n"
            "3. Use RAID-3: 3 agents attempt independent proofs, then cross-verify\n"
            "4. Formalize successful proofs in Lean 4 or Coq for verification\n"
            "5. Compare with OpenAI's published results — identify where we do better/worse\n\n"
            "Beating OpenAI's score would be massive PR for Nautilus."
        ),
        "task_type": "general_computation",
        "reward": 20,
    },

    # ── NIH Digital Supplement Education ($869K) ───────────────────────────
    {
        "title": "[NIH/HeroX $869K] Digital Supplement Education — Build interactive health literacy tools",
        "description": (
            "SOURCE: https://herox.com (NIH Office of Dietary Supplements via NASA Tournament Lab)\n\n"
            "PRIZE: Up to $869,000 across 3 development phases.\n\n"
            "TASK: Create digital tools that help consumers of all ages understand "
            "dietary supplement science — ingredients, evidence, interactions, and safety.\n\n"
            "APPROACH FOR NAUTILUS AGENTS:\n"
            "1. Survey NIH ODS database: https://ods.od.nih.gov/factsheets/\n"
            "2. Design interactive Q&A system using Nautilus LLM (Gemini/MiniMax)\n"
            "3. Build knowledge graph: supplement → evidence level → interactions → contraindications\n"
            "4. Create age-appropriate content (kids, adults, elderly)\n"
            "5. Prototype as web app with chat interface\n"
            "6. Include citations to PubMed/NIH sources for credibility\n\n"
            "OPEN — 3-phase development, early phases more accessible."
        ),
        "task_type": "research_synthesis",
        "reward": 15,
    },

    # ── Bounty Scout Task ──────────────────────────────────────────────────
    {
        "title": "[META] Bounty Scout — Continuously scan platforms for new high-value challenges",
        "description": (
            "This is a recurring META task for Nautilus agents.\n\n"
            "TASK: Scan these bounty platforms weekly and report new opportunities:\n"
            "- Kaggle: https://kaggle.com/competitions (sort by prize)\n"
            "- HeroX: https://herox.com/crowdsourcing-projects\n"
            "- InnoCentive: https://innocentive.com/challenges/\n"
            "- DrivenData: https://drivendata.org/competitions/\n"
            "- XPRIZE: https://xprize.org/competitions\n"
            "- Topcoder: https://topcoder.com/challenges\n"
            "- ARC Prize: https://arcprize.org\n"
            "- Numerai: https://numer.ai (crypto quant fund)\n"
            "- Codeforces/Project Euler (algorithm challenges)\n\n"
            "OUTPUT: Ranked list of new bounties with:\n"
            "1. Platform + URL\n"
            "2. Prize amount\n"
            "3. Deadline\n"
            "4. Required capabilities\n"
            "5. Feasibility score for Nautilus agents (1-10)\n"
            "6. Recommended RAID configuration\n\n"
            "This task should auto-repeat weekly."
        ),
        "task_type": "research_synthesis",
        "reward": 5,
    },
]


def seed():
    db = SessionLocal()
    created = 0
    try:
        for task in REAL_BOUNTIES:
            task_id = f"bounty_{random.randbytes(4).hex()}"
            try:
                db.execute(text(
                    "INSERT INTO academic_tasks "
                    "(task_id, title, description, task_type, status, token_reward, marketplace_open) "
                    "VALUES (:tid, :title, :desc, :type, 'pending', :reward, true)"
                ), {
                    "tid": task_id,
                    "title": task["title"],
                    "desc": task["description"],
                    "type": task["task_type"],
                    "reward": task["reward"],
                })
                db.commit()
                created += 1
                prize = task["title"].split("]")[0].replace("[", "")
                print(f"  [{created}] {prize} — {task['title'].split('] ')[1][:55]}...")
            except Exception as e:
                print(f"  SKIP: {e}")
                db.rollback()
        print(f"\nCreated {created}/{len(REAL_BOUNTIES)} real bounty tasks")
    finally:
        db.close()


if __name__ == "__main__":
    print("Seeding REAL bounty/challenge tasks from active platforms...\n")
    seed()
