"""Tests for the soul-fitness one-cycle orchestrator (Probe 3 Task 3).

run_cycle wires variation (proposer) + execution (modified agent on the probe set) +
selection (escape-noise gate). All deps injected -> the loop machinery is verified
end-to-end WITHOUT any LLM or Docker. (The scientific question — does the agent
improve over N cycles — needs the real compute run, NOT this test.)
"""
from evolution import EvolutionState
from evolve_cycle import run_cycle

PROBE = [{"instance_id": f"i{n}"} for n in range(6)]


def _items(pattern):
    return {f"i{n}": v for n, v in enumerate(pattern)}


def test_accepts_when_candidate_lopsided_better():
    base_items = _items([False] * 6)                 # best fails all 6
    state = EvolutionState(best_prompt="P0", best_score=0.0, history=[])
    calls = {}

    def propose_fn(prompt):
        calls["proposed"] = True
        return "```text\nP1 BETTER PROMPT\n```"

    def run_agent_fn(prompt, instances):
        calls["ran_prompt"] = prompt
        return {"patches": "..."}                    # opaque; scored by score_fn

    def score_fn(_patches, _instances):
        return _items([True] * 6)                    # candidate fixes all 6 -> 6-0 escapes

    new_state, new_base = run_cycle(state, PROBE, base_items,
                                    propose_fn=propose_fn, run_agent_fn=run_agent_fn, score_fn=score_fn)
    assert calls["proposed"] is True
    assert calls["ran_prompt"] == "P1 BETTER PROMPT"  # the modified agent ran the candidate prompt
    assert new_state.best_prompt == "P1 BETTER PROMPT"
    assert new_base == _items([True] * 6)             # accepted -> base advances to candidate
    assert new_state.history[-1]["accepted"] is True


def test_empty_proposal_is_noop_no_agent_run():
    base_items = _items([True, False, True, False, True, False])
    state = EvolutionState(best_prompt="P0", best_score=0.5, history=[])
    ran = {"agent": False}

    def propose_fn(_):
        return "no fenced block here"                 # extraction -> "" -> no-op

    def run_agent_fn(_p, _i):
        ran["agent"] = True
        return {}

    new_state, new_base = run_cycle(state, PROBE, base_items,
                                    propose_fn=propose_fn, run_agent_fn=lambda p, i: ran.update(agent=True),
                                    score_fn=lambda a, b: {})
    assert ran["agent"] is False                      # never ran the agent on an empty proposal
    assert new_state.best_prompt == "P0"
    assert new_base == base_items
    assert new_state.history[-1]["accepted"] is False
    assert new_state.history[-1].get("noop") is True


def test_rejects_within_noise_keeps_base():
    base_items = _items([True, True, True, False, False, False])  # 3/6
    state = EvolutionState(best_prompt="P0", best_score=0.5, history=[])

    new_state, new_base = run_cycle(
        state, PROBE, base_items,
        propose_fn=lambda p: "```text\nP1\n```",
        run_agent_fn=lambda p, i: None,
        score_fn=lambda a, b: _items([False, False, False, True, True, True]),  # 3/6, 6 discordant even
    )
    assert new_state.best_prompt == "P0"              # within noise -> rejected
    assert new_base == base_items
    assert new_state.history[-1]["accepted"] is False


def test_failures_passed_to_proposer():
    base_items = _items([True, False, True, False, True, False])
    state = EvolutionState(best_prompt="CUR", best_score=0.5, history=[])
    seen = {}

    def propose_fn(prompt):
        seen["prompt"] = prompt
        return "```text\nX\n```"

    run_cycle(state, PROBE, base_items, propose_fn=propose_fn,
              run_agent_fn=lambda p, i: None, score_fn=lambda a, b: base_items)
    # the proposer prompt must surface the FAILED instance ids (i1,i3,i5), and the current prompt
    assert "CUR" in seen["prompt"]
    assert "i1" in seen["prompt"] and "i3" in seen["prompt"] and "i5" in seen["prompt"]
