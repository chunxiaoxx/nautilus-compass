"""Gate B real-fuel spec 4: compass-exp-d3-payload (Feishu options payload, de-hinted).

Fuel provenance: same ledger consumed record as d2 (d2_enum_rebuild_loses_id,
2026-06-12 incident). d3 is the ③-class tribal-fact design: the transfer prompt
states only the observable requirement (final names), while the id-preservation
mechanism exists solely in the source experience — unlike d2, whose transfer
prompt leaked the merge semantics and glm-5.3 could derive it 1/3 of the time.
"""
from __future__ import annotations

from pathlib import Path

from gep.live_coding_adapter import _valid_d2_source_rule, _valid_d2_transfer, load_value_suite

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "benchmarks" / "dogfood_mvp_v1" / "value_suite_d3_fuel_v1.json"


class TestD3Suite:
    def test_suite_loads(self) -> None:
        suite = load_value_suite(SUITE)
        assert suite.suite_id == "compass-exp-d3-payload-v1"

    def test_transfer_prompt_is_de_hinted(self) -> None:
        suite = load_value_suite(SUITE)
        tp = suite.loop_plan["task"]["cases"]["transfer"]["prompt"].lower()
        # headroom: prompt must not state the id-preservation mechanism
        for leak in ("merge", "preserve", "keep", "stable id", "old id", "rebuild", "透传", "carry"):
            assert leak not in tp, f"transfer prompt leaks tribal knowledge: {leak!r}"

    def test_source_prompt_states_tribal_rule(self) -> None:
        suite = load_value_suite(SUITE)
        sp = suite.loop_plan["task"]["cases"]["source"]["prompt"].lower()
        assert "rebuild" in sp and "id" in sp

    def test_oracle_registered(self) -> None:
        from gep.live_coding_adapter import _GATE_B_SPECS

        assert "compass-exp-d3-payload-v1" in _GATE_B_SPECS


class TestD3ValidatorsReuseD2Semantics:
    def test_source_rule_accepts_id_echo(self) -> None:
        assert _valid_d2_source_rule(
            "Merge options by stable id: existing names keep their old id (pass the "
            "original object through), only genuinely new names get fresh ids from "
            "max(existing id)+1; rebuilding the list by name alone silently breaks "
            "every existing row reference."
        )

    def test_transfer_accepts_id_preserving_merge(self) -> None:
        assert _valid_d2_transfer(
            "[{'id': o['id'], 'name': o['name']} for o in existing if o['name'] in target_names]"
            " + [{'id': max(o['id'] for o in existing) + 1 + i, 'name': n}"
            " for i, n in enumerate(n for n in target_names"
            " if n not in {o['name'] for o in existing})]"
        )

    def test_transfer_rejects_name_only_rebuild(self) -> None:
        # the incident itself: rebuild by name, dropping ids — must fail the oracle
        assert not _valid_d2_transfer(
            "[{'id': i + 1, 'name': n} for i, n in enumerate(target_names)]"
        )
