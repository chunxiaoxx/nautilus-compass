"""S3 effect runner · 飞书派活表「已通过」→ 组装买方格式入交付表 + settlement 记账.

Run(cloud):
  python3 -m services.fde_delivery_runner --base http://localhost:8000 \
      --assign-app <BASE_EOVH> --assign-table tbl69fankpoBhJfw \
      --deliver-app Dx2qb1fjhaJadSs0ZeMc0teVn49 \
      --deliver-table tblFkmEKTk4LIWJM --settle-table tblFL7y3DejBQUvm [--dry-run]

环境:FEISHU_APP_ID/FEISHU_APP_SECRET。verdict 门 = GET 平台 verdict-bus(只读·无需 key)。
🔴 人是作者:本 runner 只组装专家原稿 + 记账,绝不动「提交内容」。
🔴 买方机密物理隔离:交付/结算落「独立 base」(--deliver-app ≠ 派活 base·charter §E)。
逻辑核在 services.fde_delivery(TDD green)。
"""
from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request

from services.fde_delivery import sync_deliveries
from services.fde_expert_rates import parse_expert_rates
from services.fde_task_form_schema import (
    DELIVERY_FIELDS,
    map_fields,
    plain_text,
    read_bitable_rows,
)

FEISHU = "https://open.feishu.cn/open-apis"


def _http(method: str, url: str, token: str | None = None, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            raise e


def tenant_token() -> str:
    j = _http("POST", f"{FEISHU}/auth/v3/tenant_access_token/internal", body={
        "app_id": os.environ["FEISHU_APP_ID"],
        "app_secret": os.environ["FEISHU_APP_SECRET"]})
    return j["tenant_access_token"]


def _feishu_ok(j: dict) -> dict:
    """bitable 错误是 HTTP 200 + code!=0 —— 必须显式检查(同 qc runner·review 实证)。"""
    if j.get("code") not in (0, None):
        raise RuntimeError(f"feishu error code={j.get('code')}: {str(j.get('msg'))[:120]}")
    return j


class FeishuDeliverySource:
    """派活表「已通过」→ 组装+记账 → 写独立交付 base 两表 → 标「已交付」。"""

    def __init__(self, token, assign_app, assign_table, deliver_app, deliver_table,
                 settle_table, roster_table=None, roster_app=None):
        self.token = token
        self.assign_app, self.assign_table = assign_app, assign_table
        self.deliver_app = deliver_app
        self.deliver_table, self.settle_table = deliver_table, settle_table
        self.roster_table = roster_table   # v06_行业专家 table_id(读单价)
        # 🔴 B2 路线3:专家名册在 canonical RGDK base(≠ assign_app=EOVh)→ 单独 app_token。
        # 缺省回退 assign_app(向后兼容·名册与派活同 base 时)。同租户读开放(6/15 实证 code=0)。
        self.roster_app = roster_app or assign_app
        self.record_ids: dict[str, str] = {}

    def read_expert_rates(self) -> dict:
        """RGDK v06_行业专家 → {姓名: 工时单价}(应付算·复用 parse_expert_rates)。

        roster_table 未配 → 空名册(应付维持 pending·不臆造)。从 roster_app 读
        (canonical RGDK·跨 base 只读·非 assign_app)。
        """
        if not self.roster_table:
            return {}
        rows = []
        for item in read_bitable_rows(_http, self.token, self.roster_app, self.roster_table, FEISHU):
            f = item.get("fields") or {}
            rows.append({
                "姓名": plain_text(f.get("姓名")),
                "工时单价_元每小时": plain_text(f.get("工时单价_元每小时")),
            })
        return parse_expert_rates(rows)

    def read_passed_rows(self) -> list[dict]:
        rows = []
        for item in read_bitable_rows(_http, self.token, self.assign_app, self.assign_table, FEISHU):
            f = item.get("fields") or {}
            if plain_text(f.get("状态")).strip() != "已通过":
                continue
            row = map_fields(f, DELIVERY_FIELDS)
            uid = (row.get("task_uid") or "").strip()
            if not uid:  # 跳过空 uid 行(防 record_ids 空键碰撞·同 S1/S2 实证)
                continue
            self.record_ids[uid] = item["record_id"]
            rows.append(row)
        return rows

    def already_delivered(self) -> set[str]:
        """交付表里已存的 task_uid = 幂等去重源(crash-safe 重放靠它)。"""
        seen = set()
        for item in read_bitable_rows(_http, self.token, self.deliver_app, self.deliver_table, FEISHU):
            uid = plain_text((item.get("fields") or {}).get("task_uid")).strip()
            if uid:
                seen.add(uid)
        return seen

    def write_delivery(self, p: dict) -> str:
        fields = {
            "task_uid": p["task_uid"], "业务线": p.get("line", ""),
            "L级": p.get("level", ""), "标题": p.get("title", ""),
            "领域一级": p.get("l1", ""), "领域二级": p.get("l2", ""),
            "Instruction": p.get("instruction", ""),
            "KnowledgePoints": p.get("knowledge_points", ""),
            "BackgroundKnowledge": p.get("background_knowledge", ""),
            "Task示例": p.get("task_example", ""),
            "交付正文MD": p.get("delivery_body_md", "")[:9000],
            "专家": p.get("expert", ""), "状态": p.get("status", ""),
        }
        url = f"{FEISHU}/bitable/v1/apps/{self.deliver_app}/tables/{self.deliver_table}/records"
        j = _feishu_ok(_http("POST", url, token=self.token, body={"fields": fields}))
        return (j.get("data") or {}).get("record", {}).get("record_id", "")

    def write_settlement(self, r: dict) -> None:
        fields = {
            "task_uid": r["task_uid"], "专家": r.get("expert", ""),
            "业务线": r.get("line", ""), "L级": r.get("level", ""),
            "标题": r.get("title", ""), "verdict_score": r.get("verdict_score", 0.0),
            "verdict_id": r.get("verdict_id", ""),
            "token成本USD": r.get("token_cost_usd", 0.0),
            "token模型": r.get("token_model", "none"),
            "应付状态": r.get("payable_status", "pending"),
            "状态": r.get("status", ""),
        }
        if r.get("payable_amount") is not None:  # None=待人定价·留空(最小记账不臆造)
            fields["应付金额"] = r["payable_amount"]
        url = f"{FEISHU}/bitable/v1/apps/{self.deliver_app}/tables/{self.settle_table}/records"
        _feishu_ok(_http("POST", url, token=self.token, body={"fields": fields}))

    def mark_delivered(self, task_uid: str) -> None:
        rid = self.record_ids.get(task_uid)
        if not rid:
            return
        url = (f"{FEISHU}/bitable/v1/apps/{self.assign_app}/tables/{self.assign_table}"
               f"/records/{rid}")
        _feishu_ok(_http("PUT", url, token=self.token,
                         body={"fields": {"状态": "已交付"}}))


def make_verdict_fn(base: str):
    """平台 verdict-bus GET → 最新 verdict(rows[0])。无记录=None(不交付)。"""
    def verdict_fn(uid: str):
        res = _http("GET", base + "/api/platform/fde/verdict/" + uid)
        if not res.get("success"):
            return None
        rows = res.get("data") or []
        return rows[0] if rows else None
    return verdict_fn


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
    ap.add_argument("--assign-app", required=True)
    ap.add_argument("--assign-table", required=True)
    ap.add_argument("--deliver-app", required=True)
    ap.add_argument("--deliver-table", required=True)
    ap.add_argument("--settle-table", required=True)
    ap.add_argument("--roster-app", default=None,
                    help="专家名册所在 base app_token(canonical RGDK·缺省=assign-app)")
    ap.add_argument("--roster-table", default=None,
                    help="RGDK v06_行业专家(同 assign-app·读单价算应付)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src = FeishuDeliverySource(tenant_token(), args.assign_app, args.assign_table,
                               args.deliver_app, args.deliver_table, args.settle_table,
                               roster_table=args.roster_table, roster_app=args.roster_app)
    verdict_fn = make_verdict_fn(args.base)

    if args.dry_run:
        rows = src.read_passed_rows()
        done = src.already_delivered()
        print(f"[dry] passed_rows={len(rows)} already_delivered={len(done)}")
        for row in rows:
            uid = row["task_uid"]
            v = verdict_fn(uid)
            ok = bool(v and v.get("overall_pass")) and uid not in done
            print(f"[dry] {uid} line={row.get('line')} verdict_pass="
                  f"{bool(v and v.get('overall_pass'))} would_deliver={ok}")
        return

    attention_fn = make_attention_fn(args.base)
    out = sync_deliveries(src, verdict_fn, attention_fn=attention_fn)
    print("[fde-deliver]", json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
