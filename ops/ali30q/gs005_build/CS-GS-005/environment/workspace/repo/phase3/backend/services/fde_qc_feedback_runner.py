"""S2 effect runner · 飞书派活表「已提交」→ QC → verdict/report → 反馈写回飞书.

Run(cloud): python3 -m services.fde_qc_feedback_runner --base http://localhost:8000 \
    --app-token <BASE_EOVH> --table-id tbl69fankpoBhJfw [--dry-run]

环境:FEISHU_APP_ID/FEISHU_APP_SECRET(飞书)。report/verdict 端点无需 platform key。
线2 判分:FDE_TUTORIAL_ASSEMBLER 指 vendored assemble_tutorial.py(默认本地 skill 路径)。
线1 判分:复用 services.fde_scorer_runner.make_soul_score_fn(LLM judge·需 MiniMax key·
惰性构建——纯线2 批次不碰 LLM)。逻辑核在 services.fde_qc_feedback(TDD green)。
🔴 人是作者:本 runner 只写「QC反馈」+状态,绝不动「提交内容」。
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from collections.abc import Callable
import urllib.error
import urllib.request

from services.fde_qc_feedback import line2_score, parse_tutorial_md, sync_submissions, line_code
from services.fde_task_form_schema import SUBMISSION_FIELDS, map_fields, plain_text, read_bitable_rows

FEISHU = "https://open.feishu.cn/open-apis"
_DEFAULT_ASSEMBLER = os.path.expanduser(
    "~/.claude/skills/knowledge-tutorial-assembler/scripts/assemble_tutorial.py")


def _http(method: str, url: str, token: str | None = None,
          body: dict | None = None, extra_headers: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        # 4xx/5xx 带 JSON envelope → 解析返回供调用方判;非 JSON 才视为传输故障(S1 C1)。
        try:
            return json.loads(e.read().decode())
        except Exception:
            raise e


def tenant_token() -> str:
    j = _http("POST", f"{FEISHU}/auth/v3/tenant_access_token/internal", body={
        "app_id": os.environ["FEISHU_APP_ID"],
        "app_secret": os.environ["FEISHU_APP_SECRET"]})
    return j["tenant_access_token"]


def _plain(v) -> str:
    return plain_text(v)


def _feishu_ok(j: dict) -> dict:
    """bitable 错误是 HTTP 200 + code!=0 —— 必须显式检查,静默吞=空表假象(review 实证)。"""
    if j.get("code") not in (0, None):
        raise RuntimeError(f"feishu error code={j.get('code')}: {str(j.get('msg'))[:120]}")
    return j


class FeishuSubmissionSource:
    """读派活表「状态=已提交」行 → row dict(含提交内容)。记 record_id 供写回。"""

    def __init__(self, token: str, app_token: str, table_id: str):
        self.token, self.app, self.table = token, app_token, table_id
        self.record_ids: dict[str, str] = {}

    def _all_records(self) -> list[dict]:
        return read_bitable_rows(_http, self.token, self.app, self.table, FEISHU)

    def read_submission_rows(self) -> list[dict]:
        rows = []
        for item in self._all_records():
            f = item.get("fields") or {}
            if _plain(f.get("状态")).strip() != "已提交":
                continue
            row = map_fields(f, SUBMISSION_FIELDS)
            uid = (row.get("task_uid") or "").strip()
            if not uid:  # 🔴 跳过空 task_uid 行(防 record_ids 空键碰撞·同 assignment runner)
                continue
            self.record_ids[uid] = item["record_id"]
            rows.append(row)
        return rows

    def write_feedback(self, task_uid: str, passed: bool, feedback: str,
                       status: str | None = None) -> None:
        rid = self.record_ids.get(task_uid)
        if not rid:
            return
        url = (f"{FEISHU}/bitable/v1/apps/{self.app}/tables/{self.table}"
               f"/records/{rid}")
        _feishu_ok(_http("PUT", url, token=self.token, body={"fields": {
            "状态": status or ("已通过" if passed else "已打回"),
            "QC反馈": feedback[:1900]}}))


def _load_module(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_qc_fn():
    """按业务线路由:线2=assembler validate(无LLM)·其余=checklist scorer(LLM judge)。

    两路都惰性加载:assembler 路径缺失不应阻塞纯线1 批次(对称·review 实证)。
    """
    _cache: dict[str, object] = {}

    def qc_fn(row: dict, submission: str) -> dict:
        if line_code(row.get("line")) == "2":
            if "assembler" not in _cache:
                _cache["assembler"] = _load_module(
                    os.environ.get("FDE_TUTORIAL_ASSEMBLER", _DEFAULT_ASSEMBLER),
                    "assemble_tutorial")
            return line2_score(_cache["assembler"].validate(parse_tutorial_md(submission)))
        level = (row.get("level") or "L2").strip() or "L2"
        if level not in _cache:  # 惰性:纯线2 批次不初始化 LLM scorer
            from services.fde_scorer_runner import _load_secrets, make_soul_score_fn
            _load_secrets(os.environ.get("FDE_API_SECRETS",
                          os.path.expanduser("~/.claude/.cache/.fde_api_secrets.env")))
            _cache[level] = make_soul_score_fn(level=level)
        desc = (row.get("acceptance") or "") + "\n" + (row.get("title") or "")
        return _cache[level]({"task_uid": row["task_uid"], "description": desc,
                              "output": submission})

    return qc_fn


def make_verdict_fn(base: str):
    def verdict_fn(body: dict) -> None:
        res = _http("POST", base + "/api/platform/fde/verdict", body=body)
        if not res.get("success"):
            raise RuntimeError(f"verdict ingest failed: {str(res.get('error'))[:120]}")
    return verdict_fn


def make_report_fn(base: str):
    def report_fn(uid: str, agent: str, submission: str) -> None:
        body = {"task_uid": uid, "agent_id": agent,
                "output": {"text": submission, "producer": "human"}}
        res = _http("POST", base + "/api/platform/fde/report", body=body)
        if res.get("success"):
            return
        # 自愈:行绕过 S1 直达已提交(status=open)→ 具名 claim 占座后重试一次。
        # 不占座会留 open 给 kairos 抢走 human-author 任务(review 实证)。
        if "must be claimed" in str(res.get("error") or ""):
            _http("POST", base + "/api/platform/fde/claim",
                  body={"task_uid": uid, "agent_id": agent})
            res = _http("POST", base + "/api/platform/fde/report", body=body)
            if res.get("success"):
                return
        # 仍失败不致命(verdict 已留痕)·暴露不吞
        print(f"[fde-qc] report degraded for {uid}: {str(res.get('error'))[:80]}")
    return report_fn


def make_attention_fn(base: str):
    def attention_fn(payload: dict) -> None:
        body = dict(payload)
        body.setdefault("status", "pending")
        body.setdefault("suggested_actions", [])
        body.setdefault("context", {})
        r = _http("POST", base + "/api/platform/fde/attention", body=body)
        if not r.get("success"):
            raise RuntimeError(f"attention persist failed: {str(r.get('error'))[:120]}")
    return attention_fn


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8000")
    ap.add_argument("--app-token", required=True)
    ap.add_argument("--table-id", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src = FeishuSubmissionSource(tenant_token(), args.app_token, args.table_id)
    qc_fn = make_qc_fn()

    if args.dry_run:
        verdict_fn = lambda b: print("[dry] verdict", b["verdict_id"], b["overall_pass"])  # noqa: E731
        report_fn = lambda u, a, s: print("[dry] report", u, a, len(s), "chars")           # noqa: E731
        attention_fn = lambda payload: None
    else:
        verdict_fn = make_verdict_fn(args.base)
        report_fn = make_report_fn(args.base)
        attention_fn = make_attention_fn(args.base)

    out = sync_submissions(src, qc_fn, verdict_fn, report_fn, attention_fn=attention_fn)

    for r in out["results"]:
        if args.dry_run:
            print("[dry] feedback", r["task_uid"], "passed=", r["passed"],
                  "\n" + r["feedback"])
        else:
            try:
                src.write_feedback(r["task_uid"], r["passed"], r["feedback"])
            except Exception as exc:  # noqa: BLE001 — 写回单点失败不拖批(S1 I3)
                print(f"[fde-qc] write_feedback failed for {r['task_uid']}: {str(exc)[:80]}")

    # 空提交但状态=已提交:写回打回提示,否则该行每 5min 静默重扫且专家无信号(review 实证)
    for uid in out["skipped"]:
        if not uid:
            continue
        msg = "提交内容为空:请在「提交内容」粘贴亲笔稿后,把状态改回「已提交」。"
        if args.dry_run:
            print("[dry] empty-submission bounce", uid)
        else:
            try:
                src.write_feedback(uid, False, msg)
            except Exception as exc:  # noqa: BLE001
                print(f"[fde-qc] bounce failed for {uid}: {str(exc)[:80]}")
    print("[fde-qc]", json.dumps(
        {"passed": [r["task_uid"] for r in out["results"] if r["passed"]],
         "rejected": [r["task_uid"] for r in out["results"] if not r["passed"]],
         "skipped": out["skipped"], "failed": out["failed"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
