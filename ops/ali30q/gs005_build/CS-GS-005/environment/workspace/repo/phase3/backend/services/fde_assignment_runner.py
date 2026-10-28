"""S1 effect runner · 飞书派活表 → sync_assignments → 引擎 API → 状态写回飞书.

Run(cloud): python3 -m services.fde_assignment_runner --base http://localhost:8000 \
    --app-token <BASE_EOVH> --table-id <派活表id> [--dry-run]

环境:FEISHU_APP_ID/FEISHU_APP_SECRET(飞书租户)+ PLATFORM_DISPATCH_KEY(admin·派单)。
cloud 从 .env + fde_api_secrets.env source(与 soul-scorer run.sh 同模式·key 不入日志)。

读派活表「状态=待派单」行 → sync_assignments(dispatch + 具名 expert: claim 背靠背·防
kairos 抢) → 写回每行状态(已派单/异常)。纯 effect(HTTP + 飞书),逻辑核在
services.fde_assignment(已 TDD green)。列名约定见 FIELD_MAP。
"""
from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request

from services.fde_assignment import sync_assignments
from services.fde_task_form_schema import (
    ASSIGNMENT_FIELDS,
    map_fields,
    plain_text,
    read_bitable_rows,
)

FEISHU = "https://open.feishu.cn/open-apis"


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
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        # 4xx/5xx carrying a JSON envelope (e.g. /claim 409 → {"success":False,"error":..}).
        # Return the parsed body so callers can inspect it (live success-check);
        # a non-JSON error body re-raises (genuine transport failure).
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
    """飞书富文本字段(list[{text}])或标量 → 纯文本。"""
    return plain_text(v)


class FeishuAssignmentSource:
    """读派活表「状态=待派单」行 → 标准 row dict。记 record_id 供写回。"""

    def __init__(self, token: str, app_token: str, table_id: str):
        self.token, self.app, self.table = token, app_token, table_id
        self.record_ids: dict[str, str] = {}

    def _all_records(self) -> list[dict]:
        return read_bitable_rows(_http, self.token, self.app, self.table, FEISHU)

    def read_assignment_rows(self) -> list[dict]:
        rows = []
        for item in self._all_records():
            f = item.get("fields") or {}
            if _plain(f.get("状态")).strip() != "待派单":
                continue
            row = map_fields(f, ASSIGNMENT_FIELDS)
            uid = (row.get("task_uid") or "").strip()
            if not uid:  # 🔴 跳过空 task_uid 行:否则 record_ids 空键碰撞→write_back 写错行
                continue  # (实证 2026-06-12:空行污染致 drift 被误标已派单 + 幽灵空行)
            self.record_ids[uid] = item["record_id"]
            rows.append(row)
        return rows

    def write_back(self, task_uid: str, status: str, note: str = "") -> None:
        rid = self.record_ids.get(task_uid)
        if not rid:
            return
        url = (f"{FEISHU}/bitable/v1/apps/{self.app}/tables/{self.table}"
               f"/records/{rid}")
        _http("PUT", url, token=self.token,
              body={"fields": {"状态": status, "备注": note[:200]}})


def make_dispatch_fn(base: str, key: str):
    def dispatch_fn(body: dict) -> None:
        _http("POST", base + "/api/platform/fde/dispatch", body=body,
              extra_headers={"X-Platform-Key": key})
    return dispatch_fn


def make_claim_fn(base: str):
    def claim_fn(uid: str, agent: str) -> None:
        res = _http("POST", base + "/api/platform/fde/claim",
                    body={"task_uid": uid, "agent_id": agent})
        if res.get("success"):
            return
        err = str(res.get("error") or "")
        # idempotent re-run: task already claimed by THIS same expert → treat as ours,
        # not a lost race (durable across runs when write-back lagged · fixes I2).
        if agent and agent in err:
            return
        # claimed by someone else (an agent runner) or a real failure → surface as lost.
        raise RuntimeError(f"claim lost: {err[:120]}")
    return claim_fn


def _safe_write_back(src, uid: str, status: str, note: str) -> None:
    """write-back 单点失败不中断后续 stamp(fixes I3 · 否则喂养 I2 重读隐患)。"""
    try:
        src.write_back(uid, status, note)
    except Exception as exc:  # noqa: BLE001 — best-effort stamp · log + continue
        print(f"[fde-assignment] write_back failed for {uid}: {str(exc)[:80]}")


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

    src = FeishuAssignmentSource(tenant_token(), args.app_token, args.table_id)
    key = os.environ.get("PLATFORM_DISPATCH_KEY", "")

    if args.dry_run:
        dispatch_fn = lambda b: print("[dry] dispatch", b["task_uid"])  # noqa: E731
        claim_fn = lambda uid, agent: print("[dry] claim", uid, agent)  # noqa: E731
        attention_fn = lambda payload: None
    else:
        dispatch_fn = make_dispatch_fn(args.base, key)
        claim_fn = make_claim_fn(args.base)
        attention_fn = make_attention_fn(args.base)

    out = sync_assignments(src, dispatch_fn, claim_fn, attention_fn=attention_fn)

    if not args.dry_run:
        for uid in out["assigned"]:
            _safe_write_back(src, uid, "已派单", "已进引擎·具名占座")
        for uid in out["lost_to_agent"]:
            _safe_write_back(src, uid, "异常", "被 agent 抢单/claim 失败·需人工核")
    print("[fde-assignment]", json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
