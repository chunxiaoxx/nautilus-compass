"""三项 L3 拍板落地:flywheel 试点+一页纸授权 + 三框 d6 研讨排期"""
import json
import urllib.request

BASE = "http://127.0.0.1:8000"


def post(payload: dict) -> dict:
    req = urllib.request.Request(
        BASE + "/api/platform/org/mailbox", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


# 1) flywheel:试点批复 + 一页纸授权
r1 = post({
    "from_agent": "platform", "to_agent": "flywheel",
    "trace_id": "flywheel-pilot-approved-20260831",
    "title": "[L3已批·用户拍板] 默认决策权试点通过+一页纸授权(终稿先呈用户)",
    "deadline": "2026-08-31 08:00:00",
    "body": (
        "用户 2026-08-31 拍板'三项全按平台建议执行',你提案的两项均批:\n\n"
        "① 默认决策权试点(flywheel 框,即日生效):\n"
        "- 自决范围:预算类单笔≤¥10、执行细节、优先级、对内动作——做完进日报待追认\n"
        "- 两道闸(保留,触碰即须用户明示):单笔>¥10;任何对外发送\n"
        "- 试点期 2 周(至 9/14),期满复盘:零事故则闸门阈值复议,有事故回滚\n"
        "- 与协议 §2 关系:试点额度更严(≤¥10 严于协议 ≤¥30),冲突从紧\n\n"
        "② 一页纸发第一个真实客户:授权。条件:终稿先呈用户过目(投决策卡或"
        "mailbox 均可,注明'一页纸终稿待过目'),用户确认后首发动作由用户本人"
        "执行或用户明示代发。8 月空转的直接解,9/1 起算 SLA。\n\n"
        "— platform(主持) 2026-08-31"),
})
print("flywheel:", r1["data"]["id"])

# 2) 三框:d6 研讨排期(同 trace 不同 to)
seminar_body_tpl = (
    "[L3已批·用户拍板] d6 失真研讨排期:9/1(周一)20:00-22:00 +0800,平台主持,"
    "用户终审。备料 deadline 9/1 18:00:产物落盘可复现位置+书面立场一页"
    "(trace=d6-seminar-brief-20260831,投 mailbox)。\n"
    "本框备料要求:{req}\n"
    "会议判据:预注册口径(d6 预注册文档)为裁决基线;若证实欠功效/口径错配,"
    "输出=修订后的六轮矩阵+再解冻条件;若不证实,官方定案获得预注册口径背书。"
    "全程记录进 docs/reviews/。")
reqs = {
    "v5": ("§6 预读索引全部产物落盘(评测输出/提取器代码/复现命令一键脚本);"
           "书面立场含:你主张的修订矩阵全文+每条的原始证据指针。"),
    "compass": ("独立判分方视角:v4 对账翻案的机制复盘(为何双源判分没抓住"
                "提取器 bug);对'采样量口径双源同盲'的独立意见与补测方案建议。"),
    "flywheel": ("数据管道视角:A 类'弱臂'定义(doubao/minimax vs Qwen-Coder-7B)"
                 "与垂域交付 QC 的口径关系;燃料规格单的买方侧约束输入。"),
}
for to, req in reqs.items():
    r = post({
        "from_agent": "platform", "to_agent": to,
        "trace_id": "d6-seminar-schedule-20260831",
        "title": "[研讨排期·用户已批] d6 失真研讨 9/1 20:00 · 本框备料要求内附",
        "deadline": "2026-09-01 10:00:00",
        "body": seminar_body_tpl.format(req=req),
    })
    print(to, ":", r["data"]["id"])
