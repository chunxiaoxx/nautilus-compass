# -*- coding: utf-8 -*-
"""三门真门 v1(2026-09-30 · P1-2 提前交付 · 替换 /assay/gates 占位判分)。

G1 提取门(自动化):artifacts_ref 可解析(文件存在/URL 可达/坐标格式合法)
  + MINJA 注入核验(轨迹文本含注入模式 → fail,1493 预警的落地);
G2 应用门(自动化):preregistration_ref 可解析(判据库条目存在);
G3 复算门(v1 结构版):声明可重放 + 10% 抽检标记(sample_for_recheck);
聚合:任一 fail→fail;否则任一 unverifiable→unverifiable;全过→pass。
出题触发器(P1-4):fail/unverifiable 条目 POST 回调(webhook 可配置)。
"""
import json, os, re, urllib.request, hashlib, hmac, time
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 18889
CFG_FILE = os.path.join(os.path.dirname(__file__), "gates_config.json")
KEY_FILE = os.path.expanduser("~/.claude/.cache/assay_gates_signing.key")
SIGNING_KEY = open(KEY_FILE, "rb").read() if os.path.exists(KEY_FILE) else b"dev"

INJECTION_PATTERNS = [
    r"ignore.{0,30}instructions",
    r"disregard.{0,20}(above|previous|prior|instructions)",
    r"system prompt.{0,20}(reveal|leak|print|output)",
    r"you are now.{0,30}(new|different)",
    r"</?(system|tool)_?prompt>",
    r"\bDAN\b.{0,10}mode",
    r"(忽|无)视.{0,8}(以|上|前)(的)?(全部)?(指|指?令)",
]
INJ_RE = [re.compile(p, re.I) for p in INJECTION_PATTERNS]
CRIT_KEYS = re.compile(r"(criteria|判据)@([A-Za-z0-9_\-\.]+)(?:#([A-Za-z0-9_\-\.]+))?")


def load_cfg():
    if os.path.exists(CFG_FILE):
        return json.load(open(CFG_FILE, encoding="utf-8"))
    return {"recheck_rate": 0.10, "question_webhook": ""}


CFG = load_cfg()


def _resolvable(ref):
    if not ref or not isinstance(ref, str):
        return False
    if ref.startswith(("http://", "https://")):
        try:
            r = urllib.request.urlopen(urllib.request.Request(
                ref, method="HEAD", headers={"User-Agent": "assay-g1/1.0"}), timeout=10)
            return r.status < 400
        except Exception:
            return False
    if ref.startswith(("repo@", "git@", "sha256:")):
        return len(ref) > 10
    return os.path.exists(ref)


def gate_g1(t):
    """可寻址 + 注入核验。"""
    if not _resolvable(t.get("artifacts_ref")):
        return "unverifiable", "artifacts_ref unresolvable"
    text = t.get("text", "") or ""
    for rx in INJ_RE:
        m = rx.search(text)
        if m:
            return "fail", f"injection pattern: {m.group(0)[:40]!r}"
    return "pass", ""


def gate_g2(t):
    """判据引用回查 catalog 真身(v5 1669 加严补丁语义):
    criteria@<catalog>#<entry> 须 ① catalog 在 catalog_paths 配置 ② 文件存在
    ③ 条目 id 在文件内;任一不满足 → unverifiable(诚实暴露未接线,不静默放行)。
    非判据引用(路径/URL)走 _resolvable 旧径。"""
    ref = t.get("preregistration_ref", "")
    if not ref:
        return "unverifiable", "no preregistration"
    if not isinstance(ref, str):
        return "unverifiable", "preregistration unresolvable"
    m = CRIT_KEYS.search(ref)
    if not m:
        return ("pass", "") if _resolvable(ref) else \
               ("unverifiable", "preregistration unresolvable")
    catalog, entry = m.group(2), m.group(3)
    path = (CFG.get("catalog_paths") or {}).get(catalog)
    if not path:
        return "unverifiable", f"catalog {catalog} not wired"
    if not os.path.exists(path):
        return "unverifiable", f"catalog {catalog} file missing: {path}"
    if not entry:
        return "unverifiable", f"criteria@{catalog} without entry id (#C-xxx)"
    try:
        body = open(path, encoding="utf-8").read()
    except Exception:
        return "unverifiable", f"catalog {catalog} unreadable"
    if entry not in body:
        return "unverifiable", f"entry {entry} not in catalog {catalog}"
    return "pass", ""


def gate_g3(t):
    """v1 结构版:重放声明存在 + 按率抽检标记。"""
    if not t.get("replay_ref") and not t.get("artifacts_ref"):
        return "unverifiable", "nothing replayable"
    return "pass", ""


def judge(t):
    sid = str(t.get("session_id", ""))
    g1, why1 = gate_g1(t)
    g2, why2 = gate_g2(t)
    g3, why3 = gate_g3(t)
    verdicts = [g1, g2, g3]
    v = "fail" if "fail" in verdicts else \
        ("unverifiable" if "unverifiable" in verdicts else "pass")
    recheck = v == "pass" and (hash(sid) % 100) < int(CFG["recheck_rate"] * 100)
    detail = {k: w for k, w in (("g1", why1), ("g2", why2), ("g3", why3)) if w}
    return sid, {"verdict": v, "g1": g1, "g2": g2, "g3": g3,
                 "sample_for_recheck": recheck, "detail": detail}


def fire_question_hook(results):
    """P1-4 出题触发器:fail/unverifiable → webhook(判分→自动出题)。"""
    hook = CFG.get("question_webhook")
    if not hook:
        return 0
    payload = [sid for sid, r in results.items()
               if r["verdict"] in ("fail", "unverifiable")]
    if payload:
        try:
            urllib.request.urlopen(urllib.request.Request(
                hook, data=json.dumps({"gate_failures": payload}).encode(),
                headers={"Content-Type": "application/json"}), timeout=10)
            return len(payload)
        except Exception:
            return -1
    return 0


class H(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/assay/gates":
            self.send_response(404); self.end_headers(); return
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        results = dict(judge(t) for t in body.get("trajectories", []))
        fired = fire_question_hook(results)
        ts = time.time()
        payload = json.dumps({"verdicts": {k: v["verdict"] for k, v in results.items()},
                              "detail": results, "hook_fired": fired, "ts": ts},
                             sort_keys=True, ensure_ascii=False)
        sig = hmac.new(SIGNING_KEY, payload.encode(), hashlib.sha256).hexdigest()
        out = json.dumps({"verdicts": {k: v["verdict"] for k, v in results.items()},
                          "detail": results, "hook_fired": fired,
                          "signature": sig, "ts": ts}, ensure_ascii=False)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(out.encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"service":"assay-gates-v1","gates":"G1+G2+G3 real"}')

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", PORT), H).serve_forever()
