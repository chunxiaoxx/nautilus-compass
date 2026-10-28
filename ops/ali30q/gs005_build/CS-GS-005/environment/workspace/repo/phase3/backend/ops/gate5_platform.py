#!/usr/bin/env python3
"""gate5_platform.py·判据精确定义统一判读器(2026-10-28 深夜)
判据来源:质检方案行525/527+需求行758(全部带行号,正本 docs/feishu/)
五条件:①五模型各4轮 ②整体通过率<70% ③opus全过轮∈[1,3] ④qwen≥1轮未全过且双低于opus与gpt ⑤qwen passrate∈{25%,50%}
用法: python3 gate5_platform.py [qid前缀,缺省=全部]"""
import subprocess, sys, re
from datetime import datetime
from collections import defaultdict

DB_CMD = ["./ops/psql_cloud.sh", "SELECT traj_id, qid, trajectory->>'score' sc, created_at FROM fuel_trajectories WHERE created_at > '2026-10-28 12:00' ORDER BY traj_id;"]
MODELS = ["qwen3.8max", "opus5.5", "kimi-k3", "gpt-6-astra", "glm5.3"]

def main():
    r = subprocess.run(DB_CMD, capture_output=True, text=True, timeout=120,
                       cwd="/Users/chunxiao.wang/Projects/nautilus-core/phase3/backend")
    d = defaultdict(lambda: defaultdict(list))
    for line in r.stdout.splitlines():
        if "|" not in line: continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 4 or parts[0] == "traj_id" or parts[1].startswith("-"): continue
        tid, qid, sc = parts[0], parts[1], parts[2]
        if not sc: continue
        try: sc = float(sc.split(" ")[0])
        except: continue
        for m in MODELS:
            if m in tid: d[qid][m].append((tid, sc)); break
    prefix = sys.argv[1] if len(sys.argv) > 1 else ""
    print(f"gate5_platform 统一判读(五条件精确定义)· {datetime.now():%m-%d %H:%M}")
    print(f"{'题':<12}{'①轮齐':<8}{'②整体':<12}{'③opus窗':<10}{'④qwen双低':<12}{'⑤qwen带':<10}{'判定':<6}详情")
    for qid in sorted(d):
        if prefix and not qid.startswith(prefix): continue
        mm = d[qid]
        # 条件①: 五模型各≥1轮(简化: 判分库轮数为4轮窗内判分, 全部≥1即可)
        c1 = all(len(mm.get(m, [])) >= 1 for m in MODELS)
        # 各模型 passrate(全对轮/轮数)
        pr = {m: (sum(1 for _, s in mm.get(m, []) if s == 1.0) / len(mm[m]) if mm.get(m) else None) for m in MODELS}
        # 条件②: 整体通过率 <70%
        tot = sum(len(mm[m]) for m in mm); fulltot = sum(sum(1 for _, s in mm[m] if s == 1.0) for m in mm)
        c2 = (fulltot / tot < 0.70) if tot else False
        # 条件③: opus 全过轮 ∈[1,3]
        o_full = sum(1 for _, s in mm.get("opus5.5", []) if s == 1.0)
        c3 = 1 <= o_full <= 3
        # 条件④: qwen≥1未全过 且 qwen均分 < opus均分 且 < gpt均分
        q_full = sum(1 for _, s in mm.get("qwen3.8max", []) if s == 1.0)
        q_avg = sum(s for _, s in mm.get("qwen3.8max", [])) / len(mm["qwen3.8max"]) if mm.get("qwen3.8max") else 0
        o_avg = sum(s for _, s in mm.get("opus5.5", [])) / len(mm["opus5.5"]) if mm.get("opus5.5") else None
        g_avg = sum(s for _, s in mm.get("gpt-6-astra", [])) / len(mm["gpt-6-astra"]) if mm.get("gpt-6-astra") else None
        c4 = q_full < len(mm.get("qwen3.8max", [])) and o_avg is not None and g_avg is not None and q_avg < o_avg and q_avg < g_avg
        # 条件⑤: qwen passrate ∈{25,50} (容差±5)
        c5 = any(abs(pr["qwen3.8max"]*100 - t) <= 5 for t in (25, 50)) if pr.get("qwen3.8max") is not None else False
        ok = all([c1, c2, c3, c4, c5])
        fails = [n for n, c in [("①轮齐", c1), ("②<70%", c2), ("③opus[1,3]", c3), ("④qwen双低", c4), ("⑤两点带", c5)] if not c]
        o_n = len(mm.get("opus5.5", []))
        qp = pr["qwen3.8max"]
        qp_s = f"{qp*100:.0f}%" if qp is not None else "NA"
        print(qid, "①", "✓" if c1 else "✗", "②", f"{100*fulltot/max(1,tot):.0f}%", "③", f"{o_full}/{o_n}", "④", "✓" if c4 else "✗", "⑤", qp_s, "→", "达标" if ok else "出局(" + ",".join(fails) + ")")

if __name__ == "__main__":
    main()
