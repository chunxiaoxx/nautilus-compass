"""W-D effect runner · the soul scoring poller as a runnable production service.

Wires the pure orchestration core (services.fde_scorer_poll) to REAL effects:

    source     = HTTP GET  {base}/api/platform/fde/tasks?status=produced
    score_fn   = checklist-from-task (gen checklist) + harness/checklist_scorer
                 (score output vs checklist with an LLM judge)
    verdict_fn = HTTP POST {base}/api/platform/fde/verdict   (source='soul')

This is EFFECT code (HTTP + LLM) — not unit-tested; the pure core + the HTTP loop
are proven in tests/test_fde_scorer_poll.py and tests/test_fde_scorer_loop_integration.py.

Run:
    python -m services.fde_scorer_runner --base http://localhost:8000 --dry-run
    python -m services.fde_scorer_runner --base http://localhost:8000   # writes verdicts

The soul RUBRIC scorer lives in vertical-task-factory/harness (platform-soul lane).
Its location is overridable via $FDE_SCORER_HARNESS so cloud deploy can point at a
vendored copy. Secrets (LLM key) load from $FDE_API_SECRETS or the default cache env;
keys are never logged.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import urllib.request
from typing import Callable

from services.fde_scorer_poll import is_deterministic_kind, poll_and_score

# Defaults (overridable by env) — soul lane scorer + secrets.
_DEFAULT_HARNESS = r"C:\Users\chunx\Projects\vertical-task-factory\harness\checklist_scorer.py"
_DEFAULT_CHECKLIST = r"C:\Users\chunx\.claude\skills\checklist-from-task\scripts\checklist_from_task.py"
_DEFAULT_SECRETS = r"C:\Users\chunx\.claude\.cache\.fde_api_secrets.env"


def _load_module(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_secrets(path: str) -> None:
    """Populate os.environ from a KEY=VALUE env file (never echoed).

    The soul judge (harness.make_llm_judge) talks to MiniMax's anthropic-compatible
    endpoint (api.minimaxi.com/anthropic) but reads ANTHROPIC_API_KEY, so alias the
    MiniMax key onto it when ANTHROPIC_API_KEY isn't otherwise set.
    """
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if ln and not ln.startswith("#") and "=" in ln:
                k, v = ln.split("=", 1)
                os.environ.setdefault(k, v)
    if not os.environ.get("ANTHROPIC_API_KEY") and os.environ.get("MINIMAX_API_KEY"):
        os.environ["ANTHROPIC_API_KEY"] = os.environ["MINIMAX_API_KEY"]


def _output_text(task: dict) -> str:
    """Render the produced output (dict/str) into the text the judge scores."""
    out = task.get("output")
    if isinstance(out, str):
        return out
    if isinstance(out, dict):
        txt = out.get("text") or out.get("answer") or ""
        extra = {k: v for k, v in out.items() if k not in ("text", "answer")}
        return (txt + "\n\n" + json.dumps(extra, ensure_ascii=False)) if extra else txt
    return json.dumps(out, ensure_ascii=False)


import re as _re


def parse_judge_json(raw: str):
    """健壮解析 LLM judge 的 {"pass","reason"} 输出。修 c4 Unterminated string bug。

    LLM reason 含裸换行/截断 → 朴素 json.loads 抛 Unterminated → 误判 fail。
    兜底:① 抽 {..} 直解 ② 去控制字符再解 ③ regex 抓 pass(+reason)。真不可解析 → None。
    """
    if not raw:
        return None
    s, e = raw.find("{"), raw.rfind("}")
    if s != -1 and e != -1 and e > s:
        cand = raw[s:e + 1]
        # 去控制字符(裸换行/制表 → 空格)·避 \x00 正则(部署转义脆弱)
        stripped = "".join(c if (c >= " " or c == "\t") else " " for c in cand)
        for attempt in (cand, stripped):
            try:
                obj = json.loads(attempt)
                return {"pass": bool(obj.get("pass")), "reason": str(obj.get("reason", ""))[:200]}
            except Exception:
                pass
    m = _re.search(r'"?pass"?\s*[:=]\s*(true|false)', raw, _re.IGNORECASE)
    if m:
        rm = _re.search(r'"?reason"?\s*[:=]\s*"?([^"\n}]{0,200})', raw, _re.IGNORECASE)
        return {"pass": m.group(1).lower() == "true",
                "reason": (rm.group(1).strip() if rm else "regex-parsed")[:200]}
    return None


def make_minimax_judge(cs, model: str = "MiniMax-M2") -> Callable[[dict, str], dict]:
    """urllib MiniMax judge (no litellm dep) — reuses the harness rule-text + QC prompt.

    Same one-rule-vs-answer QC contract as harness.make_llm_judge, but transported via
    urllib to MiniMax's chatcompletion_v2 (mirrors checklist_from_task). Reuses
    cs._build_rule_text so the 〔附件运用〕 tail-strip fix (batch A APPROVED) applies.
    """
    key = os.environ.get("MINIMAX_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    url = "https://api.minimaxi.com/v1/text/chatcompletion_v2"

    def judge_fn(item, model_output):
        prompt = (
            "You are a strict QC reviewer for a SWE-bench-style hard-task answer. "
            "Given ONE checklist rule and a candidate answer, decide if the answer "
            "satisfies the rule. Reply with a JSON object "
            '{"pass": true|false, "reason": "<one short sentence>"} and nothing else.\n'
            "判定原则:答案只要不违反规则即 pass。规则内的『条件动作』"
            "(如『无法确认时标注数据不足』『遇到X则Y』)仅当其条件实际发生且未执行时才算违反;"
            "条件未触发(如数据完整、无缺失)时,答案无需执行该动作即满足本项,不得因此判 fail。\n\n"
            f"## Checklist rule\n{cs._build_rule_text(item)}\n\n## Candidate answer\n{model_output}"
        )
        body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                           "max_tokens": 16000}).encode()
        req = urllib.request.Request(url, data=body, headers={
            "Authorization": "Bearer " + (key or ""), "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                j = json.loads(r.read().decode())
            raw = j["choices"][0]["message"]["content"] or ""
            parsed = parse_judge_json(raw)
            if parsed is not None:
                return parsed
            # 真不可解析(非截断/换行)→ 标记·不冤判(默认 fail 但 reason 透明)
            return {"pass": False, "reason": f"judge unparseable: {raw[:80]}"}
        except Exception as ex:
            return {"pass": False, "reason": f"judge error: {str(ex)[:80]}"}

    return judge_fn


def make_soul_score_fn(
    harness_path: str = None,
    checklist_gen_path: str = None,
    level: str = "L2",
    checklist_path: str = None,
) -> Callable[[dict], dict]:
    """Build the real score_fn: (curated or generated) checklist → judge output → scored.

    If ``checklist_path`` is given, that curated checklist.json is used for every task
    (operator-supplied, grounded). Otherwise the checklist is generated per task from
    its description via checklist-from-task (steady-state production behavior).
    """
    cs = _load_module(harness_path or os.environ.get("FDE_SCORER_HARNESS", _DEFAULT_HARNESS),
                      "checklist_scorer")
    judge_fn = make_minimax_judge(cs)

    preloaded = None
    if checklist_path:
        preloaded = json.load(open(checklist_path, encoding="utf-8"))
    else:
        cft = _load_module(checklist_gen_path or os.environ.get("FDE_CHECKLIST_GEN", _DEFAULT_CHECKLIST),
                           "checklist_from_task")

    def score_fn(task: dict) -> dict:
        uid = task["task_uid"]
        if preloaded is not None:
            ck = preloaded
        else:
            desc = task.get("description") or task.get("title") or ""
            ck = cft.gen_phase2(desc, level, uid) or cft.gen_template(desc, level, uid)
        items = ck["items"]
        scored = cs.score_checklist(_output_text(task), items, judge_fn=judge_fn)
        scored["checklist_uid"] = ck.get("task_uid", uid)
        return scored

    return score_fn


def make_http_source(base: str):
    class _Src:
        def list_produced_tasks(self):
            url = f"{base.rstrip('/')}/api/platform/fde/tasks?status=produced"
            with urllib.request.urlopen(url, timeout=30) as r:
                body = json.loads(r.read().decode())
            tasks = body.get("data", {}).get("tasks", [])
            # Only tasks not yet judged. A produced task keeps dispatch.status='produced'
            # even after a verdict (settled is a derived view-state), so without this
            # filter a standing daemon would re-score every settled task each poll.
            return [t for t in tasks if t.get("verdict") is None]
    return _Src()


def make_http_verdict_fn(base: str, dry_run: bool = False):
    url = f"{base.rstrip('/')}/api/platform/fde/verdict"

    def verdict_fn(body: dict):
        if dry_run:
            print(f"[dry-run] would POST verdict {body['verdict_id']} "
                  f"pass={body['overall_pass']} score={body['score']}")
            return {"dry_run": True}
        data = json.dumps(body).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode()).get("data")

    return verdict_fn


def main(argv=None):
    ap = argparse.ArgumentParser(description="soul FDE scoring poller (produced → verdict)")
    ap.add_argument("--base", default=os.environ.get("FDE_BASE", "http://localhost:8000"))
    ap.add_argument("--level", default="L2", choices=["L1", "L2", "L3"])
    ap.add_argument("--checklist", default=None, help="curated checklist.json (else generated per task)")
    ap.add_argument("--dry-run", action="store_true", help="score but do not POST verdicts")
    ap.add_argument("--secrets", default=os.environ.get("FDE_API_SECRETS", _DEFAULT_SECRETS))
    a = ap.parse_args(argv)

    _load_secrets(a.secrets)
    source = make_http_source(a.base)
    score_fn = make_soul_score_fn(level=a.level, checklist_path=a.checklist)
    verdict_fn = make_http_verdict_fn(a.base, dry_run=a.dry_run)

    # soul 不双判 deterministic-kind(code-fix)= compass/bench_eval turf(charter 纪律 #6)
    result = poll_and_score(source, score_fn, verdict_fn,
                            should_score=lambda t: not is_deterministic_kind(t))
    print(f"[soul-scorer] base={a.base} dry_run={a.dry_run} → "
          f"scored={result['scored']} skipped={result['skipped']} failed={result['failed']}")
    return 0 if not result["failed"] else 1


if __name__ == "__main__":
    sys.exit(main())
