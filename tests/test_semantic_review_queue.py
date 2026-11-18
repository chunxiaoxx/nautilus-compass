import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools/distill_pilot"))
import semantic_review_queue as queue


class SemanticReviewQueueTests(unittest.TestCase):
    def test_queue_binds_artifacts_and_keeps_promotion_on_hold(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = root / "runtime"
            memory = root / "memory"
            runtime.mkdir(); memory.mkdir()
            session = "session-a"
            source_sha = "a" * 64
            version = runtime / "incremental_versions" / session / source_sha
            paths = {
                "source": version / "extracted" / f"{session}.txt",
                "summary": version / "summaries" / f"{session}.md",
                "narrative": version / "prod" / f"{session}.md",
                "anchors": version / "prod" / f"{session}.anchors.txt",
            }
            for path in paths.values():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(path.name)
            (runtime / "watermark.json").write_text(json.dumps({"sessions": {
                session: {"source_sha256": source_sha, "status": "published", "j1": 1.0}
            }}))
            result = queue.build_queue(runtime, memory)
            self.assertEqual(result["counts"]["review_required"], 1)
            row = result["items"][0]
            self.assertEqual(row["action"], "review_required")
            self.assertEqual(row["promotion"], "hold")
            self.assertEqual(row["artifact_sha256"]["source"], queue.sha256(paths["source"].read_bytes()))

    def test_reviewed_session_is_not_queued(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); runtime = root / "runtime"; memory = root / "memory"
            runtime.mkdir(); memory.mkdir()
            (runtime / "watermark.json").write_text(json.dumps({"sessions": {
                "session-reviewed": {"semantic_status": "source_reviewed_scoped", "source_sha256": "b" * 64}
            }}))
            result = queue.build_queue(runtime, memory)
            self.assertEqual(result["counts"]["source_reviewed_scoped"], 1)
            self.assertEqual(result["items"], [])


if __name__ == "__main__":
    unittest.main()
