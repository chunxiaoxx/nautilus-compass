"""Soul-fitness evolution: one-cycle orchestrator (Probe 3 Task 3).

Wires the three halves: variation (proposer reads the current best + its failures),
execution (the modified agent runs the probe set), selection (escape-noise gate via
`consider_candidate`). All effects are injected (`propose_fn`, `run_agent_fn`,
`score_fn`) so the loop machinery is unit-tested without an LLM or Docker.

`run_cycle` returns (new_state, base_items_for_next_cycle): on accept the base
advances to the candidate's items; on reject/no-op the base is unchanged.
"""
from typing import Callable, Dict, List, Tuple

from evolution import EvolutionState, consider_candidate
from proposer import build_proposer_prompt, extract_proposed_prompt


def run_cycle(
    state: EvolutionState,
    probe_instances: List[Dict],
    base_items: Dict[str, bool],
    *,
    propose_fn: Callable[[str], str],
    run_agent_fn: Callable[[str, List[Dict]], object],
    score_fn: Callable[[object, List[Dict]], Dict[str, bool]],
) -> Tuple[EvolutionState, Dict[str, bool]]:
    """Run one evolution cycle. ``base_items`` = current-best resolve map on the probe."""
    by_id = {inst["instance_id"]: inst for inst in probe_instances}
    failed = [
        {
            "instance_id": iid,
            "problem_statement": by_id.get(iid, {}).get("problem_statement", ""),
            "error": "unresolved by current best",
        }
        for iid in by_id
        if not base_items.get(iid, False)
    ]

    proposer_prompt = build_proposer_prompt(state.best_prompt, failed)
    cand_prompt = extract_proposed_prompt(propose_fn(proposer_prompt))

    if not cand_prompt:
        entry = {"accepted": False, "noop": True, "reason": "empty proposal"}
        return EvolutionState(state.best_prompt, state.best_score, state.history + [entry]), base_items

    patches = run_agent_fn(cand_prompt, probe_instances)
    cand_items = score_fn(patches, probe_instances)
    accepted, new_state = consider_candidate(state, cand_prompt, cand_items, base_items)
    new_base = cand_items if accepted else base_items
    return new_state, new_base
