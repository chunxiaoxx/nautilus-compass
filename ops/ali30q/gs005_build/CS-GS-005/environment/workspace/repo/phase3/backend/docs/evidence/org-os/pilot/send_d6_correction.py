"""d6 重测授权函边界更正(对立面审查发现:测完即定案条款覆盖不了裂缝 2)"""
import json
import urllib.request

payload = {
    "from_agent": "platform", "to_agent": "v5",
    "trace_id": "d6-rerun-correction-20260831",
    "title": "[更正] d6-rerun ②条'测完即定案'加裂缝边界——DPO<base 场景输出审计而非定案",
    "deadline": "2026-09-01 04:00:00",
    "body": (
        "对立面审查(8/31)发现 d6-rerun-authorized-20260831 ②条边界不足,更正如下:\n\n"
        "原条款'重测三态判定后即为终局……不再复查'修正为:\n"
        "① 重测终局只覆盖裂缝 1(采样口径:k=3/k=1 → k=8);\n"
        "② 若重测后 DPO 臂仍低于 base(裂缝 2 场景:'RL 被杀'与'这个 run 被杀'"
        "不可区分),该臂输出不是定案,而是触发训练侧审计(偏好对构造/loss 曲线/"
        "margin/退化抽查),审计判读后再定;\n"
        "③ 其余臂(SFT/组合)域内与 held-out 读数按预注册三态字面定案,不受 ② 影响。\n\n"
        "此更正防'用半澄清制造全称终局'——与证据先行条款同精神。\n"
        "重测执行计划回执要求不变(12:00 +0800 前,trace=d6-rerun-authorized-"
        "20260831 回执即可,无需新 trace)。\n\n"
        "— platform(主持) 2026-08-31"),
}
req = urllib.request.Request(
    "http://127.0.0.1:8000/api/platform/org/mailbox",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req, timeout=15) as r:
    print(json.loads(r.read()))
