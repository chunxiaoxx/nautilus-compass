#!/usr/bin/env python3
"""
bench_eval.py — D1 可复现评测 harness(确定性·纯 stdlib·跨平台)

用法: PYTHONUTF8=1 python bench_eval.py <candidate.py>

场景: 把"带版本的记录"按 uid 合并/去重,对每个 uid 取**最新版本**(version 最大)的 payload。
候选作为子进程,从 stdin 收一组固定记录行 "uid|version|payload",须对每个 uid 输出一行
"uid|payload"(payload 取该 uid version 最大那条),按 uid 字典序排序。

固定输入故意让多个 uid 的**最高版本不在迭代末尾**(乱序到达),buggy 的
"last-in-iteration-wins" 会被后到的低版本遮蔽 → 取错版本。

门:
  G1 格式: 每个 uid 恰一行;输出 uid 集合 == 输入 uid 集合;行按 uid 字典序;每行形如 "uid|payload"。
  G2 正确性: 每个 uid 的 payload == 该 uid version 最大那条的 payload
            (ground truth 现场 group-by uid + max(version) 算·记答案无用·可换数据集)。
  G3 非作弊: 不得原样回写全部输入行(输出行数须 == 唯一 uid 数·远少于输入行数);不得漏 uid。
全部用例通过 = pass。任一 uid 取错版本 = fail(buggy 起点应在此判错)。
输出 JSON: {cases:[...], passed:bool, n_pass, n_total, reason}
"""
import sys
import json
import subprocess

# 固定记录(uid, version, payload)。故意打乱到达顺序:
#   A: v3 先到、v5 中间、v1 最后  → 正确取 v5;buggy(last-wins)取 v1(暴露点)
#   B: v2 先、v7 最后             → 正确取 v7;buggy 也取 v7(碰巧对·非暴露点对照)
#   C: v9 先、v9... 只一条相邻? 用 C 作"高版本在中间"再暴露:v4、v8、v2 → 正确 v8,buggy v2(暴露点)
#   D: 单版本 uid 对照(只 v1)     → 正确取 v1;buggy 也取 v1(单版本对照)
#   E: 相邻版本边界 v1、v2(v2 先到、v1 后到)→ 正确 v2,buggy 取 v1(相邻边界暴露点)
RECORDS = [
    ("A", 3, "a-draft-v3"),
    ("B", 2, "b-old-v2"),
    ("C", 4, "c-v4"),
    ("E", 2, "e-final-v2"),     # E 的最高版本 v2 先到(不在末尾)
    ("A", 5, "a-FINAL-v5"),     # A 最高版本 v5 在中间(不在末尾)→ buggy 漏
    ("C", 8, "c-FINAL-v8"),     # C 最高版本 v8 在中间(不在末尾)→ buggy 漏
    ("D", 1, "d-only-v1"),      # 单版本对照
    ("E", 1, "e-stale-v1"),     # E 旧版 v1 后到 → buggy 取它(相邻边界暴露)
    ("B", 7, "b-FINAL-v7"),     # B 最高版本 v7 在末尾 → buggy 碰巧对(对照)
    ("C", 2, "c-stale-v2"),     # C 旧版 v2 后到 → buggy 取它(暴露)
    ("A", 1, "a-stale-v1"),     # A 旧版 v1 最后到 → buggy 取它(暴露)
]


def build_input(records):
    lines = [f"{uid}|{ver}|{payload}" for uid, ver, payload in records]
    return ("\n".join(lines) + "\n").encode("utf-8")


def ground_truth(records):
    # 现场 group-by uid + max(version)。记答案无用·换数据集仍正确。
    best = {}
    for uid, ver, payload in records:
        if uid not in best or ver > best[uid][0]:
            best[uid] = (ver, payload)
    return {uid: pl for uid, (ver, pl) in best.items()}


def run_candidate(cand_path, stdin_bytes):
    p = subprocess.run([sys.executable, cand_path], input=stdin_bytes,
                       capture_output=True, timeout=60)
    return p.returncode, p.stdout, p.stderr


def main():
    cand = sys.argv[1]
    stdin_bytes = build_input(RECORDS)
    rc, out, err = run_candidate(cand, stdin_bytes)
    gt = ground_truth(RECORDS)
    uids = sorted(gt)
    result = {"candidate": cand, "cases": [], "n_total": len(uids)}

    if rc != 0:
        result.update(passed=False, n_pass=0,
                      reason=f"G1 崩溃 returncode={rc}; stderr_tail={err.decode('utf-8','replace')[-300:]}")
        print(json.dumps(result, ensure_ascii=False, indent=1)); sys.exit(0)

    out_lines = [ln for ln in out.decode("utf-8", "replace").splitlines() if ln.strip()]

    # G3 非作弊:输出行数须 == 唯一 uid 数(远少于输入行数);否则疑似原样回写全部输入。
    if len(out_lines) == len(RECORDS):
        result.update(passed=False, n_pass=0,
                      reason=f"G3 疑似原样回写全部输入(输出 {len(out_lines)} 行 == 输入 {len(RECORDS)} 行,未去重)")
        print(json.dumps(result, ensure_ascii=False, indent=1)); sys.exit(0)

    # 解析输出为 uid->payload。每行须恰一个 '|',形如 uid|payload。
    parsed = {}
    fmt_ok = True
    for ln in out_lines:
        if ln.count("|") < 1:
            fmt_ok = False
            break
        uid, payload = ln.split("|", 1)
        parsed[uid] = payload

    # G1 格式:uid 集合一致 + 一 uid 一行 + 字典序
    out_uid_order = [ln.split("|", 1)[0] for ln in out_lines] if fmt_ok else []
    set_ok = (set(parsed) == set(gt)) and (len(out_lines) == len(gt))
    sorted_ok = (out_uid_order == sorted(out_uid_order))

    n_pass = 0
    for uid in uids:
        expect = gt[uid]
        got = parsed.get(uid)
        ok = (got == expect)
        if ok:
            n_pass += 1
        result["cases"].append({"uid": uid, "expect": expect, "got": got, "ok": ok})

    passed = fmt_ok and set_ok and sorted_ok and (n_pass == len(uids))
    if passed:
        reason = "pass"
    elif not fmt_ok:
        reason = "G1 格式错(行不含分隔符·非 uid|payload)"
    elif not set_ok:
        reason = f"G1 uid 集合不符(漏/多 uid)·得 {sorted(parsed)} 期 {uids}"
    elif not sorted_ok:
        reason = f"G1 未按 uid 字典序输出·得 {out_uid_order}"
    else:
        reason = f"G2 取错版本 {n_pass}/{len(uids)}(用了 last-in-iteration-wins? 须 group-by uid 显式 max(version))"
    result.update(passed=passed, n_pass=n_pass, reason=reason)
    print(json.dumps(result, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
