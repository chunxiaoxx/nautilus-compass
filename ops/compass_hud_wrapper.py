#!/usr/bin/env python
# statusLine 包装器:跑 claude-hud 原生 HUD + 追加 compass 段(daemon健康 + 当前项目记忆数 + 最近drift)
import sys, os, json, subprocess, socket, glob

raw = sys.stdin.read()
try:
    info = json.loads(raw)
except Exception:
    info = {}

# 1. 跑 claude-hud(把同一 stdin 喂进去)
HUD = r"C:\Users\chunx\.claude\plugins\claude-hud\claude-hud\0.0.10\dist\index.js"
if not os.path.exists(HUD):
    # 兼容 cache 路径
    cands = glob.glob(r"C:\Users\chunx\.claude\plugins\**\claude-hud\**\dist\index.js", recursive=True)
    HUD = cands[0] if cands else None
hud_out = ""
if HUD:
    try:
        p = subprocess.run(["node", HUD], input=raw, capture_output=True, text=True, encoding="utf-8", timeout=8)
        hud_out = (p.stdout or "").rstrip("\n")
    except Exception:
        hud_out = ""

# 2. compass daemon 健康
def daemon_ok():
    try:
        s = socket.socket(); s.settimeout(4.0); s.connect(("127.0.0.1", 9876))
        s.sendall((json.dumps({"action": "recall", "query": "ping", "top_k": 1, "scope": "project", "project": "C--Users-chunx"}) + "\n").encode())
        buf = b""
        while True:
            c = s.recv(65536)
            if not c: break
            buf += c
            try: json.loads(buf.decode()); break
            except: continue
        s.close()
        return json.loads(buf.decode()).get("ok", False)
    except Exception:
        return False

# 3. 当前项目记忆数(按 cwd 编码)
cwd = info.get("cwd") or info.get("workspace", {}).get("current_dir") or os.getcwd()
enc = str(cwd).replace(":\\", "--").replace(":/", "--").replace("\\", "-").replace("/", "-")
mem_dir = os.path.join(os.path.expanduser("~"), ".claude", "projects", enc, "memory")
mem_n = len(glob.glob(os.path.join(mem_dir, "*.md"))) if os.path.isdir(mem_dir) else 0

ok = daemon_ok()

# 4. v3.0.4 · 动态段:daemon /status 5min 窗口 + 最新记忆年龄 + 本 prompt drift 分(每条 prompt 都变)
import time
dyn = ""
drift_seg = ""
last_age = ""
try:
    # drift:拿最近一次 verification_log 的 drift_score(HUD 刷新频率下最诚实的代理)
    vl = os.path.join(os.path.expanduser("~"), ".claude", "plugins", "nautilus-compass", ".cache", "verification_log.jsonl")
    if os.path.exists(vl):
        with open(vl, "rb") as f:
            f.seek(0, 2); sz = f.tell(); f.seek(max(0, sz - 8000))
            tail = f.read().decode("utf-8", "replace").strip().splitlines()
        for ln in reversed(tail):
            try:
                rec = json.loads(ln)
                ds = rec.get("drift_score")
                if ds is not None:
                    drift_seg = f" \x1b[2mdrift {ds:+.2f}\x1b[0m" + ("\x1b[31m ⚠\x1b[0m" if rec.get("drift_alert_v2") else "")
                    break
            except Exception:
                continue
except Exception:
    pass
try:
    s2 = socket.socket(); s2.settimeout(4.0); s2.connect(("127.0.0.1", 9876))
    s2.sendall(b'{"action":"status"}\n')
    b2 = s2.recv(65536); s2.close()
    st = json.loads(b2.decode())
    sl = st.get("recall", {}).get("sliding_5min", {})
    dyn = f" {sl.get('count_5min',0)}q/{sl.get('p95_ms',0)}ms"
    if sl.get("overload_5min"): dyn += " ⚠ovl"
except Exception:
    dyn = ""
try:
    mds = sorted(glob.glob(os.path.join(mem_dir, "*.md")), key=os.path.getmtime)
    if mds:
        age = (time.time() - os.path.getmtime(mds[-1])) / 60
        last_age = ("%.0fmin" % age) if age < 90 else ("%.1fh" % (age/60)) if age < 2880 else "stale"
except Exception:
    pass

# 5. v3.0.5 · 命中计数(价值可见化):今日/1h recall 命中数,来自 verification_log
hit_seg = ""
try:
    vl2 = os.path.join(os.path.expanduser("~"), ".claude", "plugins", "nautilus-compass", ".cache", "verification_log.jsonl")
    if os.path.exists(vl2):
        with open(vl2, "rb") as f:
            f.seek(0, 2); sz2 = f.tell(); f.seek(max(0, sz2 - 400000))
            lines2 = f.read().decode("utf-8", "replace").strip().splitlines()
        today = time.strftime("%Y-%m-%d", time.gmtime())
        n_today = n_1h = 0
        cutoff = time.time() - 3600
        for ln in lines2:
            try:
                r2 = json.loads(ln)
                if not (r2.get("top5")): continue
                ts = r2.get("ts", "")
                if ts[:10] == today: n_today += 1
                t2 = time.mktime(time.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")) if len(ts) >= 19 else 0
                if t2 and t2 >= cutoff: n_1h += 1
            except Exception:
                continue
        if n_today or n_1h:
            hit_seg = f" \x1b[35m🧠{n_today}hit\x1b[0m\x1b[2m/{n_1h}h\x1b[0m"
except Exception:
    pass

status = "\x1b[32m✓\x1b[0m" if ok else "\x1b[31m✗daemon\x1b[0m"
compass_seg = ("\x1b[36m📡compass\x1b[0m " + status
               + f" \x1b[2m{mem_n}mem\x1b[0m" + dyn
               + (f" \x1b[2m·最新{last_age}\x1b[0m" if last_age else "")
               + drift_seg + hit_seg)

if hud_out:
    print(hud_out + "  \x1b[2m│\x1b[0m  " + compass_seg)
else:
    print(compass_seg)

# v3.0.4 · 顺带刷新 STATUS_CACHE(combined-hud.mjs 的 🧭 段读它;原 poller 从未装上,
# 缓存冻结 8/15 → HUD 十天不变。每次 statusline 渲染即刷新,零额外进程)
try:
    from datetime import datetime, timezone
    cache_p = os.path.join(os.path.expanduser("~"), ".claude", ".cache", "compass-status.json")
    json.dump({"polled_at": datetime.now(timezone.utc).isoformat(),
               "polled_age_s": 0, "poll_interval_s": 30,
               "compass": {"ok": ok, "mem": mem_n, "dyn": dyn.strip()},
               "agents": [], "errors": []},
              open(cache_p, "w", encoding="utf-8"))
except Exception:
    pass
