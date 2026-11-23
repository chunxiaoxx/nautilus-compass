"""Offline regressions for independently reproduced candidate/admission failures."""
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tools/distill_pilot"), str(ROOT / "tools")]
import export_fuel_candidates as exporter
import p3_delta as p3
import publish_to_memory as publisher


class CandidateRegressions(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        source = self.root / "source.jsonl"
        source.write_text('Latest decision is B.\n')
        compressed = self.root / "summary.md"
        compressed.write_text('Decision A.\n')
        sha = exporter.digest(source.read_bytes())
        self.case = {
            "case_id": "fixture", "session_id": "11111111-1111-4111-8111-111111111111", "source_sha256": sha,
            "rights": {"local_candidate_allowed": True, "external_upload_allowed": False,
                       "training_allowed": False, "basis": "synthetic test"},
            "reviewer": "test reviewer", "fact_status": "source_supported",
            "evidence": [{"id": "decision", "path": str(source), "sha256": sha,
                          "line_start": 1, "line_end": 1, "excerpt_sha256": sha}],
            "compression_artifact": {"path": str(compressed), "sha256": exporter.digest(compressed.read_bytes())},
            "situation": "Old decision differs from latest.", "content": "Latest B.",
            "question": "What is current?", "response": "A", "source_reference": "Latest B.",
            "proposed_label": "fail",
            "facts": [{"text": "Latest B.", "fact_status": "source_supported", "evidence_ids": ["decision"]}],
        }
        self.manifest = self.root / "manifest.json"
        self.pool = self.root / "candidates.jsonl"

    def run_export(self, case=None):
        self.manifest.write_text(json.dumps({"cases": [case or self.case]}))
        return exporter.export(self.manifest, self.pool)

    def test_all_exported_metadata_strings_redacted(self):
        marker = "synthetic-person@example.invalid"
        token = "sk-" + "A" * 40
        self.case["reviewer"] = marker + " " + token
        self.case["rights"]["basis"] = marker + " " + token
        self.case["facts"][0]["review_note"] = [marker, token]
        raw = json.dumps(exporter.candidate(self.case))
        self.assertNotIn(marker, raw)
        self.assertNotIn(token, raw)

    def test_label_and_reviewer_corrections_get_revision_receipts(self):
        first = self.run_export()
        self.assertEqual(first["new"], 1)
        self.case["proposed_label"] = "pass"
        second = self.run_export()
        self.assertEqual(second["new"], 1)
        self.assertEqual(len(second["revisions"]), 1)
        self.case["reviewer"] = "corrected reviewer"
        third = self.run_export()
        self.assertEqual(third["new"], 1)
        rows = [json.loads(line) for line in self.pool.read_text().splitlines()]
        self.assertEqual(len({r["content_hash"] for r in rows}), 1)
        self.assertEqual(len({r["candidate_revision_sha256"] for r in rows}), 3)
        self.assertEqual(rows[1]["supersedes_candidate_revision_sha256"], rows[0]["candidate_revision_sha256"])
        self.assertEqual(self.run_export()["duplicates"], 1)

    def test_phone_like_digit_run_in_real_sha_is_preserved(self):
        source = Path(self.case["evidence"][0]["path"])
        for index in range(10000):
            raw = ("Synthetic source %d\n" % index).encode()
            sha = exporter.digest(raw)
            if exporter.clean(sha) != sha:
                break
        else:
            self.fail("Could not construct the hash-redaction regression fixture")
        source.write_bytes(raw)
        self.case["source_sha256"] = sha
        self.case["evidence"][0].update(sha256=sha, excerpt_sha256=sha)
        row = exporter.candidate(self.case)
        self.assertEqual(row["source_revision"], sha)
        self.assertEqual(row["verification"]["evidence_sha256"], [sha])
        for key in ("content_hash", "candidate_key", "candidate_revision_sha256", "compression_artifact_sha256"):
            self.assertRegex(row[key], r"^[a-f0-9]{64}$")

    def test_failed_replace_preserves_existing_pool_and_retry(self):
        self.run_export()
        before = self.pool.read_bytes()
        self.case["content"] += " revised"
        with mock.patch.object(publisher.os, "replace", side_effect=OSError("synthetic disk failure")):
            with self.assertRaises(OSError):
                self.run_export()
        self.assertEqual(self.pool.read_bytes(), before)
        self.assertEqual(self.run_export()["new"], 1)

    def test_partial_temporary_write_preserves_existing_pool_and_retry(self):
        self.run_export()
        before = self.pool.read_bytes()
        self.case["content"] += " revised"
        original = publisher.os.fdopen

        class PartialWriter:
            def __init__(self, file):
                self.file = file
            def __enter__(self):
                return self
            def __exit__(self, *args):
                self.file.close()
            def write(self, data):
                self.file.write(data[:80])
                self.file.flush()
                raise OSError("synthetic partial write")

        with mock.patch.object(publisher.os, "fdopen", side_effect=lambda *a, **k: PartialWriter(original(*a, **k))):
            with self.assertRaises(OSError):
                self.run_export()
        self.assertEqual(self.pool.read_bytes(), before)
        self.assertEqual(self.run_export()["new"], 1)

    def test_preexisting_invalid_pool_is_preserved_with_explicit_error(self):
        self.pool.write_bytes(b'{"partial":')
        with self.assertRaisesRegex(ValueError, "invalid_preserved_for_review"):
            self.run_export()
        self.assertEqual(self.pool.read_bytes(), b'{"partial":')

    def test_invalid_label_rejected(self):
        self.case["proposed_label"] = "unapproved"
        result = self.run_export()
        self.assertEqual(result["new"], 0)
        self.assertEqual(result["rejected"][0]["reason"], "invalid_proposed_label")

    def test_origin_flip_cannot_admit_pending_candidate(self):
        row = exporter.candidate(self.case)
        row["label_origin"] = "human_review"
        self.assertEqual(p3.admission_error(row), "invalid_truth_label")
        row["truth_label"] = "pass"
        self.assertEqual(p3.admission_error(row), "training_explicitly_not_allowed")
        row["rights"]["training_allowed"] = True
        row["training_admission"]["allowed"] = True
        self.assertEqual(p3.admission_error(row), "candidate_not_admitted_for_training")

    def test_legacy_valid_judgment_compatible_but_null_label_rejected(self):
        row = {"label_origin": "official_rule", "truth_label": "pass", "domain": "judge_verdict"}
        self.assertIsNone(p3.admission_error(row))
        row["truth_label"] = None
        self.assertEqual(p3.admission_error(row), "invalid_truth_label")

    def test_rejection_not_in_accepted_ledger_and_later_revision_reconsidered(self):
        delta = self.root / "corpus/delta"
        inbox = delta / "inbox"
        inbox.mkdir(parents=True)
        fingerprints = delta / "accepted_hashes.json"
        fingerprints.write_text("[]")
        row = exporter.candidate(self.case)
        paths = {"CORPUS": delta.parent, "DELTA": delta, "INBOX": inbox,
                 "ABSORBED": delta / "absorbed", "FINGERPRINTS": fingerprints}
        with contextlib.ExitStack() as stack:
            for key, value in paths.items():
                stack.enter_context(mock.patch.object(p3, key, value))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            (inbox / "fixture.jsonl").write_text(json.dumps(row) + "\n")
            p3.main()
            self.assertEqual(json.loads(fingerprints.read_text()), [])
            # Synthetic fully admitted fixture only: no production admission.
            approved = copy.deepcopy(row)
            approved.update(label_origin="human_review", truth_label="pass", candidate_status="approved_for_training")
            approved["rights"]["training_allowed"] = True
            approved["training_admission"]["allowed"] = True
            (inbox / "fixture.jsonl").write_text(json.dumps(approved) + "\n")
            p3.main()
            self.assertEqual(json.loads(fingerprints.read_text()), [row["content_hash"]])
            self.assertEqual(len(list(delta.glob("delta_*.jsonl"))), 1)


if __name__ == "__main__":
    unittest.main()
