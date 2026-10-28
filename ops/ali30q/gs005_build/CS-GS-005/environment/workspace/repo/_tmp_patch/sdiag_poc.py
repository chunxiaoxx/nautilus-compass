#!/usr/bin/env python3
"""S-诊断 PoC runner(端到端·真 doubao 采样→bench_eval→三桶 triage)。
复用 ARK completer(源 nautilus-v5/fde_capsule/_run_bvh_2arm.py·内联避跨 repo 路径耦合)。
用法: python _tmp_patch/sdiag_poc.py --fuel _tmp_patch/sdiag_fuel --k 8
env: ARK_API_KEY(本地 .fde_api_secrets.env)
"""
import argparse, json, os, re, subprocess, sys, tempfile, time
import urllib.error, urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "phase3", "backend"))
from services.fde_triage import classify_task

ARK_BASE = "https://ark.cn-beijing.volces.com/api/plan/v3"


def load_ark_key():
    p = os.path.expanduser("~/.claude/.cache/.fde_api_secrets.env")
    if os.path.exists(p) and not os.environ.get("ARK_API_KEY"):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line.startswith("ARK_API_KEY="):
                os.environ["ARK_API_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")


def ark_complete(prompt, model="doubao-seed-2.0-pro", temp=1.0, max_tokens=4000, timeout=180, retries=4):
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                       "temperature": temp, "max_tokens": max_tokens}).encode("utf-8")
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(ARK_BASE + "/chat/completions", data=body, method="POST",
                headers={"Content-Type": "application/json",
                         "Authorization": "Bearer " + os.environ["ARK_API_KEY"]})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())["choices"][0]["message"]["content"]
        except (urllib.error.URLError, ConnectionError, TimeoutError, json.JSONDecodeError) as e:
            last = e
            code = getattr(e, "code", None)
            if code is not None and 400 <= code < 500 and code != 429:
                raise
            time.sleep(2 ** attempt * 2)
    raise RuntimeError("ark failed: %s" % last)


def extract_code(text):
    m = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    return m.group(1) if m else text


def run_one_sample(fuel_dir, prompt, idx):
    """采样一次 doubao → 写候选 → 跑 bench_eval → 返回 (passed, reason)。"""
    try:
        resp = ark_complete(prompt)
    except Exception as e:
        return False, "ark_error: %s" % e
    code = extract_code(resp)
    with tempfile.NamedTemporaryFile("w", suffix="_cand%d.py" % idx, delete=False, encoding="utf-8") as f:
        f.write(code); cand = f.name
    try:
        env = dict(os.environ, PYTHONUTF8="1")
        r = subprocess.run([sys.executable, os.path.join(fuel_dir, "bench_eval.py"), cand],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=60, env=env)
        out = r.stdout.strip()
        j = {}
        if out:
            # bench_eval 输出单个 pretty-print JSON · 取第一个 { 到最后一个 }
            s, e = out.find("{"), out.rfind("}")
            if s >= 0 and e > s:
                try:
                    j = json.loads(out[s:e + 1])
                except Exception:
                    j = {}
        return bool(j.get("passed")), (j.get("reason") or ("n_pass=%s/%s" % (j.get("n_pass"), j.get("n_total"))) or r.stderr[-120:])
    except subprocess.TimeoutExpired:
        return False, "bench_eval timeout"
    finally:
        try: os.unlink(cand)
        except OSError: pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fuel", required=True)
    ap.add_argument("--k", type=int, default=8)
    a = ap.parse_args()
    load_ark_key()

    spec = open(os.path.join(a.fuel, "task_spec.md"), encoding="utf-8").read()
    buggy_files = [f for f in os.listdir(a.fuel) if f.startswith("buggy_")]
    buggy = open(os.path.join(a.fuel, buggy_files[0]), encoding="utf-8").read()
    task_uid = os.path.basename(os.path.abspath(a.fuel))

    prompt = ("你是资深工程师。下面是一道基准修复题和有 bug 的起点代码。请输出**完整修复后的代码**"
              "(单个 ```python 代码块),只改逻辑修复 bug,保持 stdin/stdout 契约不变。\n\n"
              "## 题目\n%s\n\n## 起点(buggy)\n```python\n%s\n```\n\n只输出修复后的完整代码。" % (spec, buggy))

    print("[sdiag] task=%s k=%d model=doubao-seed-2.0-pro temp=1.0" % (task_uid, a.k), flush=True)
    n_passed = 0
    for i in range(a.k):
        passed, reason = run_one_sample(a.fuel, prompt, i)
        n_passed += int(passed)
        print("  sample %d/%d: %s | %s" % (i + 1, a.k, "PASS" if passed else "FAIL", str(reason)[:80]), flush=True)

    diag = {"task_uid": task_uid, "n_samples": a.k, "n_passed": n_passed, "n_correct_but_gated": 0}
    r = classify_task(diag)
    print("\n=== S-诊断结果 ===")
    print("pass@%d: %d/%d (pass_rate=%.3f)" % (a.k, n_passed, a.k, r["pass_rate"]))
    print("桶: %s · 蒸馏候选=%s · %s" % (r["bucket"], r["distill_candidate"], r["reason"]))


if __name__ == "__main__":
    main()
