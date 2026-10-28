# -*- coding: utf-8 -*-
"""人话日报生成器(9/4 用户反馈:飞书快照全是代码/英文/术语,不是给人看的)。

读 /tmp/snap.txt(机器快照,frame_snapshot --push 已 scp 上云)→ LLM 归纳
成给老板的手机日报 → 写 /tmp/snap_human.txt。
通道:①自有中转站 api.chunxiao.wang(openai 兼容,优先)→ ②minimax anthropic
(兜底)→ ③模板规则拼装(保底),发送端永不因 digest 挂掉。

云端跑:python3 ops/digest_human.py
env:CHUNXIAO_API_KEY / CHUNXIAO_BASE_URL / CHUNXIAO_MODEL(云 .env,9/4 已配)
"""
from __future__ import annotations

import json
import os
import re
import urllib.request as u
from datetime import datetime

for _p in (".env", "/home/ubuntu/nautilus-v5/.env.systemd"):
    for _l in open(_p, encoding="utf-8"):
        if "=" in _l and not _l.startswith("#"):
            k, v = _l.strip().split("=", 1)
            os.environ.setdefault(k, v.strip('"'))

SNAP = "/tmp/snap.txt"
OUT = "/tmp/snap_human.txt"

SYSTEM = """你是一个多 agent 组织的日报编辑。组织有四个 AI 工作组:
- flywheel(飞轮):具身智能数据采集业务——招募采集员、采集人手动作数据、验收、转成机器人训练数据、对外报价
- compass(罗盘):AI 评测基准与学术研究——跑分、写论文、判分修正、对外评测服务
- v5:agent 运行底座——主脑调度、修 agent 自己的行为毛病(假产出/不干活/说谎)
- platform(平台):组织基础设施——函件总线、快照报表、部署、定时任务
- 内容线(Dev.to):组织对外发布的英文技术文章,互动/评论数是培育期生命线读数

输入是各组的 git 提交流水与系统指标(含大量技术术语)。请写给老板的手机日报,老板懂业务但不懂代码:
1. 第一行【一句话】:今天组织整体最重要的动态
2. 每组一段,组名加职能做小标题,2-3 句:这组在干什么、推进到哪一步、在等什么。把技术行为翻译成业务含义,可用生活比喻
3. 结尾【等你拍板】:只能列输入里明确出现"等用户/等拍板/待确认"字样的事项,禁止自行推断或把已完成事项列为待办;没有就写"无"
4. 若输入含"今日硬介入"(断奶读数),必须单列一行【断奶读数】,照抄今日件数与目标线(如"今日 X 件,目标 10/7 前≤8"),禁止归纳省略(9/30 用户批:读数必须推送到手,不建等访问盘面)
硬规矩:
- 全文不超过 350 字,手机一屏能读完
- 禁止出现:英文缩写、commit 编号、文件名、代码符号、括号里的技术注释
- 可以保留具体数字(件数/百分比/金额/时间)
- 诚实,不夸大进度;信息不足就说信息不足"""


def via_llm(snap: str) -> str | None:
    # 通道优先级:①自有中转站 api.chunxiao.wang(newapi,openai 兼容,9/4 用户授权直用)
    # ②v5 现役 minimax anthropic(云 .env 其余通道 9/4 实测全失效)
    ck = os.environ.get("CHUNXIAO_API_KEY")
    if ck:
        try:
            req = u.Request(
                os.environ.get("CHUNXIAO_BASE_URL",
                               "https://api.chunxiao.wang/v1") + "/chat/completions",
                data=json.dumps({
                    "model": os.environ.get("CHUNXIAO_MODEL") or "glm-5.3-flash",
                    "max_tokens": 2000,
                    "messages": [{"role": "system", "content": SYSTEM},
                                 {"role": "user", "content": snap[:12000]}],
                }).encode(),
                headers={"Authorization": "Bearer " + ck,
                         "Content-Type": "application/json"}, method="POST")
            d = json.loads(u.urlopen(req, timeout=75).read())
            text = (d.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()
            if text:
                return text
        except Exception:
            pass  # 落下一层
    try:
        base = (os.environ.get("CLAUDE_BASE_URL")
                or "https://api.minimaxi.com/anthropic").rstrip("/")
        req = u.Request(
            base + "/v1/messages",
            data=json.dumps({
                "model": os.environ.get("V5_LLM_MODEL") or "M3.1 Flash Preview",  # 10/1 用户令全切flash(免费,anthropic端点名;plan次数到量时走模板兜底)
                "max_tokens": 900,
                "system": SYSTEM,
                "messages": [{"role": "user", "content": snap[:12000]}],
            }).encode(),
            headers={"x-api-key": os.environ["MINIMAX_CODING_KEY"],
                     "anthropic-version": "2023-06-01",
                     "Content-Type": "application/json"}, method="POST")
        d = json.loads(u.urlopen(req, timeout=75).read())
        text = "".join(b.get("text", "") for b in d.get("content", [])
                       if b.get("type") == "text").strip()
        return text or None
    except Exception:
        return None


def via_template(snap: str) -> str:
    L = [f"📊 组织日报 {datetime.now():%m/%d}", "(模板版·LLM 归纳暂不可用)", ""]
    _pc = re.search(r"今日硬介入:[^\n]*", snap)  # 断奶读数固定行(9/30 用户批,模板兜底也不许丢)
    if _pc:
        L += [f"【断奶读数】{_pc.group(0)[:64]}", ""]
    for m in re.finditer(r"- \*\*(\w+)\*\*: (\d+) commits.*\n((?:  - .*\n)+)", snap):
        name, n, block = m.groups()
        lines = [re.sub(r"^[0-9:]+\s*", "", l.strip(" -")) for l in block.splitlines() if l.strip()]
        latest = (lines[0][:64] + "…") if lines and len(lines[0]) > 64 else (lines[0] or "")
        L.append(f"【{name}】今日 {n} 件;最新:{latest}")
        L.append("")
    L.append("【等你拍板】详见仓内机器版快照")
    return "\n".join(L)


def main() -> None:
    snap = open(SNAP, encoding="utf-8").read()
    dpath = "/tmp/devto_digest.txt"  # 内容线读数(10/4 培育期接线,devto_snapshot.py 产出,缺席不阻断)
    if os.path.exists(dpath):
        snap += "\n\n## 内容线(Dev.to 近 7 天)\n" + open(dpath, encoding="utf-8").read()
    out = via_llm(snap)
    src = "llm"
    if not out:
        out, src = via_template(snap), "template"
    open(OUT, "w", encoding="utf-8").write(out)
    print(f"digest ok: src={src} chars={len(out)}")


if __name__ == "__main__":
    main()
