#!/usr/bin/env python3
"""Path B(节点4)— SWE-bench correctness-binary 2-turn RSI 环(platform-soul·2026-06-19）。

KernelBench speedup-RSI 证负(p13 ceiling / p18 single-trick·都无梯度）后的 redirect。
SWE 任务天然有梯度:turn-1 patch 过 X 测试 + 留失败 traceback → 记忆喂这些报错 →
turn-2 针对性修 → 过 Y。**Y>X = RSI 机制首证(离散·无计时噪声·不需噪声门）。**

设定 = oracle-file(SWE-bench 标准设定之一·隔离 RSI 机制 vs 检索噪声):
  给模型 gold patch 触及的**非测试源文件全文** + issue → 模型返回修改后全文 →
  difflib 构 unified diff(保证 git apply 成功）→ swe_runner.run_candidate 跑 F2P 测试。

复用:services.fde_sdiagnose_run.bailian_complete(producer）· services.swe_runner
（apply+pytest）· services.swe_verify(parse/reward/记忆/Y>X）。不重复造。

用法(background·别前台 poll）:
  python scripts/rsi_swe_loop.py sympy__sympy-24102 --model deepseek-v4-pro \
      --out /c/Users/chunx/.cache/swe_bench/rsi_24102.json
前提:先跑 scripts/swe_prep_instance.py <id>(建 base_dir + venv）。
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.fde_sdiagnose_run import bailian_complete, load_secrets  # noqa: E402
from services.swe_runner import run_candidate, run_pytest  # noqa: E402
from services.swe_verify import (  # noqa: E402
    build_swe_memory, extract_failed_tests, extract_failures_section,
    parse_pytest_summary, rsi_improved, swe_reward,
)

CACHE = os.path.join(os.path.expanduser("~"), ".cache", "swe_bench")

_BLOCK = re.compile(r"```(?:python|diff|py)?\s*\n(.*?)```", re.DOTALL)
_FILE_MARK = re.compile(r"^#\s*FILE:\s*(\S+)\s*\n", re.IGNORECASE)


# ───────────────────────── 纯逻辑(TDD: test_swe_patch_build.py）─────────────────────────

def parse_file_blocks(resp: str) -> dict:
    """模型输出 → {path: full_content}。只认带 `# FILE: <path>` 首行标记的代码块。"""
    out = {}
    for m in _BLOCK.finditer(resp):
        body = m.group(1)
        fm = _FILE_MARK.match(body)
        if not fm:
            continue
        path = fm.group(1).strip()
        content = body[fm.end():]
        if not content.endswith("\n"):
            content += "\n"
        out[path] = content
    return out


def coerce_blocks(resp: str, allowed_files: list, originals: dict) -> dict:
    """稳健提取模型给的"新文件内容"。

    ① 优先 `# FILE:` 标记块(parse_file_blocks）。② 无标记但只有 1 个允许文件时:
    取最大代码块·仅当它 ≥ 40% 原文长度(像全文而非片段）才采纳(防把片段当全文删光余码）。
    多文件无标记 → {} (无法判归属·不冒险）。
    """
    marked = {k: v for k, v in parse_file_blocks(resp).items() if k in set(allowed_files)}
    if marked:
        return marked
    if len(allowed_files) != 1:
        return {}
    only = allowed_files[0]
    orig_len = len(originals.get(only, ""))
    blocks = [m.group(1) for m in _BLOCK.finditer(resp)]
    if not blocks:
        return {}
    cand = max(blocks, key=len)
    if not cand.endswith("\n"):
        cand += "\n"
    if orig_len and len(cand) >= 0.4 * orig_len:
        return {only: cand}
    return {}


_SR_BLOCK = re.compile(
    r"<{5,}\s*SEARCH\s*\n(.*?)\n?={5,}\s*\n(.*?)\n?>{5,}\s*REPLACE", re.DOTALL)


def parse_search_replace(resp: str) -> list:
    """模型的 SEARCH/REPLACE 块 → [(search, replace)]。

    Aider/SWE-agent 标准编辑格式·紧凑(不重生成全文·避截断/空响应）:
        <<<<<<< SEARCH
        <既有精确行>
        =======
        <替换行>
        >>>>>>> REPLACE
    """
    out = []
    for m in _SR_BLOCK.finditer(resp):
        search = m.group(1)
        replace = m.group(2)
        if search and not search.endswith("\n"):
            search += "\n"
        if replace and not replace.endswith("\n"):
            replace += "\n"
        out.append((search, replace))
    return out


def _fuzzy_line_replace(text: str, search: str, replace: str):
    """空白容错回退:按行 strip 后匹配 search 行块·命中唯一才替(防歧义误替）。

    模型常给缩进/尾空白略不同的 SEARCH(实测 deepseek 在 point.py 0 applied 根因）。
    返回 (new_text, ok)。匹配多处=歧义→不替(ok=False）。
    """
    s_lines = [ln.strip() for ln in search.splitlines() if ln.strip() != ""]
    if not s_lines:
        return text, False
    t_lines = text.splitlines(keepends=True)
    t_stripped = [ln.strip() for ln in t_lines]
    hits = []
    n = len(s_lines)
    for i in range(len(t_lines) - n + 1):
        window = [t_stripped[i + j] for j in range(n)]
        if window == s_lines:
            hits.append(i)
    if len(hits) != 1:
        return text, False  # 0 或多处→不冒险
    i = hits[0]
    # 用文件第一命中行的前导空白做 replace 的基准缩进
    indent = t_lines[i][:len(t_lines[i]) - len(t_lines[i].lstrip())]
    repl_lines = []
    for ln in replace.splitlines():
        repl_lines.append((indent + ln.strip() + "\n") if ln.strip() else "\n")
    new = "".join(t_lines[:i]) + "".join(repl_lines) + "".join(t_lines[i + n:])
    return new, True


def apply_edits(original: str, edits: list) -> tuple:
    """对 original 顺序应用 (search, replace) 替换。回 (new, applied, failed)。

    ① 精确匹配(只替首次）。② 精确找不到 → 空白容错行级回退(唯一命中才替）。
    都不中=failed(不强改）。空 search 跳过(不当全文插入）。
    """
    text = original
    applied = failed = 0
    for search, replace in edits:
        if not search:
            continue
        idx = text.find(search)
        if idx >= 0:
            text = text[:idx] + replace + text[idx + len(search):]
            applied += 1
            continue
        new, ok = _fuzzy_line_replace(text, search, replace)
        if ok:
            text = new
            applied += 1
        else:
            failed += 1
    return text, applied, failed


def build_unified_diff(base_dir: str, new_files: dict) -> str:
    """base_dir 现有文件 vs 模型给的新内容 → git-apply 兼容 unified diff。无变化跳过。"""
    parts = []
    for rel, new_content in new_files.items():
        fp = os.path.join(base_dir, rel.replace("/", os.sep))
        old = ""
        if os.path.exists(fp):
            with open(fp, encoding="utf-8") as f:
                old = f.read()
        if old == new_content:
            continue
        diff = difflib.unified_diff(
            old.splitlines(keepends=True), new_content.splitlines(keepends=True),
            fromfile="a/" + rel, tofile="b/" + rel)
        parts.append("".join(diff))
    return "".join(parts)


# ───────────────────────── 集成 ─────────────────────────

def _load_instance(instance_id):
    from datasets import load_dataset
    ds = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
    for r in ds:
        if r["instance_id"] == instance_id:
            return r
    raise SystemExit("instance not found: %s" % instance_id)


def _source_files_from_gold(patch: str) -> list[str]:
    """gold patch 触及的非测试文件(oracle 上下文·只给源文件不给测试）。"""
    files = []
    for m in re.finditer(r"^\+\+\+ b/(\S+)", patch, re.MULTILINE):
        p = m.group(1)
        low = p.lower()
        if "/test" in low or low.startswith("test") or "/tests/" in low:
            continue
        files.append(p)
    return files


def _build_prompt(problem, src_files, base_dir, memory=""):
    blocks = []
    for rel in src_files:
        fp = os.path.join(base_dir, rel.replace("/", os.sep))
        with open(fp, encoding="utf-8") as f:
            blocks.append("### File: %s\n```python\n%s\n```" % (rel, f.read()))
    files_to_edit = "\n".join("- " + f for f in src_files)
    return (
        "You are fixing a bug in a Python library. Below is the issue and the FULL current "
        "content of the source file(s) you may edit.\n\n"
        "## Issue\n%s\n\n"
        "## Source file(s) you may edit\n%s\n\n"
        "## Your task\n"
        "Fix the issue by emitting MINIMAL edits in SEARCH/REPLACE format. For each change, output "
        "a block EXACTLY like this (the SEARCH text must match the existing file verbatim, "
        "including indentation):\n"
        "<<<<<<< SEARCH\n<exact lines currently in the file>\n=======\n<your replacement lines>\n"
        ">>>>>>> REPLACE\n\n"
        "Rules:\n- Only edit these files: %s\n- Emit as many SEARCH/REPLACE blocks as needed.\n"
        "- Keep SEARCH blocks small and unique. Do NOT reproduce the whole file.\n"
        "- Output ONLY SEARCH/REPLACE blocks, no prose.%s"
        % (problem, "\n\n".join(blocks), files_to_edit, memory))


def _attempt(prompt, src_files, base_dir, venv_py, test_target, model, tag):
    """produce → 构 diff → run_candidate → parse。回 (summary, fails, diff, raw_out)。"""
    resp = ""
    for _try in range(2):  # 空响应重试一次(实测 deepseek 偶发空·别浪费 k）
        try:
            resp = bailian_complete(prompt, model=model)
        except Exception as ex:  # noqa: BLE001
            print("  [%s] produce_error %s" % (tag, str(ex)[:120]), flush=True)
            return None, [], "", "produce_error: %s" % ex
        if resp and resp.strip():
            break
        print("  [%s] empty resp, retry %d" % (tag, _try + 1), flush=True)
    originals = {}
    for rel in src_files:
        fp = os.path.join(base_dir, rel.replace("/", os.sep))
        if os.path.exists(fp):
            with open(fp, encoding="utf-8") as f:
                originals[rel] = f.read()
    edits = parse_search_replace(resp)
    if not edits:
        print("  [%s] no SEARCH/REPLACE block parsed (resp head: %r)" % (tag, resp[:120]), flush=True)
        return None, [], "", "no_edits\n" + resp[:500]
    # 按内容路由:每个 edit 落到 search 命中的文件(apply_edits 自动跳过不匹配的）
    new_files, total_applied = {}, 0
    for rel, orig in originals.items():
        new_text, applied, _ = apply_edits(orig, edits)
        total_applied += applied
        if applied > 0:
            new_files[rel] = new_text
    if not new_files:
        print("  [%s] %d edits parsed but 0 applied (SEARCH not found in files)" % (tag, len(edits)), flush=True)
        return None, [], "", "edits_unmatched (%d parsed)" % len(edits)
    diff = build_unified_diff(base_dir, new_files)
    if not diff.strip():
        print("  [%s] empty diff" % tag, flush=True)
        return None, [], "", "empty_diff"
    print("  [%s] %d edits, %d applied → diff %dB" % (tag, len(edits), total_applied, len(diff)), flush=True)
    out = run_candidate(base_dir, diff, test_target, python_exe=venv_py,
                        env_extra={"PYTHONPATH": ""})
    summ = parse_pytest_summary(out)
    fails = extract_failed_tests(out)
    print("  [%s] passed=%s failed=%s errored=%s parsed=%s | reward=%s"
          % (tag, summ["passed"], summ["failed"], summ["errored"], summ["parsed"],
             swe_reward(summ)), flush=True)
    return summ, fails, diff, out


def _best_of_k(prompt, src_files, base_dir, venv_py, test_target, model, tag, k):
    """k 个候选取 reward 最大(降单样本噪声·匹配 p13 best-of-k）。回 best=(s,fails,diff,out,reward)。"""
    best = None
    rewards = []
    for i in range(k):
        s, fails, diff, out = _attempt(prompt, src_files, base_dir, venv_py, test_target,
                                       model, "%s.%d" % (tag, i + 1))
        r = swe_reward(s) if s else None
        rewards.append(r)
        rv = r if r is not None else -1
        if best is None or rv > best[4]:
            best = (s, fails, diff, out, rv)
    print("  [%s] rewards across k=%d: %s → best=%s" % (tag, k, rewards, best[4] if best else None),
          flush=True)
    return best, rewards


def run(instance_id, model, out_path, k=1):
    load_secrets()
    base_dir = os.path.join(CACHE, "instances", instance_id)
    if not os.path.isdir(base_dir):
        raise SystemExit("base_dir missing — run swe_prep_instance.py %s first" % instance_id)

    inst = _load_instance(instance_id)
    problem = inst["problem_statement"]
    f2p = json.loads(inst["FAIL_TO_PASS"]) if isinstance(inst["FAIL_TO_PASS"], str) else inst["FAIL_TO_PASS"]
    src_files = _source_files_from_gold(inst["patch"])
    venv_py = os.path.join(CACHE, "venvs",
                           "%s__%s" % (inst["repo"].replace("/", "__"), inst.get("version", "na")),
                           "Scripts", "python.exe")
    if not os.path.exists(venv_py):
        venv_py = venv_py.replace(os.sep + "Scripts" + os.sep + "python.exe", os.sep + "bin" + os.sep + "python")

    # test_target = F2P node ids(从 prep 同逻辑重建·只取真测试文件）
    def _is_test_file(p):
        low = p.lower(); base = low.rsplit("/", 1)[-1]
        return ("/tests/" in low or "/test/" in low or base.startswith("test_")
                or base.endswith("_test.py"))
    tfiles = [m.group(1) for m in re.finditer(r"^\+\+\+ b/(\S+)", inst["test_patch"], re.MULTILINE)
              if _is_test_file(m.group(1))]
    if len(tfiles) == 1:
        test_target = ["%s::%s" % (tfiles[0], n) if "::" not in n and "/" not in n else n for n in f2p]
    else:
        test_target = f2p

    print("[swe-rsi] %s model=%s src_files=%s n_f2p=%d k=%d" % (instance_id, model, src_files, len(f2p), k), flush=True)

    # ── TURN 1: 无记忆(best-of-k）──
    print("\n=== TURN 1 (no memory, k=%d) ===" % k, flush=True)
    p1 = _build_prompt(problem, src_files, base_dir)
    b1, rew1 = _best_of_k(p1, src_files, base_dir, venv_py, test_target, model, "t1", k)
    s1, fails1, diff1, out1 = b1[0], b1[1], b1[2], b1[3]
    x = swe_reward(s1) if s1 else None
    print("[swe-rsi] turn-1 reward (best passed) = %s" % x, flush=True)

    # ── 抽记忆(从 turn-1 best）+ TURN 2(best-of-k）──
    y, diff2, out2, memory, s2, rew2 = None, "", "", None, None, []
    if s1 is None or x is None:
        print("[swe-rsi] turn-1 no parseable result — abort RSI (no grounded memory).", flush=True)
    else:
        memory = build_swe_memory(diff1, s1, fails1,
                                  traceback_text=extract_failures_section(out1 or ""))
        print("\n=== TURN 2 (memory injected, k=%d) ===" % k, flush=True)
        p2 = _build_prompt(problem, src_files, base_dir, memory="\n" + memory)
        b2, rew2 = _best_of_k(p2, src_files, base_dir, venv_py, test_target, model, "t2", k)
        s2, diff2, out2 = b2[0], b2[2], b2[3]
        y = swe_reward(s2) if s2 else None
        print("[swe-rsi] turn-2 reward (best passed) = %s" % y, flush=True)

    proven = rsi_improved(x, y)
    report = {
        "instance_id": instance_id, "model": model, "n_f2p": len(f2p), "k": k,
        "test_target": test_target, "src_files": src_files,
        "turn1_passed": x, "turn2_passed": y,
        "turn1_rewards_k": rew1, "turn2_rewards_k": rew2,
        "rsi_proven": proven,  # 离散 Y>X·无噪声门
        "turn1_summary": s1, "turn2_summary": (s2 if (s1 and x is not None) else None),
        "memory_injected": memory is not None,
        "turn1_diff": diff1, "turn2_diff": diff2,
        "turn1_out_tail": (out1 or "")[-1500:], "turn2_out_tail": (out2 or "")[-1500:],
    }
    print("\n========== SWE-RSI %s 结果 ==========" % instance_id, flush=True)
    print("turn-1 passed = %s · turn-2 passed = %s · rsi_proven(Y>X) = %s" % (x, y, proven), flush=True)
    if out_path:
        json.dump(report, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print("[swe-rsi] 写 %s" % out_path, flush=True)
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("instance_id")
    ap.add_argument("--model", default="deepseek-v4-pro")
    ap.add_argument("--out", default=None)
    ap.add_argument("--k", type=int, default=1, help="每 turn best-of-k 候选(降单样本噪声）")
    a = ap.parse_args()
    run(a.instance_id, a.model, a.out, k=a.k)


if __name__ == "__main__":
    main()
