import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools/distill_pilot"))
import semantic_review_worker as worker


class SemanticReviewWorkerProgressTests(unittest.TestCase):
    def test_progress_is_atomic_and_counts_legacy_and_current_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "results.jsonl"
            progress = root / "progress.json"
            output.write_text(
                json.dumps({"session_id": "legacy", "minimax": {"status": "hold"}}) + "\n"
                + json.dumps({"session_id": "current", "status": "hold"}) + "\n",
                encoding="utf-8",
            )
            worker.write_progress(
                progress, output, queue_total=5, selected=2, processed=1,
                state="running", reviewers=("minimax-m3", "kimi-k3-256k"),
                started_at_utc="2026-11-19T00:00:00+00:00",
                last_result={"session_id": "current", "status": "hold"},
            )
            payload = json.loads(progress.read_text(encoding="utf-8"))
            self.assertEqual(payload["reviewed_unique"], 2)
            self.assertEqual(payload["pending_unique"], 3)
            self.assertEqual(payload["status_counts"]["legacy_hold"], 1)
            self.assertEqual(payload["status_counts"]["hold"], 1)
            self.assertFalse(progress.with_name("progress.json.tmp").exists())


if __name__ == "__main__":
    unittest.main()
