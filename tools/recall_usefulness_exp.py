"""recall 有用性对照实验(cnt_recall_usefulness_20260823)。

问题:compass 的 recall 从未被外部裁决过"它改变过哪次任务结局"。
方法:Gate B 同款对照——
  control  : 裸模型答部落事实题
  treatment: 先自然语言 recall(查询词不含答案机制)→ top-3 注入 → 再答
  oracle   : 确定性判据(F1 复用 _valid_d2_transfer)
分层归因:
  miss        = 检索未命中(top-3 无正确记忆)
  inject_fail = 命中但答案仍错
  pass        = 命中且答对
输出:experiments 输出 json + stdout 摘要。负结果如实记录。
"""
from __future__ import annotations

import json
import os
import socket
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gep.live_coding_adapter import _valid_d2_transfer  # noqa: E402

DAEMON = ("127.0.0.1", 9876)
MODEL = "glm-5.3"
OUT = Path(__file__).resolve().parents[1] / "outputs" / "recall_usefulness_20260823.json"

FACTS = [
    {
        "id": "F1-feishu-id",
        "query": "飞书多维表格更新字段选项后既有数据全丢了,之前踩过这个坑,怎么处理",
        "question": (
            "Prepare the options payload for a Bitable single-select field update. "
            "Variables in scope: existing = the field's current options as returned "
            "by the field API (a list of small dicts); target_names = the final "
            "option names this field must have after the update. Return ONE Python "
            "expression in terms of existing and target_names that evaluates to the "
            "options list to send in the update request body. Only stdlib builtins "
            "like max/enumerate/sorted; no lambda, no def, no imports."
        ),
        "hit_keywords": ["飞书", "单选", "id"],
        "oracle": lambda a: _valid_d2_transfer(a),
    },
    {
        "id": "F2-daemon-port",
        "query": "nautilus-compass 本地记忆 daemon 用哪个端口,协议是什么",
        "question": (
            "In the nautilus-compass setup, the local memory daemon listens on "
            "which port? Answer in one short sentence."
        ),
        "hit_keywords": ["9876"],
        "oracle": lambda a: isinstance(a, str) and "9876" in a,
    },
    {
        "id": "F3-utf8-negative",
        "query": "Windows 上 Python 写中文文件乱码",
        "question": (
            "On Windows, a Python script writes Chinese text to a file and the "
            "output is garbled. Give the one-line fix."
        ),
        "hit_keywords": ["utf-8", "utf8", "encoding"],
        "oracle": lambda a: isinstance(a, str)
        and ("utf-8" in a.lower() or "utf8" in a.lower()),
        "expected": "negative-control (model already knows; delta should be 0)",
    },
]


def daemon_recall(query: str, top_k: int = 3) -> list[dict]:
    req = {
        "action": "recall", "query": query, "top_k": top_k,
        "scope": "project", "project": "C--Users-chunx-Projects-nautilus-compass",
    }
    try:  # v3.0.10 · daemon 9876 token auth
        with open(os.path.expanduser("~/.claude/.cache/compass_daemon_token"),
                  encoding="utf-8") as _tf:
            req["token"] = _tf.read().strip()
    except OSError:
        pass
    s = socket.create_connection(DAEMON, timeout=180)
    try:
        s.sendall((json.dumps(req) + "\n").encode("utf-8"))
        buf = b""
        while not buf.endswith(b"\n"):
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
    finally:
        s.close()
    reply = json.loads(buf.decode("utf-8"))
    if not reply.get("ok"):
        raise RuntimeError(str(reply.get("error"))[:200])
    return reply.get("recall", [])


MEMORY_DIR = Path.home() / ".claude" / "projects" / "C--Users-chunx-Projects-nautilus-compass" / "memory"


def hit_text(hit: dict) -> str:
    """真实消费路径:recall 只给 path/description(正文常缺)→ 消费方读文件。"""
    parts = [str(hit.get("description", ""))]
    p = hit.get("path", "")
    f = MEMORY_DIR / p
    if f.is_file():
        try:
            parts.append(f.read_text(encoding="utf-8")[:1500])
        except OSError:
            pass
    return "\n".join(x for x in parts if x)


def ask_glm(question: str, context: str | None) -> str:
    import time as _t
    import requests  # 网关过滤 python-urllib UA,urllib 一律 403(requests 实测 200)
    user = question if not context else (
        f"Relevant team memory (may or may not help):\n---\n{context}\n---\n\n{question}"
    )
    for attempt in range(6):  # 429 退避:网关突发限流
        resp = requests.post(
            os.environ["ANTHROPIC_BASE_URL"].rstrip("/") + "/v1/messages",
            json={
                "model": MODEL, "max_tokens": 900, "temperature": 0,
                "system": 'Return one JSON object {"answer": "..."} and nothing else.',
                "messages": [{"role": "user", "content": user}],
            },
            headers={
                "x-api-key": os.environ["ANTHROPIC_AUTH_TOKEN"],
                "anthropic-version": "2023-06-01",
            },
            timeout=180,
        )
        if resp.status_code == 429:
            _t.sleep(20 * (attempt + 1))
            continue
        resp.raise_for_status()
        data = resp.json()
        break
    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    t = text.strip()
    if t.startswith("```"):
        n = t.find("\n")
        if n != -1:
            t = t[n + 1:]
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    try:
        return str(json.loads(t).get("answer", ""))
    except Exception:
        return t


def main() -> None:
    runs = 3
    report = {"schema": "recall-usefulness-exp-v1", "model": MODEL, "runs": runs, "facts": []}
    for fact in FACTS:
        rows = []
        for i in range(runs):
            hits = daemon_recall(fact["query"])
            texts = [hit_text(h) for h in hits]
            hit = any(
                all(kw.lower() in t.lower() for kw in fact["hit_keywords"]) for t in texts
            ) if fact["hit_keywords"] else bool(texts)
            context = "\n\n".join(texts[:3]) if texts else None
            t0 = time.time()
            try:
                control_ans = ask_glm(fact["question"], None)
                control_ok = fact["oracle"](control_ans)
            except Exception as e:
                control_ans, control_ok = f"ERROR {e}", False
            try:
                treat_ans = ask_glm(fact["question"], context)
                treat_ok = fact["oracle"](treat_ans)
            except Exception as e:
                treat_ans, treat_ok = f"ERROR {e}", False
            if treat_ok:
                cls = "pass"
            elif treat_ans.startswith("ERROR") or control_ans.startswith("ERROR"):
                cls = "transport_error"
            elif not hit:
                cls = "miss"
            else:
                cls = "inject_fail"
            rows.append({
                "run": i + 1, "hit": hit, "hit_titles": [str(h.get("name") or h.get("path", ""))[:80] for h in hits[:3]],
                "control_ok": control_ok, "treatment_ok": treat_ok, "class": cls,
                "treat_answer_head": treat_ans[:180], "secs": round(time.time() - t0, 1),
            })
            print(f"{fact['id']} run{i+1}: hit={hit} control={control_ok} treat={treat_ok} -> {cls} ({rows[-1]['secs']}s)")
        report["facts"].append({"id": fact["id"], "expected": fact.get("expected", "positive"), "rows": rows})
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print("saved", OUT)


if __name__ == "__main__":
    main()
