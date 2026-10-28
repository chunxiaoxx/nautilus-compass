"""Soul-fitness evolution: the selection rule (Probe 3 Task 1).

Each cycle proposes a candidate agent-prompt; this module decides whether to ACCEPT
it as the new best, using the SAME conservative external-fitness gate as the probes:
a candidate is accepted only if its resolve outcomes lopsidedly beat the current-best
on the same probe instances (escape-noise) AND its mean resolve-rate is higher. This
is the heart of "evolution by external benchmark" — a lucky within-noise edit is
rejected, so the loop cannot drift on noise (anti-Goodhart, anti-over-claim).
"""
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from escape_noise_stats import aggregate_paired_multiseed  # noqa: E402


@dataclass
class EvolutionState:
    best_prompt: str
    best_score: float          # resolve-rate of the current best on the probe set
    history: List[Dict] = field(default_factory=list)


def _mean(items: Dict[str, bool]) -> float:
    return sum(items.values()) / len(items) if items else 0.0


def consider_candidate(
    state: EvolutionState,
    cand_prompt: str,
    cand_items: Dict[str, bool],
    base_items: Dict[str, bool],
) -> Tuple[bool, EvolutionState]:
    """Decide whether the candidate prompt replaces the current best.

    ``cand_items`` / ``base_items`` = {instance_id: resolved_bool} for the candidate
    and the current-best agent on the SAME probe set. Accept iff the paired
    escape-noise gate fires AND cand mean > base mean. Always records the cycle in
    history (accepted or not). Returns (accepted, new_state); state is not mutated.
    """
    base_mean, cand_mean = _mean(base_items), _mean(cand_items)
    seed = [{
        "base": {"pass_at_1": base_mean, "items": base_items},
        "cand": {"pass_at_1": cand_mean, "items": cand_items},
    }]
    agg = aggregate_paired_multiseed(seed, baseline_key="base", treatment_key="cand")
    escapes = bool(agg["escapes_noise"])
    accepted = escapes and cand_mean > base_mean

    entry = {
        "cand_prompt": cand_prompt,
        "base_mean": base_mean,
        "cand_mean": cand_mean,
        "net": cand_mean - base_mean,
        "escapes_noise": escapes,
        "sign_test_p": agg["item_level"]["sign_test_p"],
        "accepted": accepted,
    }
    new_history = state.history + [entry]
    if accepted:
        return True, EvolutionState(cand_prompt, cand_mean, new_history)
    return False, EvolutionState(state.best_prompt, state.best_score, new_history)
