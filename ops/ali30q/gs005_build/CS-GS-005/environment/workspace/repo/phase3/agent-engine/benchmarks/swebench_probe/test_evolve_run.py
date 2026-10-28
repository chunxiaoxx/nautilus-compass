"""TDD for Probe 3 Phase B driver (evolve_run.py).

Covers the pure, effect-free pieces — system-template injection, harness report
naming/parsing, and the N-cycle driver's bookkeeping under ENHANCED OBSERVATION
(validation scored on EVERY candidate, best advances only on the escape-noise gate).
The real M3 / Docker effects are exercised only in the live smoke, never here.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from evolve_run import (  # noqa: E402
    inject_system_template,
    report_filename,
    parse_resolve_map,
    run_evolution,
)


# ---- inject_system_template (pure) ----

def test_inject_overrides_system_template_without_mutating_input():
    base = {"agent": {"system_template": "OLD", "instance_template": "KEEP {{task}}"},
            "model": {"model_name": "m"}}
    out = inject_system_template(base, "NEW STRATEGY")
    assert out["agent"]["system_template"] == "NEW STRATEGY"
    # instance_template (submission mechanism) untouched
    assert out["agent"]["instance_template"] == "KEEP {{task}}"
    # input not mutated
    assert base["agent"]["system_template"] == "OLD"


# ---- report_filename (pure) ----

def test_report_filename_slashes_become_double_underscore():
    assert report_filename("anthropic/MiniMax-M3", "probe0") == "anthropic__MiniMax-M3.probe0.json"
    assert report_filename("MiniMax-M3-arm1", "p1arm1") == "MiniMax-M3-arm1.p1arm1.json"


# ---- parse_resolve_map (pure) ----

def test_parse_resolve_map_marks_only_resolved_true(tmp_path):
    rep = tmp_path / "r.json"
    rep.write_text(json.dumps({
        "resolved_ids": ["a"],
        "unresolved_ids": ["b"],
        "error_ids": ["c"],
        "empty_patch_ids": ["d"],
    }), encoding="utf-8")
    m = parse_resolve_map(str(rep))
    assert m == {"a": True, "b": False, "c": False, "d": False}


# ---- run_evolution driver (fakes, no LLM/Docker) ----

PROBE = [{"instance_id": f"p{i}", "problem_statement": f"prob {i}"} for i in range(15)]
VALID = [{"instance_id": f"v{i}", "problem_statement": f"vprob {i}"} for i in range(10)]
# cycle-0 base resolve map on probe (reused from a prior run): 5/15 resolved
BASE_PROBE = {f"p{i}": (i < 5) for i in range(15)}


def _fake_run_agent(prompt, instances):
    # returns a sentinel "patches" object carrying which prompt ran on which set
    return {"prompt": prompt, "ids": [x["instance_id"] for x in instances]}


def test_cycle0_reuses_base_probe_and_scores_validation_once():
    calls = {"agent": 0}

    def run_agent(prompt, instances):
        calls["agent"] += 1
        return _fake_run_agent(prompt, instances)

    def score(patches, instances):
        # validation: base prompt resolves 3/10
        return {iid: (i < 3) for i, iid in enumerate(patches["ids"])}

    # proposer always returns empty -> no candidate, loop is pure cycle-0
    out = run_evolution(PROBE, VALID, 2, "BASE", BASE_PROBE,
                        propose_fn=lambda p: "no fence here",
                        run_agent_fn=run_agent, score_fn=score)
    c0 = out["cycles"][0]
    assert c0["cycle"] == 0
    assert abs(c0["probe_mean"] - 5 / 15) < 1e-9      # probe reused, NOT re-run
    assert abs(c0["val_mean"] - 3 / 10) < 1e-9
    # cycle 0 ran the agent on validation only (probe reused), proposer empty after
    assert calls["agent"] == 1
    # empty proposals -> noop cycles, never accepted
    assert all(c.get("noop") for c in out["cycles"][1:])
    assert out["verdict"]["n_accepts"] == 0


def test_enhanced_scores_validation_every_candidate_even_when_gate_rejects():
    # candidate marginally better on probe (6/15) but NOT lopsided -> gate rejects;
    # yet it lifts validation to 6/10. Enhanced observation must still record that.
    def run_agent(prompt, instances):
        return _fake_run_agent(prompt, instances)

    def score(patches, instances):
        on_probe = patches["ids"][0].startswith("p")
        if patches["prompt"] == "BASE":
            return {iid: (i < (5 if on_probe else 3)) for i, iid in enumerate(patches["ids"])}
        # candidate prompt
        if on_probe:
            return {iid: (i < 6) for i, iid in enumerate(patches["ids"])}   # 6/15, marginal
        return {iid: (i < 6) for i, iid in enumerate(patches["ids"])}       # 6/10 validation

    out = run_evolution(PROBE, VALID, 1, "BASE", BASE_PROBE,
                        propose_fn=lambda p: "```text\nBETTER PROMPT\n```",
                        run_agent_fn=run_agent, score_fn=score)
    c1 = out["cycles"][1]
    assert c1["cycle"] == 1
    assert abs(c1["probe_mean"] - 6 / 15) < 1e-9
    assert abs(c1["val_mean"] - 6 / 10) < 1e-9        # validation recorded despite reject
    # marginal +1 is within noise -> rejected
    assert c1["accepted"] is False
    # enhanced verdict surfaces the best validation any candidate reached
    assert abs(out["verdict"]["val_best_any_mean"] - 6 / 10) < 1e-9
    assert out["verdict"]["val_best_any_cycle"] == 1
    # best-accepted validation stays at cycle 0 (nothing accepted)
    assert abs(out["verdict"]["val_best_accepted_mean"] - 3 / 10) < 1e-9


def test_lopsided_candidate_is_accepted_and_best_advances():
    # candidate resolves a strictly-superset, lopsidedly more -> gate fires, accept.
    def run_agent(prompt, instances):
        return _fake_run_agent(prompt, instances)

    def score(patches, instances):
        on_probe = patches["ids"][0].startswith("p")
        if patches["prompt"] == "BASE":
            return {iid: (i < (5 if on_probe else 3)) for i, iid in enumerate(patches["ids"])}
        # candidate: probe 12/15 (superset of base 5 + 7 new, base's 5 kept), validation 7/10
        if on_probe:
            return {iid: (i < 12) for i, iid in enumerate(patches["ids"])}
        return {iid: (i < 7) for i, iid in enumerate(patches["ids"])}

    out = run_evolution(PROBE, VALID, 1, "BASE", BASE_PROBE,
                        propose_fn=lambda p: "```text\nGREAT PROMPT\n```",
                        run_agent_fn=run_agent, score_fn=score)
    c1 = out["cycles"][1]
    assert c1["accepted"] is True
    assert out["verdict"]["n_accepts"] == 1
    assert abs(out["verdict"]["val_best_accepted_mean"] - 7 / 10) < 1e-9


def test_proposer_sees_current_best_prompt_and_failures():
    seen = {}

    def propose(proposer_prompt):
        seen["prompt"] = proposer_prompt
        return ""   # empty -> noop, we only inspect the framing

    run_evolution(PROBE, VALID, 1, "BASE-PROMPT-XYZ", BASE_PROBE,
                  propose_fn=propose, run_agent_fn=_fake_run_agent,
                  score_fn=lambda patches, inst: {i: False for i in patches["ids"]})
    # proposer prompt embeds the current best prompt and at least one failed instance id
    assert "BASE-PROMPT-XYZ" in seen["prompt"]
    assert "p5" in seen["prompt"]   # p5..p14 are unresolved at base
