# -*- coding: utf-8 -*-
"""全框生产快照 v0(哨兵度量面)——平台框每日跑一次,治"拿平台度量面冒充组织全景"。
输出: frame_snapshot_YYYYMMDD.md(四仓 git 24h + 云关键表 + 拍板登记处)
本地跑: python docs/evidence/org-os/pilot/frame_snapshot.py
"""
import subprocess
import sys
import urllib.request
import json
from datetime import datetime
from pathlib import Path

REPOS = {
    "flywheel": r"C:\Users\chunx\Projects\nautilusflywheel",
    "v5": r"C:\Users\chunx\nautilus-v5",
    "compass": r"C:\Users\chunx\Projects\nautilus-compass",
    "platform": r"C:\Users\chunx\Projects\nautilus-core",
}
GOALS = {
    "flywheel": "GOALS.md", "v5": "GOAL_ACTIVE.md",
    "compass": "(无专属,看仓内 docs)", "platform": r"docs\GOAL_STACK.md",
}

L = [f"# 全框生产快照 {datetime.now():%Y-%m-%d %H:%M}", ""]

L.append("## 四框 git(24h)")
for name, path in REPOS.items():
    # FRAME.yaml 存在性:三件配方函(id154/156,9/3)合规自报采集——
    # 追踪靠每日快照亮牌,不靠人工催办(9/4 实测 compass/platform ✓ v5/flywheel ✗)
    fr = "✓" if (Path(path) / "FRAME.yaml").exists() else "✗未落"
    n = subprocess.run(["git", "-C", path, "rev-list", "--count",
                        "--since=24 hours ago", "HEAD"], capture_output=True,
                       text=True).stdout.strip() or "0"
    last = subprocess.run(["git", "-C", path, "log", "-3", "--pretty=%ad %s",
                           "--date=format:%H:%M"], capture_output=True, text=True
                          ).stdout.strip().splitlines()
    L.append(f"- **{name}**: {n} commits · goals={GOALS[name]} · FRAME={fr}")
    for ln in last:
        L.append(f"  - {ln[:96]}")

L += ["", "## 云关键表(经 backend API 只读)"]
try:
    q = json.dumps({"query": "SELECT 1"}).encode()  # API 无通用查询,走 ssh 快查
    r = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=10", "cloud",
         "cd /home/ubuntu/nautilus-mvp/phase3/backend && python3 -c \""
         "import sys; sys.path.insert(0,'.');"
         "import models.agent_survival"
         "from models.org_mailbox import OrgMailbox"  # noqa - 保 mapper
         "\""], capture_output=True, text=True, timeout=30)
except Exception:
    pass
db = subprocess.run(
    ["ssh", "-o", "ConnectTimeout=12", "cloud",
     r"""cd /home/ubuntu/nautilus-mvp/phase3/backend && python3 - <<'PYEOF'
import sys; sys.path.insert(0,'.')
import models.agent_survival
from utils.database import SessionLocal
from sqlalchemy import text
s=SessionLocal()
mb=s.execute(text("SELECT COUNT(*),MAX(created_at)::date FROM org_mailbox WHERE created_at>now()-interval '24h'")).fetchone()
cap=s.execute(text("SELECT agent_id,last_at::date FROM platform_agent_capability_stats ORDER BY last_at DESC LIMIT 3")).fetchall()
und=s.execute(text("SELECT COUNT(*) FROM feishu_decisions WHERE choice IS NULL AND card_sent")).fetchone()
led=s.execute(text("SELECT trace_id,title FROM feishu_decisions WHERE trace_id LIKE 'decision-%' ORDER BY id DESC LIMIT 5")).fetchall()
ag=s.execute(text("SELECT COUNT(*) FROM agents WHERE last_heartbeat>now()-interval '1h'")).fetchone()
# 三盲区读数 9/22(soul 活性/agent 池存量——沉默类入每日对账,治"只盯事件不看沉默存量")
ag7=s.execute(text("SELECT COUNT(*) FROM agents WHERE last_heartbeat>now()-interval '7 days'")).fetchone()
ag30=s.execute(text("SELECT COUNT(*) FROM agents WHERE last_heartbeat>now()-interval '30 days'")).fetchone()
sl=s.execute(text("SELECT COUNT(*),MAX(created_at)::date FROM org_mailbox WHERE from_agent='soul' AND created_at>now()-interval '2 days'")).fetchone()
# 交付时钟矩阵 RED(A2-P1,9/23 上线 GET /api/platform/org/delivery-clock)——活体身份
# 的 RED 入日报(历史死号/测试账号自滤:LIVE_IDS 白名单外的 RED 是几月前测试痕迹)
dc=None
try:
    import requests as _rq
    _r=_rq.get("https://www.nautilus.social/api/platform/org/delivery-clock",timeout=15)
    dc=_r.json()["data"]
except Exception as _e:
    dc={"red":[],f"err":str(_e)[:60]}
LIVE_IDS={"v5","compass","flywheel","soul","vc_daily","platform","kairos","nautilus-prime-001","v7-telegram","ag_local_laptop_001","nautilus-v5","v7-orchestrator","unknown"}
dc_live_red=[a for a in dc.get("red",[]) if a in LIVE_IDS]
# 经营对账存量水位(9/21 接线:洞=积压无声,快照只记流量不数存量)
gov=s.execute(text("SELECT COUNT(*),MIN(created_at)::date,COUNT(*) FILTER (WHERE created_at<now()-interval '3 days') FROM platform_improvement_proposals WHERE status='pending'")).fetchone()
tk=s.execute(text("SELECT COUNT(*) FROM academic_tasks WHERE status IN ('open','claimed','in_progress')")).fetchone()
pen=s.execute(text("SELECT id,title,deadline::date FROM org_mailbox WHERE deadline>now() ORDER BY deadline LIMIT 5")).fetchall()
undt=s.execute(text("SELECT trace_id,title FROM feishu_decisions WHERE choice IS NULL AND card_sent ORDER BY id DESC LIMIT 5")).fetchall()
# 场分离读数(U31 20261001:plane 列,生产资格要挣;入每日读数防场分离成一过性文档)+soul形态门计数
pl=s.execute(text("SELECT plane, count(*) FROM platform_agents GROUP BY plane")).fetchall()
sg=s.execute(text("SELECT count(*) FROM org_mailbox WHERE ack_note LIKE '%形态门打回%'")).scalar()
print(f"plane_agents={[(str(p[0]),p[1]) for p in pl]} soul_gate_rejected={sg}")
# PC-004 断奶仪表(U28 20260930 用户拍:口径=硬介入only)——7日硬拍板类函化石
pc=s.execute(text("SELECT created_at::date,from_agent,title FROM org_mailbox WHERE created_at>now()-interval '7 days' AND (title LIKE '%转呈%' OR title LIKE '%呈批%' OR title LIKE '%拍板%' OR title LIKE '%终裁%' OR title LIKE '%待人工%' OR title LIKE '%呈用户%') ORDER BY id")).fetchall()
print(f"pc004_hard_letters_7d={[(str(p[0]),p[1],p[2][:36]) for p in pc]}")
print(f"mailbox_24h={mb[0]} last={mb[1]}")
print(f"capability_recent={cap}")
print(f"cards_undecided_sent={und[0]}")
print(f"ledger_latest={[l[0] for l in led]}")
print(f"agents_heartbeat_1h={ag[0]}")
print(f"agents_hb_7d={ag7[0]} agents_hb_30d={ag30[0]}")
print(f"soul_letters_48h={sl[0]} soul_last={sl[1]}")
print(f"delivery_clock_red_live={dc_live_red} (历史死号自滤)")
print(f"gov_pending={gov[0]} oldest={gov[1]} older3d={gov[2]}")
print(f"tasks_open_chain={tk[0]}")
print(f"mailbox_live_deadlines={[(p[0],p[1][:40],str(p[2])) for p in pen]}")
print(f"undecided_cards_detail={[(u[0],u[1][:40]) for u in undt]}")
# 商业读数(9/22 A 项:对账第一屏必须是钱,不是内部卫生——收银台已通,账本接钱箱)
o1=s.execute(text("SELECT COUNT(*),COALESCE(SUM(paid_amount),0),COALESCE(SUM(quoted_price),0) FROM orders")).fetchone()
o2=s.execute(text("SELECT status,COUNT(*) FROM platform_orders GROUP BY status")).fetchall()
recent=s.execute(text("SELECT order_no,status,COALESCE(paid_amount,0) FROM orders ORDER BY id DESC LIMIT 3")).fetchall()
print(f"biz_orders_total={o1[0]} paid_sum={o1[1]} quoted_sum={o1[2]}")
print(f"biz_platform_orders={o2}")
print(f"biz_recent={recent}")
# DCR 钱箱(compass #812 方案A直查;真单口径=tag≠test)——9/23 端到端过,收钱线读数入日报首屏
try:
    import sqlite3 as _sq
    _dc=_sq.connect('/home/ubuntu/nautilus-data/accounts.db')
    _dr=_dc.execute("SELECT status,COUNT(*),COALESCE(SUM(amount_cents),0) FROM orders WHERE COALESCE(json_extract(metadata,'$.tag'),'')!='test' AND plan NOT IN ('test','e2e_1fen','team') GROUP BY status").fetchall()
    _e2e=_dc.execute("SELECT order_id,status FROM orders WHERE order_id='HR202609231609176F0DE7'").fetchone()
    _dc.close()
    print(f"biz_dcr_real={_dr} (分,tag!=test口径)")
    print(f"biz_dcr_e2e_firstpay={_e2e}")
except Exception as _e:
    print(f"biz_dcr_real=ERR {str(_e)[:60]}")
s.close()
PYEOF"""], capture_output=True, text=True, timeout=40)
for ln in (db.stdout or db.stderr).strip().splitlines()[:22]:
    L.append(f"- {ln}")

# 商业读数提到帧首(注意力锚定:商业线第一屏)
_biz = [l for l in L if l.startswith("- biz_")]
if _biz:
    L = [L[0], "", "## 💰 商业读数(钱箱)", *_biz] + [x for x in L[1:] if not x.startswith("- biz_")]

L += ["", "## 经营对账·资产探活(外部触点健康,9/21 外发双杀教训固化)"]
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/128"}
ASSETS = [  # (名, URL, 过时标志词;判不到=UNKNOWN 防误报;词命中=🔴STALE)
    # www:标志词=旧定位在售("AI Agent Task Marketplace"=已判死方向,现业务=具身数采/验证平台)。
    # 门户转正前每日报旧定位亮牌(9/22 三盲区:网站七个月未更无人知;soul 9/21 已附转正方案 0d20c01a8)
    ("www.nautilus.social", "https://www.nautilus.social", "Task Marketplace"),
    ("dev.to@chunxiaoxx", "https://dev.to/feed/chunxiaoxx", None),
    ("github/nautilus-compass", "https://github.com/chunxiaoxx/nautilus-compass", None),
    ("data.nautilus.social", "https://data.nautilus.social", None),
    ("HN@chunxiao", "https://news.ycombinator.com/user?id=chunxiao", None),
    # 注:账号级状态(banned/shadow-kill)本地直连拿不到(reddit WAF 拦、HN 对僵号静默),
    # 状态事实登记在 docs/CHANNEL_REGISTRY.md 资产册;探活只判服务可达,UNKNOWN 不误报
    ("Reddit@JaneRoberts93", "https://www.reddit.com/user/JaneRoberts93", None),
]
for name, url, kw in ASSETS:
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=15)
        body = r.read(4000).decode("utf-8", "ignore")
        flag = f"🔴STALE(仍含'{kw}')" if kw and kw in body else "OK"
        L.append(f"- {name}: {r.status} {flag}")
    except Exception as e:  # noqa: BLE001
        L.append(f"- {name}: UNKNOWN({str(e)[:40]})")

# 差距判读(规则化,阈值醒牌——对账的对象是存量差距,不是事件)
# 云心跳对账(timer/cron 活≠产出活——9/22 do_one_thing 权限失败首案:
# syslog CMD 行每 6min 在案但产物 log 从未建;timer active/heartbeat 200 都不是"在干活"的证据)
tm = subprocess.run(
    ["ssh", "-o", "ConnectTimeout=12", "cloud",
     "for t in $(systemctl list-timers --all --no-pager | grep -F .timer | "
     "awk '{print $(NF-1)}' | grep -E 'nautilus|v5|compass|org-|fde|v7-|soul|stake'); do "
     "p=$(systemctl cat $t 2>/dev/null | grep -cE 'OnCalendar|OnUnitActiveSec'); "
     "echo P$p $(systemctl list-timers $t --no-pager 2>/dev/null | grep -F .timer); done; "
     "echo --LOG--; stat -c %y /var/log/do_one_thing.log 2>/dev/null || echo NEVER_RAN"],
    capture_output=True, text=True, timeout=40)
_tm_out = tm.stdout or ""
_orgt = [l for l in _tm_out.splitlines() if l.startswith("P") and ".timer" in l]
# 只判周期型(P1=带 OnCalendar/OnUnitInactiveSec);boot 型(OnBootSec 一次性,如
# compass-fleet-capsule 9/22 首案)重启前不跑是设计行为,判静默=误报
_stale = [l.split()[-2] for l in _orgt if l.startswith("P1")
          and ("n/a" in l or ("ago" in l and any(w in l for w in ("day", "week", "month"))))]
L += ["", "## 经营对账·云心跳对账(timer 活≠产出活)"]
# 端点接线对账(U29 20261001 用户批,square 死挂载首例):机制不会消失只会静默掉线,
# 每日对账 main.py import vs include_router——import 未挂载=🔴;孤儿 router=🟡 登记
try:
    _ea = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parents[4] / "ops" / "endpoint_audit.py")],
        capture_output=True, text=True, timeout=30)
    _ea1 = (_ea.stdout or "").strip().splitlines()[0] if (_ea.stdout or "").strip() else "ERR"
    L.append(("- 🔴 " if _ea.returncode == 2 else "- ") + _ea1[:180])
except Exception as e:  # noqa: BLE001
    L.append(f"- 端点接线对账跳过({str(e)[:40]})")
L.append(f"- systemd timers: 组织域周期型 {len([l for l in _orgt if l.startswith('P1')])} 个;超 24h 未跑/无记录: "
         + (", ".join(_stale) if _stale else "无✅"))
_dl = _tm_out.split("--LOG--")[-1].strip() or "NEVER_RAN"
L.append(f"- cron do_one_thing 产物 log: "
         + ("NEVER(权限失败未修,证据函#788 呈 v5;修后本读数自动转绿)" if "NEVER" in _dl else _dl[:44]))
if _stale:
    L.append("- 🔴 云 timer 超静默项(上)——按 timer 名查 journalctl/产物 mtime,勿信 timer active")

L += ["", "## 经营对账·差距判读"]
_out = db.stdout or ""
def _num(prefix, line_source):
    ln = next((l for l in line_source.splitlines() if l.startswith(prefix)), "")
    try:
        return int(ln[len(prefix):].split()[0].strip("([,"))
    except Exception:  # noqa: BLE001
        return -1
_gov = next((l for l in _out.splitlines() if l.startswith("gov_pending=")), "")
try:
    _gp, _o3 = int(_gov.split()[0].split("=")[1]), int(_gov.split("older3d=")[1].split()[0])
except Exception:  # noqa: BLE001
    _gp, _o3 = -1, -1
if _gp >= 40:  # 9/24 棘轮收紧:旧阈值>50 不含等号,恰好50条压线未亮(实锤修复)
    L.append(f"- 🔴 治理积压水位: {_gp} pending(超3d {_o3}) — 按 docs/GOV_PENDING_TRIAGE_20260924.md 分诊执行(9/26)")
if _num("cards_undecided_sent=", _out) > 3:
    L.append(f"- 🟡 决策卡未决 {_num('cards_undecided_sent=', _out)} 张(>48h 未决默认过时,重发或撤)")
for _l in _out.splitlines():
    if _l.startswith("mailbox_live_deadlines=") and _l != "mailbox_live_deadlines=[]":
        L.append(f"- 🟡 在途函 deadline: {_l[len('mailbox_live_deadlines='):]}"[:200])
if _num("agents_hb_7d=", _out) == 0:
    L.append("- 🔴 agent 池 7d 零活跃(354 注册全休眠,干活的是六框身份;外部池=待引流资产,勿当现役)")
if _num("soul_letters_48h=", _out) == 0:
    L.append("- 🔴 soul 48h 零来函(timer 活≠产出活:查云 systemd timer 实跑与 workspace commit 时间线)")
# 状态函刻面(998-② 9/25 第三刀):digest_human 会把本节带进每日人话推送
L.append(f"- 状态函·待用户: 决策卡未决 {_num('cards_undecided_sent=', _out)} 张;介入计数→见下方 PC-004 断奶仪表节(U28 9/30 用户拍:口径=硬only,本快照自供)")
_dc_red = [l for l in _out.splitlines() if l.startswith("delivery_clock_red_live=")]
if _dc_red and _dc_red[0] != "delivery_clock_red_live=[] (历史死号自滤)":
    L.append(f"- 🔴 交付矩阵 RED 活体: {_dc_red[0][len('delivery_clock_red_live='):]}"[:200]
             + "(A2-P1 矩阵;超 48h 零交付——断供处置线候选,协议 V1 §5)")
if "🔴BANNED" in "\n".join(L) or "🔴STALE" in "\n".join(L) or "UNKNOWN" in "\n".join(L):
    L.append("- 🔴 外部资产异常(见上节;STALE=门户旧文案在售)——发布/外发动作前先修资产")

# PC-004 断奶仪表(M0·U28 20260930 晚用户三拍:M0/M1 开工/口径=硬only/预授权池≤¥200)
# 硬介入=用户拍板或动手;自动源=函化石(转呈/呈批/拍板/终裁/待人工/呈用户类函),
# 手工源=intervention_log.jsonl(session 闭轮登记,ops/log_intervention.py)——
# 手工恒 0 而函化石高=登记纪律失守,亮牌(文档不是肌肉,登记纪律也要被对账)。
try:
    import ast as _ast
    _pc_line = next((l for l in _out.splitlines() if l.startswith("pc004_hard_letters_7d=")), "")
    _pc_rows = _ast.literal_eval(_pc_line[len("pc004_hard_letters_7d="):]) if _pc_line else []
    _by_day: dict = {}
    for _d, _fa, _ti in _pc_rows:
        _by_day.setdefault(_d, set()).add((_fa, _ti))  # 同(发件人,标题)去重=唯一拍板件
    _today_s = datetime.now().date().isoformat()
    _ilog = Path(__file__).parent / "intervention_log.jsonl"
    _manual = []
    if _ilog.exists():
        for _ln in _ilog.read_text(encoding="utf-8").splitlines():
            try:
                _manual.append(json.loads(_ln))
            except Exception:  # noqa: BLE001
                pass
    _man_today = [r for r in _manual if str(r.get("ts", ""))[:10] == _today_s]
    L += ["", "## PC-004 断奶仪表(硬介入分类账·口径=硬only,U28 9/30 用户拍)"]
    _auto_today = len(_by_day.get(_today_s, set()))
    L.append(f"- 今日硬介入: 自动 {_auto_today} 件(函化石) + 手工 {len(_man_today)} 件(session 登记) = {_auto_today + len(_man_today)}")
    _trend = " ".join(f"{d[5:]}:{len(v)}" for d, v in sorted(_by_day.items()))
    L.append(f"- 7 日函化石逐日(唯一件): {_trend or '无'}")
    for r in _manual[-5:]:
        L.append(f"- 手工台账 [{str(r.get('ts', ''))[:10]}] {r.get('category', '?')}: "
                 f"{str(r.get('summary', ''))[:44]}(可移交={r.get('could_delegate', '?')} 宿主={r.get('host') or '未定'})")
    _dl004 = (datetime(2026, 10, 7).date() - datetime.now().date()).days
    L.append("- 目标线: 10/7≤8 → 10月底≤3 → 11月中≤2(基线重测中:旧口径 15-20 含软/被动,"
             "硬-only 首周=新基线,目标不随口径上调)")
    L.append(f"- 距 10/7 读数日 {_dl004} 天")
except Exception as e:  # noqa: BLE001
    L.append(f"- PC-004 仪表跳过({str(e)[:60]})")

# 预注册判据回访(9/24 首案:mailbox/驾驶舱判据注册后到期多日无人验——预注册无回访债,
# 与"心跳≠产出"同构;登记处=preregistered_checks.json,只收无其他强制位盯着的判据,
# 有 SLA 载体(函件 deadline/闹钟)的不重复挂;验证后填 status=verified 即消音)
try:
    _pcr = json.loads((Path(__file__).parent / "preregistered_checks.json").read_text(encoding="utf-8"))
    _open = [r for r in _pcr if r.get("status") not in ("verified", "abandoned")]  # abandoned=9/30 起路线核销档(PC-002 首例),同 verified 消音
    _due_n = _warn_n = 0
    for r in _open:
        d = (datetime.now().date() - datetime.strptime(r["due"], "%Y-%m-%d").date()).days
        if d > 0:
            L.append(f"- 🔴 [PC:{r['id']}] {r['what'][:40]}: due {r['due']} 已过期{d}天未验 — verify: {r['verify'][:44]}")
            _due_n += 1
        elif d > -7:
            L.append(f"- 🟡 [PC:{r['id']}] {r['what'][:40]}: {-d}天后到期 — verify: {r['verify'][:44]}")
            _warn_n += 1
    if _open and _due_n == 0 and _warn_n == 0:
        L.append(f"- 预注册判据回访: {len(_open)}项在册,无到期未验✅")
except Exception as e:  # noqa: BLE001
    L.append(f"- 预注册判据回访跳过({str(e)[:40]})")

# 免疫肌肉年检(轮换抽验):每日按日号轮换报一行登记表——文档不会自动成为肌肉,
# 登记过的"肌肉"也要被抽验(能自动验的已被本快照各读数覆盖,其余当日人工核;LVD 衰减案=抽检必要性首证)
try:
    _ledger = Path(__file__).resolve().parents[6] / "docs" / "IMMUNE_LEDGER.md"
    _lrows = [r for r in _ledger.read_text(encoding="utf-8").splitlines()
              if r.startswith("|") and "教训" not in r and "---" not in r]
    _c = [c.strip() for c in _lrows[datetime.now().day % len(_lrows)].strip("|").split("|")]
    L.append(f"- 🎯 今日肌肉抽验(轮换 {datetime.now().day % len(_lrows) + 1}/{len(_lrows)}):"
             f"{_c[0][:40]} → 验证:{_c[3][:44]}")
except Exception as e:  # noqa: BLE001
    L.append(f"- 肌肉抽验跳过({str(e)[:40]})")

L += ["", "## 判读口诀",
      "- 判断组织状态以本快照+各框 GOALS 为准,勿拿单框度量外推全景;",
      "- 决策卡/发函前:先查 ledger_latest 有无同主题更新拍板(>48h 未决卡默认过时);",
      "- 快照缺失某框=该框 24h 零 commit(正常休眠,不是死亡)。",
      "- 复盘新教训:必过 docs/IMMUNE_LEDGER.md 五类强制位找落位,无位明示'当前无肌肉'——文档不是肌肉,禁只写文档结案。"]

out = Path(__file__).parent / f"frame_snapshot_{datetime.now():%Y%m%d}.md"
out.write_text("\n".join(L), encoding="utf-8")
print(f"written {out} ({len(L)} lines)")
print("\n".join(L[:14]))

# 顺带重扫架构机器层(防"做完就丢":结构数据每日再生成,零人工维护)
# sys.executable:任务计划上下文无 python 别名,裸 "python" 会失败(9/4 org_snapshot_daily 实测)
try:
    subprocess.run([sys.executable, str(Path(__file__).resolve().parents[2] / "ops" / "gen_architecture.py")],
                   capture_output=True, text=True, timeout=180)
except Exception as e:  # noqa: BLE001
    print("arch rescan skipped:", str(e)[:80])

# 顺带表健康采一条,每日幂等追加本地 jsonl(趋势=git 历史;云端纯读零写入——
# 不写 platform_metrics_snapshots:其消费方无类型过滤读 LIMIT 1,插入会污染业务健康分)
try:
    th = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=12", "cloud",
         "cd /home/ubuntu/nautilus-mvp/phase3/backend && python3 ops/table_health.py"],
        capture_output=True, text=True, timeout=45)
    jl = [l for l in (th.stdout or "").splitlines() if l.startswith("JSON: ")]
    if jl:
        rec_th = json.loads(jl[0][6:])
        jp = Path(__file__).parent / "table_health.jsonl"
        prev = jp.read_text(encoding="utf-8").splitlines() if jp.exists() else []
        done = set()
        for ln in prev:
            try:
                done.add(json.loads(ln).get("date"))
            except Exception:
                pass
        if rec_th["date"] not in done:
            with jp.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec_th, ensure_ascii=False) + "\n")
            print("table_health recorded:", rec_th["date"])
        else:
            print("table_health: today already recorded")
except Exception as e:  # noqa: BLE001
    print("table_health skipped:", str(e)[:80])


def push_to_feishu(path: Path) -> None:
    """快照推飞书 p2p:scp 快照上云 → 云端 ops/send_snapshot_push.py 发(凭据在云)。"""
    scp = subprocess.run(["scp", "-o", "ConnectTimeout=15", str(path),
                          "cloud:/tmp/snap.txt"], capture_output=True, text=True)
    if scp.returncode != 0:
        print("scp fail:", scp.stderr[:120]); return
    r = subprocess.run(["ssh", "-o", "ConnectTimeout=15", "cloud",
                        "cd /home/ubuntu/nautilus-mvp/phase3/backend && "
                        "python3 ops/send_snapshot_push.py"],
                       capture_output=True, text=True, timeout=90)
    print((r.stdout or r.stderr).strip()[:120])


if "--push" in sys.argv:
    push_to_feishu(out)
