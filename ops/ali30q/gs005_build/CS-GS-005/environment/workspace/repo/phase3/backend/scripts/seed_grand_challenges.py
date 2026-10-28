#!/usr/bin/env python3
"""
Seed Grand Challenge tasks — real open problems for Nautilus agents to tackle.

These are high-value tasks from math, CS, science, and bounty platforms.
Agents that make progress on these prove the platform's value.
"""
import os, sys, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from utils.database import SessionLocal
from sqlalchemy import text

GRAND_CHALLENGES = [
    # ── Mathematics: Millennium Prize Problems ──────────────────────────────
    {
        "title": "Millennium Prize: P vs NP — Survey current proof approaches and identify most promising attack vectors",
        "description": (
            "Survey the landscape of P vs NP proof attempts. Classify approaches into: "
            "(1) barrier results (relativization, natural proofs, algebrization), "
            "(2) circuit complexity lower bounds, (3) algebraic geometry approaches, "
            "(4) information-theoretic approaches. For each, assess: current state, "
            "key open sub-problems, and feasibility score (1-10). "
            "Identify the 3 most promising directions and what specific sub-results would constitute progress. "
            "Output: structured markdown report with citations to key papers (arXiv IDs)."
        ),
        "task_type": "research_synthesis",
        "reward": 20,
    },
    {
        "title": "Millennium Prize: Riemann Hypothesis — Computational verification and zero-free region analysis",
        "description": (
            "Task 1: Verify the first 10 billion non-trivial zeros of the Riemann zeta function "
            "lie on the critical line Re(s)=1/2. Report any anomalies. "
            "Task 2: Survey zero-free regions — what is the current best result? "
            "(de la Vallée-Poussin, Vinogradov-Korobov, etc.) "
            "Task 3: Analyze the connection between RH and prime distribution — "
            "quantify how much better prime counting would be if RH is true vs current bounds. "
            "Output: numerical results + survey report."
        ),
        "task_type": "statistical_analysis",
        "reward": 20,
    },
    {
        "title": "Millennium Prize: Navier-Stokes — Regularity analysis via computational fluid dynamics",
        "description": (
            "Investigate the 3D Navier-Stokes regularity problem computationally. "
            "Set up high-resolution simulations of known blowup candidate scenarios "
            "(Kato's conditions, Ladyzhenskaya-Prodi-Serrin criteria). "
            "Test: (1) Does the enstrophy grow unboundedly? "
            "(2) What is the critical Reynold's number for apparent singularity? "
            "(3) Compare with Tao's averaged Navier-Stokes blowup construction. "
            "Output: simulation results, plots, and analysis of whether blowup is genuine or numerical artifact."
        ),
        "task_type": "ode_simulation",
        "reward": 20,
    },

    # ── Mathematics: Other Famous Conjectures ───────────────────────────────
    {
        "title": "Collatz Conjecture: Statistical analysis of trajectory lengths and stopping times",
        "description": (
            "Perform comprehensive statistical analysis of the Collatz conjecture for n up to 10^12. "
            "Compute: (1) distribution of stopping times, (2) record-breaking trajectory lengths, "
            "(3) correlation between starting value and stopping time, "
            "(4) test the Terras density conjecture (proportion reaching 1). "
            "Apply methods from: Lagarias (2010), Tao (2019) density result. "
            "Identify any statistical anomalies that could guide proof attempts. "
            "Output: statistical report with histograms and power-law fits."
        ),
        "task_type": "monte_carlo",
        "reward": 10,
    },
    {
        "title": "Goldbach's Conjecture: Verify to 10^18 and analyze partition density",
        "description": (
            "Extend verification of Goldbach's conjecture (every even n>2 is sum of two primes). "
            "For even numbers up to 10^12: (1) count the number of Goldbach partitions, "
            "(2) find the even numbers with the fewest partitions (Goldbach comet), "
            "(3) test Hardy-Littlewood conjecture for partition asymptotics. "
            "Compare with Helfgott's 2013 proof of weak Goldbach. "
            "Output: verification report + partition statistics + asymptotic analysis."
        ),
        "task_type": "general_computation",
        "reward": 10,
    },
    {
        "title": "Twin Prime Conjecture: Gap distribution analysis post-Zhang-Maynard-Tao",
        "description": (
            "Analyze the current state of bounded prime gaps. "
            "Zhang (2013) proved gaps ≤ 70,000,000; Polymath8 reduced to 246. "
            "Task: (1) Compute prime gap distribution for primes up to 10^11, "
            "(2) Compare empirical distribution with Hardy-Littlewood prediction, "
            "(3) Analyze what prevents further reduction below 246, "
            "(4) Survey sieve theory limitations (Bombieri-Vinogradov, Elliott-Halberstam). "
            "Output: gap statistics + theoretical analysis report."
        ),
        "task_type": "statistical_analysis",
        "reward": 10,
    },

    # ── Computer Science: Open Problems ─────────────────────────────────────
    {
        "title": "AI Alignment: Survey and classify current alignment approaches with feasibility assessment",
        "description": (
            "Comprehensive survey of AI alignment research directions: "
            "(1) RLHF and its limitations (reward hacking, Goodhart's law), "
            "(2) Constitutional AI and rule-based approaches, "
            "(3) Debate and recursive reward modeling, "
            "(4) Interpretability (mechanistic, probing, concept bottleneck), "
            "(5) Formal verification of neural networks. "
            "For each: key papers, current results, open problems, and scalability assessment. "
            "Rate feasibility (1-10) for solving alignment at ASI level. "
            "Output: structured survey with comparison matrix."
        ),
        "task_type": "research_synthesis",
        "reward": 15,
    },
    {
        "title": "Multi-Agent Coordination: Optimal task allocation in heterogeneous agent swarms",
        "description": (
            "Formalize and solve: given N heterogeneous agents with different capabilities, "
            "M tasks with dependencies, and communication constraints — "
            "find optimal task allocation minimizing total completion time. "
            "Compare: (1) Hungarian algorithm for bipartite matching, "
            "(2) auction-based mechanisms (CBBA), (3) reinforcement learning (MARL), "
            "(4) market-based approaches. "
            "Benchmark on Nautilus's actual agent-task data (166 agents, 8 task types). "
            "Output: algorithm comparison + recommendation for Nautilus task router."
        ),
        "task_type": "general_computation",
        "reward": 15,
    },

    # ── Physics ─────────────────────────────────────────────────────────────
    {
        "title": "Quantum Computing: Simulate quantum error correction threshold for surface codes",
        "description": (
            "Simulate the threshold theorem for topological surface codes. "
            "Compute: (1) logical error rate vs physical error rate for d=3,5,7,9 codes, "
            "(2) threshold error rate under depolarizing noise, "
            "(3) comparison with Google Willow's recent results (below threshold with d=7). "
            "Use minimum weight perfect matching decoder. "
            "Analyze: how many physical qubits needed for 1 logical qubit at 10^-12 error rate? "
            "Output: simulation data + threshold curves + qubit overhead estimates."
        ),
        "task_type": "monte_carlo",
        "reward": 15,
    },
    {
        "title": "Protein Folding: Predict structure for 5 CASP16 targets using physics-based methods",
        "description": (
            "Select 5 recent CASP16 target proteins. For each: "
            "(1) Run homology search (HHblits/MMseqs2) to find templates, "
            "(2) Apply coevolution analysis (DCA/plmDCA) for contact prediction, "
            "(3) Build 3D models using distance geometry + energy minimization, "
            "(4) Score models with DOPE/MolProbity/GDT-TS. "
            "Compare with AlphaFold3 predictions. Identify cases where physics-based "
            "methods provide insight that ML-only approaches miss. "
            "Output: PDB files + GDT-TS scores + analysis report."
        ),
        "task_type": "research_synthesis",
        "reward": 15,
    },

    # ── Bounty Platform Tasks ───────────────────────────────────────────────
    {
        "title": "Kaggle Challenge Prep: Design RAID-3 multi-agent strategy for tabular prediction competitions",
        "description": (
            "Design a multi-agent strategy for Kaggle tabular competitions using Nautilus RAID-3. "
            "Agent 1: XGBoost/LightGBM specialist — feature engineering + hyperparameter tuning. "
            "Agent 2: Neural network specialist — TabNet/FT-Transformer/TabPFN. "
            "Agent 3: Ensemble specialist — stacking/blending/weighted averaging. "
            "For each agent: define inputs, outputs, evaluation criteria. "
            "Define RAID consensus: how to combine 3 agents' predictions. "
            "Test on 3 past Kaggle competitions (provide leaderboard comparison). "
            "Output: complete strategy document + code templates."
        ),
        "task_type": "research_synthesis",
        "reward": 15,
    },
    {
        "title": "HeroX/InnoCentive Challenge Scout: Find and rank top 10 active bounties for AI agent teams",
        "description": (
            "Scout active challenge/bounty platforms: HeroX, InnoCentive, Kaggle, "
            "DrivenData, Topcoder, Quantitative Finance challenges, XPRIZE. "
            "For each active bounty: (1) prize amount, (2) deadline, "
            "(3) required capabilities, (4) current leaderboard state, "
            "(5) feasibility score for Nautilus agents (1-10). "
            "Rank by ROI (prize / estimated agent-hours). "
            "Output: ranked list with direct links and recommended agent team composition."
        ),
        "task_type": "research_synthesis",
        "reward": 10,
    },

    # ── Cryptography & Security ─────────────────────────────────────────────
    {
        "title": "Post-Quantum Crypto: Benchmark lattice-based schemes on resource-constrained devices",
        "description": (
            "Benchmark NIST PQC standards (ML-KEM/Kyber, ML-DSA/Dilithium, SLH-DSA/SPHINCS+) "
            "on simulated constrained environments (ARM Cortex-M4 equivalent). "
            "Measure: key generation time, encapsulation/signing time, verification time, "
            "memory usage, bandwidth. Compare with pre-quantum RSA-2048 and ECDSA-P256. "
            "Analyze: at what point does PQ overhead become unacceptable? "
            "Output: benchmark tables + overhead analysis + migration recommendations."
        ),
        "task_type": "general_computation",
        "reward": 10,
    },

    # ── Economics & Game Theory ─────────────────────────────────────────────
    {
        "title": "Token Economics: Design optimal NAU emission/burn schedule using mechanism design theory",
        "description": (
            "Apply mechanism design theory to optimize NAU token economics. "
            "Model: agents as utility-maximizing rational actors, tasks as public goods. "
            "Design: (1) emission curve (inflationary vs deflationary), "
            "(2) burn mechanisms (task fees, slashing, buyback), "
            "(3) staking rewards for high-quality agents. "
            "Simulate 1000 agents over 365 days with different strategies. "
            "Find Nash equilibrium and Pareto-optimal emission parameters. "
            "Compare: Bitcoin halving, Ethereum EIP-1559, Osmosis thirdening. "
            "Output: mechanism design + simulation results + recommended parameters."
        ),
        "task_type": "monte_carlo",
        "reward": 15,
    },
]


def seed():
    db = SessionLocal()
    created = 0
    try:
        for task in GRAND_CHALLENGES:
            task_id = f"grand_{random.randbytes(4).hex()}"
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
                print(f"  [{created}] {task['title'][:70]}...")
            except Exception as e:
                print(f"  SKIP: {e}")
                db.rollback()
        print(f"\nCreated {created}/{len(GRAND_CHALLENGES)} grand challenge tasks")
    finally:
        db.close()


if __name__ == "__main__":
    print("Seeding Grand Challenge tasks...\n")
    seed()
