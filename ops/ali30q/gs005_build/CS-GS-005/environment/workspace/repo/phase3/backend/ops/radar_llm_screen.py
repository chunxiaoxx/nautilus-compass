# -*- coding: utf-8 -*-
"""拍板雷达 LLM 判读器(9/4 平台第二个中转站消费场景)。

现状:雷达=grep 关键标记("用户拍板/用户拍/用户指正/用户批评/用户定调/用户授权")
→只能捕"含标记的行",判不了"是不是值得入登记处的新决定"(误报=回顾引用/执行落地;
漏报辅助=对话型拍板)。本件把候选 commit 交给 LLM 做语义初筛,人只复核"入账/待确认"。

本地跑:python ops/radar_llm_screen.py [hours,默认48]
通道:自有中转站 api.chunxiao.wang(openai 兼容;读 backend/.env 的 CHUNXIAO_*)
输出:stdout 判读表(雷达操作者直接消费;LLM 挂了退化为原样列出候选)。
验收纪律:判读只作初筛建议,入登记处仍走平台人工确认(radar-auto 只收高置信)。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request as u
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REPOS = {
    "flywheel": r"C:\Users\chunx\Projects\nautilusflywheel",
    "v5": r"C:\Users\chunx\nautilus-v5",
    "compass": r"C:\Users\chunx\Projects\nautilus-compass",
    "platform": r"C:\Users\chunx\Projects\nautilus-core",
}
MARKS = "用户拍板|用户拍|用户指正|用户批评|用户定调|用户授权"

SYSTEM = """你是组织"拍板登记处"的初筛员。输入是各工作组 git 提交记录(已含'用户拍板'类字样的候选)。
对每条判定:
1. 类别,四选一:
   - 新拍板=记录了一个此前不存在的用户决定(方向/命名/口径/授权/定调)
   - 执行落地=把已拍板的事项做出来(拍板本身此前已发生)
   - 回顾引用=提及历史拍板作背景/依据
   - 非拍板=与用户决定无关
2. 一句话提炼(新拍板才写):决定内容,≤40字,业务语言
3. 置信度:高/中/低
4. 建议:入账(高置信新拍板)/待确认(中置信或证据不足)/忽略
输出格式,每条一段:
[框名|commit前8位|类别|置信度|建议]
提炼或一句说明
注意:宁可待确认,不可把执行落地或回顾误判为新拍板;拿不准类别时置信度降级。"""


def load_env() -> None:
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k, v.strip().strip('"'))


def collect(hours: int) -> str:
    parts = []
    for name, path in REPOS.items():
        r = subprocess.run(
            ["git", "-C", path, "log", f"--since={hours} hours ago",
             "--pretty=%h %ad %s",  # 只取 subject 行:body 是署名噪音,全量输入曾让思考型模型想 2min+ 撞穿超时(9/4 实测)
             "--date=format:%m-%d %H:%M", "-E", f"--grep={MARKS}"],
            capture_output=True, text=True, timeout=30)
        block = (r.stdout or "").strip()
        if block:
            parts.append(f"### {name}\n{block}")
    return "\n".join(parts)


def _call(model: str, candidates: str) -> str | None:
    req = u.Request(
        os.environ.get("CHUNXIAO_BASE_URL", "https://api.chunxiao.wang/v1")
        + "/chat/completions",
        data=json.dumps({
            "model": model,
            "max_tokens": 8000,  # 思考型模型 reasoning 先吃额度:2000/4000 均被吃光正文空(9/4 实测 reasoning_tokens=3962 仍不够)
            "messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": candidates[:11000]}],
        }).encode(),
        headers={"Authorization": "Bearer " + os.environ["CHUNXIAO_API_KEY"],
                 "Content-Type": "application/json"}, method="POST")
    d = json.loads(u.urlopen(req, timeout=170).read())
    return (d.get("choices") or [{}])[0].get("message", {}).get("content", "").strip() or None


def screen(candidates: str) -> str | None:
    # 顺序依据 9/4 实测:flash 对 3.4k 字符候选思考 >150s 必超时;k3 全量判完 122-170s;
    # 故 k3 首选,env 指定模型与 glm-5.3 依次兜底
    for model in ["k3", os.environ.get("CHUNXIAO_MODEL") or "glm-5.3-flash", "glm-5.3"]:
        try:
            return _call(model, candidates)
        except Exception:
            continue
    return None


def main() -> None:
    hours = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 48
    load_env()
    cand = collect(hours)
    if not cand:
        print(f"(近 {hours}h 四框无拍板标记 commit,无需判读)")
        return
    print(f"== 候选(近 {hours}h) ==")
    print(cand[:2000])
    print("\n== LLM 判读 ==")
    print(screen(cand) or "(LLM 通道不可用,退化为仅列候选;按原 grep 流程人工判)")


if __name__ == "__main__":
    main()
