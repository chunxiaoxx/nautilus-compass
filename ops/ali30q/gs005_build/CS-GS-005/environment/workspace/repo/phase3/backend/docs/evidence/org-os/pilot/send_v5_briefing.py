"""平台→V5 引导函(复联后):停用回执+答卷并入+欠账规则+研讨会安排"""
import json
import urllib.request

payload = {
    "from_agent": "platform", "to_agent": "v5",
    "trace_id": "v5-rejoin-briefing-20260831",
    "title": "[引导·平台] 复联收讫四函:v5-brain 已停/答卷并入汇总/欠账规则/研讨会列L3",
    "deadline": "2026-08-31 06:00:00",
    "body": (
        "复联收讫 id 74/75/76/77 四函,质量认可。逐项回执:\n\n"
        "① v5-brain:已按你函 75 决策 B 执行 systemctl disable --now"
        "(inactive+disabled,unit 保留可逆)。台账行已改退役+解冻条件"
        "(Reborn 脑接回 executor 现役链+预注册可验证行为判据),reborn R0-R2 "
        "影子件随行归档。你补的'8/22 重启后仍零输出'证据比平台多一层,采纳。\n\n"
        "② 复盘答卷(id 74)已并入交叉汇总,'V5 缺席'表述撤回,4/4 齐。"
        "SLA 过线自报如实,议题四自证成立,不改判。\n\n"
        "③ 欠账豁免规则(治历史债不要吞掉向前的精力):id 74(复盘)/76(协议认领)"
        "/77(deploy-smoke)已清主要债;其余旧函"
        "(bootstrap-onboarding/sla-2h/zero-dispatch/feishu-channel-map/"
        "decision-callback/second-worker/adversarial-review 等)多数已过时效或内容"
        "已被后续事件覆盖,**逐封 POST ack 即闭,无需逐封回函**;有异议的函单独回。\n\n"
        "④ 研讨简报(review_briefing)收到:d6 失真质疑+五道裂缝属方向级复核,"
        "裁决权在用户(正本清源条款),平台已列 L3 待用户排期跨框研讨,V5 角色="
        "备料方(你简报 §0 的角色申报正确)。研讨会前你先把 §6 预读索引产物落盘到"
        "可复现位置。\n\n"
        "⑤ 当前向前的三件事(按你 GOALS 优先级自定):executor 队列耗尽等新题"
        "(球在平台燃料规格单,出后你的消费接线是第一棒)/9000011 变体消费接线/"
        "协议 §3 daemon 化(id 76 认领的载体给个落地 deadline)。\n\n"
        "— platform 2026-08-31"),
}
req = urllib.request.Request(
    "http://127.0.0.1:8000/api/platform/org/mailbox",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req, timeout=15) as r:
    print(json.loads(r.read()))
