"""Regression controls for source-bound tool evidence in session extraction."""
import hashlib
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools/distill_pilot"))
import extract_sample as extractor
import compress_arm as compressor


class ToolEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "session.jsonl"
        self.output = self.root / "extracted.txt"

    def write(self, rows):
        self.source.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))

    def call(self, identifier="call-a", uuid="assistant-a", name="Bash"):
        return {"type": "assistant", "uuid": uuid, "timestamp": "2026-11-01T16:18:58Z",
                "message": {"content": [{"type": "tool_use", "id": identifier,
                                         "name": name, "input": {"command": "ls NanoJev"}}]}}

    def result(self, identifier="call-a", parent="assistant-a", text="NanoJev\n"):
        return {"type": "user", "uuid": "result-a", "sourceToolAssistantUUID": parent,
                "message": {"content": [{"type": "tool_result", "tool_use_id": identifier,
                                         "is_error": False, "content": text}]}}

    def extract(self, **kwargs):
        stats = extractor.extract_file(self.source, self.output, include_tool_evidence=True, **kwargs)
        records = [json.loads(line) for line in self.output.read_text().splitlines()
                   if line.startswith('{"kind": "tool_')]
        return stats, records

    def test_default_text_output_retains_legacy_bytes(self):
        self.write([{"type": "user", "timestamp": "t1", "message": {"content": "请核查"}},
                    self.call(), self.result(),
                    {"type": "assistant", "timestamp": "t4", "message": {"content": [{"type": "text", "text": "待核对"}, {"type": "thinking", "thinking": "private"}]}}])
        stats = extractor.extract_file(self.source, self.output)
        self.assertEqual(self.output.read_text(), "=== u #1 t1 ===\n请核查\n=== a #4 t4 ===\n待核对\n")
        self.assertEqual((stats["n_user_msg"], stats["n_asst_msg"]), (1, 1))
        self.assertNotIn("tool_evidence", stats)

    def test_tool_result_binds_call_line_uuid_and_original_bytes(self):
        self.write([self.call(), self.result()])
        source_bytes = self.source.read_bytes()
        stats, records = self.extract()
        call, result = records
        self.assertEqual(stats["tool_evidence"]["source_sha256"], hashlib.sha256(source_bytes).hexdigest())
        self.assertEqual(result["source_line"], 2)
        self.assertEqual(result["source_block"], 0)
        self.assertEqual(result["tool_name"], "Bash")
        self.assertEqual(result["call_match"]["status"], "matched")
        self.assertEqual(result["call_match"]["candidates"][0]["source_line"], 1)
        self.assertEqual(call["source_line_sha256"], hashlib.sha256(source_bytes.splitlines(keepends=True)[0]).hexdigest())
        self.assertEqual(self.source.read_bytes(), source_bytes)

    def test_false_outer_error_flag_does_not_remove_shell_error(self):
        result = self.result(text="NanoJev\n(eval):1: no matches found: /Projects/*assay*\n")
        result["toolUseResult"] = {"exit_code": 2}
        self.write([self.call(), result])
        _, records = self.extract()
        self.assertFalse(records[-1]["reported_is_error"])
        self.assertEqual(records[-1]["reported_exit_codes"], {"exit_code": 2})
        self.assertIn("no matches found", records[-1]["text_head"])

    def test_duplicate_ids_require_matching_parent_or_report_ambiguity(self):
        self.write([self.call(uuid="first", name="Read"), self.call(uuid="second"),
                    self.result(parent="first"), self.result(parent=None)])
        _, records = self.extract()
        self.assertEqual(records[2]["tool_name"], "Read")
        self.assertEqual(records[2]["call_match"]["status"], "matched")
        self.assertEqual(records[3]["call_match"]["status"], "ambiguous")
        self.assertNotIn("tool_name", records[3])

    def test_request_blob_replays_do_not_count_as_new_tool_execution(self):
        replay = self.call()
        replay['type'] = 'api-request-blob'
        self.write([self.call(), replay, self.result()])
        stats, records = self.extract()
        self.assertEqual(stats['tool_evidence']['tool_records_seen'], 2)
        self.assertEqual(records[-1]['call_match']['status'], 'matched')

    def test_unknown_or_conflicting_invocation_is_explicit(self):
        self.write([self.call(), self.result(identifier="other"), self.result(parent="other")])
        _, records = self.extract()
        self.assertEqual([r["call_match"]["status"] for r in records[1:]], ["unmatched", "unmatched"])

    def test_head_tail_budget_reports_missing_source_text(self):
        self.write([self.call(), self.result(text="A" * 100 + "ERROR_IN_MIDDLE" + "Z" * 100)])
        stats, records = self.extract(tool_excerpt_chars=40, tool_budget_chars=20)
        self.assertLessEqual(stats["tool_evidence"]["excerpt_chars"], 20)
        self.assertGreater(records[-1]["omitted_text_chars"], 0)
        self.assertTrue(records[-1]["text_head"].startswith("A"))
        self.assertTrue(records[-1]["text_tail"].endswith("Z"))
        self.assertEqual(records[-1]["text_chars"], 215)

    def test_record_limit_keeps_edges_and_links_omitted_call(self):
        self.write([self.call(identifier="first"), self.result(identifier="first"),
                    self.call(identifier="last", uuid="last-parent"),
                    self.result(identifier="last", parent="last-parent")])
        stats, records = self.extract(tool_record_limit=2)
        self.assertEqual([r["source_line"] for r in records], [1, 4])
        self.assertEqual(stats["tool_evidence"]["tool_records_omitted"], 2)
        self.assertEqual(records[-1]["call_match"]["candidates"][0]["source_line"], 3)

    def test_zero_limits_and_nontext_blocks(self):
        result = self.result()
        result["message"]["content"][0]["content"] = [{"type": "text", "text": "visible"}, {"type": "image", "data": "binary-secret"}]
        self.write([self.call(), result])
        stats, records = self.extract(tool_record_limit=0)
        self.assertEqual(records, [])
        self.assertEqual(stats["tool_evidence"]["tool_records_omitted"], 2)
        _, records = self.extract(tool_excerpt_chars=0)
        self.assertEqual(records[-1]["text_chars"], 7)
        self.assertNotIn("binary-secret", self.output.read_text())

    def test_api_error_provenance_and_tool_only_user_role(self):
        self.write([self.call(), self.result(), {"type": "assistant", "isApiErrorMessage": True,
                    "message": {"content": "API Error: ECONNREFUSED"}}])
        stats, _ = self.extract()
        self.assertIn("来源类别: chat_api_error", self.output.read_text())
        self.assertEqual(stats["n_user_msg"], 0)
        self.assertEqual(stats["n_asst_msg"], 1)

    def test_source_change_preserves_previous_output(self):
        self.write([{"type": "user", "message": {"content": "request"}}])
        self.output.write_text("previous verified extraction")
        real_loads = json.loads
        changed = False
        def changing_loads(text):
            nonlocal changed
            value = real_loads(text)
            if not changed:
                changed = True
                with self.source.open("a") as stream:
                    stream.write('{}\n')
            return value
        with mock.patch.object(extractor.json, "loads", side_effect=changing_loads):
            with self.assertRaisesRegex(RuntimeError, "changed"):
                self.extract()
        self.assertEqual(self.output.read_text(), "previous verified extraction")

    def test_metadata_only_change_is_checked_against_source_bytes(self):
        self.write([self.call(), self.result()])
        original = self.source.read_bytes()
        real_loads = json.loads
        def metadata_update(text):
            value = real_loads(text)
            self.source.chmod(0o600)
            return value
        with mock.patch.object(extractor.json, "loads", side_effect=metadata_update):
            self.extract()
        self.assertEqual(self.source.read_bytes(), original)

    def test_malformed_records_and_commands_are_inert(self):
        marker = self.root / "must-not-exist"
        call = self.call()
        call["message"]["content"][0]["input"] = {"command": "touch " + str(marker)}
        self.write([[], {"type": "user", "message": "bad"}, call, self.result()])
        with self.source.open("a") as stream:
            stream.write('invalid-json\n')
        self.extract()
        self.assertFalse(marker.exists())
        with self.assertRaises(ValueError):
            extractor.extract_file(self.source, self.source)

    def test_compression_tool_rules_apply_to_chunks_and_rollup(self):
        self.output.write_text("=== u #1 ===\nrequest\n=== tool_result #2 ===\nresult\n")
        summary = self.root / "summary.md"
        with mock.patch.object(compressor, "chat", return_value="source-bound note") as chat:
            compressor.compress_session(self.output, summary, "local", "model", 24, tool_evidence=True)
        self.assertGreaterEqual(chat.call_count, 3)
        self.assertTrue(all(compressor.TOOL_EVIDENCE_CONTEXT in call.args[2] for call in chat.call_args_list))
        self.assertIn(hashlib.sha256(self.output.read_bytes()).hexdigest(), summary.read_text())

    def test_text_only_compression_keeps_existing_prompt(self):
        self.output.write_text("ordinary text")
        with mock.patch.object(compressor, "chat", return_value="note") as chat:
            compressor.compress_session(self.output, self.root / "summary.md", "local", "model", 1000)
        self.assertEqual(chat.call_args.args[2], compressor.SYSTEM_CHUNK)

    def test_changed_compression_input_preserves_previous_summary(self):
        self.output.write_text("original input")
        summary = self.root / "summary.md"
        summary.write_text("previous reviewed summary")
        def changed(*args):
            self.output.write_text("new input")
            return "candidate"
        with mock.patch.object(compressor, "chat", side_effect=changed):
            with self.assertRaisesRegex(RuntimeError, "changed"):
                compressor.compress_session(self.output, summary, "local", "model", 1000, tool_evidence=True)
        self.assertEqual(summary.read_text(), "previous reviewed summary")

    def test_tool_mode_cli_replaces_old_cache_with_history_then_reuses_bound_output(self):
        extracted = self.root / 'extracted'
        extracted.mkdir()
        (extracted / 'session.txt').write_text('source tool evidence')
        summaries = self.root / 'summaries_local'
        summaries.mkdir()
        summary = summaries / 'session.md'
        summary.write_text('legacy summary')
        manifest = self.root / 'manifest.json'
        manifest.write_text(json.dumps({'groups': {'review': [{'session_id': 'session'}]}}))
        args = ['compress_arm.py', '--manifest', str(manifest), '--out', str(self.root),
                '--groups', 'review', '--tool-evidence']
        with mock.patch.object(sys, 'argv', args), mock.patch.object(compressor, 'chat', return_value='new note') as chat, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(compressor.main(), 0)
            self.assertEqual(chat.call_count, 1)
            self.assertEqual(compressor.main(), 0)
            self.assertEqual(chat.call_count, 1)
        history = list((summaries / 'history/session.md').glob('*.md'))
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].read_text(), 'legacy summary')


if __name__ == "__main__":
    unittest.main()
