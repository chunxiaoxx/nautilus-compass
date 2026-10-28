# RSI+FDE 整合控制台 · Phase 1+2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** 把 RSI+FDE 环的后两臂接上生产(Phase 1)+ 把 /control 从只读升级为环的"显性化+控制台"(Phase 2:drill-down 看实况 + admin 门控 dispatch)。

**Architecture:** 复用现成 building block(anchor #5):Phase 1 外科 scp 已建好的 fde_grounding/fde_rsi_delta 路由+migration 到 cloud 分叉分支(soul-audit-increment1·不 pull master)。Phase 2 新 `api/control_plane_actions.py` 用 admin-email 白名单门(require_admin 包 get_current_user),dispatch 复用 platform_dispatch._ROUTES,drill-down 复用现成查询;前端 ControlCenterPage 加 is_admin 显隐 + 弹层 + 确认框。

**Tech Stack:** FastAPI · PostgreSQL(本地 5433 / cloud) · alembic · React19+TS+Vite · pytest TDD · 生产 cloud SSH 外科部署。

**设计依据:** `docs/plans/2026-06-10-rsi-fde-integrated-control-plane-design.md`

---

# Phase 1 · 闭环后两臂上生产(外科部署)

> cloud backend 在分叉分支 `soul-audit-increment1`(`/home/ubuntu/nautilus-mvp`),control_plane 已在(本 session 投过),但 fde_grounding/fde_rsi_delta/migration **不在** cloud。本地 worktree 已有且 main.py 已 wire(L86-87/638-639)+ migration `alembic/versions/c4f8a1b6d3e9_fde_rsi_deltas.py`。

### Task 1.1: 外科投放文件 + 备份
**Step 1:** 本地确认在位:`ls phase3/backend/api/fde_grounding.py phase3/backend/api/fde_rsi_delta.py phase3/backend/models/fde_rsi_delta.py phase3/backend/services/fde_grounding.py phase3/backend/alembic/versions/c4f8a1b6d3e9_fde_rsi_deltas.py`。
**Step 2:** 备份 cloud main.py:`ssh cloud 'cd /home/ubuntu/nautilus-mvp/phase3/backend && cp main.py main.py.bak_pre_rsiwire_$(date +%Y%m%d_%H%M%S)'`。
**Step 3:** scp 5 文件到 cloud 对应路径(api/、models/、services/、alembic/versions/)。
**Step 4:** 验证落地:`ssh cloud 'ls -l <5 paths>'` 字节数>0。
**Step 5:** Commit(无本地改动则跳过·此 task 纯 ops)。

### Task 1.2: wire cloud main.py(idempotent)
**Step 1:** python3 脚本(同 control_plane wire 模式)在 cloud main.py 插入(若未含 `fde_grounding_router`):
```
from api.fde_grounding import router as fde_grounding_router
from api.fde_rsi_delta import router as fde_rsi_delta_router
app.include_router(fde_grounding_router)
app.include_router(fde_rsi_delta_router)
```
锚点 = `app.include_router(control_plane_router)` 之后插入。
**Step 2:** 确认:`ssh cloud 'grep -n fde_grounding_router main.py'` 出现 import+include。

### Task 1.3: cloud alembic migrate fde_rsi_deltas 表
**Step 1:** 先查 cloud alembic 多 head 风险:`ssh cloud 'cd .../backend && <venv-python> -m alembic heads'`(cloud python 是 python3/venv·先 `which python3`+找 venv)。
**Step 2:** 若单 head 路径含 c4f8a1b6d3e9 祖先 → `alembic upgrade c4f8a1b6d3e9`。若多 head 冲突 → **不 merge heads**(memory 警告),改直接建表:从 migration 的 `upgrade()` 提取 CREATE TABLE SQL,`psql` 直接执行(标注绕过 alembic·记录)。
**Step 3:** 验证表存在:`ssh cloud 'psql ... -c "\d fde_rsi_deltas"'` 显示 14 列。
**Step 4:** 记录所用方式(alembic vs 直建)。

### Task 1.4: restart + 公网验证(binding-DONE Phase 1)
**Step 1:** `ssh cloud 'sudo systemctl restart nautilus-backend && sleep 5 && systemctl is-active nautilus-backend'`。
**Step 2:** 公网验:`curl -s https://www.nautilus.social/api/platform/fde/grounding -o /dev/null -w "%{http_code}"` → 200。
**Step 3:** `curl https://www.nautilus.social/api/platform/fde/rsi_delta` → 200(GET list)。
**Step 4:** control-plane 仍 200(回归):`curl .../api/platform/control-plane`。
**Step 5:** Phase 1 binding-DONE 记录。Commit(ops 记录到 plan 或 memory)。

---

# Phase 2 · /control = 环控制台

## 后端(TDD·新 `api/control_plane_actions.py`)

### Task 2.1: require_admin + GET whoami
**Files:** Create `phase3/backend/api/control_plane_actions.py` · Test `phase3/backend/tests/test_control_plane_actions.py`
**Step 1 失败测试:** `test_whoami_admin_vs_nonadmin`:自建 app+mount router+override get_current_user 返伪 User(email)。env `CONTROL_ADMIN_EMAILS="boss@x.com"`。admin user → `GET /api/platform/control-plane/whoami` `{is_admin:true}`;非 admin → `{is_admin:false}`。
**Step 2:** 跑 → FAIL。
**Step 3 实现:**
```python
import os
from fastapi import APIRouter, Depends, HTTPException, Body
from utils.database import get_db
from utils.auth import get_current_user

router = APIRouter(prefix="/api/platform/control-plane", tags=["Control Plane Actions"])

def _admin_emails() -> set[str]:
    raw = os.environ.get("CONTROL_ADMIN_EMAILS", "")
    return {e.strip().lower() for e in raw.split(",") if e.strip()}

def is_admin_user(user) -> bool:
    allow = _admin_emails()
    if not allow:
        return False  # 未配置 → 默认无人 admin(fail-closed)
    cand = {str(getattr(user, "email", "")).lower(), str(getattr(user, "username", "")).lower()}
    return bool(cand & allow)

def require_admin(user=Depends(get_current_user)):
    if not is_admin_user(user):
        raise HTTPException(status_code=403, detail="control-plane: admin only")
    return user

@router.get("/whoami")
def whoami(user=Depends(get_current_user)):
    return {"success": True, "data": {"is_admin": is_admin_user(user),
            "identity": getattr(user, "email", None) or getattr(user, "username", None)}, "error": None}
```
**Step 4:** 跑 → PASS。**Step 5:** Commit。

### Task 2.2: POST /dispatch 服务端代理(admin 门·复用 _ROUTES)
**Files:** Modify `api/control_plane_actions.py` · Test 同文件
**Step 1 失败测试:** `test_dispatch_admin_routes_and_nonadmin_403`:admin POST `{target:"soul",action:"ping",payload:{}}` → 200 含 `routed_to`;非 admin → 403;未知 target → 400。
**Step 2:** FAIL。
**Step 3 实现:**(复用 platform_dispatch 的路由表·不重造)
```python
from api.platform_dispatch import _ROUTES

@router.post("/dispatch")
def cp_dispatch(body: dict = Body(...), user=Depends(require_admin)):
    target = (body or {}).get("target"); action = (body or {}).get("action")
    if not target or not action:
        raise HTTPException(400, "target+action required")
    route = _ROUTES.get(target)
    if route is None:
        raise HTTPException(400, f"unknown target · valid: {', '.join(_ROUTES)}")
    routed_to, adapter = route
    delivered, detail = adapter(action, (body or {}).get("payload") or {})
    # 审计:emit event(复用现成·fail-soft)
    _audit("dispatch", user, {"target": target, "action": action, "delivered": delivered})
    return {"success": True, "data": {"target": target, "action": action,
            "routed_to": routed_to, "delivered": delivered, "detail": detail}, "error": None}
```
`_audit(kind,user,meta)` = try 调现成 outcome/event emit·except pass(fail-soft·不崩)。admin 门替代 platform-key(不持 key)。
**Step 4:** PASS。**Step 5:** Commit。

### Task 2.3: POST /goal(派 goal 给 soul·admin)
**Step 1 失败测试:** `test_goal_admin_forwards`:admin POST `/goal {goal:"...",payload:{}}` → 200(经 target=soul 转发·delivered best-effort);非 admin → 403。
**Step 2:** FAIL。
**Step 3 实现:** 薄封装 → 复用 `_ROUTES["soul"]` adapter,action="dispatch_goal",payload 带 goal。返回 routed_to/delivered/detail + `_audit`。
**Step 4:** PASS。**Step 5:** Commit。

### Task 2.4: drill-down GET verdict/agent/task(复用现成查询)
**Step 1 失败测试:** `test_drilldown_shapes`:seed 1 FdeVerdict(items 含 reason)+ 1 Agent → `GET /verdict/{id}` 返 items+reason;`GET /agent/{id}` 返 survival/基本;缺 → 404。(admin 门可选·drill 只读·设为 require_admin 一致门控)
**Step 2:** FAIL。
**Step 3 实现:** 三个 GET,查 FdeVerdict/Agent/Task by id,组装详情 dict,fail-soft。复用 models 查询不新建表。
**Step 4:** PASS。**Step 5:** Commit。

### Task 2.5: wire main.py(本地)+ 源级 wiring 测试
**Files:** Modify `phase3/backend/main.py` · Test `tests/test_control_plane_actions_wired.py`
**Step 1-5:** import+include control_plane_actions_router(control_plane_router 后)· 源级断言测试(main 本地不可 import·同 test_control_plane_wired 模式)red→green · Commit。

## 前端(ControlCenterPage 升级)

### Task 2.6: is_admin 显隐
**Files:** Modify `phase3/website/src/pages/ControlCenterPage.tsx`
**Step 1:** 加 state `isAdmin`,mount fetch `GET /api/platform/control-plane/whoami` 设 isAdmin。
**Step 2:** 控制件(下面 dispatch/drill 按钮)`{isAdmin && ...}` 包裹;非 admin 维持现只读。
**Step 3:** build(`npm run build` 须带 canonical .env·VITE_API_URL 裸 origin)→ 0 error。**Step 4:** Commit。

### Task 2.7: drill-down 弹层
**Files:** `ControlCenterPage.tsx` + Create `src/components/DrillDownModal.tsx`
**Step 1:** verdict 行/agent 卡可点 → 打开 DrillDownModal,fetch `/control-plane/verdict|agent/{id}`,渲染 items+reason / survival。
**Step 2:** loading/error 态 + 关闭。**Step 3:** build green。**Step 4:** Commit。

### Task 2.8: dispatch 面板 + goal + 确认框
**Files:** `ControlCenterPage.tsx` + Create `src/components/ConfirmDialog.tsx`
**Step 1:** admin 区:target 选(soul/compass/agent)+ action 输入 + 派 goal 快捷 → 点击先弹 ConfirmDialog(明示将 POST 什么)→ 确认才 POST `/control-plane/dispatch` 或 `/goal` → 显 routed_to/delivered。
**Step 2:** 错误态。**Step 3:** build green。**Step 4:** Commit。

### Task 2.9: 前端 e2e(admin 预览)
**Step 1:** 起 control-plane dev server(8077·或全后端)+ vite(`VITE_API_PROXY` 指后端·`CONTROL_ADMIN_EMAILS` 含测试身份)。
**Step 2:** 临时 public 预览路由(同上次 `/__control_preview`·验完删)渲染 → 浏览器(host.docker.internal)看:is_admin 控制件显示、点 verdict 开弹层、dispatch 确认框→触发。截图。
**Step 3:** 删临时路由。**Step 4:** Commit。

## 部署(外科)+ binding-DONE

### Task 2.10: 生产部署 + 四判据验收
**Step 1:** 后端:scp `api/control_plane_actions.py` + wire cloud main.py(idempotent)+ **cloud .env 设 `CONTROL_ADMIN_EMAILS=<用户登录 email/username>`**(用户提供·或先设占位) + restart。
**Step 2:** 前端:`npm run build`(带 canonical .env)→ tar/scp → 备份 current → rsync --delete → chown www-data。
**Step 3 binding-DONE 四判据:**
① admin JWT `curl POST /api/platform/control-plane/dispatch` → routed;非 admin JWT → 403;无 token → 401。
② 公网 `GET /control-plane/whoami` 带 admin token → is_admin:true。
③ 浏览器以 admin 登录开 /control → 点 verdict 开详情 + dispatch 确认框真派 goal;非 admin 只读无控制件。
④ 控制动作出现在审计(control-plane feed / event)。
**Step 4:** 站点 root 200 未坏(回归)。**Step 5:** 四判据全绿 → Commit + 更新 memory + finishing-a-development-branch。

---

## 执行
worktree `rsi-fde-integrated-control-plane`(已建)· subagent-driven · TDD red→green 每后端 task · 复用 _ROUTES/get_current_user/现成查询不重造 · admin-email 门 fail-closed · 写动作确认框+审计 · 生产外科部署备份验证 · scope 冻结(舰桥 v2:拓扑图/5深挖/time-travel/完整角色/demo 不碰)。
