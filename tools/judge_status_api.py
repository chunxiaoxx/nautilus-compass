#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""判读卡状态 API(P2 待建件,R333 主件):受理台账只读查询。
数据源:platform_nau_ledger + 受理登记表(暂用书信 trace 代替,v1 接 intake 台账);
输出:GET /api/judge_status?id=<受理编号> → 六步状态 JSON。"""
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import urllib.parse

# v0 演示台账(受理 API 上线前;与 status.html DEMO 同源)
LEDGER = {
    "nautilus-l1-0004": {
        "title": "4096/9225 冲正重算窗 · 五门独立验收(compass 判读)",
        "status": "done",
        "criteria_sha16": "b81eca8436887785",
        "steps": [
            ["2026-10-09T01:0x+08", "recompute_executed_by_platform", "done"],
            ["2026-10-09T08:3x+08", "independent_db_verification", "done"],
            ["2026-10-09T08:4x+08", "five_gate_verdict", "done"],
            ["2026-10-09T08:4x+08", "card_issued", "done"]],
        "result_url": "/criteria/",
        "verdict": "pass",
        "evidence": "Five gates independently verified via read-only SQL (not self-report): A1 last-row SUM=balance_after 0/37 mismatch; A2 continuity+first-row 0 violations; A4 both trigger functions contain SUM(delta), mounts stake=BEFORE UPDATE OF claimed_by / release=AFTER UPDATE OF status; A5 ledger rows 9315/9322 = -20 stake, balance 30236/30452 exact match vs v5 pre-run baseline; roster 0 real drift (36 seed-only-by-design agents disclosed, per #10712). A3 ERRATUM (per #10761 final state): 209 orphan stakes re-audited by platform — 201 were false duplicates (slash backfill reversal, append-only), 8 real debts repaid (+50 NAU); user approval no longer required, case closed. A3 gate semantics V2: orphan = same bounty with no release/slash row across agents (pool-wide NOT EXISTS). Formula erratum accepted: A1 last-row semantics + A2 prev_bal+current-delta (independent run used corrected forms). Evidence: docs/metering/S6_RECOMPUTE_ACCEPTANCE_20261009.md V2.",
    },
    "nautilus-l1-0003": {
        "title": "S6 recompute fidelity · Round1 A-arm 30-case recompute",
        "status": "done",
        "criteria_sha16": "b81eca8436887785",
        "steps": [
            ["2026-10-08T20:49+08", "recompute_batches_1_15", "done"],
            ["2026-10-09T02:20+08", "four_bucket_merge", "done"],
            ["2026-10-09T02:40+08", "fidelity_compare_vs_orig_3_reports", "done"],
            ["2026-10-09T02:50+08", "card_issued", "done"]],
        "result_url": "/registry.html",
        "verdict": "pass",
        "evidence": "29/30 per-case four-bucket identical vs original run (9R/5U/2EP exact; sole drift django-16560 error->resolved, direction aligned with Round1 judging-fix precedent). Reports: runtime/s6_runs/ (15, VCS-protected). Doc: docs/metering/S6_RECOMPUTE_FIDELITY_20261009.md. Issuer=self, independently recomputable (batch_run.sh + preds_arm_a.json).",
    },
    "nautilus-l1-0001": {
        "title": "Round 1 · v5-harness vs mini-swe-agent",
        "status": "done",
        "criteria_sha16": "b81eca8436887785",
        "steps": [
            ["2026-10-05T14:02+08", "intake", "done"],
            ["2026-10-05T14:20+08", "criteria_prereg", "done"],
            ["2026-10-06T02:10+08", "three_state_judging", "done"],
            ["2026-10-06T02:15+08", "self_recheck", "done"],
            ["2026-10-06T02:30+08", "card_issued", "done"],
            ["2026-10-06T03:00+08", "casebook_entry", "done"]],
        "result_url": "/leaderboard.html",
    },
    "nautilus-l1-0002": {
        "title": "L1 selftest-claude-code v1.0.0 · 平台自检单(管线首例)",
        "status": "done",
        "criteria_sha16": "5c8e0a7ce3a0048b",
        "verdict": "insufficient_evidence",
        "steps": [
            ["2026-10-08T12:01+08", "intake", "done"],
            ["2026-10-08T16:30+08", "criteria_prereg", "done"],
            ["2026-10-08T16:35+08", "metadata_check", "done"],
            ["2026-10-08T16:40+08", "three_state_judging", "done"],
            ["2026-10-08T16:45+08", "card_issued", "done"]],
        "verdict_detail": {
            "metadata": "[实测] repo=anthropics/claude-code HTTP 200(149820 stars);version_anchor=1.0.0 npm 口径可锚(git tag 无——单未声明锚口径,披露)",
            "evaluation_evidence": "[实测缺失] 任务集读数(SWE-bench Verified resolved%)=零;评测产物=零;模型配置/采样参数=零",
            "three_state": "insufficient_evidence —— 无可判读评测读数;单据自述『平台自检单,非真实评测需求』与证据状态一致",
            "disposition": "不予收录(不进名次区/观察区);管线 intake→judging→delivered 首例走通;可携评测产物重提走正常判读",
        },
        "submission": "72fdcb665e79482b",
        "result_url": "/leaderboard.html",
    },
    "demo": {
        "title": "(示例)L1 收取中",
        "status": "running",
        "steps": [
            ["-", "intake", "done"],
            ["-", "criteria_prereg", "running"],
            ["-", "three_state_judging", "queued"],
            ["-", "card_issued", "queued"]],
    },
}


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path != "/api/judge_status":
            self.send_response(404); self.end_headers(); return
        q = urllib.parse.parse_qs(u.query)
        # 无参默认返回可查询卡清单(2026-10-08 修:原默认 demo 卡被平台复核
        # 误读为"API 返 demo 无 sha"——10664;demo 卡仅 ?id=demo 显式可查)
        cid = (q.get("id") or [""])[0].strip()
        if not cid:
            rec = {"ok": True, "cards": sorted(LEDGER.keys()),
                   "note": "pass ?id=<card_id> to query; live cards carry criteria_sha16"}
            self.send_response(200)
            body = json.dumps(rec, ensure_ascii=False).encode()
        elif (rec := LEDGER.get(cid)) is not None:
            self.send_response(200)
            body = json.dumps({"ok": True, "id": cid, **rec},
                              ensure_ascii=False).encode()
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print("judge_status api on :9890")
    ThreadingHTTPServer(("127.0.0.1", 9890), H).serve_forever()
