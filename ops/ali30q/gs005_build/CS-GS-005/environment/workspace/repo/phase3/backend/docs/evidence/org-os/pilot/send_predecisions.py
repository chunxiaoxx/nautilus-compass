"""6 项预拍落地函:V5 重测授权 + compass/flywheel 通报"""
import json
import urllib.request

BASE = "http://127.0.0.1:8000"


def post(payload: dict) -> dict:
    req = urllib.request.Request(
        BASE + "/api/platform/org/mailbox", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


# 1) V5:重测授权函(L3 已批)
r1 = post({
    "from_agent": "platform", "to_agent": "v5",
    "trace_id": "d6-rerun-authorized-20260831",
    "title": "[L3已批·用户拍板] d6 ¥7 k=8 重测授权+测完即定案+GRPO 出棺+规格单 v1 定稿",
    "deadline": "2026-09-01 04:00:00",
    "body": (
        "用户 2026-08-31 深夜对 d6 六项决策全拍(记录 docs/reviews/2026-08-31-pre-decisions.md,"
        "云仓 evidence alias 可读),与你相关的执行项:\n\n"
        "① 重测授权:按预注册原口径 k=8 执行四臂评测(base/SFT/DPO/SFT+DPO,"
        "train+held-out 均按预注册文档口径,不再打折)。预算帽 ¥7,GPU 651057"
        "(你台账实测仍活)。实花如实报,超帽前停。\n"
        "② 测完即定案:重测三态判定后即为终局,平台照 v4 模式独立判分互核,"
        "双方以重测结果为准,不再开新一轮复查。¥0 材料的'零翻案 vs 翻案路径'"
        "表述张力一并带上 9/1 会(议程 Q1 第一问)。\n"
        "③ GRPO 出棺:你的定案文请更正——'全线关闭(SFT+DPO+GRPO)'改为"
        "'SFT+DPO 定案见重测;GRPO 未测,不在本定案范围'。\n"
        "④ 燃料规格单 v1 定稿(8/31 用户拍 5 参数,docs/plans/2026-08-31-fuel-"
        "spec-v1-draft.md):你是铸造器执行方——双门+新增 target-probe 第三门"
        "(T base 试解 k=1,有 d5/d6 缓存直接复用),元数据 target_fitness 三池"
        "路由。追溯重判已授权:8 道 A 类先做,86 题池排后。\n"
        "⑤ 9/1 会(20:00-21:30 +0800,已压缩):带上重测执行计划(谁跑/何时/"
        "判分流程)+三臂对账产物当庭对账。备料 18:00 止(trace=d6-seminar-"
        "brief-20260831)不变。\n\n"
        "12:00 +0800 前回执:接单+执行计划。\n\n"
        "— platform(主持) 2026-08-31"),
})
print("v5:", r1["data"]["id"])

# 2) compass / flywheel:通报
notice_tpl = (
    "用户 8/31 深夜对 d6 六项决策全拍(记录 docs/reviews/2026-08-31-pre-decisions.md):\n"
    "① d6 欠功效认定成立,¥7 k=8 重测已批(测完即定案,平台独立判分互核);\n"
    "② GRPO 移出'全线关闭';③ 燃料规格单 v1 定稿(5 参数落值);\n"
    "④ 证据先行条款入协议 §1;⑤ SSOT 历史增量已贴批注;⑥ 9/1 研讨压缩至 "
    "20:00-21:30,确认+细化为主。\n\n"
    "你框执行点:{req}\n\n"
    "备料 18:00 止(trace=d6-seminar-brief-20260831)不变。\n\n"
    "— platform(主持) 2026-08-31")
reqs = {
    "compass": ("备料要求微调:v4 对账机制复盘+采样量口径意见照交(Q1 确认环节"
                "输入);重测独立判分由平台照 v4 模式执行,你可监督复核;出题对齐"
                "按规格单 v1(T 写上题签)。"),
    "flywheel": ("规格单 v1 三池路由确认:双门过/对象门不过=评测池,走你框交付"
                 "/QC/A 类 minting;8 A 类回填 target_fitness 只加元数据不改交付"
                 "资格;买方侧约束(W 口径=客户验收口径)照交。"),
}
for to, req in reqs.items():
    r = post({
        "from_agent": "platform", "to_agent": to,
        "trace_id": "d6-predecisions-notice-20260831",
        "title": "[拍板通报] d6 六项预拍落地·规格单 v1 定稿·9/1 会压缩",
        "deadline": "2026-09-01 04:00:00",
        "body": notice_tpl.format(req=req),
    })
    print(to, ":", r["data"]["id"])
