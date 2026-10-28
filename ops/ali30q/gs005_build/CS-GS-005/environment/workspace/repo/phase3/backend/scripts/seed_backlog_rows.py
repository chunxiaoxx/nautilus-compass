"""一次性:把真实 backlog 灌进 FDE派活表(tbl69fankpoBhJfw·状态=待派单).

Run(本地·金库凭据): python phase3/backend/scripts/seed_backlog_rows.py
幂等:task_uid 已存在则跳过(不重复写)。

backlog 三档(诚实分层·非编造·备注标档·全部纯 backlog 不预指派):
  A 可亲笔(二类·工程/AI 领域·我们真踩过)→ PM/专家按能力自领
  B 可设计(一类·科技软件与AI工作流·我们能出题)→ 待指派
  C 待招募(一类·其他买方类目占位)→ 待招募领域专家(每行=一个招募目标)
🔴 全部指派专家=空 → S1 poller 不派(待派单 backlog·设 assignee 才 dispatch)。
   不一次性把多道亲笔砸给单专家;验收标准前置必填,领活时填指派专家即进引擎。
"""
import json
import os
import urllib.request
import urllib.error

APP, TABLE = "EOVhbQwA0a1HEOsgmxecgkBVnwh", "tbl69fankpoBhJfw"
F = "https://open.feishu.cn/open-apis"

ACC_T2 = ("RUBRIC §11(二类):①五部分齐(标题/领域/Instruction/Knowledge Points/"
          "Background+Task示例) ②Background 正文1k-30k字·专家亲笔(否决:纯AI/搜索拼凑·"
          "买方实跑AI检测) ③知识密度≥5知识点 ④Task示例带正确执行+结果")
ACC_T1 = ("RUBRIC §11(一类):①16字段齐全 ②真实场景出发·≥8h人类专家复杂度"
          "(下限=需agentic发现非秒解·上限=~8h有参考解) ③真实附件脱敏·不堆附件凑数 "
          "④客观checklist可判·9固定一级类目对齐 ⑤不把信息全喂题目→要求模型自行判断")

# task_uid, 标题, 业务线, 一级类目, 三级领域, L级, 指派专家, 验收标准, 备注
ROWS = [
    # A · 可亲笔(二类·工程/AI·assignee 空=纯 backlog·按能力自领)
    ("expert_t2_drift_detection_20260612", "persona drift BGE 检测 v2:从逢触必报到 score 门",
     "2", "工程", "AI Agent 可观测性", "L2", "", ACC_T2,
     "[A可亲笔] 题源:11.5k 真实流量证 max_neg_hit≥0.538 逢触必报 64.5% 误报→v2 score 门(真修过)"),
    ("expert_t2_verdict_bus_design_20260612", "verdict-bus 事件脊柱:从死记录到可消费总线",
     "2", "工程", "分布式系统/事件驱动", "L2", "", ACC_T2,
     "[A可亲笔] 题源:fde_verdicts 表+ingest 端点替共享文件·verdict-join 遮蔽 bug(真设计+踩坑)"),
    ("expert_t2_feishu_bitable_ops_20260612", "飞书多维表 ops 工程化:options清值/富文本/分页/code非0",
     "2", "工程", "SaaS 集成/低代码平台", "L2", "", ACC_T2,
     "题源:单选改options重建清空既有行值·富文本_plain展平·>100行分页·HTTP200+code!=0(真踩坑)"),
    ("expert_t2_fixed_modal_portal_20260612", "fixed 模态被祖先 transform 困住:createPortal 根治",
     "2", "工程", "前端工程/CSS 包含块", "L2", "", ACC_T2,
     "题源:Reveal 的 translate-y 成 fixed 包含块→模态 top=2980 不覆盖视口·Portal 到 body 修(真 bug)"),
    # B · 可设计(一类·科技软件与AI工作流·待指派)
    ("expert_t1_rsi_grounded_eval_20260612", "设计题:判定 grounded-retrieval 是否真外部 RSI 增量的系统任务",
     "1", "科技软件与 AI 工作流", "AI 评测/RSI 工程", "L3", "", ACC_T1,
     "题源:two-sample 置换检验+escapes_noise 门+gated build(我们真跑出 radix +0.0734 escapes=True)"),
    ("expert_t1_control_plane_agg_20260612", "设计题:多源状态聚合控制面(fail-soft+限流)系统任务",
     "1", "科技软件与 AI 工作流", "平台工程/可观测性", "L2", "", ACC_T1,
     "题源:control-plane 聚合脊柱+429 根因(200/hr 打爆)+轮询面板限流 1200/hr(真生产修)"),
    # C · 待招募(一类·其他买方类目占位·每行=一个招募目标)
    ("expert_t1_finance_placeholder_20260612", "[待招募金融专家] 金融服务与财富投研 ≥8h 高难题",
     "1", "金融服务与财富投研", "待领域专家定", "L2", "", ACC_T1,
     "招募目标:金融领域真实业务专家·进专家库 CRM 后指派"),
    ("expert_t1_legal_placeholder_20260612", "[待招募法律专家] 法律政务与公共服务 ≥8h 高难题",
     "1", "法律政务与公共服务", "待领域专家定", "L2", "", ACC_T1,
     "招募目标:法律/政务领域真实业务专家"),
    ("expert_t1_ecommerce_placeholder_20260612", "[待招募电商专家] 品牌市场与电商零售 ≥8h 高难题",
     "1", "品牌市场与电商零售", "待领域专家定", "L2", "", ACC_T1,
     "招募目标:电商/品牌营销领域真实业务专家"),
]
COLS = ["task_uid", "标题", "业务线", "一级类目", "三级领域", "L级",
        "指派专家", "验收标准", "备注"]


def _http(method, url, token=None, body=None):
    data = json.dumps(body).encode() if body is not None else None
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())


def _plain(v):
    if isinstance(v, list):
        return "".join(s.get("text", "") for s in v if isinstance(s, dict))
    return "" if v is None else str(v)


p = os.path.expanduser("~/.claude/.cache/.fde_api_secrets.env")
for ln in open(p, encoding="utf-8"):
    ln = ln.strip()
    if ln and not ln.startswith("#") and "=" in ln:
        k, v = ln.split("=", 1)
        os.environ.setdefault(k, v)
tok = _http("POST", f"{F}/auth/v3/tenant_access_token/internal", body={
    "app_id": os.environ["FEISHU_APP_ID"],
    "app_secret": os.environ["FEISHU_APP_SECRET"]})["tenant_access_token"]

# 已存在的 task_uid(幂等)
existing = set()
j = _http("GET", f"{F}/bitable/v1/apps/{APP}/tables/{TABLE}/records?page_size=100", token=tok)
for it in (j.get("data") or {}).get("items") or []:
    existing.add(_plain((it.get("fields") or {}).get("task_uid")).strip())

created = 0
for row in ROWS:
    rec = dict(zip(COLS, row))
    if rec["task_uid"] in existing:
        print("exists:", rec["task_uid"])
        continue
    fields = {k: v for k, v in rec.items() if v}     # 空字段(如指派专家)不写
    fields["状态"] = "待派单"
    r = _http("POST", f"{F}/bitable/v1/apps/{APP}/tables/{TABLE}/records", token=tok,
              body={"fields": fields})
    ok = r.get("code") == 0
    print(("created:" if ok else "FAIL:"), rec["task_uid"], "" if ok else r.get("msg"))
    created += ok

print(f"DONE · 新建 {created} 行 · 派活表 {TABLE}")
