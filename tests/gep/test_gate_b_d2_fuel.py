"""Gate B real-fuel spec 3: compass_exp_d2 (Feishu enum options rebuild loses stable ids).

Fuel provenance: cloud /home/ubuntu/auto-mint/fuel/d2_enum_rebuild_loses_id/
(ledger row consumed 2026-08-22). Real incident (2026-06-12): updating a Feishu
single-select field's options by name-only payload rebuilt every option with NEW ids,
silently breaking all existing row references. This is project-idiosyncratic tribal
knowledge — expected to have genuine headroom after c2e/v1 (generic lessons) measured
delta=0.
"""
from __future__ import annotations

from pathlib import Path

from gep.live_coding_adapter import _valid_d2_source_rule, _valid_d2_transfer, load_value_suite

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "benchmarks" / "dogfood_mvp_v1" / "value_suite_d2_fuel_v1.json"


class TestD2SourceRule:
    def test_accepts_id_merge_rule(self) -> None:
        assert _valid_d2_source_rule(
            "Merge options by stable id: existing names keep their old id (pass the "
            "original object through), only genuinely new names get fresh ids from "
            "max(existing id)+1; rebuilding the list by name alone silently breaks "
            "every existing row reference."
        )

    def test_rejects_name_only_answer(self) -> None:
        assert not _valid_d2_source_rule("update the options list to match the target names")

    def test_rejects_non_string(self) -> None:
        assert not _valid_d2_source_rule(None)


class TestD2Transfer:
    def test_accepts_correct_merge(self) -> None:
        assert _valid_d2_transfer(
            "[{'id': o['id'], 'name': o['name']} for o in existing if o['name'] in target_names]"
            " + [{'id': max(o['id'] for o in existing) + 1 + i, 'name': n}"
            " for i, n in enumerate(n for n in target_names"
            " if n not in {o['name'] for o in existing})]"
        )

    def test_rejects_rebuild_with_fresh_ids(self) -> None:
        # the real incident: rebuild by name, dropping old ids
        assert not _valid_d2_transfer(
            "[{'id': i + 1, 'name': n} for i, n in enumerate(target_names)]"
        )

    def test_rejects_wrong_merge(self) -> None:
        # keeps existing but assigns new ids anyway
        assert not _valid_d2_transfer(
            "[{'id': i + 1, 'name': o['name']} for i, o in enumerate(existing"
            " if o['name'] in target_names)]"
        )

    def test_rejects_non_expression(self) -> None:
        assert not _valid_d2_transfer("def f(existing, target_names): return []")

    def test_rejects_non_string(self) -> None:
        assert not _valid_d2_transfer(5)


class TestD2Suite:
    def test_suite_loads(self) -> None:
        suite = load_value_suite(SUITE)
        assert suite.suite_id == "compass-exp-d2-idmerge-v1"
        tp = suite.loop_plan["task"]["cases"]["transfer"]["prompt"].lower()
        # headroom: prompt must not state the merge-by-id strategy or max+1 rule
        for leak in ("stable id", "keep.*old id", "max(", "merge by id"):
            assert leak not in tp
