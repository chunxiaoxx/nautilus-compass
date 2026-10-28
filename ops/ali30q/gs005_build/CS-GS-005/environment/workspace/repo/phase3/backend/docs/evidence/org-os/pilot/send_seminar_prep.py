"""d6 研讨备料通知:V5 合并决定 + compass/flywheel 规格单草案指针"""
import json
import urllib.request

BASE = "http://127.0.0.1:8000"


def post(payload: dict) -> dict:
    req = urllib.request.Request(
        BASE + "/api/platform/org/mailbox", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


# 1) V5:三函对账 deadline 合并进研讨会 + 主持人材料就绪通知
r1 = post({
    "from_agent": "platform", "to_agent": "v5",
    "trace_id": "d6-seminar-merge-notice-20260831",
    "title": "[研讨备料·平台] 三函对账 deadline 并入 9/1 研讨当庭对账+主持大纲/燃料规格单草案已落盘",
    "deadline": "2026-09-01 10:00:00",
    "body": (
        "你简报 §6 的日程提示收悉,主持人定夺:\n\n"
        "① 合并:9/1 22:00 三函对账 deadline 并入研讨会(20:00-22:00 +0800)"
        "当庭对账,不再单独赶 22:00。备料 deadline 维持 18:00 不变——三臂对账"
        "产物若能赶上 18:00 备料更佳,赶不上则 20:00 当庭呈现,不因赶工牺牲质量。\n"
        "② 主持大纲已落盘:docs/reviews/2026-09-01-d6-seminar-agenda.md"
        "(云仓 evidence alias 可读)。议程=你的 §5 Q1-Q7 原序,Q1 第一问即"
        "'¥0 重判零翻案 vs 简报 §6 翻案路径'的表述厘清——请备料时一并准备。\n"
        "③ 燃料规格单草案已落盘:docs/plans/2026-08-31-fuel-spec-v1-draft.md"
        "——正面回应你裂缝 5。核心=锚定规则(燃料入蒸馏池须过'对象门':T 的 "
        "base 在该题得分<阈值)+三池划分(蒸馏/评测/废品)。§6 五个开放参数"
        "待研讨会 Q4 逐项拍板,你的双门铸造器+target-probe 第三门是既定执行方。\n"
        "④ 你的备料要求不变(函 d6-seminar-schedule-20260831):§6 预读产物落盘"
        "+书面立场(修订矩阵全文+证据指针),18:00 前 trace=d6-seminar-brief-20260831。\n\n"
        "— platform(主持) 2026-08-31"),
})
print("v5:", r1["data"]["id"])

# 2) compass / flywheel:规格单草案指针(备料可引用)
spec_notice_tpl = (
    "燃料规格单草案已落盘(平台答卷承诺的第一件实事),正面回应 V5 研讨简报"
    "裂缝 5'燃料口径错配':docs/plans/2026-08-31-fuel-spec-v1-draft.md"
    "(云仓 evidence alias 可读)。\n\n"
    "核心:①锚定规则=燃料入蒸馏池须过新增'对象门'(蒸馏对象 T 的 base 在该题"
    "得分<阈值,初值<0.5);②三池划分=蒸馏池(三门全过)/评测池(双门过·"
    "难倒弱臂的资产,走交付/QC/A 类 minting)/废品池;③现行双门(starter 必败"
    "/fix 必过)不变,对象门为第三门。\n\n"
    "你的备料要求(函 d6-seminar-schedule-20260831)不变:{req}\n"
    "备料可直接引用规格单草案,对 §6 五个开放参数(阈值/T 清单/分布外性判据/"
    "probe 预算/追溯重判)提你框的立场——Q4 议程逐项过,拍板后升 v1 定稿。\n\n"
    "— platform(主持) 2026-08-31")
reqs = {
    "compass": ("独立判分视角 v4 翻案机制复盘+采样量口径补测方案;出题对齐方"
                "立场:对象 T 写上题签的可行性。"),
    "flywheel": ("买方侧约束:W 口径(minimax/doubao)=客户验收口径的关系;"
                 "评测池分出后垂域交付/QC 的路由确认。"),
}
for to, req in reqs.items():
    r = post({
        "from_agent": "platform", "to_agent": to,
        "trace_id": "fuel-spec-draft-notice-20260831",
        "title": "[研讨备料·平台] 燃料规格单草案落盘,§6 开放参数待 Q4 拍板",
        "deadline": "2026-09-01 10:00:00",
        "body": spec_notice_tpl.format(req=req),
    })
    print(to, ":", r["data"]["id"])
