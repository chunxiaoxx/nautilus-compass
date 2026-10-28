"""Soul-fitness evolution proposer (Probe 3 Task 2) — the variation operator.

Reads the current agent prompt + a sample of its failures and frames a request for
ONE improved prompt. Pure framing (`build_proposer_prompt`) + parsing
(`extract_proposed_prompt`); the real M3 call is injected at run time (`propose_fn`).
"""
import re
from typing import Dict, List

_PROPOSER_SYSTEM = (
    "You improve the SYSTEM/INSTRUCTION prompt of a SWE-bench coding agent. You are "
    "given the agent's current prompt and a sample of instances it FAILED. Propose a "
    "single revised prompt that would help it resolve more — keep it general (do NOT "
    "hard-code answers to these specific instances), concise, and aligned with the "
    "agent's submission mechanism. Output ONLY the revised prompt inside one fenced "
    "```text block."
)


def build_proposer_prompt(
    current_prompt: str,
    failed_instances: List[Dict],
    *,
    max_failures: int = 5,
) -> str:
    """Frame the current prompt + up to ``max_failures`` failures into a proposer ask."""
    lines = [_PROPOSER_SYSTEM, "", "## Current agent prompt", "```text", current_prompt, "```", "", "## A sample of FAILED instances"]
    for f in failed_instances[:max_failures]:
        lines.append(
            f"- instance_id={f.get('instance_id','?')} | "
            f"problem={str(f.get('problem_statement',''))[:300]} | "
            f"failure={str(f.get('error',''))[:200]}"
        )
    lines += ["", "## Your task", "Propose ONE improved agent prompt inside a single ```text block."]
    return "\n".join(lines)


_FENCE_RE = re.compile(r"```(?:text)?\s*\n(.*?)```", re.DOTALL)


def extract_proposed_prompt(llm_output: str) -> str:
    """Return the LAST fenced block's content, stripped; "" when no fence present."""
    blocks = [b.strip("\n").strip() for b in _FENCE_RE.findall(llm_output)]
    return blocks[-1] if blocks else ""
