"""P1.1 燃料分桶写出路由(双门分拣后 → 燃料池 / 买方表 / 丢)。

双门分拣(services.fde_triage.classify_distillation_fuel)出桶后路由:
  distillation_fuel(bucket-A)→ mint 进 dispatch 带 task_family='distillation_fuel'
                                (RSI 燃料·V5 W1/W2 按 family claim)+ 组装买方 T3 payload
                                (难倒题 buyer 料·一鱼两吃)
  buyer_stump(bucket-B)       → 组装买方 T3 payload(真前沿护城河·免费副产品)·不 mint
  true_wall_pending_strong_gate → hold(gate B 未测·不臆造燃料·诚实)
  pseudo_wall/gate_artifact/too_easy → drop + log

纯路由 · effect 注入(mint_fn / write_delivery_fn / log_fn)。runner 侧接真 dispatch
+ 飞书写。设计见 docs/plans/2026-06-20-p1-third-class-flywheel-autonomy-plan.md(G2-G4)。

🔴 决策(2026-06-20 baked):燃料池 = dispatch 队列 + task_family='distillation_fuel'
   (FdeDispatch 无 task_family 列 → 嵌 description JSON·V5 自 desc 读)。bench_family
   (kernelbench-stump)另存供 V5 W3 跨题 peer 记忆。
🔴 红线(charter §2):自动产物的买方 payload 标 provisional + _DRAFT_NOTICE —— 须真人
   脱敏 + 过买方 AI 检测后才是终品。本模块只组装·不冒充终稿。
"""
from __future__ import annotations

import json
from typing import Callable

FUEL_TASK_FAMILY = "distillation_fuel"

# 自动产物兜底红线标(charter §2·与 fde_t3_scratch row_to_write 既有约定一致)
_DRAFT_NOTICE = "【自动产物·待真人脱敏 + 过买方 AI 检测后才是终品·charter§2·勿直接交付】"

# 第3类买方 L3 样例表默认领域(9 固定一级类目之一 + KernelBench 默认二三级·可被候选覆盖)
_DEFAULT_L1 = "科技软件与AI工作流"
_DEFAULT_L2 = "高性能计算与AI算子优化"
_DEFAULT_L3 = "CUDA自定义算子融合优化"


def _first_para(text: str, limit: int = 600) -> str:
    """task_spec 首段(去标题行)作任务概括。"""
    lines = [ln for ln in (text or "").splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    return ("\n".join(lines)[:limit]).strip()


def _first_line(text: str) -> str:
    for ln in (text or "").splitlines():
        s = ln.strip().lstrip("#").strip()
        if s:
            return s[:120]
    return ""


def is_buyer_deliverable(candidate: dict) -> bool:
    """该候选是否走买方交付轨(写 L3 表)。

    🔴 三框收敛(2026-06-20):SWE = 纯 RSI substrate·**非**买方交付(charter §1.3
    coding 类买方已自采)→ track='swe' 只产蒸馏燃料不写买方表。
    KernelBench/12 类(track 缺省)= 买方交付轨(speed-stump 口径)。
    """
    return candidate.get("track") != "swe"


def build_fuel_desc(candidate: dict, task_family: str = FUEL_TASK_FAMILY) -> str:
    """组装 mint 进 dispatch 的 description JSON(自包含·V5 claim→produce 不依赖文件)。

    必带 task_family(燃料池键·V5 W1/W2 claim)。bench_family 保留 benchmark 族(族级·
    供 V5 W3 跨题 peer 记忆)。两轨:
      - SWE(swe_instance_id 存)= RSI substrate·desc 带 problem_statement + 实例 + rsi_proof。
        verify=swebench harness(soul verify-side P1.3b 路由·≠ KernelBench kb_eval)。
      - KernelBench = starter_inline + verifier_inline + kb_level/kb_problem_id/fast1。
    """
    if candidate.get("swe_instance_id"):
        desc = {
            "fde_class": 3,
            "kind": "swe-rsi-fuel",
            "task_family": task_family,
            "bench_family": candidate.get("bench_family", ""),
            "swe_instance_id": candidate["swe_instance_id"],
            "swe_repo": candidate.get("swe_repo", ""),
            "verifier": "swebench-harness",
            "任务概括": _first_para(candidate.get("spec", ""), 300),
            "problem_statement": candidate.get("spec", ""),
            "rsi_proof": candidate.get("rsi_proof"),
        }
        # 契约 B(2026-06-20):内嵌 buggy 原文 + edit_paths → V5 producer 出修正全文→
        # difflib 算 git-apply 兼容 diff(零网络零 dataset)。prep 未跑则缺这两字段。
        if candidate.get("original_files"):
            desc["edit_paths"] = candidate.get("edit_paths") or list(candidate["original_files"].keys())
            desc["original_files"] = candidate["original_files"]
        return json.dumps(desc, ensure_ascii=False)
    desc = {
        "fde_class": 3,
        "kind": "code-fix-with-deterministic-verifier",
        "task_family": task_family,
        "bench_family": candidate.get("bench_family", ""),
        "任务概括": _first_para(candidate.get("spec", ""), 300),
        "starter_inline": candidate.get("starter", ""),
        "verifier_inline": candidate.get("verifier", ""),
    }
    if candidate.get("kb_problem_id") is not None:
        desc["kb_level"] = candidate.get("kb_level", 2)
        desc["kb_problem_id"] = candidate["kb_problem_id"]
        desc["fast1"] = bool(candidate.get("fast1", True))
    return json.dumps(desc, ensure_ascii=False)


def _repro_note(classified: dict) -> str:
    bucket = classified.get("bucket")
    which = classified.get("which_model")
    if bucket == "distillation_fuel":
        return ("doubao-2.0-pro pass@k=0(难倒证据)· 强模型(%s)在同 harness 解出 → "
                "有干净 correct trace(可蒸馏)" % (which or "强模型"))
    if bucket == "buyer_stump":
        return ("doubao-2.0-pro pass@k=0 且强模型也解不出 → 真前沿护城河(教师亦无 trace)")
    return classified.get("reason", "")


def assemble_t3_payload(candidate: dict, classified: dict) -> dict:
    """第3类(基准/难倒题)→ 买方 L3 样例表 payload(列结构 ≠ 线1/2 教案 16 列)。

    列锚 = L3 基准样例表(EOVhbQwA0a1HEOsgmxecgkBVnwh / tblhD4O4f0esTyXc)实际列。
    自动产物 → status='provisional' + _DRAFT_NOTICE(charter §2 红线)。
    """
    spec = candidate.get("spec", "")
    return {
        "UID": str(candidate.get("task_uid") or "").strip(),
        "题目": candidate.get("title") or _first_line(spec),
        "题目领域一级目录": candidate.get("l1", _DEFAULT_L1),
        "题目领域二级目录": candidate.get("l2", _DEFAULT_L2),
        "题目领域三级目录": candidate.get("l3", _DEFAULT_L3),
        "任务概括": _first_para(spec),
        "标注专家工作年限（未工作的可以写最高学历）": candidate.get("expert_years", ""),
        "人类所需完成时间": candidate.get("human_time", ""),
        "相关附件": candidate.get("attachment_name", "buggy_starter.py"),
        "附件格式标签": candidate.get("attachment_fmt", "Python"),
        "附件内容（总结概括）": candidate.get(
            "attachment_summary", "基线 PyTorch Model 实现(待优化为自定义 CUDA kernel ModelNew)"),
        "产物格式标签": candidate.get("product_fmt", "Python (.py · ModelNew)"),
        "产物内容（总结概括）": candidate.get(
            "product_summary", "正确且相对 PyTorch eager 有真实加速的自定义 CUDA kernel"),
        "做题关键步骤（可选）": candidate.get("key_steps", ""),
        "任务类型": candidate.get("task_type", "L3系统性"),
        "打分checklist": candidate.get(
            "checklist", "确定性 verifier bench_eval.py:correctness(1e-2+1e-3 双门)"
                         "+ 加速门(speedup>1·>2× 反作弊)+ 真自定义 kernel 门"),
        "复现验证": _repro_note(classified),
        "reward": "1.0 当且仅当全 G 门通过(确定性)",
        "status": "provisional",
        "bucket": classified.get("bucket"),
        "_DRAFT_NOTICE": _DRAFT_NOTICE,
    }


def route_bucket(classified: dict, candidate: dict, *,
                 mint_fn: Callable[[str, str, str], dict],
                 write_delivery_fn: Callable[[dict], dict],
                 log_fn: Callable | None = None) -> dict:
    """双门分桶 → 写出路由(纯路由·effect 注入)。

    mint_fn(task_uid, title, description) -> dict  : POST dispatch(带 task_family 燃料)
    write_delivery_fn(payload) -> dict            : 写买方 L3 表(自动产物 provisional)
    log_fn(event, **kv)                            : 进度日志(可选)
    返回 {task_uid, bucket, action, ...} —— action ∈ {mint+deliver, deliver, hold, drop}。
    """
    bucket = classified.get("bucket")
    uid = str(classified.get("task_uid") or candidate.get("task_uid") or "").strip()
    title = candidate.get("title") or uid
    _log = log_fn or (lambda *a, **k: None)

    buyer = is_buyer_deliverable(candidate)

    if bucket == "distillation_fuel":
        minted = mint_fn(uid, title, build_fuel_desc(candidate))
        out = {"task_uid": uid, "bucket": bucket, "task_family": FUEL_TASK_FAMILY,
               "minted": minted}
        if buyer:  # KernelBench/12 类 = 一鱼两吃·也写买方表
            out["delivered"] = write_delivery_fn(assemble_t3_payload(candidate, classified))
            out["action"] = "mint+deliver"
        else:      # SWE = 纯 RSI 燃料·只 mint 不写买方表
            out["action"] = "mint"
        _log("route", task_uid=uid, bucket=bucket, action=out["action"])
        return out

    if bucket == "buyer_stump":
        if not buyer:  # SWE 落 buyer_stump = 非燃料非买方 → drop
            _log("route", task_uid=uid, bucket=bucket, action="drop")
            return {"task_uid": uid, "bucket": bucket, "action": "drop",
                    "reason": "SWE 强模型无改进·非燃料非买方交付"}
        delivered = write_delivery_fn(assemble_t3_payload(candidate, classified))
        _log("route", task_uid=uid, bucket=bucket, action="deliver")
        return {"task_uid": uid, "bucket": bucket, "action": "deliver", "delivered": delivered}

    if bucket == "true_wall_pending_strong_gate":
        _log("route", task_uid=uid, bucket=bucket, action="hold")
        return {"task_uid": uid, "bucket": bucket, "action": "hold",
                "reason": "gate B(强模型先解)未测·不臆造燃料"}

    # pseudo_wall / gate_artifact / too_easy → 丢
    _log("route", task_uid=uid, bucket=bucket, action="drop")
    return {"task_uid": uid, "bucket": bucket, "action": "drop",
            "reason": classified.get("reason", "")}
