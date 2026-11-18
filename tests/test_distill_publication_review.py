"""Offline regression of the observed reviewed-card overwrite and its custody boundary."""
import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools/distill_pilot"))
import incremental_distill as incr
import publish_to_memory as pub
from extract_sample import extract_file


class ReviewPublication(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.memory = self.root / "memory"
        self.memory.mkdir()
        self.md = self.root / "session-a.md"
        self.md.write_text("# 当前决定\n新模型用于提取。聊天 429 未绑定评测端点。全链成功未证实。\n")
        self.anchors = self.root / "session-a.anchors.txt"
        self.anchors.write_text("/logs/first-failure.json\n")
        self.source = self.root / "source.jsonl"
        self.source.write_text('新决定。\n会话接口 API Error 429。\n旧接力退出 1，后续仅冒烟退出 0。\n')
        self.source_sha = pub.sha256(self.source.read_bytes())
        self.card = self.memory / "distill-session-a.md"

    def review(self, **changes):
        raw = self.source.read_bytes()
        review = {
            "schema": "distill-source-review/1", "decision": "approved", "session_id": "session-a",
            "source_path": str(self.source), "source_sha256": self.source_sha,
            "summary_sha256": pub.sha256(self.md.read_bytes()),
            "anchors_sha256": pub.sha256(self.anchors.read_bytes()),
            "previous_memory_sha256": pub.sha256(self.card.read_bytes()) if self.card.exists() else None,
            "reviewer": "offline-test-fixture", "reviewed_at_utc": "2026-11-09T00:00:00Z",
            "evidence": [{"id": "source", "path": str(self.source), "sha256": self.source_sha,
                          "line_start": 1, "line_end": 3, "excerpt_sha256": pub.sha256(raw)}],
            "checks": [{"id": key, "status": "supported", "evidence_ids": ["source"],
                        "rationale": "Synthetic fixture only, not production semantic acceptance"}
                       for key in ("latest_decision", "error_attribution", "completion_evidence")],
        }
        review.update(changes)
        path = self.root / "review.json"
        path.write_text(json.dumps(review))
        return path

    def publish(self, review=None):
        return pub.publish_document(self.md, self.anchors, self.memory, self.source_sha, review)

    def test_legacy_reviewed_card_is_never_automatically_replaced(self):
        self.card.write_text("旧版本已按原文核过，无新 metadata。")
        before = self.card.read_bytes()
        receipt = self.publish()
        self.assertEqual(receipt["status"], "review_required")
        self.assertFalse(receipt["changed"])
        self.assertEqual(self.card.read_bytes(), before)

    def test_unreviewed_first_publication_is_labelled_and_idempotent(self):
        receipt = self.publish()
        self.assertEqual(receipt["semantic_status"], "unreviewed_j1_only")
        self.assertFalse(self.publish()["changed"])

    def test_exact_review_replaces_card_and_archives_previous(self):
        self.card.write_text("old card")
        before = self.card.read_bytes()
        review = self.review()
        receipt = self.publish(review)
        self.assertEqual(receipt["semantic_status"], "source_reviewed_scoped")
        archive = self.root / ".published_history/session-a" / (pub.sha256(before) + ".md")
        self.assertEqual(archive.read_bytes(), before)
        self.assertFalse(self.publish(review)["changed"])

    def test_review_cannot_approve_another_summary(self):
        review = self.review()
        self.md.write_text("same-source different summary")
        with self.assertRaisesRegex(ValueError, "exact source and candidate"):
            self.publish(review)
        self.assertFalse(self.card.exists())

    def test_review_cannot_approve_new_source_revision(self):
        review = self.review()
        self.source.write_text(self.source.read_text() + "new decision\n")
        with self.assertRaisesRegex(ValueError, "source changed"):
            self.publish(review)

    def test_concurrent_manual_edit_survives_stale_review(self):
        self.card.write_text("before review")
        review = self.review()
        self.card.write_text("new manual correction")
        with self.assertRaisesRegex(ValueError, "destination changed"):
            self.publish(review)
        self.assertEqual(self.card.read_text(), "new manual correction")

    def test_failed_semantic_check_cannot_publish(self):
        path = self.review()
        review = json.loads(path.read_text())
        review["checks"][1]["status"] = "failed"
        path.write_text(json.dumps(review))
        with self.assertRaisesRegex(ValueError, "unresolved semantic"):
            self.publish(path)

    def test_fabricated_evidence_excerpt_cannot_publish(self):
        path = self.review()
        review = json.loads(path.read_text())
        review["evidence"][0]["excerpt_sha256"] = "0" * 64
        path.write_text(json.dumps(review))
        with self.assertRaisesRegex(ValueError, "excerpt"):
            self.publish(path)

    def test_chat_error_provenance_is_preserved(self):
        self.source.write_text(json.dumps({"type": "assistant", "isApiErrorMessage": True,
            "message": {"model": "<synthetic>", "content": "API Error: 429"}}) + "\n" +
            json.dumps({"type": "assistant", "message": {"content": "评测请求返回 429，详见原日志"}}) + "\n")
        output = self.root / "extracted.txt"
        extract_file(self.source, output)
        text = output.read_text()
        self.assertEqual(text.count("来源类别: chat_api_error"), 1)
        self.assertIn("没有被评测服务端点的绑定证据", text)
        self.assertIn("评测请求返回 429，详见原日志", text)

    def test_real_publisher_pipeline_does_not_overwrite_reviewed_latest_or_recompress(self):
        runtime, bucket = self.root / "runtime", self.root / "bucket"
        runtime.mkdir(); bucket.mkdir()
        path = bucket / "session-a.jsonl"
        path.write_text(json.dumps({"type": "user", "message": {"content": "新决定"}}) + "\n")
        os.utime(path, (time.time()-7200, time.time()-7200))
        self.card.write_text("existing reviewed memory")
        prod = runtime / "summaries_9b_prod/session-a.md"
        prod.parent.mkdir(); prod.write_text("existing reviewed narrative")
        revision = incr.source_revision(path)
        paths = incr.version_paths(runtime, path.stem, revision["sha256"])
        for name, target in paths.items():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("new candidate " + name)
        state = incr.load_state(runtime, self.memory)
        state["sessions"][path.stem] = {"source_sha256": revision["sha256"], "status": "ready", "gate": "ok",
            "j1": 1.0, "artifact_sha256": {k: pub.sha256(v.read_bytes()) for k,v in paths.items()}}
        args = argparse.Namespace(runtime=runtime, memory_dir=self.memory)
        with mock.patch.object(incr, "ensure_server") as server, mock.patch.object(incr, "compress_session") as compressor:
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(incr.run_batch(args, state, [(path, revision)]), 0)
            server.assert_not_called(); compressor.assert_not_called()
        self.assertEqual(state["sessions"][path.stem]["status"], "review")
        self.assertEqual(self.card.read_text(), "existing reviewed memory")
        self.assertEqual(prod.read_text(), "existing reviewed narrative")
        with mock.patch.object(incr, "MIN_SIZE", 1):
            self.assertEqual(incr.collect_pending(bucket, runtime, state), [])

    def test_incremental_requires_semantic_receipt_before_new_publication(self):
        runtime, bucket = self.root / "runtime", self.root / "bucket"
        runtime.mkdir(); bucket.mkdir()
        path = bucket / "session-new.jsonl"
        path.write_text(json.dumps({"type": "user", "message": {"content": "新候选"}}) + "\n")
        self.card.unlink(missing_ok=True)
        revision = incr.source_revision(path)
        paths = incr.version_paths(runtime, path.stem, revision["sha256"])
        for name, target in paths.items():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("new candidate " + name)
        state = incr.load_state(runtime, self.memory)
        state["sessions"][path.stem] = {
            "source_sha256": revision["sha256"], "status": "ready", "gate": "ok", "j1": 1.0,
            "artifact_sha256": {k: pub.sha256(v.read_bytes()) for k, v in paths.items()},
        }
        args = argparse.Namespace(runtime=runtime, memory_dir=self.memory)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(incr.run_batch(args, state, [(path, revision)]), 0)
        self.assertEqual(state["sessions"][path.stem]["status"], "review")
        self.assertEqual(state["sessions"][path.stem]["pending_publication"]["reason"],
                         "semantic_review_receipt_required")
        self.assertFalse((self.memory / "distill-session-new.md").exists())

    def test_pending_selection_excludes_old_and_recursive_sessions(self):
        runtime, bucket = self.root / "runtime", self.root / "bucket"
        runtime.mkdir(); bucket.mkdir()
        recent = bucket / "recent.jsonl"
        recent.write_text("x" * 20)
        old = bucket / "old.jsonl"
        old.write_text("x" * 20)
        recursive = bucket / "recursive.jsonl"
        recursive.write_text(json.dumps({"type": "user", "message": {
            "content": "蒸馏器 prompt 自身回灌 蒸馏纪要 distill-recursive"}}) + "\n")
        now = time.time()
        os.utime(recent, (now - 3600, now - 3600))
        os.utime(old, (now - 8 * 86400, now - 8 * 86400))
        os.utime(recursive, (now - 3600, now - 3600))
        state = incr.load_state(runtime, self.memory)
        with mock.patch.object(incr, "MIN_SIZE", 1), mock.patch.object(incr, "AUTO_MAX_AGE_SECONDS", 7 * 86400):
            default = {p.stem for p, _ in incr.collect_pending(bucket, runtime, state)}
            archive = {p.stem for p, _ in incr.collect_pending(bucket, runtime, state, True)}
        self.assertEqual(default, {"recent"})
        self.assertEqual(archive, {"recent", "old"})


if __name__ == "__main__":
    unittest.main()
