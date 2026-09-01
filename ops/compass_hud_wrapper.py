#!/usr/bin/env python
# statusLine 包装器 v3.0.9:claude-hud 原生段 + compass 段(人话版)
#
# v3.0.9 (2026-09-01) · 治"HUD 又不正常显示"+"内容看不懂":
#   根因① claude-hud 移到 plugins\cache\ 下,硬编码 0.0.10 路径失效 →
#         每次渲染递归 glob 全 plugins 目录兜底(热路径 0.3s+)
#   根因② verification_log.jsonl 涨到 54.8MB,每次渲染读尾部 400KB 逐行
#         json.loads 算今日召回数 → 单次渲染 4.5s → statusline 超时"时有时无"
#   修复:① node 路径探测结果写缓存文件,主流程零 glob
#         ② 今日召回数移入 60s 一次的后台刷新,主流程纯读缓存
#   内容人话:🧭 记忆正常 · 146条 · 今日召回28 · drift -0.03
#         (砍常显的 Nq/P95ms 与"最新stale";仅 p95>5s 或过载时显示 ⚠响应慢)
import sys, os, json, subprocess, glob, time, threading, hashlib

def _cwd_tag():
    # 稳定短 hash(str hash 跨进程随机化会漂移,不能做文件名)
    return hashlib.md5(CWD.encode("utf-8", "replace")).hexdigest()[:8] if CWD else "nocwd"

CACHE_P = os.path.join(os.path.expanduser("~"), ".claude", ".cache", "hud_daemon_cache.json")
HUD_CACHE_P = os.path.join(os.path.expanduser("~"), ".claude", ".cache", "hud_out_cache.txt")
HUD_BIN_CACHE = os.path.join(os.path.expanduser("~"), ".claude", ".cache", "hud_bin_path.txt")
VL_P = os.path.join(os.path.expanduser("~"), ".claude", "plugins", "nautilus-compass",
                    ".cache", "verification_log.jsonl")
CWD = ""


def _mem_count():
    try:
        enc = (CWD.replace(":\\", "--").replace(":/", "--")
               .replace("\\", "-").replace("/", "-"))
        d = os.path.join(os.path.expanduser("~"), ".claude", "projects", enc, "memory")
        return len(glob.glob(os.path.join(d, "*.md"))) if os.path.isdir(d) else 0
    except Exception:
        return 0


def _watchdog():
    try:
        with open(CACHE_P, encoding="utf-8") as f:
            c = json.load(f)
        hit = f" · 今日召回{c['hits_today']}" if c.get("hits_today") else ""
        st = "正常" if c.get("ok") else "服务未响应"
        print(f"\x1b[36m🧭 记忆{st}\x1b[0m{hit} · {_mem_count()}条 \x1b[2m(降级)\x1b[0m")
    except Exception:
        print("\x1b[36m🧭 记忆(降级)\x1b[0m")
    sys.stdout.flush()
    os._exit(1)


_wd = threading.Timer(8.0, _watchdog)
_wd.daemon = True  # 主流程<8s 正常退出时解释器不等看门狗
_wd.start()


def _load_cache(ttl=60.0):
    try:
        with open(CACHE_P, encoding="utf-8") as f:
            c = json.load(f)
        return c, (time.time() - float(c.get("ts", 0))) < ttl
    except Exception:
        return None, False


raw = sys.stdin.read()
try:
    info = json.loads(raw)
except Exception:
    info = {}
CWD = info.get("cwd") or info.get("workspace", {}).get("current_dir") or os.getcwd()

# 1. claude-hud 段:输出读 30s 缓存;miss 派 detached 后台刷新(60s 节流,防 node
#    挂死堆进程)。v3.0.9 · node 路径走缓存文件,插件升级换目录后不再每渲染 glob。
def _hud_bin():
    try:
        with open(HUD_BIN_CACHE, encoding="utf-8") as f:
            p = f.read().strip()
        if p and os.path.exists(p):
            return p
    except Exception:
        pass
    p = r"C:\Users\chunx\.claude\plugins\cache\claude-hud\claude-hud\0.0.10\dist\index.js"
    if not os.path.exists(p):
        cands = glob.glob(r"C:\Users\chunx\.claude\plugins\**\claude-hud\**\dist\index.js",
                          recursive=True)
        p = cands[0] if cands else ""
    if p:
        try:
            os.makedirs(os.path.dirname(HUD_BIN_CACHE), exist_ok=True)
            with open(HUD_BIN_CACHE, "w", encoding="utf-8") as f:
                f.write(p)
        except Exception:
            pass
    return p


hud_out = ""
_hc_fresh = False
try:
    with open(HUD_CACHE_P, encoding="utf-8") as f:
        _hc = json.load(f)
    # v3.0.11 · 缓存按 cwd 分桶:多窗口各自目录,全局单份缓存曾互相覆盖
    # (B 窗口命中 A 窗口的 repo/目录 = "工作目录和仓库混乱")。
    # 兼容旧单份格式(带 'hud' 键的 dict 视作废弃直接重建)。
    _e = _hc.get(CWD) if isinstance(_hc.get(CWD), dict) else None
    if _e:
        hud_out = (_e.get("hud") or "").rstrip("\n")
        _hc_fresh = (time.time() - float(_e.get("ts", 0))) < 30.0
except Exception:
    pass
_spawn_ok = True
_spawn_f = "%s.%s.last_spawn" % (HUD_CACHE_P, _cwd_tag())
try:
    with open(_spawn_f, encoding="utf-8") as f:
        _spawn_ok = (time.time() - float(f.read().strip() or 0)) > 60.0
except Exception:
    pass
if not _hc_fresh and _spawn_ok:
    hud_bin = _hud_bin()
    if hud_bin:
        try:
            with open(_spawn_f, "w", encoding="utf-8") as f:
                f.write(str(time.time()))
            raw_p = "%s.%s.in" % (HUD_CACHE_P, _cwd_tag())
            os.makedirs(os.path.dirname(HUD_CACHE_P), exist_ok=True)
            with open(raw_p, "w", encoding="utf-8") as f:
                f.write(raw)
            _bg = ("import json,time,subprocess,os\n"
                   f"raw=open({raw_p!r},encoding='utf-8').read()\n"
                   f"CP={HUD_CACHE_P!r}\n"
                   "try:\n"
                   f"    p=subprocess.run(['node',{hud_bin!r}],input=raw,capture_output=True,"
                   "text=True,encoding='utf-8',timeout=20)\n"
                   "    out=(p.stdout or '').strip()\n"
                   "    if out:\n"
                   "        try:cwd=json.loads(raw).get('cwd','')\n"
                   "        except Exception:cwd=''\n"
                   "        try:d=json.load(open(CP,encoding='utf-8'))\n"
                   "        except Exception:d={}\n"
                   "        if not isinstance(d,dict):d={}\n"
                   "        d[cwd]={'ts':time.time(),'hud':out}\n"
                   "        json.dump(d,open(CP,'w',encoding='utf-8'),ensure_ascii=False)\n"
                   "except Exception:\n"
                   "    pass\n")
            subprocess.Popen([sys.executable, "-c", _bg], stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             creationflags=0x08000000)  # CREATE_NO_WINDOW
        except Exception:
            pass

# 2. compass daemon 段:主流程零网络,读 60s 缓存;过期/缺失派后台刷新。
#    v3.0.9 · 后台进程顺带算"今日召回"(54.8MB log 尾部解析移出主流程)。
def _refresh_async():
    _bg = (
        "import json,socket,time,os\n"
        f"C={CACHE_P!r}\nVL={VL_P!r}\n"
        "TOK=''\n"
        "try:TOK=open(os.path.expanduser('~/.claude/.cache/compass_daemon_token'),"
        "encoding='utf-8').read().strip()\n"
        "except Exception:pass\n"
        "out={'ts':time.time(),'ok':False,'p95':0,'ovl':False,'hits_today':0}\n"
        "try:\n"
        "    s=socket.socket();s.settimeout(2.0);s.connect(('127.0.0.1',9876))\n"
        "    s.sendall((json.dumps({'action':'recall','query':'ping','top_k':1,"
        "'scope':'project','project':'C--Users-chunx','token':TOK})+'\\n').encode())\n"
        "    buf=b'';dl=time.time()+3.0\n"
        "    while True:\n"
        "        c=s.recv(65536)\n"
        "        if not c:break\n"
        "        buf+=c\n"
        "        if time.time()>dl:break\n"
        "        try:json.loads(buf.decode());break\n"
        "        except Exception:continue\n"
        "    s.close()\n"
        "    out['ok']=json.loads(buf.decode()).get('ok',False)\n"
        "    s2=socket.socket();s2.settimeout(2.0);s2.connect(('127.0.0.1',9876))\n"
        "    s2.sendall((json.dumps({'action':'status','token':TOK})+'\\n').encode())\n"
        "    st=json.loads(s2.recv(65536).decode());s2.close()\n"
        "    sl=st.get('recall',{}).get('sliding_5min',{})\n"
        "    out['p95']=sl.get('p95_ms',0)\n"
        "    out['ovl']=bool(sl.get('overload_5min'))\n"
        "except Exception:\n"
        "    pass\n"
        "try:\n"
        "    with open(VL,'rb') as f:\n"
        "        f.seek(0,2);sz=f.tell();f.seek(max(0,sz-400000))\n"
        "        lines=f.read().decode('utf-8','replace').strip().splitlines()\n"
        "    today=time.strftime('%Y-%m-%d')\n"
        "    n=0\n"
        "    for ln in lines:\n"
        "        try:\n"
        "            r=json.loads(ln)\n"
        "            if r.get('top5') and str(r.get('ts',''))[:10]==today: n+=1\n"
        "        except Exception:continue\n"
        "    out['hits_today']=n\n"
        "except Exception:\n"
        "    pass\n"
        "try:json.dump(out,open(C,'w',encoding='utf-8'))\n"
        "except Exception:pass\n")
    try:
        subprocess.Popen([sys.executable, "-c", _bg], stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=0x08000000)  # CREATE_NO_WINDOW
    except Exception:
        pass


cached, fresh = _load_cache()
if cached is None:
    ok, p95, ovl, hits, cache_age = False, 0, False, 0, None
    _refresh_async()
elif fresh:
    ok = cached.get("ok", False)
    p95, ovl, hits = cached.get("p95", 0), cached.get("ovl", False), cached.get("hits_today", 0)
    cache_age = None
else:
    ok = cached.get("ok", False)
    p95, ovl, hits = cached.get("p95", 0), cached.get("ovl", False), cached.get("hits_today", 0)
    cache_age = int(time.time() - float(cached.get("ts", 0)))
    _refresh_async()

# 3. drift 分(verification_log 尾 8KB,快,保留在线读)
drift_seg = ""
try:
    if os.path.exists(VL_P):
        with open(VL_P, "rb") as f:
            f.seek(0, 2); sz = f.tell(); f.seek(max(0, sz - 8000))
            tail = f.read().decode("utf-8", "replace").strip().splitlines()
        for ln in reversed(tail):
            try:
                rec = json.loads(ln)
                ds = rec.get("drift_score")
                if ds is not None:
                    if rec.get("drift_alert_v2") or ds <= -0.07:
                        drift_seg = f" \x1b[31m⚠drift {ds:+.2f}\x1b[0m"
                    else:
                        drift_seg = f" \x1b[2mdrift {ds:+.2f}\x1b[0m"
                    break
            except Exception:
                continue
except Exception:
    pass

# 4. 组装人话段:状态 · N条 · 今日召回N · drift
seg = "\x1b[36m🧭 记忆\x1b[0m"
if cached is None:
    seg += "\x1b[33m检测中\x1b[0m"
elif ok and cache_age is None:
    seg += "\x1b[32m正常\x1b[0m"
elif ok:
    seg += f"\x1b[32m正常\x1b[0m\x1b[2m·缓存{cache_age}s前\x1b[0m"
else:
    seg += "\x1b[31m服务未响应\x1b[0m"
n = _mem_count()
if n:
    seg += f" \x1b[2m· {n}条\x1b[0m"
if hits:
    seg += f" · 今日召回\x1b[35m{hits}\x1b[0m"
if ok and (ovl or p95 > 5000):
    seg += " \x1b[31m⚠响应慢\x1b[0m"
seg += drift_seg

if hud_out:
    print(hud_out + "  \x1b[2m│\x1b[0m  " + seg)
else:
    print(seg)

# v3.0.4 · 顺带刷新 STATUS_CACHE(combined-hud.mjs 的 🧭 段读它)
try:
    from datetime import datetime, timezone
    cache_p = os.path.join(os.path.expanduser("~"), ".claude", ".cache", "compass-status.json")
    json.dump({"polled_at": datetime.now(timezone.utc).isoformat(),
               "polled_age_s": 0, "poll_interval_s": 30,
               "compass": {"ok": ok, "mem": n,
                           "dyn": ("slow" if (ovl or p95 > 5000) else "ok")},
               "agents": [], "errors": []},
              open(cache_p, "w", encoding="utf-8"))
except Exception:
    pass
