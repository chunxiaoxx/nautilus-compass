# -*- coding: utf-8 -*-
"""投入分布证据级对账:git log 全量 commit 按六线(+G)分类。
只读;输出 月×线矩阵 + B线完整清单 + 未归类清单。口径见脚本内规则表。"""
import subprocess, json, re
from collections import Counter, defaultdict

out = subprocess.run(
    ["git", "log", "--since=2026-07-14", "--date=short", "--format=%h|%ad|%s"],
    capture_output=True)
lines = out.stdout.decode("utf-8", errors="replace").splitlines()
commits = []
for ln in lines:
    p = ln.split("|", 2)
    if len(p) == 3:
        commits.append({"h": p[0], "d": p[1], "s": p[2]})

# 规则:有序,先命中先归线。顺序即优先级(B 最具体故最前)。
RULES = [
    ("B", ["org_fuel", "ORG-FUEL", "fuel", "语料", "corpus", "棘轮", "selflabel",
           "relabel", "strongmodel", "sevenb", "8B", "1.7B", "7B", "SFT", "LoRA",
           "lora", "自举", "真人卷", "quiz", "盲评", "重训", "NACRE", "letters",
           "函件判例", "registry.html", "65%"]),
    ("A", ["判读", "判例", "CASEBOOK", "复算", "背书", "gaurav", "考场", "发卡",
           "l1-0", "l2-0", "判分", "判官", "pilot", "judge", "考点", "题",
           "Kairos", "RTV", "冲正", "裁定", "复读", "总账", "对账", "审计",
           "audit", "intake", "开业", "launch", "unipat", "L2管线", "样例",
           "V2首单", "代演", "计量", "Infistar", "wall", "周考", "AGREE",
           "验签", "VB", "DCR", "commercial", "支付"]),
    ("F", ["rsi-bench", "assay", "VerifyPack", "jev", "LME", "基准", "replay",
           "PyPI", "pypi", "跑分", "评测", "PRECOR", "paper", "论文", "对拍",
           "Conan", "出榜", "E1", "embedder", "Embedder", "bge", "4B", "榜",
           "scaling", "RFC", "research", "调研", "mem0", "Jev", "TypeSafe",
           "typesafe", "cohort", "f15", "F15", "DIM3", "deepsync", "基线",
           "N2", "NautilusMem", "GEP", "成绩"]),
    ("D", ["outreach", "awesome", "dev.to", "HN", "genesis", "创世", "知乎",
           "discord", "邮件", "gmail", "PR#", "推广", "外联", "README",
           "bc1", "BC1", "portal", "发布", "essay", "G4", "Report3", "report3",
           "marketing", "话术", "aiworks", "提报", "Runbook", "demo", "skills",
           "glama", "物料"]),
    ("E", ["函", "platform", "openclaw", "flywheel", "迁移", "NAS", "bootstrap",
           "governance", "thread", "touch", "信箱", "开轮", "organization",
           "org/", "workbuddy", "XERJ", "CLA", "Mac", "SSH", "隧道", "tunnel",
           "内网穿透", "白名单", "ack", "cloud", "v5", "sync", "对齐", "互评",
           "ssot", "inbound", "广播"]),
    ("C", ["daemon", "HUD", "deploy", "部署", "nginx", "GPU", "M5", "memgate",
           "节流", "磁盘", "网关", "venv", "探针", "watcher", "9876", "性能",
           "MCP", "mcp", "内存", "perf", "memx", "fact_status", "queue",
           "终检", "final_check", "lint", "ruff", "ci:", "嵌入缓存", "S6",
           "GUARD", "镜像", "垫跑", "归档", "check_env", "training", "hf",
           "security", "凭据", "feishu", "S1", "S3", "probe", "执法器",
           "ledger", "端口", "夜巡", "值守", "watchdog", "landing", "test"]),
    ("G", ["勘误", "errata", "复盘", "retro", "soul", "章程", "charter", "决策",
           "周综合", "教训", "拍板", "anchor", "主log", "log", "周报", "总结",
           "战略", "strategy", "路线图", "总纲", "ORG_LOOP", "HANDOFF",
           "handoff", "死线", "记账", "状态锚", "roadmap", "度量衡"]),
]
FALLBACK = re.compile(r"R\d{3}")
FALLBACK = re.compile(r"R\d{3}")

def classify(subj):
    for line, kws in RULES:
        for kw in kws:
            if kw in subj:
                return line, kw
    if FALLBACK.search(subj):
        return "G", "R###"
    return "U", ""

# B 线子分类:用户核心问题="无效自举线吃了多少精力",须与有效燃料分开
B1_SELFBOOT = ["org_fuel", "ORG-FUEL", "fuel_gen", "harvest", "棘轮", "selflabel",
               "relabel", "strongmodel", "盲评", "merged", "入池", "扩容", "过门",
               "grain", "飞轮源", "quiz", "真人卷", "gate_passed", "flywheel源",
               "R536", "四源", "第三源", "第四源", "跨框语料", "语料2", "语料3"]
B2_VALID = ["exporter", "split", "LME", "labelled", "rejudge", "北极星", "LoRA",
            "重训机制", "判分API", "训练脚本", "判官升级", "P2v2", "p2v2"]

def b_sub(subj):
    if any(k in subj for k in B2_VALID) and not any(
            k in subj for k in ["org_fuel", "ORG-FUEL", "棘轮", "盲评", "merged",
                                "入池", "语料2"]):
        return "B2"
    if any(k in subj for k in B1_SELFBOOT):
        return "B1"
    return "B3"

month_line = defaultdict(Counter)
b_list, u_list = [], []
kw_hit = defaultdict(Counter)  # line -> keyword -> count (供存疑审计)
for c in commits:
    line, kw = classify(c["s"])
    month = c["d"][:7]
    month_line[month][line] += 1
    kw_hit[line][kw] += 1
    if line == "B":
        b_list.append(f'{c["h"]}|{c["d"]}|{b_sub(c["s"])}|{c["s"]}')
    if line == "U":
        u_list.append(f'{c["h"]}|{c["d"]}|{c["s"]}')

months = sorted(month_line)
all_lines = ["A", "B", "C", "D", "E", "F", "G", "U"]

rep = []
rep.append("# 投入分布对账 · git 全量 commit 六线分类(脚本 _effort_account.py)\n")
rep.append(f"- 窗口: 2026-07-14 起 · 总 commit = {len(commits)}\n")
rep.append("## 月×线矩阵\n")
hdr = "| 月 | " + " | ".join(all_lines) + " | 合计 |"
rep.append(hdr)
rep.append("|" + "---|" * (len(all_lines) + 2))
for m in months:
    cnt = month_line[m]
    tot = sum(cnt.values())
    row = [m] + [str(cnt[l]) for l in all_lines] + [str(tot)]
    rep.append("| " + " | ".join(row) + " |")
tot_c = Counter()
for m in months:
    tot_c.update(month_line[m])
row = ["合计"] + [str(tot_c[l]) for l in all_lines] + [str(sum(tot_c.values()))]
rep.append("| " + " | ".join(row) + " |")
rep.append("\n## B 线完整清单(自产燃料线,%d 条)\n" % len(b_list))
rep.extend("`" + x + "`" for x in b_list)
rep.append("\n## 未归类 U(%d 条)\n" % len(u_list))
rep.extend("`" + x + "`" for x in u_list)
rep.append("\n## 关键词命中分布(供存疑审计)\n")
for line in all_lines:
    top = kw_hit[line].most_common(8)
    rep.append(f"- {line}: " + ", ".join(f"{k}×{v}" for k, v in top))

with open("runtime/_effort_account_result.md", "w", encoding="utf-8") as f:
    f.write("\n".join(rep))
print("total=%d months=%s" % (len(commits), months))
print("lines:", dict(tot_c))
