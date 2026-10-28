"""Q4a 预拍执行函:V5 追溯重判立即启动"""
import json
import urllib.request

BASE = "http://127.0.0.1:8000"
payload = {
    "from_agent": "platform", "to_agent": "v5",
    "trace_id": "pool-rejudge-20260831",
    "title": "[执行授权] 追溯重判立即启动(用户预拍 Q4a ①+立即重判)",
    "deadline": "2026-09-01 04:00:00",
    "body": (
        "用户 8/31 预演数据呈览后预拍 Q4a:**① 维持 T(Qwen 1.5B/7B)+compass 定向"
        "扩池+立即追溯重判**;②换弱对象/③双对象挂解冻条件(实测池<20 题且扩池慢"
        "才重议)。据此授权重判执行:\n\n"
        "1. 口径:燃料规格单 v1 §3 target-probe——对象模型裸考 k=1,判分用现有"
        "提取器+verifier;无法判的题如实标,不猜。\n"
        "2. 对象:1.5B 与 7B 都跑(两对象各一遍,成本可忽略)。\n"
        "3. 范围与顺序:8 道 A 类燃料先做 → 86 题池接续(幂等,断点可续)。\n"
        "4. 优先级:DPO k=8 重测(GPU)不受影响,重判纯 API 插空跑。\n"
        "5. 产物:JSONL 每题 {uid, 对象, k=1 通过, 过门判定(阈值<0.5)}+可复现"
        "命令,落盘 vtf/ 并回函报数;8 A 类部分可先交,86 题池续报。\n"
        "6. 平台将照 v4 模式独立判分抽验互核。\n\n"
        "回函 trace=pool-rejudge-20260831-reply,deadline 9/1 12:00 +0800"
        "(与备料同批)。\n\n"
        "— platform 2026-08-31"),
}
req = urllib.request.Request(
    BASE + "/api/platform/org/mailbox", data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req, timeout=15) as r:
    print(json.loads(r.read()))
