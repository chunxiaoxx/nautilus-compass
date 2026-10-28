#!/usr/bin/env python3
"""dogfood 组件① · 云端监督 supervisor(转移线① · 2026-08-27 单边先行)。

设计: docs/plans/2026-08-25-dogfood-supervision-wiring-design.md §3 ①
- 数据源全只读: convergence API / fde_verdicts 归因 / 各仓 git log --since
- 状态机(预注册,出结果不改): ACTIVE(有实物) → CLAIM_ONLY(容忍1轮) → ZERO(升级)
- 产出: docs/evidence/supervisor/report-YYYYMMDD.jsonl(心跳行 + 状态行)
- Telegram 护栏: 仅 ZERO 升级时推 1 条,消息带 trace_id(用户批准 P1 条款)
运行: python3 ops/supervisor.py(由 systemd timer 每 30min 调起,oneshot)
"""
from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))  # ops/ 脚本需 backend 在 path(models/utils)
REPORT_DIR = BACKEND / "docs" / "evidence" / "supervisor"
STATE_FILE = REPORT_DIR / ".state.json"
TRACE = "dogfood-supervisor-v1"
API = os.environ.get("SUPERVISOR_API", "http://localhost:8000/api/platform/convergence")
REPOS = {  # 双 clone 问题解决前两个都读;V5 本地已归档则只读云端
    "cloud-core": os.path.expanduser("~/nautilus-mvp"),
    "cloud-v5": os.path.expanduser("~/nautilus-v5"),
    "cloud-compass": os.path.expanduser("~/nautilus-compass"),
}
SINCE = "26.hours.ago"


def classify(prev: str, has_evidence: bool, want_notify: bool = False) -> str:
    """预注册状态机(纯函数):ACTIVE/CLAIM_ONLY/ZERO。"""
    if has_evidence:
        return "ACTIVE"
    if prev == "ACTIVE":
        return "CLAIM_ONLY"      # 容忍 1 轮(PoC 不落盘时滞)
    return "ZERO"                # 连续 2 轮无实物 → 升级


def build_report(run_id: str, state: str, obs: dict) -> str:
    return json.dumps({
        "schema": "supervisor-report-v1", "run_id": run_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        "heartbeat": True, "state": state, "trace": TRACE, "obs": obs,
    }, ensure_ascii=False)


def _git_has_new(repo: Path) -> dict:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "log", f"--since={SINCE}", "--oneline"],
            capture_output=True, timeout=30)
        n = len([l for l in out.stdout.decode("utf-8", "replace").splitlines() if l.strip()])
        return {"ok": True, "commits_26h": n}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "err": str(exc)[:80]}


def collect() -> dict:
    obs: dict = {"sources": {}}
    # ① convergence API
    try:
        with urllib.request.urlopen(API, timeout=10) as r:
            obs["sources"]["convergence"] = {"ok": True,
                                             "body": json.loads(r.read().decode())}
    except Exception as exc:  # noqa: BLE001
        obs["sources"]["convergence"] = {"ok": False, "err": str(exc)[:80]}
    # ② git 押送点
    for name, repo in REPOS.items():
        if Path(repo).exists():
            obs["sources"][f"git:{name}"] = _git_has_new(Path(repo))
    # ③ 智星云 GPU(云端无 CLI 时记 unavailable,由本地侧 loop 补)
    obs["sources"]["gpu_cli"] = {"ok": False, "note": "unavailable-on-cloud"}
    # ④ 三曲线记录(台阶一判据数据源): capability 行数 + verified 总数(convergence 已含 7d)
    try:
        import models.agent_survival  # noqa: F401
        from utils.database import SessionLocal
        from models.database import AgentCapabilityStat
        from sqlalchemy import text as _text
        _db = SessionLocal()
        try:
            _n = _db.execute(_text(
                "SELECT count(*) FROM agent_capability_stats "
                "WHERE task_type NOT LIKE 'legacy%'")).scalar()
            _v = _db.execute(_text(
                "SELECT count(*) FROM fde_verdicts WHERE external_verified")).scalar()
        finally:
            _db.close()
        obs["curves"] = {"capability_rows": int(_n or 0), "verified_total": int(_v or 0)}
    except Exception as exc:  # noqa: BLE001
        obs["curves"] = {"capability_rows": None, "err": str(exc)[:60]}
    # 注: memory 曲线(compass obs 数)待 compass 回函确认表名后接入
    # 判定: 任一 git 押送点 26h 内有新 commit 或 convergence 有 7d 增量
    ev = any(v.get("commits_26h", 0) > 0 for k, v in obs["sources"].items()
             if k.startswith("git:"))
    conv = obs["sources"].get("convergence", {}).get("body", {}).get("data", {})
    ev = ev or (conv.get("external_verified", {}).get("last_7d", 0) or 0) > 0
    # 判据补丁(8/27 实证盲区):git 活跃会掩盖生产停机——executor 停了但仓在动,
    # ACTIVE 是假阴性。生产活性 = verified_total 相比上轮有增量(curves 已查 DB)。
    prev_v = None
    if STATE_FILE.exists():
        try:
            prev_v = json.loads(STATE_FILE.read_text()).get("verified_total")
        except Exception:  # noqa: BLE001
            prev_v = None
    cur_v = obs.get("curves", {}).get("verified_total")
    obs["production_delta"] = (cur_v is not None and prev_v is not None
                               and cur_v > prev_v)
    # 生产停机降级:git 有活动但 verified 连续 0 增量 → 视为 CLAIM_ONLY 级(有声明无产出)
    obs["has_evidence"] = ev and (obs["production_delta"] or prev_v is None)
    return obs


def _telegram_creds() -> tuple[str, str]:
    token = chat = ""
    for env_file in (BACKEND / ".env",
                     Path("/home/ubuntu/nautilus-v5/.env")):  # watchdog 同源
        try:
            for line in env_file.read_text().splitlines():
                if line.startswith("TELEGRAM_BOT_TOKEN=") and not token:
                    token = line.split("=", 1)[1].strip().strip('"')
                elif line.startswith("TELEGRAM_CHAT_ID=") and not chat:
                    chat = line.split("=", 1)[1].strip().strip('"')
        except OSError:
            continue
    return token, chat


def _send_telegram(msg: str) -> bool:
    """通用 telegram 发送(P0.5 mailbox 牙齿复用)。返回是否成功。"""
    token, chat = _telegram_creds()
    if not token or not chat:
        print("[supervisor] telegram creds missing; skip notify")
        return False
    try:
        subprocess.run(["curl", "-sS", "-m", "10",
                        f"https://api.telegram.org/bot{token}/sendMessage",
                        "--data-urlencode", f"chat_id={chat}",
                        "--data-urlencode", f"text={msg}"],
                       capture_output=True, timeout=15)
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[supervisor] telegram send failed: {exc}")
        return False


def check_mailbox(warn_hours: int = 12) -> int:
    """org_mailbox 牙齿(P0.5 · org/bootstrap 设计 §3):due<warn_hours 未 ack 未 notified
    → telegram 亮牌一次并置 notified_at(去重)。fail-soft,返回提醒数。"""
    try:
        import models.agent_survival  # noqa: F401  (Agent mapper chain needs AgentSurvival)
        from utils.database import SessionLocal
        from models.org_mailbox import OrgMailbox
    except Exception as exc:  # noqa: BLE001
        print(f"[supervisor] mailbox import skip: {exc}")
        return 0
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    sent = 0
    try:
        db = SessionLocal()
        try:
            rows = (db.query(OrgMailbox)
                    .filter(OrgMailbox.ack_at.is_(None),
                            OrgMailbox.notified_at.is_(None),
                            OrgMailbox.deadline <= now + timedelta(hours=warn_hours))
                    .all())
            for r in rows:
                msg = (f"[{TRACE}] mailbox due: '{r.title}' → {r.to_agent} "
                       f"deadline {r.deadline:%m-%d %H:%M} (trace {r.trace_id}) 未回执")
                if _send_telegram(msg):
                    r.notified_at = datetime.utcnow()
                    sent += 1
            db.commit()
        finally:
            db.close()
    except Exception as exc:  # noqa: BLE001
        print(f"[supervisor] mailbox check skip: {exc}")
    return sent


def _notify(state: str, obs: dict) -> None:
    if state != "ZERO":
        return
    token, chat = _telegram_creds()
    if not token or not chat:
        print("[supervisor] telegram creds missing; skip notify")
        return
    msg = (f"[{TRACE}] ZERO: 连续 2 轮无实物押送。"
           f"sources={json.dumps({k: v.get('ok') for k, v in obs['sources'].items()})}")
    try:
        subprocess.run(["curl", "-sS", "-m", "10",
                        f"https://api.telegram.org/bot{token}/sendMessage",
                        "--data-urlencode", f"chat_id={chat}",
                        "--data-urlencode", f"text={msg}"],
                       capture_output=True, timeout=15)
    except Exception as exc:  # noqa: BLE001
        print(f"[supervisor] telegram send failed: {exc}")


# ── LLM 中转健康探测(2026-08-30 用户拍板 · 8/29 中转间歇 503 事故固化)────
# 背景:全框 Claude Code 走第三方中转(settings.json ANTHROPIC_BASE_URL),
# 8/29 起 glm-claude-pro 分组间歇 503/401,"对话框一直崩溃"根因。故障时
# 本地逃生门 = ~/.claude/failover_claude_api.py(switch kimi / restore)。
LLM_RELAY_PROBE_URL = os.environ.get(
    "LLM_RELAY_PROBE_URL", "https://newapi.07211996.xyz/v1/messages")
LLM_RELAY_PROBE_MODEL = os.environ.get("LLM_RELAY_PROBE_MODEL", "glm-5.3-flash")
RELAY_ALERT_THRESHOLD = 2  # 连续 2 轮(≈1h)FAIL 才告警——防探针自身网络抖动误报


def probe_llm_relay(token: str | None, timeout: int = 30) -> dict:
    """1-token 探测中转:200=OK;HTTP 错/超时=FAIL(带状态);无 token=SKIP(fail-soft)。"""
    if not token:
        return {"status": "SKIP"}
    body = json.dumps({"model": LLM_RELAY_PROBE_MODEL, "max_tokens": 8,
                       "messages": [{"role": "user", "content": "ping"}]}).encode()
    req = urllib.request.Request(
        LLM_RELAY_PROBE_URL, data=body,
        headers={"x-api-key": token, "authorization": f"Bearer {token}",
                 "anthropic-version": "2023-06-01",
                 "content-type": "application/json",
                 "user-agent": "nautilus-supervisor/1.0"})
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        r.read(64)
        return {"status": "OK", "http": r.status}
    except urllib.error.HTTPError as e:
        return {"status": "FAIL", "http": e.code,
                "detail": e.read(120).decode("utf-8", "replace")}
    except Exception as e:  # noqa: BLE001 — 网络层一切异常都归 FAIL
        return {"status": "FAIL", "http": None,
                "detail": f"{type(e).__name__}: {str(e)[:80]}"}


def _relay_token() -> str:
    """探测 token:env 优先,兜底读 BACKEND/.env(同 _telegram_creds 模式·systemd 无需注入)。"""
    tok = os.environ.get("LLM_RELAY_PROBE_TOKEN", "")
    if tok:
        return tok
    try:
        for line in (BACKEND / ".env").read_text().splitlines():
            if line.startswith("LLM_RELAY_PROBE_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    return ""


def check_relay(streak: int) -> int:
    """探测+翻转告警:连续达阈值发 1 条 telegram(持续期不重发),恢复发 1 条。
    返回新 streak(调用方写回 STATE_FILE)。fail-soft。"""
    res = probe_llm_relay(_relay_token())
    if res["status"] == "SKIP":
        return 0
    if res["status"] == "OK":
        if streak >= RELAY_ALERT_THRESHOLD:
            _send_telegram(f"[supervisor] ✅ LLM 中转恢复({LLM_RELAY_PROBE_URL} → 200)")
        return 0
    streak += 1
    if streak == RELAY_ALERT_THRESHOLD:  # 恰达阈值发一条;之后持续失败不重发
        _send_telegram(
            f"[supervisor] 🔴 LLM 中转异常连续{streak}轮: "
            f"HTTP {res.get('http')} {str(res.get('detail') or '')[:80]}"
            f" → 本地跑 python ~/.claude/failover_claude_api.py switch kimi 可切 k3-256k")
    return streak


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    prev = "ACTIVE"
    if STATE_FILE.exists():
        try:
            prev = json.loads(STATE_FILE.read_text()).get("state", "ACTIVE")
        except Exception:  # noqa: BLE001
            prev = "ACTIVE"
    obs = collect()
    state = classify(prev, obs["has_evidence"])
    if state == "ACTIVE":
        import json as _j0
        try:
            _st = _j0.loads(STATE_FILE.read_text())
            if _st.get("zero_dispatched"):
                _st["zero_dispatched"] = False
                STATE_FILE.write_text(_j0.dumps(_st))
        except Exception:  # noqa: BLE001
            pass
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    line = build_report(run_id, state, obs)
    day_file = REPORT_DIR / f"report-{datetime.now(timezone.utc):%Y%m%d}.jsonl"
    with day_file.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    try:  # 读-改-写:保留扩展键(relay_fail_streak 等),不整文件覆写
        _st_all = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}
    except Exception:  # noqa: BLE001
        _st_all = {}
    _st_all["relay_fail_streak"] = check_relay(
        int(_st_all.get("relay_fail_streak", 0)))  # LLM 中转探测(2026-08-30)
    _st_all.update({"state": state,
                    "verified_total": obs.get("curves", {}).get("verified_total"),
                    "ts": datetime.now(timezone.utc).isoformat()})
    STATE_FILE.write_text(json.dumps(_st_all))
    _notify(state, obs)
    check_mailbox()  # org/bootstrap P0.5 · mailbox deadline 牙齿(fail-soft)
    if state == "ZERO":
        _on_zero_dryrun(prev, state, obs, run_id)
    print(f"[supervisor] run={run_id} prev={prev} state={state} "
          f"evidence={obs['has_evidence']} -> {day_file.name}")
    return 0




# ── ZERO→派单翻译器(P0 dry-run · 2026-08-28 用户批 · 设计 v1.1)───────
EXP_KEYWORDS = ("distill", "dpo", "loop", "train", "sft", "rl")
V5_REPO = os.path.expanduser("~/nautilus-v5")
V5_REF = "origin/session/agent-self-improve-20260526"  # 工作分支(fetch 后可见,免 merge)


def classify_cause(commits) -> str:
    """死因分类:YIELDED(让位)/CRASHED(故障)/UNKNOWN(无仓)。"""
    if commits is None:
        return "UNKNOWN"
    hits = sum(1 for subj, _ in commits
               if any(k in subj.lower() for k in EXP_KEYWORDS))
    return "YIELDED" if hits >= 1 else "CRASHED"


def _v5_recent_commits() -> list | None:
    try:
        subprocess.run(["git", "-C", V5_REPO, "fetch", "origin",
                        "refs/heads/session/*:refs/remotes/origin/session/*"],
                       capture_output=True, timeout=60)
        out = subprocess.run(
            ["git", "-C", V5_REPO, "log", V5_REF, "--since=48.hours.ago",
             "--pretty=%s||%h"], capture_output=True, timeout=20)
        lines = [l for l in out.stdout.decode("utf-8", "replace").splitlines() if l]
        # NUL 字节不能作 subprocess 参数(embedded null byte),用 || 分隔
        return [tuple(l.split("||", 1)) for l in lines] or []
    except Exception:  # noqa: BLE001
        return None


def should_dispatch(prev: str, state: str, already: bool) -> bool:
    """仅进入 ZERO 的那一轮触发;连续期/已派过不重发。"""
    return state == "ZERO" and prev in ("ACTIVE", "CLAIM_ONLY") and not already


_INSTR = {
    "YIELDED": "[dry-run] 死因=资源让位(实验 commit 在跑)。指令:向资源 owner 发升级函件,要 executor 恢复 ETA 或并行决策——白名单重启对此无效。",
    "CRASHED": "[dry-run] 死因=疑似故障。指令:①查最后 verdict 时间戳 ②查 unit/进程 ③白名单内重启 systemctl restart nautilus-backend(executor 相关) ④2h 内复核 verified_total。",
    "UNKNOWN": "[dry-run] 死因未知(V5 仓不可读)。指令:诊断(查进程/日志尾部),勿动进程。",
}


def build_dispatch_rec(cause: str, run_id: str, detail: dict) -> dict:
    return {"schema": "zero-dispatch-rec-v1", "run_id": run_id, "cause": cause,
            "mode": "dry-run", "instruction": _INSTR[cause], "detail": detail}


ORG_MAILBOX_API = os.environ.get(
    "ORG_MAILBOX_API", "http://localhost:8000/api/platform/org/mailbox")


def post_dispatch_mail(cause: str, run_id: str, detail: dict) -> bool:
    """P0.5(2026-08-29 · SLA 2h):ZERO 判定轮给 owner 框投 mailbox 工作单。
    deadline=now+2h(用户拍板回函 SLA);幂等 trace=zero-dispatch-<run_id>。
    fail-soft:投递失败只影响 rec.mail_posted,不拖垮监督主流程。"""
    try:
        dl = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(
            timespec="seconds")
        payload = {
            "from_agent": "platform", "to_agent": "v5",
            "trace_id": f"zero-dispatch-{run_id}",
            "title": f"[supervisor] executor ZERO 派单(死因={cause})",
            "body": f"{_INSTR[cause]} run={run_id} "
                    f"detail={json.dumps(detail, ensure_ascii=False)}",
            "deadline": dl,
        }
        req = urllib.request.Request(
            ORG_MAILBOX_API, data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return getattr(r, "status", 200) == 200
    except Exception as exc:  # noqa: BLE001
        print(f"[supervisor] dispatch mail post failed (non-fatal): {exc}")
        return False


def _on_zero_dryrun(prev: str, state: str, obs: dict, run_id: str) -> None:
    """P0:只写建议记录+telegram 建议,不真派单。fail-soft。"""
    try:
        import json as _j
        st = _j.loads(STATE_FILE.read_text())
        if not should_dispatch(prev, state, st.get("zero_dispatched", False)):
            return
        commits = _v5_recent_commits()
        cause = classify_cause(commits)
        detail = {"commits_48h": len(commits or [])}
        rec = build_dispatch_rec(cause, run_id, detail)
        # P0.5:派单函投 owner 框 mailbox(SLA 2h);fail-soft,结果记入 rec
        rec["mail_posted"] = post_dispatch_mail(cause, run_id, detail)
        rec_path = REPORT_DIR / "dispatch_recommendations.jsonl"
        with rec_path.open("a", encoding="utf-8") as f:
            f.write(_j.dumps(rec, ensure_ascii=False) + chr(10))
        st["zero_dispatched"] = True
        STATE_FILE.write_text(_j.dumps(st))
        print(f"[supervisor] ZERO dispatch-rec (dry-run) cause={cause} -> {rec_path.name}")
        # telegram 建议文案(P0 复用 ZERO 通道之外追加一条,周护栏:事件级非演练级)
        _notify("ZERO", {"sources": {"dispatch_rec": {"ok": True,
                                                      "cause": cause,
                                                      "note": rec["instruction"][:120]}}})
    except Exception as exc:  # noqa: BLE001
        print(f"[supervisor] zero-dispatch failed (non-fatal): {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
