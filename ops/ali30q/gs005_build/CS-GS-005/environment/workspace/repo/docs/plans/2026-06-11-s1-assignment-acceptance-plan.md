# S1 派活+验收标准(human-author 路径)Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 专家(首例=用户扮演)从飞书派活表领到 1 道实际买方任务并看到前置验收标准,任务同步进已证转引擎 fde_dispatch(具名 claim·human-author 路径),闭后废弃"名册 md+手工 curl"老路径。

**Architecture:** 零后端 API 改动——复用现成 `/api/platform/fde/dispatch|claim` 端点。新增:① 纯编排模块 `services/fde_assignment.py`(飞书行→dispatch body→具名 claim·本地 TDD)② cloud effect runner(镜像 `fde_scorer_runner` 模式·vendored feishu client 读派活表→调本地 API→状态写回飞书)③ 飞书「FDE派活表」(base EOVh·一次性 bootstrap)。设计来源:`2026-06-11-fde-org-production-engine-design.md` S1 节。

**Tech Stack:** Python 3.10(cloud)/3.13(本地)· FastAPI 现成端点 · 飞书 bitable v1 API(tenant token·凭据 `~/.claude/.cache/.fde_api_secrets.env` 同款·cloud 在 `/home/ubuntu/fde-toolbox/feishu_client.py`)· systemd timer(镜像 soul-scorer)

**🔴 关键 gotcha(2026-06-11 实证·设计依据):**
1. **agent 抢单竞态**:fde-runner@kairos 对 open 任务 +20s 自动 claim。human 任务绝不能停留在 open——`sync_assignments` 必须 dispatch 后**立即**用 `agent_id="expert:<assignee>"` claim(背靠背·亚秒窗口)。若仍被抢(409),记入 `lost_to_agent` 并继续(fail-soft),由 runner 日志暴露。
2. **verdict-join 遮蔽**:task_uid 绝不复用已有 verdict 的 uid(`api/fde_dispatch.py:157`)。派活表 task_uid 命名约定 `expert_<line>_<slug>_<date>`(如 `expert_t1_crossend_20260612`),与 compass_autolab_*/data_* 不冲突。
3. **cloud = fork(soul-audit-increment1)只 scp 不 pull**;本地 master main.py 不可 import(分叉遗留)——但 S1 不碰 main.py,纯新模块,无此风险。
4. 本地跑测试:`cd phase3/backend && python -m pytest`(Windows 用 `python` 非 python3)。

---

### Task 1: 纯核心 · `build_assignment_dispatch`(飞书行→dispatch body)

**Files:**
- Create: `phase3/backend/services/fde_assignment.py`
- Test: `phase3/backend/tests/test_fde_assignment.py`

**Step 1: 写失败测试**

```python
"""S1 派活+验收标准 · 纯编排核心 TDD(design: 2026-06-11-fde-org-production-engine-design.md S1)."""
from services.fde_assignment import build_assignment_dispatch


def _row(**over):
    base = {
        "task_uid": "expert_t1_crossend_20260612",
        "title": "跨端体验一致性方案(二期 L2)",
        "line": "1",                      # 业务线 1/2/3
        "category": "互联网与平台业务",     # 一级类目(9 固定)
        "domain": "跨端产品架构",           # 三级领域
        "level": "L2",
        "assignee": "chunxiao",            # 具名专家
        "acceptance": "c1 方案≥2套(否决)\nc2 附Excel分析表\nc3 引用全部8附件",
    }
    base.update(over)
    return base


def test_build_dispatch_packs_human_spec_into_description_json():
    import json
    body = build_assignment_dispatch(_row())
    assert body["task_uid"] == "expert_t1_crossend_20260612"
    assert body["title"].startswith("跨端")
    spec = json.loads(body["description"])
    assert spec["producer"] == "human"           # human-author 路径标记
    assert spec["assignee"] == "chunxiao"
    assert spec["level"] == "L2"
    assert "c1" in spec["acceptance"]            # 验收标准前置随单走


def test_build_dispatch_missing_required_returns_none():
    assert build_assignment_dispatch(_row(task_uid="")) is None
    assert build_assignment_dispatch(_row(assignee="")) is None      # 无具名专家=不派
    assert build_assignment_dispatch(_row(acceptance="")) is None    # 无验收标准=不派(S1 第一痛点)
```

**Step 2: 跑测试确认失败**

Run: `cd phase3/backend && python -m pytest tests/test_fde_assignment.py -v`
Expected: FAIL `ModuleNotFoundError: services.fde_assignment`

**Step 3: 最小实现**

```python
"""S1 派活+验收标准 · human-author 路径纯编排核心.

turf:平台 own 派活决策;飞书读写=effect runner(vendored compass client);
引擎=现成 fde_dispatch API(零改动)。
🔴 human 任务不停留 open(kairos +20s 抢单实证)→ sync 必须 dispatch+具名 claim 背靠背。
"""
from __future__ import annotations

import json
from typing import Callable, Iterable

REQUIRED = ("task_uid", "title", "assignee", "acceptance")


def build_assignment_dispatch(row: dict) -> dict | None:
    """飞书派活行 → POST /dispatch body。缺 task_uid/assignee/acceptance 任一 = 不派(None)。

    验收标准(acceptance)是 S1 的第一痛点——没有它专家盲写,强制必填。
    富 spec 打包进 description JSON(dispatch 只持久化 3 字段·schema 实证)。
    """
    if not all(str(row.get(k) or "").strip() for k in REQUIRED):
        return None
    spec = {
        "producer": "human",
        "assignee": str(row["assignee"]).strip(),
        "line": str(row.get("line") or ""),
        "category": str(row.get("category") or ""),
        "domain": str(row.get("domain") or ""),
        "level": str(row.get("level") or ""),
        "acceptance": str(row["acceptance"]),
    }
    return {
        "task_uid": str(row["task_uid"]).strip(),
        "title": str(row["title"]).strip(),
        "description": json.dumps(spec, ensure_ascii=False),
    }
```

**Step 4: 跑测试确认通过**

Run: `cd phase3/backend && python -m pytest tests/test_fde_assignment.py -v`
Expected: 2 passed

**Step 5: Commit**

```bash
git add phase3/backend/services/fde_assignment.py phase3/backend/tests/test_fde_assignment.py
git commit -m "feat(s1): build_assignment_dispatch 飞书派活行→human-author dispatch body(TDD)"
```

---

### Task 2: 纯核心 · `sync_assignments`(dispatch+具名 claim 背靠背 · fail-soft)

**Files:**
- Modify: `phase3/backend/services/fde_assignment.py`(追加)
- Test: `phase3/backend/tests/test_fde_assignment.py`(追加)

**Step 1: 追加失败测试**

```python
from services.fde_assignment import sync_assignments


class _FakeSource:
    def __init__(self, rows): self._rows = rows
    def read_assignment_rows(self): return self._rows


def test_sync_dispatches_then_claims_for_named_expert():
    calls = []
    src = _FakeSource([_row()])
    out = sync_assignments(
        src,
        dispatch_fn=lambda b: calls.append(("dispatch", b["task_uid"])),
        claim_fn=lambda uid, agent: calls.append(("claim", uid, agent)),
    )
    # dispatch 后立即具名 claim(防 kairos 抢单·背靠背)
    assert calls == [
        ("dispatch", "expert_t1_crossend_20260612"),
        ("claim", "expert_t1_crossend_20260612", "expert:chunxiao"),
    ]
    assert out["assigned"] == ["expert_t1_crossend_20260612"]


def test_sync_skips_invalid_and_already_assigned_failsoft():
    rows = [_row(), _row(task_uid="expert_t2_dup", acceptance=""),  # 无验收→skip
            _row(task_uid="expert_t1_crossend_20260612")]           # 重复→skip
    boom = _row(task_uid="expert_t9_boom")
    rows.append(boom)
    def _claim(uid, agent):
        if uid == "expert_t9_boom":
            raise RuntimeError("409 already claimed")  # 被 agent 抢
    out = sync_assignments(_FakeSource(rows), dispatch_fn=lambda b: None, claim_fn=_claim,
                           already_assigned={"expert_known"})
    assert out["assigned"] == ["expert_t1_crossend_20260612"]
    assert "expert_t2_dup" in out["skipped"]
    assert out["lost_to_agent"] == ["expert_t9_boom"]   # 暴露竞态·不吞
```

**Step 2: 跑测试确认失败**

Run: `cd phase3/backend && python -m pytest tests/test_fde_assignment.py -v`
Expected: 新 2 个 FAIL(`ImportError: sync_assignments`)

**Step 3: 追加最小实现**

```python
def sync_assignments(
    source,
    dispatch_fn: Callable[[dict], object],
    claim_fn: Callable[[str, str], object],
    already_assigned: Iterable[str] | None = None,
) -> dict:
    """读派活表 → 去重 → dispatch+具名 claim 背靠背 → 汇总。fail-soft 单行不拖批。

    Returns {"assigned": [...], "skipped": [...], "lost_to_agent": [...], "failed": [...]}
    """
    seen = set(already_assigned or ())
    assigned, skipped, lost, failed = [], [], [], []
    for row in source.read_assignment_rows():
        body = build_assignment_dispatch(row)
        uid = (row.get("task_uid") or "").strip() or None
        if body is None or body["task_uid"] in seen:
            skipped.append(uid)
            continue
        uid = body["task_uid"]
        expert = "expert:" + json.loads(body["description"])["assignee"]
        try:
            dispatch_fn(body)
        except Exception:
            failed.append(uid)
            continue
        try:
            claim_fn(uid, expert)          # 立即占座·防 agent 抢(+20s 实证)
        except Exception:
            lost.append(uid)               # 被抢/失败 → 暴露不吞
            seen.add(uid)
            continue
        assigned.append(uid)
        seen.add(uid)
    return {"assigned": assigned, "skipped": skipped,
            "lost_to_agent": lost, "failed": failed}
```

**Step 4: 跑全部测试确认通过**

Run: `cd phase3/backend && python -m pytest tests/test_fde_assignment.py -v`
Expected: 4 passed

**Step 5: 回归既有 FDE 测试不碰坏**

Run: `cd phase3/backend && python -m pytest tests/test_fde_poller.py tests/test_fde_dispatch_v1.py -v`
Expected: 全 passed(没动它们·确认即可)

**Step 6: Commit**

```bash
git add phase3/backend/services/fde_assignment.py phase3/backend/tests/test_fde_assignment.py
git commit -m "feat(s1): sync_assignments dispatch+具名claim背靠背(防agent抢单·fail-soft·TDD)"
```

---

### Task 3: effect runner(cloud·镜像 fde_scorer_runner 模式·不单测)

**Files:**
- Create: `phase3/backend/services/fde_assignment_runner.py`

**Step 1: 写 runner(effect 代码·HTTP+飞书·模式抄 `services/fde_scorer_runner.py`)**

```python
"""S1 effect runner · 飞书派活表 → sync_assignments → 引擎 API → 状态写回飞书.

Run(cloud): python3 -m services.fde_assignment_runner --base http://localhost:8000 \
    --app-token <BASE_EOVH> --table-id <派活表id> [--dry-run]

飞书凭据:环境 FEISHU_APP_ID/FEISHU_APP_SECRET(cloud 从 fde_api_secrets.env source·
与 soul-scorer run.sh 同模式)。读表用 bitable v1 records;写回更新「状态/引擎task_uid」列。
列名约定(中文·与派活表 bootstrap 一致):
  task_uid/标题/业务线/一级类目/三级领域/L级/指派专家/验收标准/状态/备注
"""
from __future__ import annotations

import argparse, json, os, urllib.request

from services.fde_assignment import sync_assignments

FEISHU = "https://open.feishu.cn/open-apis"


def _http(method: str, url: str, token: str | None = None, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def tenant_token() -> str:
    j = _http("POST", f"{FEISHU}/auth/v3/tenant_access_token/internal", body={
        "app_id": os.environ["FEISHU_APP_ID"], "app_secret": os.environ["FEISHU_APP_SECRET"]})
    return j["tenant_access_token"]


class FeishuAssignmentSource:
    """读派活表「状态=待派单」行 → 标准 row dict。记录 record_id 供写回。"""

    FIELD_MAP = {"task_uid": "task_uid", "标题": "title", "业务线": "line",
                 "一级类目": "category", "三级领域": "domain", "L级": "level",
                 "指派专家": "assignee", "验收标准": "acceptance"}

    def __init__(self, token: str, app_token: str, table_id: str):
        self.token, self.app, self.table = token, app_token, table_id
        self.record_ids: dict[str, str] = {}

    def read_assignment_rows(self):
        url = (f"{FEISHU}/bitable/v1/apps/{self.app}/tables/{self.table}/records"
               f"?page_size=100")
        j = _http("GET", url, token=self.token)
        rows = []
        for item in (j.get("data") or {}).get("items") or []:
            f = item.get("fields") or {}
            if str(f.get("状态") or "").strip() != "待派单":
                continue
            row = {std: _plain(f.get(feishu)) for feishu, std in
                   [(k, v) for k, v in self.FIELD_MAP.items()]}
            self.record_ids[row.get("task_uid") or ""] = item["record_id"]
            rows.append(row)
        return rows

    def write_back(self, task_uid: str, status: str, note: str = ""):
        rid = self.record_ids.get(task_uid)
        if not rid:
            return
        url = f"{FEISHU}/bitable/v1/apps/{self.app}/tables/{self.table}/records/{rid}"
        _http("PUT", url, token=self.token,
              body={"fields": {"状态": status, "备注": note[:200]}})


def _plain(v):
    """飞书富文本字段 → 纯文本(多段拼接)。"""
    if isinstance(v, list):
        return "".join(seg.get("text", "") for seg in v if isinstance(seg, dict))
    return "" if v is None else str(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8000")
    ap.add_argument("--app-token", required=True)
    ap.add_argument("--table-id", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src = FeishuAssignmentSource(tenant_token(), args.app_token, args.table_id)
    key = os.environ.get("PLATFORM_DISPATCH_KEY", "")

    def dispatch_fn(body):
        if args.dry_run:
            print("[dry] dispatch", body["task_uid"]); return
        _http("POST", args.base + "/api/platform/fde/dispatch",
              body={**body}, token=None) if False else _dispatch(args.base, key, body)

    def claim_fn(uid, agent):
        if args.dry_run:
            print("[dry] claim", uid, agent); return
        _http("POST", args.base + "/api/platform/fde/claim",
              body={"task_uid": uid, "agent_id": agent})

    out = sync_assignments(src, dispatch_fn, claim_fn)
    for uid in out["assigned"]:
        if not args.dry_run:
            src.write_back(uid, "已派单", "已进引擎·具名占座")
    for uid in out["lost_to_agent"]:
        if not args.dry_run:
            src.write_back(uid, "异常", "被 agent 抢单/claim 失败·需人工核")
    print("[fde-assignment]", json.dumps(out, ensure_ascii=False))


def _dispatch(base: str, key: str, body: dict):
    data = json.dumps(body).encode()
    req = urllib.request.Request(base + "/api/platform/fde/dispatch", data=data, headers={
        "Content-Type": "application/json", "X-Platform-Key": key})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


if __name__ == "__main__":
    main()
```

**Step 2: 本地语法校验(不连飞书)**

Run: `cd phase3/backend && python -c "import ast; ast.parse(open('services/fde_assignment_runner.py', encoding='utf-8').read()); print('syntax ok')"`
Expected: `syntax ok`

**Step 3: Commit**

```bash
git add phase3/backend/services/fde_assignment_runner.py
git commit -m "feat(s1): fde_assignment_runner 飞书派活表→引擎 effect runner(镜像 scorer_runner 模式)"
```

---

### Task 4: 飞书「FDE派活表」bootstrap(cloud·一次性)

**Files:**
- Create: `phase3/backend/scripts/bootstrap_assignment_table.py`(一次性·建表+列)

**Step 1: 写 bootstrap 脚本**

```python
"""一次性:在 base EOVhbQwA0a1HEOsgmxecgkBVnwh(第3类 canonical·权限已验)建「FDE派活表」.

Run(cloud): FEISHU_APP_ID=.. FEISHU_APP_SECRET=.. python3 scripts/bootstrap_assignment_table.py
输出 table_id —— 记入 FDE_BUSINESS_CHARTER §1 飞书表清单(防表丢失契约)。
"""
import json, os, urllib.request

BASE_APP = "EOVhbQwA0a1HEOsgmxecgkBVnwh"
FIELDS = [
    {"field_name": "task_uid", "type": 1},
    {"field_name": "标题", "type": 1},
    {"field_name": "业务线", "type": 1},
    {"field_name": "一级类目", "type": 1},
    {"field_name": "三级领域", "type": 1},
    {"field_name": "L级", "type": 1},
    {"field_name": "指派专家", "type": 1},
    {"field_name": "验收标准", "type": 1},
    {"field_name": "状态", "type": 3, "property": {"options": [
        {"name": "待派单"}, {"name": "已派单"}, {"name": "已领取"},
        {"name": "已提交"}, {"name": "异常"}]}},
    {"field_name": "备注", "type": 1},
]

def _http(method, url, token=None, body=None):
    data = json.dumps(body).encode() if body else None
    h = {"Content-Type": "application/json"}
    if token: h["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

tok = _http("POST", "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            body={"app_id": os.environ["FEISHU_APP_ID"],
                  "app_secret": os.environ["FEISHU_APP_SECRET"]})["tenant_access_token"]
j = _http("POST", f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_APP}/tables",
          token=tok, body={"table": {"name": "FDE派活表", "fields": FIELDS}})
print("TABLE_ID:", j["data"]["table_id"])
```

**Step 2: cloud 执行(scp 上去跑·凭据 source 自 fde_api_secrets.env 同款来源)**

```bash
scp phase3/backend/scripts/bootstrap_assignment_table.py cloud:/tmp/
ssh cloud 'set -a; source ~/fde-toolbox/.fde_api_secrets.env 2>/dev/null || source ~/.fde_api_secrets.env; set +a; python3 /tmp/bootstrap_assignment_table.py'
```
Expected: `TABLE_ID: tblXXXXXXXX`(记下)
注:凭据文件实际路径以 cloud 实况为准(`grep -l FEISHU_APP_ID` 找);若 base EOVh 建表权限不足 → 降级:用户在飞书 UI 手动按 FIELDS 建表(5 分钟),table_id 从 URL 取。**别为权限卡死——表怎么来不重要,列 schema 一致就行。**

**Step 3: 填入第 1 道实际买方任务(用户=专家#1)**

PM(本 session=我)经飞书 UI 或 create record API 在派活表填 1 行实际任务,例:
- task_uid=`expert_t2_cpu_starve_20260612` · 业务线=2 · 指派专家=用户 · 状态=待派单
- 验收标准=从 RUBRIC §11 摘:5 部分齐 / Background 1k-30k 字亲笔 / 知识密度 ≥5 点 / 反 AI 检测红线
(任务内容=实际教案任务·非演习;线 2 量级金融/法律 200-500 条是当前买方需求)

**Step 4: Commit**

```bash
git add phase3/backend/scripts/bootstrap_assignment_table.py
git commit -m "feat(s1): 飞书 FDE派活表 bootstrap 脚本(base EOVh·一次性)"
```

---

### Task 5: cloud 部署 runner(外科 scp·systemd timer 镜像 soul-scorer)

**Step 1: scp 两个文件到 cloud(fork 分支·绝不 pull)**

```bash
scp phase3/backend/services/fde_assignment.py cloud:~/nautilus-mvp/phase3/backend/services/
scp phase3/backend/services/fde_assignment_runner.py cloud:~/nautilus-mvp/phase3/backend/services/
```

**Step 2: cloud dry-run 验证(真飞书读·不写)**

```bash
ssh cloud 'cd ~/nautilus-mvp/phase3/backend && set -a; source .env; source <凭据文件>; set +a; \
  python3 -m services.fde_assignment_runner --base http://localhost:8000 \
  --app-token EOVhbQwA0a1HEOsgmxecgkBVnwh --table-id <Task4的table_id> --dry-run'
```
Expected: `[dry] dispatch expert_t2_... · [dry] claim expert_t2_... expert:<用户>` + 汇总 JSON

**Step 3: 真跑一轮(手动·闭环验证用)**

同命令去掉 `--dry-run`。Expected: `assigned: ["expert_t2_cpu_starve_20260612"]`

**Step 4: 验证引擎侧(具名 claim 成立·没被 kairos 抢)**

```bash
ssh cloud 'cd ~/nautilus-mvp/phase3/backend && set -a; source .env; set +a; python3 - << "EOF"
import os, psycopg2, re
m = re.match(r"postgresql(?:\+[a-z]+)?://([^:]+):([^@]+)@([^:/]+):?([0-9]*)?/([^?]+)",
             os.environ["DATABASE_URL"]) 
u,pw,h,p,db = m.groups()
c = psycopg2.connect(host=h, port=p or 5432, user=u, password=pw, dbname=db)
cur = c.cursor()
cur.execute("SELECT status, claimed_by FROM fde_dispatch WHERE task_uid LIKE %s", ("expert_%",))
print(cur.fetchall())
EOF'
```
Expected: `[('claimed', 'expert:<用户>')]` —— claimed_by 是 expert: 前缀,不是 kairos。

**Step 5: systemd timer(每 5min·镜像 soul-scorer 模式)+ Commit**

cloud 建 `/home/ubuntu/fde-assignment/run.sh`(export 凭据 + exec runner·抄 `/home/ubuntu/soul-scorer/run.sh` 结构)+ `fde-assignment.service/.timer`(OnUnitActiveSec=5min)·`sudo systemctl enable --now fde-assignment.timer`。
验证: `systemctl list-timers | grep fde-assignment` 出现。
本地 commit 部署纪录(把 run.sh 内容存 `phase3/backend/scripts/fde_assignment_run.sh.example`)。

---

### Task 6: 走骨架闭环验收(S1 binding-DONE 判据)

**Step 1: 用户(专家#1)打开飞书派活表**
确认:看到指派给自己的行 · 状态=已派单 · 验收标准列内容完整可读。
用户把状态改成「已领取」(领活动作=专家在飞书的唯一操作)。

**Step 2: 公网验证引擎同步在位**

```bash
curl -s "https://www.nautilus.social/api/platform/fde/tasks" | python -c "
import sys, json
d = json.load(sys.stdin)
print([t for t in d['data']['tasks'] if t['task_uid'].startswith('expert_')])"
```
Expected: expert_ 行 status=claimed · claimed_by=expert:<用户>

**Step 3: 截图/记录证据 → memory**
S1 闭环判据全中:专家从飞书领到实际买方任务+看到验收标准+引擎同步。落 memory(binding-DONE+证据)。

---

### Task 7: 废弃老路径 + 收尾

**Step 1:** FDE_BUSINESS_CHARTER §1 防丢失契约追加:「FDE派活表 = base EOVh / table <id>·派单唯一入口·名册 md+手工 curl dispatch 自 2026-06-12 废弃(S1 闭环)」+ commit charter。
**Step 2:** memory 索引更新(MEMORY.md 一行)。
**Step 3:** 跨框 outbound 投 cloud:告知 compass(派活表已立·12 题名册模式谢幕)/v5(expert: 前缀 claim 行别碰·human-author 路径)。

---

## 验收总查(S1 Definition of Done)
- [ ] 4 个 TDD 测试 green + 既有 FDE 测试无回退
- [ ] 飞书派活表在位·schema 10 列·记入宪章
- [ ] 1 道实际买方任务:飞书行→runner→dispatch+expert: claim→写回「已派单」→用户领取
- [ ] 公网 /tasks 可见 expert_ 行 claimed_by=expert:<用户>
- [ ] kairos 没抢走 human 任务(claimed_by 验证)
- [ ] timer 在跑(5min 轮询=生产路径·不靠手)
- [ ] 老路径废弃声明入宪章 + 跨框已告知
