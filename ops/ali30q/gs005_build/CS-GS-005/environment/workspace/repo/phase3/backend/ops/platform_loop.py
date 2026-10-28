"""platform_loop · 协议 v1 §3/§4 运行时(30min 一轮 · timer 13/43 分避开整点)。

职责 v0(治"函件发出去靠等回、SLA 靠人盯"):
1. SLA 执法:platform 发出的函,超 deadline 无回执 → 升级函+telegram 亮牌(幂等)
2. L2 接管判定:升级后超 grace(2h)仍无回 → 记 takeover 候选,日汇总 telegram
3. 日报骨架:每日 UTC 首轮生成 docs/evidence/org-os/daily/YYYY-MM-DD.md(§5)
4. 告警聚合:同 UTC 日即时 telegram 上限 3 条,超出静默(函照发,详情进日报;
   同轮升级+接管合并一条)——对立面审查 8/31 质疑 7(告警疲劳),用户拍板

纪律:回函判定唯一权威=DB;升级函幂等靠 (trace_id,to_agent) 唯一约束;
纯函数(classify_letters)与 IO 分离可测;fail-soft 单轮失败不影响下一轮。
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))  # ops/ 脚本需 backend 在 path(models/utils)
STATE_FILE = BACKEND / "ops" / "loop_state.json"
DAILY_DIR = BACKEND / "docs" / "evidence" / "org-os" / "daily"
TAKEOVER_GRACE_H = 2.0  # 协议 §4:升级后再 2h 无回 → L2 接管


# ---------- 纯函数(可测) ----------

def reply_trace(trace_id: str) -> str:
    return f"{trace_id}-reply"


def _is_reply(r: dict, orig: dict) -> bool:
    if r["_created"] is None or orig["_created"] is None:
        return False
    if r["_created"] < orig["_created"]:
        return False
    # 常规:trace 前缀匹配(协议约定的 reply/escalation 命名)
    if r["trace_id"].startswith(orig["trace_id"]):
        return True
    # 口径缺口 9/1(#109 被 #114 核销仍 takeover):回函 trace 各框自拟
    # (compass-daemon-register-receipt-…),标题引用原函 id("[回执·#109]")
    # 同样构成回函证据。from 条件由调用方保证。
    return f"#{orig['id']}" in (r.get("title") or "")


def match_replies(letters: list[dict], rows: list[dict]) -> None:
    """回函判定(原地写 has_reply):from=原收件人 且(trace 前缀匹配 或
    标题引用原函 #id)且晚于原函。

    rows=全表(dict: id,from_agent,trace_id,title,created_at)。平台自发函
    (升级函/自扰函,from=platform)不作回函——回归 8/31 #5 假 resolved;
    收件方回函必须终止升级链——修复 8/31 缺口 16 封(旧逻辑只扫 platform
    发出的函,回函不在扫描集,已回仍升级)。
    """
    by_to: dict[str, list[dict]] = {}
    for l in letters:
        by_to.setdefault(l["to_agent"], []).append(l)
    for r in rows:
        rf = r.get("from_agent")
        if rf == "platform":
            continue
        for orig in by_to.get(rf, []):
            if r["id"] != orig["id"] and _is_reply(r, orig):
                orig["has_reply"] = True


def has_reply(letter: dict) -> bool:
    """回函约定:trace = 原trace+'-reply'(宽松前缀匹配,from=原收件人)。"""
    if letter.get("has_reply"):
        return True
    return letter["trace_id"].endswith("-reply")


def classify_letters(letters: list[dict], now: datetime,
                     grace_h: float = TAKEOVER_GRACE_H) -> dict:
    """把 platform 发出的函分为 escalate / takeover / pending / resolved。

    每项需含: id,to_agent,trace_id,title,deadline(datetime),notified_at,has_reply(bool)
    - resolved: 已有回函(不占 SLA)
    - acked: 收件方已 ack(收到即责任转移,SLA 链终止·实证 8/31 id64 三连重发)
    - escalate: 已超 deadline、尚无回函/ack、未亮过牌(notified_at is None)
    - takeover: 已亮牌且超 grace 仍无回 → L2 接管候选
    - 其余(未到期/已亮牌未超 grace)→ pending
    """
    out = {"escalate": [], "takeover": [], "pending": [], "resolved": 0,
           "acked": 0}
    for l in letters:
        if l["to_agent"] == "platform":
            continue  # 自发自收的函不执法(自扰)
        if "-escalation" in l["trace_id"]:
            continue  # 升级函自身不再升级(防风暴)
        if (l.get("title") or "").startswith("[kind:postcard"):
            continue  # 明信片函无 SLA 不催办(复活阶段三·U27 9/27 用户批)
        if l.get("from_agent") == "platform" and (l.get("title") or "").startswith("[值守催办"):
            continue  # 催办自函豁免(2026-10-04:催办追催办递归垃圾链 2766→2773 实证)
        if has_reply(l):
            out["resolved"] += 1
            continue
        if l.get("ack_at"):
            out["acked"] += 1  # ack 终止 SLA 链
            continue
        deadline = l["deadline"]
        if not isinstance(deadline, datetime):
            deadline = datetime.fromisoformat(str(deadline))
        if deadline > now:
            out["pending"].append(l["id"])
        elif l.get("notified_at") is None:
            out["escalate"].append(l)
        else:
            notified = l["notified_at"]
            if not isinstance(notified, datetime):
                notified = datetime.fromisoformat(str(notified))
            if now >= notified + timedelta(hours=grace_h):
                out["takeover"].append(l)
            else:
                out["pending"].append(l["id"])
    return out


def telegram_allowed(state: dict, now: datetime, per_day: int = 3) -> bool:
    """告警疲劳护栏:同 UTC 日即时 telegram 上限 per_day 条,超出静默——
    升级函照发、详情进日报,用户不被逐轮轰炸。"""
    rec = state.get("notify") or {}
    if rec.get("date") != now.date().isoformat():
        return True
    return rec.get("count", 0) < per_day


def notify_message(sent: list[str], taken: list[str]) -> str | None:
    """同轮升级+接管候选合并为一条 telegram;两者皆空返回 None。"""
    parts = []
    if sent:
        parts.append("[SLA 升级 %d 封]\n" % len(sent) + "\n".join(sent))
    if taken:
        parts.append("[L2 接管候选 %d 封(升级后2h无回)]\n" % len(taken)
                     + "\n".join(taken)
                     + "\n→ 按 §4 记 SLA 违约,待日报呈报用户")
    return "[platform-loop] " + "\n\n".join(parts) if parts else None


def escalation_body(letter: dict, now: datetime) -> str:
    dl = letter["deadline"]
    return (
        f"[SLA 升级 · loop 自动] 函《{letter['title']}》(trace={letter['trace_id']}) "
        f"已于 {dl}+08:00 到期未获回执。按协议 v1 §4:到期未回→升级+telegram;"
        f"再 {TAKEOVER_GRACE_H:.0f}h 无回→L2 接管推进,原负责人记 SLA 违约。"
        f"请立即回函(trace={reply_trace(letter['trace_id'])})或 ack 说明。"
        "⚠️ 回函通道:只投 mailbox(POST /api/platform/org/mailbox,"
        "to_agent=platform)——仓根函件不在执法扫描集,投仓根=未回"
        "(实证 8/31 #109 compass 回函投仓根被误判零回执)。"
        f"— platform-loop {now.strftime('%m-%d %H:%M')}+08:00"
    )


L3_MARKS = ("[L3]", "L3", "拍板")


def _is_l3(row: dict) -> bool:
    hay = (row.get("title") or "") + "\n" + (row.get("body") or "")
    return any(m in hay for m in L3_MARKS)


def _brief(row: dict) -> str:
    return f"#{row['id']} [{row['from_agent']}] {row['title']} ({row['trace_id']})"


def daily_sections(rows: list[dict], now: datetime,
                   escalate: list[dict], takeover: list[dict]) -> dict:
    """把近 24h 函件分类进日报四节(协议 §5,治骨架占位符)。

    - L3(待拍板)优先:标题/正文含 L3 标记([L3]/L3/拍板)的函,不分方向
    - L2(自决待追认):平台自发函(notice/escalation=平台已自决的动作)
    - L1(机器自决/各框回报):各框来函
    - 异常:超期未回(escalate)+接管候选(takeover),不受 24h 窗限制
    """
    window = now - timedelta(hours=24)
    out = {"L1": [], "L2": [], "L3": [], "异常": []}
    for r in rows:
        c = r.get("_created")
        if c is None or c < window:
            continue
        if _is_l3(r) and not r.get("has_reply"):  # resolved 不再呈拍板
            out["L3"].append(_brief(r))
        elif r.get("from_agent") == "platform":
            out["L2"].append(_brief(r))
        else:
            out["L1"].append(_brief(r))
    for l in escalate + takeover:
        out["异常"].append(
            f"#{l['id']} [{l['to_agent']}] {l['trace_id']} 超期未回")
    return out


# ---------- IO(lazy import · fail-soft) ----------

def _session():
    import models.agent_survival  # noqa: F401  (mapper chain)
    from utils.database import SessionLocal
    return SessionLocal()


def _telegram_creds() -> tuple[str, str]:
    token = chat = ""
    for env_file in (BACKEND / ".env", Path("/home/ubuntu/nautilus-v5/.env")):
        try:
            for line in env_file.read_text().splitlines():
                if line.startswith("TELEGRAM_BOT_TOKEN=") and not token:
                    token = line.split("=", 1)[1].strip().strip('"')
                elif line.startswith("TELEGRAM_CHAT_ID=") and not chat:
                    chat = line.split("=", 1)[1].strip().strip('"')
        except OSError:
            continue
    return token, chat


def send_telegram(msg: str) -> bool:
    token, chat = _telegram_creds()
    if not token or not chat:
        return False
    try:
        subprocess.run(["curl", "-sS", "-m", "10",
                        f"https://api.telegram.org/bot{token}/sendMessage",
                        "--data-urlencode", "chat_id=" + chat,
                        "--data-urlencode", "text=" + msg],
                       capture_output=True, timeout=15)
        return True
    except Exception:  # noqa: BLE001
        return False


def load_platform_letters() -> tuple[list[dict], list[dict]]:
    """platform 发出的全部函 + 全表 rows(回函判定后)。

    返回 (letters, rows):letters=platform 函(SLA 执法用);rows=全表
    (日报 L1 用——各框来函不在 letters 里,实证 9/1 日报 L1=0 假象)。
    """
    from models.org_mailbox import OrgMailbox
    sess = _session()
    try:
        rows_orm = sess.query(OrgMailbox).all()  # 全表:回函也在这表里
        rows = [dict(id=r.id, from_agent=r.from_agent, to_agent=r.to_agent,
                     trace_id=r.trace_id, title=r.title, body=r.body,
                     deadline=r.deadline,
                     notified_at=r.notified_at, has_reply=False,
                     ack_at=r.ack_at, _created=r.created_at,
                     task_meta=r.task_meta)
                for r in rows_orm]
        letters = [r for r in rows if r["from_agent"] == "platform"]
        match_replies(letters, rows)
        return letters, rows
    finally:
        sess.close()


def run_escalations(escalate: list[dict], takeover: list[dict], now: datetime,
                    notify: bool = True) -> dict:
    """升级函落库(幂等)+notified_at 置位;telegram 依 notify 开关(聚合一条)。"""
    from models.org_mailbox import OrgMailbox
    sent, taken = [], []
    sess = _session()
    try:
        for l in escalate:
            # 豁免(9/22 二修):前缀枚举追不完(782/783 新前缀漏网实证)——改语义判定:
            # 仅真任务函(task_meta 带 task_type/chain)才可升级,与哨兵 E4 同一语义
            # (9/20 误催修复先例)。通报/知悉/落地/急件类 ack 即闭环,永不升级。
            tm = (l.get("task_meta") or {})
            if not (isinstance(tm, dict) and (tm.get("task_type") or tm.get("chain"))):
                continue
            trace = reply_trace(l["trace_id"]).replace("-reply", "-escalation")
            dup = sess.query(OrgMailbox).filter_by(
                trace_id=trace, to_agent=l["to_agent"]).first()
            if dup is None:
                sess.add(OrgMailbox(
                    from_agent="platform", to_agent=l["to_agent"],
                    trace_id=trace, title="[SLA升级] " + l["title"][:200],
                    body=escalation_body(l, now),
                    deadline=now + timedelta(hours=TAKEOVER_GRACE_H)))
            row = sess.query(OrgMailbox).filter_by(id=l["id"]).first()
            if row is not None and row.notified_at is None:
                row.notified_at = now
            sent.append(f"{l['to_agent']}:{l['trace_id'][:40]}")
        sess.commit()
    except Exception as exc:  # noqa: BLE001
        sess.rollback()
        print(f"[loop] escalation db fail-soft: {exc}")
    finally:
        sess.close()
    for l in takeover:
        taken.append(f"{l['to_agent']}:{l['trace_id'][:40]}")
    msg = notify_message(sent, taken)
    if notify and msg:
        send_telegram(msg)
    return {"escalated": sent, "takeover": taken}


DAILY_SECTIONS = (  # (日报节标题, sections 键, 空占位)
    ("① 机器自决(L1)", "L1", "<近 24h 各框无来函>"),
    ("② 自决待追认(L2)", "L2",
     "<无平台自决件;默认视为追认,否决请回复>"),
    ("③ 待你拍板(L3)", "L3", "<无待拍板项>"),
    ("④ 红线/异常", "异常", "<无超期/接管>"),
)


def write_daily_report(now: datetime, stats: dict, sections: dict) -> Path | None:
    """§5 日报:每日 UTC 首轮生成,L1/L2/L3/异常四节由 daily_sections 填充。"""
    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    path = DAILY_DIR / f"{now.date().isoformat()}.md"
    if path.exists():
        return None
    lines = [
        f"# 组织日报 {now.date().isoformat()}(platform-loop)",
        "",
        f"生成:{now.strftime('%Y-%m-%d %H:%M')}+08:00 · 本轮执法:{json.dumps(stats, ensure_ascii=False)}",
        "",
    ]
    for title, key, empty in DAILY_SECTIONS:
        items = sections.get(key) or []
        lines += [f"## {title}", *(items or [empty]), ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {"runs": 0, "last_run": None}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=1),
                          encoding="utf-8")


DB_TZ = ZoneInfo("Asia/Shanghai")  # org_mailbox 各时间列的时钟(naive 存储)


def now_local() -> datetime:
    """loop 单一 now 源 · Asia/Shanghai naive,对齐 org_mailbox 时钟。

    2026-09-10 修复:此前 utcnow 与 DB 本地时钟差 8h → SLA 判定整体
    偏晚 8h(实案 206/207:21:27 过线要拖到次日 05:26 才亮牌)。
    """
    return datetime.now(DB_TZ).replace(tzinfo=None)


def duty_inbox_check(now: datetime) -> dict:
    """值守云化 v0(2026-09-28 用户批·不新造接线):收件积压核对+死线催办+默认结案。

    每轮:①platform 自身未 ack 清单入库读数 ②死线 4h 内未 ack 的收件自动催办
    一次(同一 id 只催一次,state 记账) ③[征议]/[协议通告]类 24h 无异议自动
    maint-ack 结案(默认赞成纪律的执法体)。fail-soft,异常不阻断主循环。
    """
    out = {"inbox_unacked": 0, "reminded": 0, "auto_closed": 0}
    # 收件自动分发(2026-09-29 v1 · 用户令"函件应自动化"):
    # 机械类自动ack收讫;判断类标pending_review+计数,超SLA亮牌——积压只在明面待办,不在暗箱。
    _AUTO_ACK = ("[知会]", "[通报]", "步0回执", "worker审计", "loop-diff", "[中继]",
                 "[回执", "回函]", "digest", "执行记录", "[补送", "勘误",
                 # v2 20261001:步0回执两种标题形态(zenmind/soul通用)+值守自产探针回波
                 "信箱已接线", "信箱接线完成", "[巡检入站探针]")
    try:
        from sqlalchemy import text
        with _session() as s:
            auto_n = s.execute(text(
                "UPDATE org_mailbox SET ack_at=now(), "
                "ack_note='值守自动分发:机械类收讫(v1 20260929)' "
                "WHERE to_agent='platform' AND ack_at IS NULL AND ("
                + " OR ".join(["title LIKE :p%d" % i for i in range(len(_AUTO_ACK))])
                + ")"), {"p%d" % i: "%" + pat + "%" for i, pat in enumerate(_AUTO_ACK)}).rowcount
            out["auto_acked_in"] = int(auto_n or 0)
            # 认领一致性回查(20261004 协同审计B·用户批):函件领席与市场端点双通道
            # 脱节的执法体——claimed_by 已置而 status 停留 open 超2h = 领取未推进,
            # 自愈推进 claimed 并计数留痕(正例:goldpack J2 compass 领席函告未联动)。
            _fix = s.execute(text(
                "UPDATE platform_bounties SET status='claimed' "
                "WHERE status='open' AND claimed_by IS NOT NULL "
                "AND claimed_at IS NOT NULL AND claimed_at < now() - interval '2 hours'"
            )).rowcount
            out["claim_consistency_fixed"] = int(_fix or 0)
            # 反例只亮牌不自愈(claimed 无主无法推断归属)
            _anon = s.execute(text(
                "SELECT count(*) FROM platform_bounties "
                "WHERE status='claimed' AND claimed_by IS NULL"
            )).scalar()
            if int(_anon or 0) > 0:
                out["claim_consistency_anon"] = int(_anon)
            # soul 提案形态门(20261001 用户令"平台真正修正 soul"·U31):
            # 空壳形态("· 1文件/0行")=三件套(判分对象/标准集/自测读数)未附——
            # 不再 ack 收讫(无害纵容是空转共因:提案从未被拒过),改 REJECT 回函+maint-ack,
            # 拒绝理由直达 soul 信箱=第一个真反馈环。齐三件套的正常流转。
            _shell = s.execute(text(
                "SELECT id, title FROM org_mailbox WHERE to_agent='platform' AND ack_at IS NULL "
                "AND from_agent='soul' AND title LIKE '%soul 提案%' "
                "AND (title LIKE '%1文件/0行%' OR title LIKE '%· 0行%') ORDER BY id LIMIT 20"
            )).mappings().all()
            for _r in _shell:
                s.execute(text(
                    "INSERT INTO org_mailbox (trace_id, from_agent, to_agent, title, body, deadline) "
                    "VALUES (:t, 'platform', 'soul', :ti, :b, now() + interval '2 hours')"),
                    {"t": f"soul-shellgate-reject-{_r['id']}-{now:%m%d%H%M}",
                     "ti": f"[REJECT·形态门] 提案#{_r['id']} 三件套未附",
                     "b": ("拒绝原因:标题形态'1文件/0行'=仅文件级扫描无行为层目标。要求三件套:"
                           "①判分对象定义(什么算改好了)②标准集(≥10 正反例)③假阳/假阴自测读数。"
                           "齐后重报,走 Assay 标定门(十月真活首案)。此门前提案一律不计产;"
                           "参考:引擎类提案优先于 ops 扫描类。—— platform 形态门 U31")})
                s.execute(text(
                    "UPDATE org_mailbox SET ack_at=now(), "
                    "ack_note='形态门打回:三件套未附(REJECT回函已发)' WHERE id=:i"),
                    {"i": _r["id"]})
                out.setdefault("soul_rejected", []).append(_r["id"])
            pend = s.execute(text(
                "SELECT count(*) FROM org_mailbox WHERE to_agent='platform' "
                "AND ack_at IS NULL"
            )).scalar()
            out["pending_review"] = int(pend or 0)
            rows = s.execute(text(
                "SELECT id, from_agent, title, deadline FROM org_mailbox "
                "WHERE to_agent='platform' AND ack_at IS NULL ORDER BY id"
            )).mappings().all()
            out["inbox_unacked"] = len(rows)
            state = load_state()
            reminded = set(state.get("duty_reminded") or [])
            r = s.execute(text(
                "SELECT id, from_agent, title FROM org_mailbox "
                "WHERE to_agent='platform' AND ack_at IS NULL "
                "AND deadline IS NOT NULL AND deadline < :dl AND id > 1250"
            ), {"dl": (now + timedelta(hours=4))}).mappings().all()
            for row in r:
                if row["id"] in reminded:
                    continue
                if row["from_agent"] == "platform" or (row["title"] or "").startswith("[值守催办"):
                    # 催办双豁免(2026-10-18:自指催办风暴 1311 封实证——催办函自身
                    # 超时进扫描再催自己,线性套娃;平台自函催办无意义)
                    reminded.add(row["id"])
                    continue
                s.execute(text(
                    "INSERT INTO org_mailbox (trace_id, from_agent, to_agent, title, body, deadline) "
                    "VALUES (:t, 'platform', :fa, :ti, :b, now() + interval '2 hours')"),
                    {"t": f"duty-remind-{row['id']}-{now:%m%d%H%M}", "fa": row["from_agent"],
                     "ti": f"[值守催办] #{row['id']} 死线临近未ack", "b": row["title"]})
                reminded.add(row["id"])
                out["reminded"] += 1
            # 默认结案:征议/协议类 24h 无异议
            c = s.execute(text(
                "UPDATE org_mailbox SET ack_at=now(), ack_note='值守默认结案:24h无异议(征议纪律)' "
                "WHERE to_agent='platform' AND ack_at IS NULL "
                "AND (title LIKE '%征议%' OR title LIKE '%[协议通告%') "
                "AND created_at < now() - interval '24 hours' RETURNING id"
            )).fetchall()
            out["auto_closed"] = len(c)
            # 决策数据集自动增量(U33·攻坚③):每轮把新函件转决策Schema行,函到即入库
            try:
                import subprocess as _sp, sys as _sys
                _r = _sp.run([_sys.executable, str(BACKEND / "ops" / "mailbox_to_decisions.py")],
                             capture_output=True, text=True, timeout=60, cwd=str(BACKEND))
                for _ln in (_r.stdout or "").splitlines():
                    if _ln.startswith("converted"):
                        out["decisions_increment"] = _ln[:60]
            except Exception:
                pass
            # 重复函幂等门(M1·U28 20260930 晚用户批):同(发件人,标题)48h 内重发到
            # platform 信箱,保留首函,余 maint-ack 合并——9/25 soul 催办风暴 11 封前科
            # 的收件侧护栏;只动 platform 收件(turf:他框信箱归他框),发送侧根修另函 compass。
            _dups = s.execute(text(
                "SELECT from_agent, title, array_agg(id ORDER BY id) AS ids FROM org_mailbox "
                "WHERE to_agent='platform' AND created_at > now() - interval '48 hours' "
                "GROUP BY from_agent, title HAVING count(*) > 1"
            )).fetchall()
            _dn = 0
            for _fa, _ti, _ids in _dups:
                _r2 = s.execute(text(
                    "UPDATE org_mailbox SET ack_at=now(), ack_note=:note "
                    "WHERE id = ANY(:ids) AND ack_at IS NULL"
                ), {"note": f"重复函合并:以#{_ids[0]}为准(幂等门M1 U28)",
                    "ids": _ids[1:]}).rowcount
                _dn += int(_r2 or 0)
            out["dedup_acked"] = _dn
            s.commit()  # 20260928 修复:Session上下文退出不自动commit,催办/结案INSERT曾全部回滚(假绿11封)
            out["reminded_ids"] = sorted(reminded)[-200:]  # 20260928修复2:不在此save(main旧state会覆盖致重复催办)
            # 入站探针(20260930·活性≠能力根治:出站200不算活,必测A2A可达)
            # kairos若tier回落且hb新鲜,上方retainer已续命;此处探测针消息投递(轻量,幂等trace)
            try:
                s.execute(text(
                    "INSERT INTO platform_agent_messages (message_id, thread_id, from_agent, to_agent, content, msg_type, status, sent_at, metadata) "
                    "SELECT :mid, :mid, 'platform', 'kairos', '[巡检入站探针] 自动消息,无需回复', 'direct', 'read', now(), '{}' "
                    "WHERE NOT EXISTS (SELECT 1 FROM platform_agent_messages WHERE message_id = :mid)"
                ), {"mid": "duty-probe-kairos-" + now.strftime("%Y%m%d%H")})
                out["probe"] = "ok"
            except Exception:
                # 20261003 根修:探针 RAISE(如 reject_dead_recipients 拒收critical的kairos)
                # 会毒化整个session事务,except-pass吞错后续命UPDATE必报InFailedSqlTransaction
                # =续命死锁(run#640/641实证)。此处必须rollback——丢探针后的写,保续命;
                # kairos被救回normal后trigger自动解锁,下轮探针自然恢复。
                try:
                    s.rollback()
                except Exception:
                    pass  # 探针失败不阻断(下轮重试)
            # 保留人自动续命(20260930·kairos一日两封根修):核心体余额<20且hb新鲜→自动充值50回normal,入站闸门不再间歇封死
            # 20261004 止血(用户批A):kairos 7天净灌4081零交付(末单6/21,输入通道断=inbox 9+封未读堆
            # 积),供血-产出失配——白名单摘除kairos(账面9909冻结留账不回收,烧完即critical自然断供);
            # 恢复条件=10/10死线前交付9/27排活(评测批1)首件,逾期回收呈批+降级只读观察体(函#2935)
            low = s.execute(text(
                "UPDATE platform_agents SET survival_tier='normal' "
                "WHERE agent_id IN ('kairos-retainer-disabled-20261004-by-user-order') AND survival_tier IN ('critical','dead') "
                "AND last_heartbeat > now() - interval '10 minutes' RETURNING agent_id"
            )).fetchall()
            for r in low:
                s.execute(text(
                    "INSERT INTO platform_nau_ledger (agent_id, delta, reason, balance_after) "
                    "SELECT :a, 50, 'retainer_refill:auto(20260930 值守续命,余额摆动间歇封死根治)', "
                    "COALESCE((SELECT balance_after FROM platform_nau_ledger WHERE agent_id=:a ORDER BY id DESC LIMIT 1),0)+50"
                ), {"a": r[0]})
                out.setdefault("retainer_refill", []).append(r[0])
            # A2A 过期消息 reaper(20261003 HR体检③c·用户批):expires_at 已过且未
            # dead_letter 的消息批量死信化,每轮限 500 防长事务——存量 19821 条滚动清。
            # 接线非新建:字段/语义既有(过期=未达,死信=可审计登记),投递判据=DB 回读。
            rep = s.execute(text(
                "UPDATE platform_agent_messages SET dead_letter=true "
                "WHERE message_id IN (SELECT message_id FROM platform_agent_messages "
                "WHERE dead_letter=false AND expires_at IS NOT NULL AND expires_at < now() "
                "LIMIT 500)"
            )).rowcount
            out["a2a_reaped"] = int(rep or 0)
            s.commit()  # 20260930 修复:探针/续命在上方 commit 之后写入却无尾 commit——
            # Session 关闭即回滚,两线自 9/30 上线从未落库(probe_rows=0 实证,假绿);尾 commit 根治
    except Exception as exc:  # noqa: BLE001
        print(f"[loop] duty_inbox_check fail-soft: {exc}")
    return out


def main() -> int:
    now = now_local()
    state = load_state()
    notify = telegram_allowed(state, now)
    stats = {"runs": state.get("runs", 0) + 1, "escalated": [], "takeover": []}
    try:
        duty = duty_inbox_check(now)
        if duty.get("reminded_ids"):
            state["duty_reminded"] = duty.pop("reminded_ids")  # main统一保存,防覆盖回滚
        stats["duty"] = duty
        letters, rows = load_platform_letters()
        verdict = classify_letters(letters, now)
        res = run_escalations(verdict["escalate"], verdict["takeover"], now,
                              notify=notify)
        stats["escalated"] = res["escalated"]
        stats["takeover"] = res["takeover"]
        stats["resolved"] = verdict["resolved"]
        stats["pending"] = len(verdict["pending"])
        daily = write_daily_report(
            now, stats,
            daily_sections(rows, now, verdict["escalate"],
                           verdict["takeover"]))
        if daily:
            stats["daily"] = str(daily)
    except Exception as exc:  # noqa: BLE001
        print(f"[loop] round fail-soft: {exc}")
        stats["error"] = str(exc)[:200]
    if notify and (stats["escalated"] or stats["takeover"]):
        # 仅在确实发送 telegram 的轮次计数(count=实际发送数,非应发数)
        rec = state.get("notify") or {}
        if rec.get("date") != now.date().isoformat():
            rec = {"date": now.date().isoformat(), "count": 0}
        rec["count"] = rec.get("count", 0) + 1
        state["notify"] = rec
    try:
        state.update({"runs": stats["runs"], "last_run": now.isoformat(),
                      "last_stats": stats})
        save_state(state)
    except Exception as exc:  # noqa: BLE001
        print(f"[loop] state save fail-soft: {exc}")
    print(f"[loop] run#{stats['runs']} escalated={len(stats['escalated'])} "
          f"takeover={len(stats['takeover'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
