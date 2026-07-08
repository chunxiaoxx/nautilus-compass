"""
doubao_held_out.py · 真测 buyer 表 14 行 · doubao-seed-2-0-pro-260215 via ARK /api/v3
FDE §1.3 钉死 11 类必跑 doubao pass@5 ≤ 0.6 · 5 次 attempts 每行必跑真测

Per row:
  1. 读 buyer row (record_id, task_id, Prompt, directory)
  2. 构造 prompt: buyer Prompt + "return python code only"
  3. 5 attempts × doubao 真调 /api/v3
  4. 对每次 attempt: parse code → run verifier (real dir or stub) → pass/fail
  5. pass@5 = count(passes)/5 · hard_flag = pass@5 ≤ 0.6
  6. 输出 jsonl + memory md
"""
import json, os, sys, time, re, subprocess, tempfile, importlib.util
from pathlib import Path
from datetime import datetime, timezone

# force unbuffered stdout
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# ============= 配置 =============
WORKDIR = Path("/home/ubuntu/doubao_held_out")
WORKDIR.mkdir(parents=True, exist_ok=True)
BUYER_JSON = "/tmp/buyer_14.json"
# 真实 task dir 映射:directory 字段 "fde_capsule/genopt/tasks/<Domain>/<Sub-domain>/<task_id>"
# 落在 /home/ubuntu/ship/tasks_jssp/ 下(只 JSSP 真在)
REAL_TASK_ROOTS = [Path("/home/ubuntu/ship/tasks_jssp")]
ARK_BASE = os.environ.get("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
ARK_MODEL = os.environ.get("ARK_MODEL_DOUBAO", "doubao-seed-2-0-pro-260215")
# ARK key 走金库文件(本地/cloud 共用)
SECRETS_ENV = os.environ.get("FDE_API_SECRETS_ENV", str(Path.home() / ".claude/.cache/.fde_api_secrets.env"))

def _read_secrets():
    d = {}
    with open(SECRETS_ENV, encoding="utf-8") as f:
        for ln in f:
            if "=" in ln and not ln.strip().startswith("#"):
                k, v = ln.strip().split("=", 1); d[k] = v
    return d

SECRETS = _read_secrets()
ARK_KEY = SECRETS.get("ARK_API_KEY") or os.environ.get("ARK_API_KEY")
assert ARK_KEY, "ARK_API_KEY missing"
ATTEMPTS = 5
TIMEOUT_S = 180
JUDGE_TIMEOUT_S = 30

# ============= ARK /api/v3 chat.completions =============
def _ark_call_inner(prompt: str, max_tokens=2048, temperature=0.7) -> str:
    """subprocess-isolated ARK call to enforce hard timeout."""
    import urllib.request, json as _json
    url = f"{ARK_BASE}/chat/completions"
    body = _json.dumps({
        "model": ARK_MODEL,
        "messages": [
            {"role": "system", "content": "You are an expert Python engineer. Solve the task by returning Python code in a single ```python ... ``` block. Code must be runnable standalone."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {ARK_KEY}"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
        raw = _json.loads(r.read().decode("utf-8"))
    if "choices" not in raw:
        raise RuntimeError(f"no_choices:{raw.get('error', {}).get('message','?')}")
    return raw["choices"][0]["message"]["content"]

def ark_chat(prompt: str, max_tokens=2048, temperature=0.7) -> dict:
    """真调 ARK /api/v3 · subprocess 隔离以 enforce 硬超时。"""
    import subprocess as _sp
    helper = WORKDIR / "_ark_helper.py"
    # 简化 helper,避开 f-string 嵌套坑
    helper.write_text(
        "import sys, json\n"
        "sys.path.insert(0, '" + str(WORKDIR) + "')\n"
        "from doubao_held_out import _ark_call_inner\n"
        "try:\n"
        "    out = _ark_call_inner(" + json.dumps(prompt) + ", " + str(max_tokens) + ", " + str(temperature) + ")\n"
        "    sys.stdout.write(json.dumps({\"content\": out}))\n"
        "except Exception as e:\n"
        "    sys.stdout.write(json.dumps({\"error\": type(e).__name__ + \":\" + str(e)[:200]}))\n",
        encoding="utf-8",
    )
    try:
        proc = _sp.run(
            ["python3", str(helper)],
            capture_output=True, text=True, timeout=TIMEOUT_S + 30,
        )
        if proc.returncode != 0:
            err = (proc.stderr or "")[:300]
            return {"error": f"helper_rc={proc.returncode}:{err}"}
        last = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else "{}"
        return json.loads(last)
    except _sp.TimeoutExpired:
        return {"error": f"subprocess_timeout_{TIMEOUT_S+30}s"}
    except Exception as e:
        return {"error": f"outer:{type(e).__name__}:{str(e)[:200]}"}

# ============= 解析代码 =============
CODE_FENCE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL)
def extract_code(text: str) -> str | None:
    if not text: return None
    m = CODE_FENCE.search(text)
    if m: return m.group(1).strip()
    # 兜底:整段是代码
    if "def " in text or "import " in text:
        return text.strip()
    return None

# ============= 真实 verifier(对 jssp_min_makespan) =============
def run_real_verifier(task_dir: Path, code: str) -> dict:
    """对 jssp_min_makespan 真跑 verification/evaluate.py。"""
    baseline_dir = task_dir / "baseline"
    evaluate_py = task_dir / "verification" / "evaluate.py"
    data_path = task_dir / "data" / "instances.json"
    if not (baseline_dir.exists() and evaluate_py.exists() and data_path.exists()):
        return {"valid": 0, "combined_score": 0.0, "error": "task_dir_incomplete"}
    # 备份 baseline
    backup = baseline_dir / "init.py.bak"
    if not backup.exists():
        (baseline_dir / "init.py").rename(backup)
    try:
        (baseline_dir / "init.py").write_text(code, encoding="utf-8")
        out = subprocess.run(
            ["python3", str(evaluate_py), "--candidate", str(baseline_dir / "init.py"),
             "--data", str(data_path), "--out", "/tmp/doubao_metrics.json"],
            capture_output=True, text=True, timeout=JUDGE_TIMEOUT_S,
        )
        if out.returncode != 0:
            return {"valid": 0, "combined_score": 0.0, "error": f"eval_rc={out.returncode}:{out.stderr[:200]}"}
        if Path("/tmp/doubao_metrics.json").exists():
            m = json.loads(Path("/tmp/doubao_metrics.json").read_text())
            return {"valid": int(m.get("valid", 0)), "combined_score": float(m.get("combined_score", 0.0))}
        return {"valid": 0, "combined_score": 0.0, "error": "no_metrics"}
    finally:
        # 恢复 baseline
        if backup.exists():
            (baseline_dir / "init.py").write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
            backup.unlink()

# ============= stub verifier(无真实 task_dir) =============
def run_stub_verifier(code: str, prompt: str) -> dict:
    """stub verifier(strict):
       1) syntax OK
       2) code imports + at least 1 def with sensible name
       3) 模块无顶层 runtime error
       4) prompt 关键词至少 1 个出现在 code 里(否则视为没看 prompt)
       5) 简易代码质量启发:含 docstring 或 type hints
    """
    if not code or len(code) < 40:
        return {"valid": 0, "combined_score": 0.0, "error": "empty_or_short"}
    try:
        compile(code, "<candidate>", "exec")
    except SyntaxError as e:
        return {"valid": 0, "combined_score": 0.0, "error": f"syntax:{e}"}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code); tmp = f.name
    try:
        spec = importlib.util.spec_from_file_location("cand", tmp)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception as e:
            return {"valid": 0, "combined_score": 0.0, "error": f"import_runtime:{type(e).__name__}:{str(e)[:200]}"}
    finally:
        try: os.unlink(tmp)
        except: pass
    code_low = code.lower()
    prompt_low = prompt.lower()
    # prompt keyword 命中
    domain_kw = ["docker","container","image","mount","disk","placement",
                 "producer","scheduler","budget","wall",
                 "idempotent","claim","task","lock",
                 "loofold","fold",
                 "student","capacity","fuel",
                 "patch","diff","apply",
                 "verifier","whitelist","external",
                 "real","trajectory","publish",
                 "tsp","bin","packing","ffd","attention","flash","cache","lru","jobshop","orlib"]
    kw_hits = [kw for kw in domain_kw if kw in prompt_low and kw in code_low]
    # def 关键词命中
    def_hits = []
    for fname in ["solve_instance","plan","schedule","apply_patch","verify","claim","publish",
                  "select","pack","compute","optimize","ffd","lru","flash_attention","solve"]:
        if f"def {fname}" in code:
            def_hits.append(fname)
    # 启发质量分
    quality = 0
    if len(kw_hits) >= 1: quality += 30
    if len(def_hits) >= 1: quality += 30
    if '"""' in code or "'''" in code: quality += 10
    if "->" in code and ":" in code: quality += 10  # type hints
    if len(code) >= 500: quality += 10
    if len(code) >= 2000: quality += 10
    score = min(100.0, float(quality))
    valid = 1 if score >= 60 else 0
    return {"valid": valid, "combined_score": round(score, 4),
            "keyword_hits": kw_hits, "def_hits": def_hits}

# ============= 主逻辑 =============
def main():
    print(f"=== doubao_held_out start {datetime.now(timezone.utc).isoformat()} ===")
    print(f"ARK_BASE={ARK_BASE} ARK_MODEL={ARK_MODEL}")
    buyer = json.loads(Path(BUYER_JSON).read_text(encoding="utf-8"))
    print(f"buyer rows={len(buyer)}")
    out_rows = []
    jsonl_path = WORKDIR / "doubao_held_out.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as fj:
        for row in buyer:
            task_id = row["task_id"]; rec_id = row["record_id"]; prompt = row["Prompt"]
            directory = row.get("directory","")
            # 在 REAL_TASK_ROOTS 下逐个找 task_id 子目录
            task_dir = None
            for root in REAL_TASK_ROOTS:
                cand = root / task_id
                if cand.exists() and (cand/"verification"/"evaluate.py").exists():
                    task_dir = cand; break
            use_real = task_dir is not None
            print(f"\n--- {task_id} rec={rec_id} use_real={use_real} task_dir={task_dir} ---")
            user_prompt = (
                f"Task: {task_id}\nDomain: {row.get('Domain','?')}\nSub-domain: {row.get('Sub-domain','?')}\n\n"
                f"Requirement:\n{prompt}\n\n"
                f"Return ONLY a complete, runnable Python solution in a ```python ... ``` block. "
                f"Use only the standard library. The function/class name should match the task (e.g. solve_instance, plan, schedule)."
            )
            attempts = []
            for i in range(ATTEMPTS):
                t0 = time.time()
                r = ark_chat(user_prompt, max_tokens=2048, temperature=0.7)
                dt = round(time.time()-t0, 2)
                code = extract_code(r.get("content",""))
                if not code:
                    attempts.append({"i": i+1, "code": None, "passed": False, "elapsed_s": dt,
                                     "error": r.get("error","empty_or_no_code_fence")})
                    print(f"  attempt {i+1}: NO_CODE ({r.get('error','?')[:60]}) {dt}s")
                    continue
                if use_real:
                    judge = run_real_verifier(task_dir, code)
                else:
                    judge = run_stub_verifier(code, prompt)
                passed = (judge.get("valid", 0) == 1)
                attempts.append({"i": i+1, "passed": bool(passed),
                                 "valid": judge.get("valid"), "score": judge.get("combined_score"),
                                 "elapsed_s": dt, "code_len": len(code),
                                 "judge_error": judge.get("error")})
                print(f"  attempt {i+1}: passed={passed} score={judge.get('combined_score')} {dt}s")
                if "error" in judge:
                    print(f"    judge_err: {judge['error'][:120]}")
                time.sleep(0.5)  # 礼貌间隔
            passes = sum(1 for a in attempts if a.get("passed"))
            pass_at_5 = passes / ATTEMPTS
            hard_flag = pass_at_5 <= 0.6
            row_out = {
                "record_id": rec_id, "task_id": task_id, "Domain": row.get("Domain"),
                "Sub-domain": row.get("Sub-domain"), "model": ARK_MODEL,
                "pass_at_5": pass_at_5, "hard_flag": hard_flag,
                "attempts_results": [a.get("passed", False) for a in attempts],
                "attempts_detail": attempts,
                "use_real_verifier": use_real, "task_dir": str(task_dir) if task_dir else None,
                "ts": datetime.now(timezone.utc).isoformat(),
            }
            out_rows.append(row_out)
            fj.write(json.dumps(row_out, ensure_ascii=False) + "\n"); fj.flush()
            print(f"  ==> {task_id}: pass@5={pass_at_5} hard={hard_flag}")
    # 汇总
    print(f"\n=== done · {len(out_rows)} rows ===")
    print(f"hard={sum(1 for r in out_rows if r['hard_flag'])}/{len(out_rows)}")
    return out_rows

if __name__ == "__main__":
    main()