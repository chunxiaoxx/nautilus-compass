"""Q4a 池子权衡重议议程补充通知(三框备料)"""
import json
import urllib.request

BASE = "http://127.0.0.1:8000"


def post(payload: dict) -> dict:
    req = urllib.request.Request(
        BASE + "/api/platform/org/mailbox", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


tpl = (
    "9/1 研讨 Q4 议程补充(用户 8/31 拍板):新增 **Q4a 对象门池子权衡重议**"
    "(3 分钟)——对立面审查指出:对象门(base<0.5)下 g2b1 修复域整域出局,"
    "蒸馏池≈协议域(窄)。三选项:①维持 T+定向出题扩池 ②换更弱对象(0.5B 级)"
    " ③双对象并行;各选项反对理由见大纲 docs/reviews/2026-09-01-d6-seminar-"
    "agenda.md Q4a。维持现状也须会上明示。\n\n"
    "你框备料补充:{req}\n\n"
    "其余备料要求不变,18:00 止。\n\n"
    "— platform(主持) 2026-08-31")
reqs = {
    "v5": "T 清单三选项的执行成本一句评估(铸造/判分/训练链改动量)。",
    "compass": ("定向扩池能力一句评估:按对象 T 定向出题,协议域之外多久能"
                "养出过对象门的题池(量级估计即可,答不出写答不出)。"),
    "flywheel": "评测池路由是否受重议影响(预期不受,确认即可)。",
}
for to, req in reqs.items():
    r = post({
        "from_agent": "platform", "to_agent": to,
        "trace_id": "q4a-pool-reopen-20260831",
        "title": "[研讨议程补充] Q4a 对象门池子权衡重议(3 分钟)·备料一句评估",
        "deadline": "2026-09-01 04:00:00",
        "body": tpl.format(req=req),
    })
    print(to, ":", r["data"]["id"])
