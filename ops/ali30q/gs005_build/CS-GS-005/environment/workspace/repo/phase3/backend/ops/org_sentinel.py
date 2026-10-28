# -*- coding: utf-8 -*-
"""组织值守哨兵(系统级 cron,非 LLM)· 2026-09-12 用户拍板 A。

设计:值守 = 事件发生→通知用户,不是 LLM 轮询想事。
E1 to_agent=platform 的新函出现(通知一次;催办归 platform_loop telegram 链)
E2 关注函集 ack 翻转(对方 ack 了我们的等待项)
无变化静默退出;首轮建基线只发一条上线概览(兼作飞书链路验证)。
状态文件在 repo 外(不污染 git);挂 org-sentinel.timer 15min。
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # backend/ 入 sys.path

from sqlalchemy.orm import Session  # noqa: E402

from models.org_mailbox import OrgMailbox  # noqa: E402
from models.fde_dispatch import FdeDispatch  # noqa: E402
import models.agent_survival  # noqa: E402,F401 — mapper dependency(Agent↔AgentSurvival)

# E8:三臂盲评窗口到期时刻(9/19 12:00 投递 + 72h,预注册规则)
ARMS_DEADLINE = datetime(2026, 9, 22, 12, 0)
from utils.database import SessionLocal  # noqa: E402

# 广播三投(202-204 中的未 ack 两封)+ v5 自荐 + soul 拆单征询
WATCH_IDS = [203, 204, 211, 212]
STATE_PATH = os.environ.get("SENTINEL_STATE", "/home/ubuntu/org_sentinel_state.json")


def collect_events(db: Session, state: dict,
                   flywheel_head: str | None = None) -> tuple[list[str], dict]:
    """纯函数:当前 DB/仓状态 vs 上轮快照 → 事件列表 + 新快照。"""
    events: list[str] = []

    # E1 新回函(to=platform 且未通知过)——人话格式(9/14 用户反馈看不懂)
    inbound = (db.query(OrgMailbox)
               .filter_by(to_agent="platform")
               .order_by(OrgMailbox.id).all())
    seen: set[int] = set(state.get("notified_ids", []))
    for r in inbound:
        if r.id not in seen:
            # 贾维斯自身台账(feishu-cmd-*,to=platform)自处理自 ack,
            # 推给用户=纯自指噪音(9/16 用户实收两条误报);计 seen 不推送
            if (r.trace_id or "").startswith("feishu-cmd-"):
                seen.add(r.id)
                continue
            dl = ""
            if r.deadline:
                h = r.deadline.strftime("%m月%d日 %H:%M")
                dl = f"(建议 {h} 前处理)"
            title = r.title.replace("[通报]", "").replace("[回函]", "").strip("[] ")
            events.append(f"📮 要处理:{r.from_agent} 来信 ——「{title[:36]}」{dl}")
            seen.add(r.id)

    # E2 关注函 ack 翻转
    acked: dict[str, bool] = dict(state.get("acked", {}))
    watched = db.query(OrgMailbox).filter(OrgMailbox.id.in_(WATCH_IDS)).all()
    for r in watched:
        was = acked.get(str(r.id), False)
        now_acked = r.ack_at is not None
        if now_acked and not was:
            note = (r.ack_note or "").replace("已处理：", "")[:40] or "已收到"
            events.append(f"✅ 有回应:{r.to_agent} 确认了之前的信 —— {note}")
        acked[str(r.id)] = now_acked

    # E3 飞轮仓 HEAD 变化(GitHub 远程,业务线动态直达——治"产出互相看不见")
    fw = dict(state.get("frames", {}))
    if flywheel_head is not None:
        if fw.get("flywheel_head") and fw["flywheel_head"] != flywheel_head:
            events.append("🔄 飞轮有新进展(数据/业务在推进,细节可问飞轮那边)")
        fw["flywheel_head"] = flywheel_head

    now = datetime.now()
    # E7 欠函镜像检查(9/20:vc_daily PING 教训——我只扫新函,自己欠的回函
    # 靠对方催才暴露。收函>3h 未 ack 的外部来函=潜在欠函,提醒自己)
    my_owed = (db.query(OrgMailbox)
               .filter(OrgMailbox.to_agent == "platform",
                       OrgMailbox.from_agent != "platform",
                       OrgMailbox.ack_at.is_(None),
                       OrgMailbox.created_at < now - timedelta(hours=3),
                       ~OrgMailbox.trace_id.like("%-workered%"),
                       ~OrgMailbox.trace_id.like("%-escalated%"))
               .count())
    if my_owed > 0:
        events.append(f"🔔 平台欠函自查:{my_owed} 封外部来函>3h未回执——请检查是否需回函")

    # E4/E5 共用:按批次聚合任务函(chain=m1),final 收官链的历史任务函不算超时。
    # 9/18 修:final 终报函不带 task_meta(dispatch 生成时即无),只扫 task_meta
    # 非空的行会漏识别 final→豁免失效(sim50 285 被误催实证)。final 单独按
    # trace 识别,批次名=trace 去壳。
    final_batches = {r.trace_id[len("m1-"):-len("-final")]
                     for r in db.query(OrgMailbox)
                     .filter(OrgMailbox.trace_id.like("m1-%-final")).all()
                     if r.trace_id}
    chain_rows = (db.query(OrgMailbox)
                  .filter(OrgMailbox.task_meta.isnot(None))
                  .order_by(OrgMailbox.id.desc()).all())
    batches: dict[str, tuple[bool, datetime | None]] = {}
    for r in chain_rows:
        tm = r.task_meta or {}
        b = tm.get("batch")
        if not b or tm.get("chain") != "m1":
            continue
        has_final, last_at = batches.get(b, (False, None))
        last = r.created_at if (last_at is None or (r.created_at and r.created_at > last_at)) else last_at
        batches[b] = (has_final or (b in final_batches), last)

    # E4 任务函 SLA 超时(9/17 空转保险丝 v0:deadline 已过且未 ack 的任务函,
    # 每函只提醒一次——v5 RSI V2 超时 6h 无人知晓的教训;now 已在 E7 前定义)
    overdue = (db.query(OrgMailbox)
               .filter(OrgMailbox.task_meta.isnot(None),
                       OrgMailbox.deadline < now,
                       OrgMailbox.ack_at.is_(None),
                       OrgMailbox.to_agent != "platform")
               .all())
    sla_warned = set(state.get("sla_warned_ids", []))
    for r in overdue:
        if r.id in sla_warned:
            continue
        tm = r.task_meta or {}
        if not (tm.get("task_type") or tm.get("chain")):
            continue  # 非任务函(9/20 批量回执 task_meta=JSON null 过 SQL
            # isnot(None) 过滤被误催实证):SLA 催办只适用真任务函
        if tm.get("chain") == "m1" and batches.get(tm.get("batch"), (True, None))[0]:
            continue  # 已收官链的历史任务函,收官报即终点,不追超时
        late_h = int((now - r.deadline).total_seconds() // 3600)
        events.append(f"⏰ 任务超时:{r.to_agent} 未回「{(r.title or '')[:32]}」(已过期 {late_h} 小时)")
        sla_warned.add(r.id)
        # E4b 自动催办(9/18:超时即代投催办函,消人肉追函;催办函自身无
        # task_meta,不会再触发 E4;每函一次由 sla_warned 幂等保证)
        from datetime import timedelta as _td
        utrace = f"platform-urge-auto-{r.id}"
        if not db.query(OrgMailbox).filter_by(trace_id=utrace, to_agent=r.to_agent).first():
            db.add(OrgMailbox(from_agent="platform", to_agent=r.to_agent, trace_id=utrace,
                              title=f"[SLA自动催办] 「{(r.title or '')[:40]}」已超时 {late_h} 小时",
                              body="哨兵检测到此任务函已超时未回。请回函:进展状态或阻塞点(哪怕一行)。\n"
                                   "(本函由值守哨兵自动投递,trace 幂等,不会重复催)",
                              deadline=now + _td(hours=2), created_at=now))
            db.commit()

    # E5 活跃链停滞(空转保险丝 P3 操作化 v0:无 final 的链最新函件 >72h 前
    # →提醒;v0 只提醒不自动熔断,自动停链等读数后再议)
    stalled_warned = dict(state.get("stalled_warned", {}))
    today = now.date().isoformat()
    for b, (has_final, last_at) in sorted(batches.items()):
        if has_final or last_at is None:
            continue
        idle_h = int((now - last_at).total_seconds() // 3600)
        if idle_h < 72:
            continue
        if stalled_warned.get(b) == today:
            continue
        events.append(f"🔗 链停滞:m1-{b} 已 {idle_h} 小时无推进(无收官报)——考虑熔断或人工介入")
        stalled_warned[b] = today

    # E6 已办维度(9/19 价值感知整改:自动化不可见悖论——完美运行=安静。
    # 每日首轮附"昨日组织替你完成的事"统计,推一次)
    done_day = now.date().isoformat()
    if state.get("done_reported") != done_day:
        y0 = now.replace(hour=0, minute=0, second=0, microsecond=0)
        n_all = db.query(OrgMailbox).filter(OrgMailbox.created_at >= y0).count()
        n_work = (db.query(OrgMailbox)
                  .filter(OrgMailbox.trace_id.like("%-workered"),
                          OrgMailbox.created_at >= y0).count())
        n_v5 = (db.query(OrgMailbox)
                .filter(OrgMailbox.from_agent == "v5",
                        OrgMailbox.created_at >= y0).count())
        n_score = (db.query(OrgMailbox)
                   .filter(OrgMailbox.title.like("%成绩单%"),
                           OrgMailbox.created_at >= y0).count())
        events.append(f"📋 今日已替你办:组织函件 {n_all} 封 · worker 自动执行 {n_work} 件 · "
                      f"v5 产出 {n_v5} 件 · 成绩单 {n_score} 份(值守/判分/纠错全程自动)")

    # E8 三臂降级保险丝(9/19 预注册规则自动化,免到期人肉执行/遗忘):
    # 72h 窗 prime/v7 六变体零认领 → 降级两臂 + 公布密封映射(trace 幂等)。
    # 有认领的半态不自动降级,提醒人工裁决(规则未覆盖态不猜)。
    if now > ARMS_DEADLINE and not state.get("arms_degraded"):
        arm_uids = [f"exam3arm-q{i}-{a}" for i in (1, 2, 3) for a in ("prime", "v7")]
        n_open = (db.query(FdeDispatch)
                  .filter(FdeDispatch.task_uid.in_(arm_uids),
                          FdeDispatch.status == "open").count())
        dtrace = "platform-3arm-degrade-2arm-20260922"
        if n_open == len(arm_uids):
            if not db.query(OrgMailbox).filter_by(trace_id=dtrace).first():
                db.add(OrgMailbox(
                    from_agent="platform", to_agent="compass", trace_id=dtrace,
                    title="[三臂降级] 72h零认领——按预注册降两臂,密封映射公布:v5→C/v7→B/prime→A",
                    body="预注册规则自动执行(哨兵E8):exam3arm prime/v7 六变体 72h 窗内零认领,\n"
                         "三臂降为两臂(v5 臂三卷已交,判卷 1/1/1,判分线不受影响)。\n"
                         "密封映射公布:v5→ARM-C · v7-telegram→ARM-B · nautilus-prime-001→ARM-A。\n"
                         "六变体保持 open 由平台 Loop 轮标注处置,compass 判分读数以 v5 臂为准。",
                    deadline=now + timedelta(hours=2), created_at=now))
                db.commit()
            events.append("🎯 三臂降级:72h 零认领,已按预注册降两臂+公布映射(函已投 compass)")
            state["arms_degraded"] = True
        elif n_open < len(arm_uids) and not state.get("arms_partial_noted"):
            events.append(f"🎯 三臂窗口到期但存在认领(open {n_open}/6)——预注册未覆盖,请人工裁决")
            state["arms_partial_noted"] = True

    # E9 自动工单生成器(2026-09-21 · RSI 蓝图 S2,反馈段自动化=四段内核最后缺口):
    # 失败即燃料——判分 disagree 模式/催办不响应模式 → 自动 INSERT pending 工单。
    # 安全边界:只产 pending(治理归 soul,approve 权不在本件);确定性 id 幂等。
    # 表无 ORM 模型(仓内服务层同款裸 SQL 风格)。
    try:
        from sqlalchemy import text as _text
        n_e9 = 0

        def _emit(prop_id, rc, change_json, impact, rb):
            nonlocal n_e9
            if db.execute(_text("SELECT 1 FROM platform_improvement_proposals WHERE id=:i"),
                          {"i": prop_id}).first():
                return
            db.execute(_text(
                "INSERT INTO platform_improvement_proposals "
                "(id, task_id, agent_id, root_cause, proposed_change, expected_impact, "
                "rollback_plan, status, vote_score, vote_count, created_at, updated_at) "
                "VALUES (:i, 9000001, 9000002, :rc, CAST(:pc AS jsonb), :im, :rb, "
                "'pending', 0, 0, now(), now())"),
                {"i": prop_id, "rc": rc, "pc": json.dumps(change_json, ensure_ascii=False),
                 "im": impact, "rb": rb})
            n_e9 += 1

        # 触发器1:近 24h 判分 disagree(score=0)≥2 → 模式工单
        dis = db.execute(_text(
            "SELECT task_uid FROM fde_verdicts "
            "WHERE created_at > :t AND score = 0"),
            {"t": now - timedelta(hours=24)}).fetchall()
        if len(dis) >= 2:
            _emit(f"auto-e9-verdict-disagree-{today}",
                  f"24h 内判分 disagree {len(dis)} 次"
                  f"({', '.join(r[0][:24] for r in dis[:4])})",
                  {"type": "verdict_disagree_pattern", "source": "sentinel-e9",
                   "evidence": [r[0] for r in dis[:6]]},
                  "复盘产出侧共性挂点(apply 漂移/未完成),提炼教训块进交卷前置",
                  "工单 pending 无副作用,拒绝即止")
            events.append(f"🔧 E9 工单:24h disagree×{len(dis)} 模式入 P1 池(auto)")
        # 触发器2:24h 内自动催办≥2 次(总催≥2=有任务停滞) → 停滞工单
        urg_n = db.execute(_text(
            "SELECT count(*) FROM org_mailbox WHERE trace_id LIKE 'platform-urge-auto-%' "
            "AND created_at > :t"), {"t": now - timedelta(hours=24)}).scalar() or 0
        if urg_n >= 2:
            _emit(f"auto-e9-stalled-{today}",
                  f"24h 内自动催办 {urg_n} 次(任务响应停滞信号)",
                  {"type": "stalled_task_pattern", "source": "sentinel-e9"},
                  "停滞任务根因分类(收件方过载/通道死/任务不适配),呈报处置",
                  "工单 pending 无副作用,拒绝即止")
            events.append(f"🔧 E9 工单:催办×{urg_n} 停滞模式入 P1 池(auto)")
        if n_e9:
            db.commit()
    except Exception as e:  # noqa: BLE001 — E9 失败不阻塞哨兵主职责
        print(f"E9 error: {e}")

    new_state = {"notified_ids": sorted(seen), "acked": acked, "frames": fw,
                 "done_reported": done_day,
                 "sla_warned_ids": sorted(sla_warned),
                 "stalled_warned": stalled_warned,
                 "arms_degraded": state.get("arms_degraded"),
                 "arms_partial_noted": state.get("arms_partial_noted"),
                 "updated_at": datetime.utcnow().isoformat()}
    return events, new_state


def _baseline(db: Session) -> tuple[str, dict]:
    """首轮:建基线 + **列出全部待处理函明细**。

    9/14 事故定谳:baseline 只报数量不列明细,上线前 14 分钟落库的 213/214/215
    (主线解锁事件)被静默收编,用户零感知。修法=baseline 必须带明细清单,
    宁可首条消息长一点,不吞任何前史事件。
    """
    events, state = collect_events(db, {"notified_ids": [], "acked": {}})
    inbound = [e.replace("📮 ", "") for e in events if e.startswith("📮")]
    acked_n = sum(1 for v in state["acked"].values() if v)
    if not inbound:
        detail = "没有待处理的信"
    elif len(inbound) <= 10:
        detail = "\n".join(inbound)
    else:
        detail = "\n".join(inbound[:10]) + f"\n…(还有 {len(inbound) - 10} 封没列出)"
    text = (f"🛰 值守哨兵已上线(每 15 分钟自动巡查一次)\n"
            f"目前有 {len(inbound)} 封待你处理的信:\n{detail}\n"
            f"之后有新信或新动态会随时推送,没动静就不打扰。")
    return text, state


def main() -> int:
    from ops.feishu_push import push_text

    # E3 数据源:飞轮仓 GitHub 远程 HEAD(匿名 ls-remote,云上无飞轮 git 仓)
    flywheel_head = None
    try:
        import subprocess
        r = subprocess.run(
            ["git", "ls-remote", "https://github.com/chunxiaoxx/nautilusflywheel.git", "main"],
            capture_output=True, text=True, timeout=15)
        if r.returncode == 0 and r.stdout.strip():
            flywheel_head = r.stdout.split()[0][:12]   # hash 即动态信号
    except Exception:  # noqa: BLE001 — 观测源故障不阻塞哨兵主职责
        pass

    db = SessionLocal()
    try:
        state_file = Path(STATE_PATH)
        if not state_file.exists():
            text, state = _baseline(db)
            print(push_text(text))
        else:
            state = json.loads(state_file.read_text(encoding="utf-8"))
            events, state = collect_events(db, state, flywheel_head)
            if events:
                print(push_text("🛰 值守快报:\n" + "\n".join(events)))
            else:
                print("silent: no change")
        state_file.write_text(json.dumps(state, ensure_ascii=False, indent=1),
                              encoding="utf-8")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
