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
