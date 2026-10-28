"""
AutoResearch Loop - Agent self-improvement through iterative prompt optimization.

Inspired by karpathy/autoresearch:
  - train.py = prompt templates (the thing being optimized)
  - prepare.py = eval dataset (fixed constants)
  - program.md = this file's logic (the optimization loop)

Loop:
  1. Evaluate current active prompt → baseline score
  2. Ask LLM to propose an improved prompt
  3. Evaluate the new prompt → candidate score
  4. If candidate > baseline → promote candidate
  5. Log experiment results
  6. Repeat

Run: cd phase3/agent-engine && python -m bootstrap.autoresearch_loop --rounds=5
"""
import json
import time
import logging
import argparse
import os
import sys
from datetime import datetime
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

logger = logging.getLogger(__name__)


# Default prompt templates (v1 baseline)
DEFAULT_SENTIMENT_SYSTEM = "You are a precise data labeling AI. Label each item accurately. Always respond in valid JSON."

DEFAULT_SENTIMENT_TASK = """Analyze the sentiment of each text item.

Items to analyze:
{items_text}

Respond as a JSON array:
[{{"id": <id>, "text": "<original text>", "label": "positive"|"negative"|"neutral", "confidence": <0.0-1.0>}}, ...]"""


class AutoResearchLoop:
    """
    Core optimization loop for agent self-improvement.

    Constraints (like autoresearch's 5-min budget):
    - Max API cost per round: $0.05
    - Max evaluation items: 20
    - Max prompt length: 2000 chars
    """

    MAX_COST_PER_ROUND = 0.05
    MAX_EVAL_ITEMS = 20
    MAX_PROMPT_LENGTH = 2000

    def __init__(self, eval_type: str = "sentiment"):
        from bootstrap.prompt_registry import PromptRegistry
        from bootstrap.eval_dataset import get_all_eval_sets
        from llm.client import get_llm_client

        self.registry = PromptRegistry()
        self.llm = get_llm_client()
        self.eval_type = eval_type

        # Load eval dataset
        eval_sets = get_all_eval_sets()
        self.eval_data = eval_sets.get(eval_type, eval_sets["sentiment"])

        # Ensure baseline prompts exist
        self._ensure_baseline()

        # Experiment log
        self.experiments = []

    def _ensure_baseline(self):
        """Register default prompts if none exist."""
        system_name = f"{self.eval_type}_system"
        task_name = f"{self.eval_type}_task"

        if not self.registry.get_active(system_name):
            self.registry.register(system_name, DEFAULT_SENTIMENT_SYSTEM, created_by="human", activate=True)
            logger.info(f"Registered baseline system prompt: {system_name}")

        if not self.registry.get_active(task_name):
            self.registry.register(task_name, DEFAULT_SENTIMENT_TASK, created_by="human", activate=True)
            logger.info(f"Registered baseline task prompt: {task_name}")

    def run(self, rounds: int = 5, verbose: bool = True) -> dict:
        """
        Run the optimization loop for N rounds.

        Returns summary with baseline and final scores.
        """
        from bootstrap.metrics_evaluator import evaluate_labeling_prompt

        system_name = f"{self.eval_type}_system"
        task_name = f"{self.eval_type}_task"

        # Step 1: Evaluate baseline
        active_system = self.registry.get_active(system_name)
        active_task = self.registry.get_active(task_name)

        if verbose:
            print(f"\n{'='*60}")
            print(f"AutoResearch Loop: {self.eval_type} prompt optimization")
            print(f"{'='*60}")
            print(f"Eval dataset: {len(self.eval_data)} items")
            print(f"Rounds: {rounds}")
            print(f"Baseline system prompt v{active_system.version}")
            print(f"Baseline task prompt v{active_task.version}")

        baseline_result = evaluate_labeling_prompt(
            self.llm, active_system.template, active_task.template,
            self.eval_data, self.eval_type, max_items=self.MAX_EVAL_ITEMS,
        )

        baseline_score = baseline_result.score
        self.registry.update_metrics(system_name, active_system.version, {
            "accuracy": baseline_result.accuracy,
            "avg_latency_s": baseline_result.avg_latency_s,
            "score": baseline_score,
        })

        if verbose:
            print(f"\nBaseline: accuracy={baseline_result.accuracy:.0%}, "
                  f"latency={baseline_result.avg_latency_s:.2f}s/item, "
                  f"score={baseline_score:.3f}")

        best_score = baseline_score
        improvements = 0

        # Step 2-6: Optimization loop
        for round_num in range(1, rounds + 1):
            if verbose:
                print(f"\n--- Round {round_num}/{rounds} ---")

            # Ask LLM to propose improvement
            improvement = self._propose_improvement(
                active_system.template, active_task.template, baseline_result
            )

            if not improvement:
                if verbose:
                    print("  No improvement proposed, skipping")
                continue

            new_system = improvement.get("system_prompt", active_system.template)
            new_task = improvement.get("task_prompt", active_task.template)
            reasoning = improvement.get("reasoning", "No reasoning provided")

            # Enforce constraints
            if len(new_system) > self.MAX_PROMPT_LENGTH:
                new_system = new_system[:self.MAX_PROMPT_LENGTH]
            if len(new_task) > self.MAX_PROMPT_LENGTH:
                new_task = new_task[:self.MAX_PROMPT_LENGTH]

            if verbose:
                print(f"  Reasoning: {reasoning[:100]}...")

            # Register candidate
            candidate_sys = self.registry.register(system_name, new_system, created_by="agent")
            candidate_task = self.registry.register(task_name, new_task, created_by="agent")

            # Evaluate candidate
            candidate_result = evaluate_labeling_prompt(
                self.llm, new_system, new_task,
                self.eval_data, self.eval_type, max_items=self.MAX_EVAL_ITEMS,
            )

            candidate_score = candidate_result.score

            # Update metrics
            self.registry.update_metrics(system_name, candidate_sys.version, {
                "accuracy": candidate_result.accuracy,
                "avg_latency_s": candidate_result.avg_latency_s,
                "score": candidate_score,
            })
            self.registry.update_metrics(task_name, candidate_task.version, {
                "accuracy": candidate_result.accuracy,
                "avg_latency_s": candidate_result.avg_latency_s,
                "score": candidate_score,
            })

            # Compare
            improved = candidate_score > best_score
            delta = candidate_score - best_score

            experiment = {
                "round": round_num,
                "baseline_score": best_score,
                "candidate_score": candidate_score,
                "delta": delta,
                "improved": improved,
                "accuracy": candidate_result.accuracy,
                "reasoning": reasoning,
                "system_version": candidate_sys.version,
                "task_version": candidate_task.version,
                "timestamp": datetime.utcnow().isoformat(),
            }
            self.experiments.append(experiment)

            if improved:
                # Promote candidate
                self.registry.promote(system_name, candidate_sys.version)
                self.registry.promote(task_name, candidate_task.version)
                best_score = candidate_score
                improvements += 1
                active_system = candidate_sys
                active_task = candidate_task

                if verbose:
                    print(f"  IMPROVED: {baseline_result.accuracy:.0%} → {candidate_result.accuracy:.0%} "
                          f"(score {delta:+.3f})")
            else:
                if verbose:
                    print(f"  No improvement: {candidate_result.accuracy:.0%} vs baseline "
                          f"(score {delta:+.3f}), keeping current")

        # Save experiment log
        self._save_experiments()

        # Summary
        summary = {
            "eval_type": self.eval_type,
            "rounds": rounds,
            "improvements": improvements,
            "baseline_score": baseline_result.score,
            "final_score": best_score,
            "total_improvement": best_score - baseline_result.score,
            "baseline_accuracy": baseline_result.accuracy,
            "final_accuracy": self.registry.get_active(system_name).metrics.get("accuracy", 0),
            "experiments": self.experiments,
        }

        if verbose:
            print(f"\n{'='*60}")
            print(f"SUMMARY")
            print(f"{'='*60}")
            print(f"Rounds: {rounds}")
            print(f"Improvements: {improvements}")
            print(f"Baseline score: {baseline_result.score:.3f} (accuracy: {baseline_result.accuracy:.0%})")
            print(f"Final score: {best_score:.3f}")
            print(f"Total improvement: {best_score - baseline_result.score:+.3f}")

        return summary

    def _propose_improvement(self, current_system: str, current_task: str, eval_result) -> Optional[dict]:
        """Ask LLM to propose an improved prompt based on evaluation results."""
        # Show the agent its own performance data
        error_examples = [d for d in eval_result.details if not d["correct"]][:5]
        error_text = json.dumps(error_examples, indent=2) if error_examples else "None"

        prompt = f"""You are optimizing a data labeling prompt for better accuracy.

Current system prompt:
```
{current_system}
```

Current task prompt template:
```
{current_task}
```

Current performance:
- Accuracy: {eval_result.accuracy:.0%} ({eval_result.correct}/{eval_result.total})
- Avg latency: {eval_result.avg_latency_s:.2f}s per item

Misclassified examples:
{error_text}

Propose an improved version of BOTH prompts. Focus on:
1. Fixing the misclassifications shown above
2. Making instructions clearer and more specific
3. Reducing ambiguity in label definitions

Respond in JSON:
{{
  "system_prompt": "<improved system prompt>",
  "task_prompt": "<improved task prompt, must contain {{items_text}} placeholder>",
  "reasoning": "<brief explanation of changes>"
}}

IMPORTANT: The task_prompt MUST contain the literal string {{items_text}} as a placeholder."""

        try:
            response = self.llm.chat(
                prompt=prompt,
                system="You are a prompt engineering expert. Propose concrete improvements. Respond ONLY with JSON.",
                temperature=0.4,
                max_tokens=2048,
            )

            # Parse response
            import re
            response = re.sub(r'ThinkingBlock\([^)]*(?:\([^)]*\)[^)]*)*\)', '', response, flags=re.DOTALL).strip()

            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # Try extracting JSON
                start = response.find("{")
                end = response.rfind("}") + 1
                if start >= 0 and end > start:
                    return json.loads(response[start:end])

        except Exception as e:
            logger.error(f"Failed to propose improvement: {e}")

        return None

    def _save_experiments(self):
        """Save experiment log to disk."""
        log_path = os.path.join(os.path.dirname(__file__), "experiment_log.json")
        try:
            # Load existing
            existing = []
            if os.path.exists(log_path):
                with open(log_path) as f:
                    existing = json.load(f)

            existing.extend(self.experiments)

            with open(log_path, "w") as f:
                json.dump(existing, f, indent=2)

            logger.info(f"Saved {len(self.experiments)} experiments to {log_path}")
        except Exception as e:
            logger.warning(f"Failed to save experiments: {e}")


def main():
    parser = argparse.ArgumentParser(description="Nautilus Agent Bootstrap - AutoResearch Loop")
    parser.add_argument("--rounds", type=int, default=5, help="Number of optimization rounds")
    parser.add_argument("--eval-type", choices=["sentiment", "spam", "intent"], default="sentiment")
    parser.add_argument("--verbose", action="store_true", default=True)
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
    )

    loop = AutoResearchLoop(eval_type=args.eval_type)
    summary = loop.run(rounds=args.rounds, verbose=args.verbose)

    # Exit with success if any improvement was made
    sys.exit(0 if summary["improvements"] > 0 else 1)


if __name__ == "__main__":
    main()
