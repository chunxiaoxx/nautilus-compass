"""Submit 1 GenOpt RL JobShop row to FDE派活表 S1.

派活表 base = EOVhbQwA0a1HEOsgmxecgkBVnwh
派活表 table = tbl69fankpoBhJfw (10 列 task_uid/标题/业务线/一级类目/三级领域/L级/指派专家/验收标准/状态/备注)

Run on cloud via SSH (feishu IP whitelist = cloud egress IP, not 本机 1.192.64.248).
"""
import os, sys
sys.path.insert(0, os.path.expanduser("~"))
import feishu_client  # noqa

APP_TOKEN = "EOVhbQwA0a1HEOsgmxecgkBVnwh"
TABLE_ID = "tbl69fankpoBhJfw"


def main():
    task_uid = "genopt_or_jobshop_orlib_v1_001_20260702"
    fields = {
        "task_uid": task_uid,
        "标题": "OR-Library JobShop v1_001 · 6 jobs × 5 machines 启发式求解",
        "业务线": "GenOpt",
        "一级类目": "投资、战略、专业服务与企业经营",
        "三级领域": "Operations Research · Job-Shop Scheduling",
        "L级": "L3",
        "指派专家": "platform-soul",
        "验收标准": (
            "doubao-seed-2-0-pro-260215 pass@5 ≤ 0.6 (难倒测试); "
            "GPT5.5 N=3 trajectory gap_closed=0.6843 best=93.1034 Easy; "
            "fde_verdicts 行真落库 (verdict_id=verdict-genopt-genopt_or_jobshop_orlib_v1_001_20260702-9000009-94df54d0); "
            "verifier 三铁律(确定性+只读+超时) 全 PASS"
        ),
        "状态": "已提交",
        "备注": (
            "producer=h800-genopt-runner-007 (agent_id=9000009); "
            "5 trajectory rounds (3 GPT5.5 v7 + 1 doubao fallback + 1 confirm); "
            "extracted_code_preview 含 Giffler-Thompson active scheduler; "
            "model=doubao-seed-2-0-pro-260215 (buyer spec §5 允许代理模型 trajectory)"
        ),
    }
    tok = feishu_client.tenant_token()
    print(f"[OK] tenant_token 前6 {tok[:6]}...")
    resp = feishu_client.create_bitable_record(APP_TOKEN, TABLE_ID, fields, tok)
    code = resp.get("code", -1)
    if code == 0:
        rid = resp.get("data", {}).get("record", {}).get("record_id", "?")
        print(f"[OK] {task_uid} → record_id={rid}")
        return 0
    else:
        print(f"[err] code={code} msg={resp.get('msg', '?')}")
        return 2


if __name__ == "__main__":
    sys.exit(main())