#!/usr/bin/env python3
"""
B3: 在平台上发布3个真实学术任务并等待 agents 竞标/完成

用法:
  python scripts/b3_bootstrap_tasks.py [--api-url http://localhost:8000] [--wait]

任务设计原则:
  - 真实可执行（不是占位符）
  - 输入数据内嵌在 description 中，无需上传文件
  - 覆盖3种不同 task_type，增加 agent 多样性
  - token_reward 足够吸引 agents 竞标

选项:
  --wait    发布后轮询等待所有任务完成（最多30分钟）
"""
import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime

try:
    import aiohttp
except ImportError:
    os.system(f"{sys.executable} -m pip install aiohttp -q")
    import aiohttp


API_URL = os.getenv("NAUTILUS_API_URL", "http://localhost:8000")

TASKS = [
    # ─────────────────────────────────────────────────────────────────────────
    # Task 1: Monte Carlo option pricing (finance + simulation)
    # ─────────────────────────────────────────────────────────────────────────
    {
        "title": "Monte Carlo Option Pricing: European Call on NVDA",
        "description": (
            "Compute the fair value of a European call option on NVIDIA Corporation (NVDA) "
            "using the Black-Scholes Monte Carlo simulation method.\n\n"
            "Parameters:\n"
            "- Spot price S0 = 875.00 USD (current NVDA price)\n"
            "- Strike price K = 900.00 USD\n"
            "- Risk-free rate r = 0.052 (5.2% annualized)\n"
            "- Volatility σ = 0.45 (45% annualized, NVDA historical vol)\n"
            "- Time to expiry T = 0.25 years (3 months)\n"
            "- Number of simulations N = 100,000\n"
            "- Number of time steps per path = 252\n\n"
            "Required output:\n"
            "1. Estimated option price (mean of discounted payoffs)\n"
            "2. 95% confidence interval for the estimate\n"
            "3. Standard error of the Monte Carlo estimator\n"
            "4. Delta (numerical: ΔC/ΔS using bump-and-reprice)\n"
            "5. Gamma (numerical second derivative)\n"
            "6. Comparison with Black-Scholes analytical formula result\n\n"
            "Please provide Python code used and all numerical results."
        ),
        "task_type": "monte_carlo",
        "parameters": {
            "source": "b3_bootstrap",
            "domain": "quantitative_finance",
            "difficulty": "intermediate",
        },
        "expected_output": (
            "Numerical results for option price, CI, SE, Delta, Gamma, "
            "plus Black-Scholes comparison and Python code."
        ),
        "token_reward": 50,
    },
    # ─────────────────────────────────────────────────────────────────────────
    # Task 2: ODE simulation — Lotka-Volterra predator-prey dynamics
    # ─────────────────────────────────────────────────────────────────────────
    {
        "title": "Lotka-Volterra Predator-Prey Dynamics: Parameter Sensitivity Analysis",
        "description": (
            "Simulate the classical Lotka-Volterra predator-prey system and perform "
            "a parameter sensitivity analysis.\n\n"
            "The system:\n"
            "  dx/dt = αx - βxy    (prey)\n"
            "  dy/dt = δxy - γy    (predators)\n\n"
            "Baseline parameters:\n"
            "  α = 0.1  (prey birth rate)\n"
            "  β = 0.02 (predation rate)\n"
            "  δ = 0.01 (predator reproduction rate)\n"
            "  γ = 0.1  (predator death rate)\n"
            "Initial conditions: x(0) = 40, y(0) = 9\n"
            "Time span: t ∈ [0, 200]\n\n"
            "Required:\n"
            "1. Solve the ODE system using scipy.integrate.odeint or solve_ivp\n"
            "2. Plot prey and predator populations over time\n"
            "3. Plot phase portrait (predator vs prey)\n"
            "4. Perform sensitivity analysis: vary each parameter ±20% and "
            "   report how the period and amplitude of oscillations change\n"
            "5. Find the equilibrium point analytically and verify numerically\n"
            "6. Calculate the period of oscillation for the baseline case\n\n"
            "Deliverable: Python code, numerical results table, and descriptions of plots."
        ),
        "task_type": "ode_simulation",
        "parameters": {
            "source": "b3_bootstrap",
            "domain": "mathematical_biology",
            "difficulty": "intermediate",
        },
        "expected_output": (
            "ODE solution, equilibrium coordinates, oscillation period, "
            "sensitivity analysis table, and Python code."
        ),
        "token_reward": 60,
    },
    # ─────────────────────────────────────────────────────────────────────────
    # Task 3: Research synthesis — AI Agent frameworks comparison
    # ─────────────────────────────────────────────────────────────────────────
    {
        "title": "Research Synthesis: Multi-Agent AI Frameworks Comparison 2025",
        "description": (
            "Synthesize a comprehensive comparison of the leading multi-agent AI frameworks "
            "available in 2025. This should be a thorough, structured research report.\n\n"
            "Frameworks to cover:\n"
            "1. LangGraph (LangChain)\n"
            "2. CrewAI\n"
            "3. AutoGen (Microsoft)\n"
            "4. Claude Code (Anthropic) — focus on KAIROS scheduling and tool plugin system\n"
            "5. OpenAI Swarm / Assistants API\n"
            "6. MetaGPT\n\n"
            "Evaluation dimensions:\n"
            "- Architecture pattern (centralized vs decentralized orchestration)\n"
            "- Memory model (short-term, long-term, shared)\n"
            "- Communication protocol (message passing, shared state, function calling)\n"
            "- Tool/plugin ecosystem\n"
            "- Production readiness (deployment, monitoring, observability)\n"
            "- Economic model (if any — token rewards, billing)\n"
            "- Best use cases and known limitations\n\n"
            "Format: Executive summary (200 words) + comparison table + "
            "detailed sections per framework + conclusion with recommendations.\n"
            "Target audience: senior engineers evaluating which framework to build on."
        ),
        "task_type": "research_synthesis",
        "parameters": {
            "source": "b3_bootstrap",
            "domain": "ai_engineering",
            "difficulty": "advanced",
            "output_format": "structured_report",
        },
        "expected_output": (
            "Executive summary, comparison table, 6 framework deep-dives, "
            "and recommendations. Min 2000 words."
        ),
        "token_reward": 80,
    },
]


async def create_task(session: aiohttp.ClientSession, task: dict) -> str | None:
    """POST to /api/academic/submit and return the task_id."""
    url = f"{API_URL}/api/academic/submit"
    try:
        async with session.post(
            url,
            json=task,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            body = await resp.json()
            if resp.status in (200, 201):
                # API returns task object directly (201) or wrapped in {"success": ..., "data": ...}
                task_id = (
                    body.get("task_id")
                    or body.get("data", {}).get("task_id")
                    or body.get("data", {}).get("id")
                )
                return task_id
            else:
                print(f"  HTTP {resp.status}: {body}")
                return None
    except Exception as e:
        print(f"  Error creating task: {e}")
        return None


async def poll_task(session: aiohttp.ClientSession, task_id: str, timeout: int = 1800) -> dict:
    """Poll task status until completed/failed or timeout."""
    url = f"{API_URL}/api/academic/{task_id}"
    deadline = time.time() + timeout
    last_status = None

    while time.time() < deadline:
        await asyncio.sleep(20)
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                body = await resp.json()
                # Handle both wrapped {"data": {...}} and direct task object
                raw = body.get("data", body)
                status = raw.get("status", "unknown")
                if status != last_status:
                    print(f"  [{task_id}] status={status}")
                    last_status = status
                if status in ("completed", "failed", "cancelled"):
                    return raw
        except Exception as e:
            print(f"  [{task_id}] poll error: {e}")

    return {"status": "timeout", "task_id": task_id}


async def main(api_url: str, wait: bool) -> None:
    global API_URL
    API_URL = api_url

    print(f"\nNautilus B3 Bootstrap — Posting {len(TASKS)} academic tasks")
    print(f"API: {API_URL}\n")

    created: list[tuple[str, str]] = []  # (task_id, title)

    connector = aiohttp.TCPConnector(ssl=api_url.startswith("https"))

    async with aiohttp.ClientSession(connector=connector) as session:
        for i, task in enumerate(TASKS, 1):
            print(f"[{i}/{len(TASKS)}] Creating: {task['title']}")
            task_id = await create_task(session, task)
            if task_id:
                print(f"  Created: task_id={task_id}, reward={task['token_reward']} tokens")
                created.append((task_id, task["title"]))
            else:
                print(f"  Failed to create task {i}")

        if not created:
            print("\nNo tasks created. Check API URL and server status.")
            return

        print(f"\nCreated {len(created)}/{len(TASKS)} tasks:")
        for tid, title in created:
            print(f"  {tid}: {title}")

        if wait:
            print(f"\nWaiting for tasks to complete (timeout: 30 minutes)...")
            polls = [poll_task(session, tid) for tid, _ in created]
            results = await asyncio.gather(*polls)

            print("\n=== Task Results ===")
            for (tid, title), result in zip(created, results):
                status = result.get("status", "unknown")
                output = (result.get("result_output") or "")[:200]
                nau = result.get("token_reward", 0)
                print(f"\n{title}")
                print(f"  task_id={tid}, status={status}, reward={nau} NAU")
                if output:
                    print(f"  output preview: {output}...")
        else:
            print("\nTasks posted. Agents will bid and process them automatically.")
            print("Check status at:")
            for tid, _ in created:
                print(f"  GET {API_URL}/api/academic/{tid}")

    # Save results
    output = {
        "timestamp": datetime.now().isoformat(),
        "api_url": API_URL,
        "tasks_created": [{"task_id": tid, "title": title} for tid, title in created],
    }
    out_path = Path(__file__).parent / "b3_tasks_created.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSummary saved: {out_path}")


if __name__ == "__main__":
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Bootstrap 3 academic tasks on Nautilus platform")
    parser.add_argument(
        "--api-url",
        default=os.getenv("NAUTILUS_API_URL", "http://localhost:8000"),
        help="Nautilus API base URL",
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Poll until all tasks complete (up to 30 minutes)",
    )
    args = parser.parse_args()
    asyncio.run(main(args.api_url, args.wait))
