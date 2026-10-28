#!/usr/bin/env python3
"""Auto-mint poller · 维持 marketplace 有 open code-fix 燃料,让 RSI 飞轮自转。

每 fire:数 open code-fix,< TARGET_OPEN 则从燃料池轮转 mint 一道(fresh uid·防遮蔽)。
V5 消费者自动 claim->produce->compass/bench_eval verify->settle。持续供燃料=V5 棘轮 churn + demo 飞轮自转。
安全:维持 <=TARGET_OPEN open · 燃料轮转 · 单进程 timer 每5min。
env: PLATFORM_DISPATCH_KEY(cloud .env)· FUEL_DIR(默认 ./fuel)· BASE(默认 localhost)· TARGET_OPEN(默认1)
"""
import glob, json, os, subprocess, sys, time
from pathlib import Path

BASE = os.environ.get("BASE", "http://localhost:8000")
FUEL_DIR = Path(os.environ.get("FUEL_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "fuel")))
STATE = Path(os.environ.get("MINT_STATE", os.path.join(os.path.dirname(os.path.abspath(__file__)), ".mint_state.json")))
TARGET_OPEN = int(os.environ.get("TARGET_OPEN", "1"))

def curl(method, path, body=None, headers=None):
    cmd = ["curl","-s","--max-time","30","-X",method,f"{BASE}{path}","-H","Content-Type: application/json"]
    for k,v in (headers or {}).items(): cmd += ["-H", f"{k}: {v}"]
    if body is not None: cmd += ["--data", json.dumps(body, ensure_ascii=False)]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if p.returncode==0 and p.stdout.strip():
        try: return json.loads(p.stdout)
        except json.JSONDecodeError: return {"_raw": p.stdout[:200]}
    return {"_error": f"curl rc={p.returncode}"}

def dispatch_key():
    for p in (os.path.expanduser("~/nautilus-mvp/phase3/backend/.env"), ".env"):
        if os.path.exists(p):
            for ln in Path(p).read_text(encoding="utf-8", errors="ignore").splitlines():
                if ln.startswith("PLATFORM_DISPATCH_KEY="):
                    return ln.split("=",1)[1].strip().strip('"').strip("'")
    return os.environ.get("PLATFORM_DISPATCH_KEY")

def count_open_codefix():
    r = curl("GET","/api/platform/fde/tasks?status=open")
    rows = (r.get("data") or {}).get("tasks", [])
    return sum(1 for t in rows if "code-fix-with-deterministic-verifier" in (t.get("description") or ""))

def fuel_dirs():
    return sorted([Path(p) for p in glob.glob(str(FUEL_DIR/"*")) if (Path(p)/"bench_eval.py").exists()])

def next_fuel():
    dirs = fuel_dirs()
    if not dirs: return None
    idx = 0
    if STATE.exists():
        try: idx = json.loads(STATE.read_text()).get("idx",0)
        except Exception: idx = 0
    fuel = dirs[idx % len(dirs)]
    STATE.write_text(json.dumps({"idx": (idx+1) % len(dirs)}))
    return fuel

def mint(pdkey):
    fuel = next_fuel()
    if not fuel: print("[auto-mint] no fuel"); return False
    bf = glob.glob(str(fuel/"buggy_*.py"))
    if not bf: print(f"[auto-mint] no buggy {fuel.name}"); return False
    spec = (fuel/"task_spec.md").read_text(encoding="utf-8")
    buggy = Path(bf[0]).read_text(encoding="utf-8")
    bench = (fuel/"bench_eval.py").read_text(encoding="utf-8")
    uid = f"compass_exp_{fuel.name}_automint_{int(time.time())}"
    desc = json.dumps({"fde_class":3,"kind":"code-fix-with-deterministic-verifier",
                       "任务概括":spec[:300],"starter_inline":buggy,"verifier_inline":bench}, ensure_ascii=False)
    r = curl("POST","/api/platform/fde/dispatch",
             {"task_uid":uid,"title":f"自动飞轮燃料 {fuel.name}","description":desc},
             {"X-Platform-Key":pdkey})
    st = (r.get("data") or {}).get("status")
    print(f"[auto-mint] minted {uid} status={st}")
    return st=="open"

def main():
    pdkey = dispatch_key()
    if not pdkey: print("[auto-mint] missing PLATFORM_DISPATCH_KEY"); return 1
    n = count_open_codefix()
    print(f"[auto-mint] open code-fix={n} target={TARGET_OPEN}")
    if n >= TARGET_OPEN: print("[auto-mint] enough · skip"); return 0
    mint(pdkey); return 0

if __name__ == "__main__":
    sys.exit(main())
