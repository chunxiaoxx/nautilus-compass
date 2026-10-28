"""跨对话框看板 · pull 聚合(创新机制 · 替 push 副本同步)。

根因(7/6 grounded):"SSOT canonical + 副本手动同步各 repo 根"已失效 —
V5 副本停 7/4、compass 7/6 才追一次,各框拿过期框架 = 精神分裂 + qixuw 3 天重复排查。

创新:弃 push(各框互相同步副本),改 pull(platform 定期聚合各框自己 repo 的
LOOP_STATE + git log)。各框只维护自己那份 LOOP_STATE,platform 拉取生成一份
活的 CROSS_DIALOG_BOARD.md。各框 session-start 读这份看板(不再指望副本同步)。

用法:
    python tools/cross_dialog_board.py            # 生成 CROSS_DIALOG_BOARD.md
    python tools/cross_dialog_board.py --days 7   # 只看最近 7 天 commit
"""

import argparse
import os
import subprocess
import sys

# 各对话框 repo(from reference_dialog_repos_locations_20260706)
DIALOGS = [
    {"name": "platform-soul", "repo": r"C:\Users\chunx\Projects\nautilus-core",
     "turf": "OR 域(JobShop/TSP/BinPack)+ 平台 infra + verdict 持久化 + dispatch"},
    {"name": "agent(V5)", "repo": r"C:\Users\chunx\Projects\nautilus-v5",
     "turf": "GenOpt 出题主体(#2-#10 模板)+ 外环飞轮 + RSI producer"},
    {"name": "compass", "repo": r"C:\Users\chunx\Projects\nautilus-compass",
     "turf": "KernelEng(matmul/conv2d/rmsnorm)+ ComputerSys + env/verify + feishu 读写"},
    {"name": "FDE", "repo": r"C:\Users\chunx\Projects\_nautilus_fde_inspect",
     "turf": "生产管理底座(飞书多维表格 base + 5 角色 + 招募)", "github": True},
]


def git(repo, *args):
    try:
        r = subprocess.run(["git", "-C", repo, *args], capture_output=True,
                           text=True, timeout=30, encoding="utf-8", errors="replace")
        return r.stdout.strip()
    except Exception as e:
        return f"[git err: {e}]"


def loop_state_target(repo):
    """从各框 LOOP_STATE.md 抓「当前闭环目标」行。"""
    for fn in ("LOOP_STATE_SSOT.md", "LOOP_STATE.md"):
        path = os.path.join(repo, fn)
        if os.path.isfile(path):
            try:
                with open(path, encoding="utf-8", errors="replace") as f:
                    for line in f:
                        if "当前闭环目标" in line:
                            # 取表格 | 当前闭环目标 | XXX | 的 XXX
                            parts = line.split("|")
                            if len(parts) >= 3:
                                return parts[2].strip()[:180]
            except Exception:
                pass
    return "(无 LOOP_STATE 或未找到目标行)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--out", default=r"C:\Users\chunx\Projects\nautilus-core\CROSS_DIALOG_BOARD.md")
    ap.add_argument("--fetch", action="store_true", help="FDE github repo 先 fetch")
    args = ap.parse_args()

    since = f"{args.days}.days.ago"
    lines = [
        "# 🧭 跨对话框看板(pull 聚合 · 非副本同步)",
        "",
        f"> platform 拉取各框自己 repo 的 LOOP_STATE + git log 生成 · 各框 session-start 读这份 · 弃 push 副本(已证失效)",
        f"> 生成方式:`python tools/cross_dialog_board.py --days {args.days}` · 各框只维护自己 LOOP_STATE",
        "",
        "## 各框状态(grounded · 各自 repo)",
        "",
        "| 框 | 近 %dd commit | 最近 commit | 当前闭环目标(自己 LOOP_STATE) |" % args.days,
        "|---|---|---|---|",
    ]

    for d in DIALOGS:
        repo = d["repo"]
        if not os.path.isdir(repo):
            lines.append(f"| {d['name']} | (repo 不存在) | - | - |")
            continue
        if d.get("github") and args.fetch:
            git(repo, "fetch", "origin")
        ref = "origin/main" if d.get("github") else "HEAD"
        n = git(repo, "log", ref, "--oneline", f"--since={since}")
        n_count = len([x for x in n.splitlines() if x.strip()]) if not n.startswith("[git") else "?"
        last = git(repo, "log", ref, "-1", "--format=%ad %s", "--date=format:%m-%d %H:%M")
        target = loop_state_target(repo)
        lines.append(f"| **{d['name']}** | {n_count} | {last[:60]} | {target} |")

    lines += ["", "## 域/算子分工(grounded 算子不撞 · turf)", ""]
    for d in DIALOGS:
        lines.append(f"- **{d['name']}**:{d['turf']}")

    lines += [
        "",
        "## 各框近期 commit(近 %dd · 各自 repo)" % args.days,
        "",
    ]
    for d in DIALOGS:
        repo = d["repo"]
        if not os.path.isdir(repo):
            continue
        ref = "origin/main" if d.get("github") else "HEAD"
        log = git(repo, "log", ref, "--oneline", f"--since={since}")
        rows = [x for x in log.splitlines() if x.strip()][:8]
        lines.append(f"### {d['name']}")
        if rows:
            lines += [f"- {r}" for r in rows]
        else:
            lines.append("- (近期无 commit)")
        lines.append("")

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[ok] 看板生成: {args.out}")
    print(f"     {len(DIALOGS)} 框 · 近 {args.days}d")


if __name__ == "__main__":
    sys.exit(main())
