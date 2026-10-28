"""P1.1 燃料分桶写出路由 TDD(2026-06-20·双门分拣后路由)。

route_bucket 纯路由 · effect 注入(mint_fn/write_delivery_fn/log_fn):
  distillation_fuel(bucket-A)→ mint dispatch 带 task_family='distillation_fuel' + 写买方表
  buyer_stump(bucket-B)      → 写买方表(护城河)·不 mint
  true_wall_pending_strong_gate → hold(gate B 未测·不臆造燃料)
  pseudo/gate_artifact/too_easy → drop+log
"""
import json

from services.fde_fuel_router import (
    build_fuel_desc, assemble_t3_payload, route_bucket, is_buyer_deliverable,
)


def _swe_candidate():
    return {
        "task_uid": "psf__requests-2148", "track": "swe",
        "bench_family": "requests", "swe_instance_id": "psf__requests-2148",
        "swe_repo": "psf/requests", "title": "requests-2148 socket timeout",
        "spec": "When a socket timeout occurs requests raises the wrong exception...",
        "rsi_proof": {"turn1": 2, "turn2": 6, "n_f2p": 10, "model": "qwen3.7-max",
                      "source": "session_20260619 N=3"},
    }


def _candidate():
    return {
        "task_uid": "kb_l2_p13_x",
        "title": "KernelBench L2 p13 · ConvTranspose3d 融合优化",
        "spec": "# KernelBench L2 p13\n为以下架构写自定义 CUDA 优化版。\n要求:正确且更快。",
        "starter": "import torch\nclass Model(torch.nn.Module): ...",
        "verifier": "print('{\"passed\": false, \"n_passed\": 0, \"n_samples\": 50}')",
        "bench_family": "kernelbench-stump",
        "kb_level": 2,
        "kb_problem_id": 13,
        "fast1": True,
    }


def _classified(bucket, which_model=None):
    d = {"task_uid": "kb_l2_p13_x", "bucket": bucket, "reason": "r",
         "pass_rate": 0.0, "distill_candidate": bucket == "distillation_fuel"}
    if bucket in ("distillation_fuel", "buyer_stump", "true_wall_pending_strong_gate"):
        d["gate_a_true_wall"] = True
        d["strong_model_passed"] = (which_model is not None) if bucket != "true_wall_pending_strong_gate" else None
    if which_model:
        d["which_model"] = which_model
    return d


# ---- build_fuel_desc ----

def test_build_fuel_desc_carries_distillation_family():
    desc = build_fuel_desc(_candidate())
    j = json.loads(desc)
    assert j["task_family"] == "distillation_fuel"
    assert j["fde_class"] == 3
    assert j["starter_inline"].strip()
    assert j["verifier_inline"].strip()


def test_build_fuel_desc_preserves_bench_family_and_kb_route():
    j = json.loads(build_fuel_desc(_candidate()))
    assert j["bench_family"] == "kernelbench-stump"   # V5 W3 peer 记忆键
    assert j["kb_problem_id"] == 13 and j["kb_level"] == 2 and j["fast1"] is True


def test_build_fuel_desc_omits_kb_fields_for_cpu_fuel():
    cand = _candidate()
    cand.pop("kb_problem_id"); cand.pop("kb_level"); cand.pop("fast1")
    j = json.loads(build_fuel_desc(cand))
    assert "kb_problem_id" not in j


# ---- assemble_t3_payload ----

def test_assemble_t3_payload_has_buyer_l3_columns():
    p = assemble_t3_payload(_candidate(), _classified("buyer_stump"))
    for col in ("UID", "题目", "任务概括", "题目领域一级目录",
                "产物格式标签", "打分checklist", "复现验证"):
        assert col in p, col
    assert p["UID"] == "kb_l2_p13_x"


def test_assemble_t3_payload_flags_provisional():
    # 自动产物必须标待真人脱敏过 AI 检测(charter §2 红线)
    p = assemble_t3_payload(_candidate(), _classified("buyer_stump"))
    assert "_DRAFT_NOTICE" in p and p["_DRAFT_NOTICE"]


def test_assemble_t3_payload_repro_reflects_bucket():
    fuel = assemble_t3_payload(_candidate(), _classified("distillation_fuel", "qwen3.7-max"))
    stump = assemble_t3_payload(_candidate(), _classified("buyer_stump"))
    assert "qwen3.7-max" in fuel["复现验证"] or "可解" in fuel["复现验证"]
    assert "解不出" in stump["复现验证"] or "护城河" in stump["复现验证"]


# ---- route_bucket ----

class _Rec:
    def __init__(self):
        self.mints = []
        self.delivers = []
        self.logs = []

    def mint_fn(self, uid, title, desc):
        self.mints.append({"uid": uid, "title": title, "desc": desc})
        return {"status": "open", "task_uid": uid}

    def write_delivery_fn(self, payload):
        self.delivers.append(payload)
        return {"record_id": "rec_%d" % len(self.delivers)}

    def log_fn(self, *a, **k):
        self.logs.append((a, k))


def test_route_distillation_fuel_mints_and_delivers():
    r = _Rec()
    out = route_bucket(_classified("distillation_fuel", "qwen3.7-max"), _candidate(),
                       mint_fn=r.mint_fn, write_delivery_fn=r.write_delivery_fn, log_fn=r.log_fn)
    assert out["action"] == "mint+deliver"
    assert len(r.mints) == 1 and len(r.delivers) == 1
    assert json.loads(r.mints[0]["desc"])["task_family"] == "distillation_fuel"
    assert out["task_family"] == "distillation_fuel"


def test_route_buyer_stump_delivers_no_mint():
    r = _Rec()
    out = route_bucket(_classified("buyer_stump"), _candidate(),
                       mint_fn=r.mint_fn, write_delivery_fn=r.write_delivery_fn, log_fn=r.log_fn)
    assert out["action"] == "deliver"
    assert len(r.mints) == 0 and len(r.delivers) == 1


def test_route_too_easy_drops():
    r = _Rec()
    out = route_bucket({"task_uid": "x", "bucket": "too_easy", "reason": "易"}, _candidate(),
                       mint_fn=r.mint_fn, write_delivery_fn=r.write_delivery_fn, log_fn=r.log_fn)
    assert out["action"] == "drop"
    assert len(r.mints) == 0 and len(r.delivers) == 0


def test_route_gate_artifact_drops():
    r = _Rec()
    out = route_bucket({"task_uid": "x", "bucket": "gate_artifact", "reason": "洗门"}, _candidate(),
                       mint_fn=r.mint_fn, write_delivery_fn=r.write_delivery_fn, log_fn=r.log_fn)
    assert out["action"] == "drop"
    assert len(r.mints) == 0 and len(r.delivers) == 0


# ---- SWE 燃料轨(P1.3·RSI substrate·非买方交付) ----

def test_build_fuel_desc_swe_branch():
    j = json.loads(build_fuel_desc(_swe_candidate()))
    assert j["kind"] == "swe-rsi-fuel"
    assert j["task_family"] == "distillation_fuel"      # claim 键
    assert j["bench_family"] == "requests"              # 记忆键·族级(非实例)
    assert j["swe_instance_id"] == "psf__requests-2148"
    assert j["swe_repo"] == "psf/requests"
    assert "kb_problem_id" not in j                     # 非 KernelBench
    assert j.get("rsi_proof", {}).get("turn2") == 6


def test_build_fuel_desc_swe_embeds_original_files(_=None):
    # 契约 B:mint 内嵌 buggy 原文 + edit_paths → V5 daemon 零网络零 dataset 依赖
    cand = _swe_candidate()
    cand["edit_paths"] = ["requests/adapters.py"]
    cand["original_files"] = {"requests/adapters.py": "class HTTPAdapter:\n    pass\n"}
    j = json.loads(build_fuel_desc(cand))
    assert j["edit_paths"] == ["requests/adapters.py"]
    assert j["original_files"]["requests/adapters.py"].startswith("class HTTPAdapter")


def test_build_fuel_desc_swe_omits_empty_original_files():
    # 没 original_files(prep 没跑)→ 不塞空字段(V5 据缺失判 prep 未就绪)
    j = json.loads(build_fuel_desc(_swe_candidate()))
    assert "original_files" not in j and "edit_paths" not in j


def test_is_buyer_deliverable_swe_false_kernelbench_true():
    assert is_buyer_deliverable(_swe_candidate()) is False  # SWE 非买方交付
    assert is_buyer_deliverable(_candidate()) is True       # KernelBench=买方


def test_route_swe_distillation_fuel_mints_only_no_buyer_table():
    r = _Rec()
    out = route_bucket(_classified("distillation_fuel", "qwen3.7-max"), _swe_candidate(),
                       mint_fn=r.mint_fn, write_delivery_fn=r.write_delivery_fn, log_fn=r.log_fn)
    assert out["action"] == "mint"                  # 只 mint 燃料·不写买方表
    assert len(r.mints) == 1 and len(r.delivers) == 0
    j = json.loads(r.mints[0]["desc"])
    assert j["task_family"] == "distillation_fuel" and j["bench_family"] == "requests"


def test_route_swe_buyer_stump_drops_not_delivered():
    # SWE 若落 buyer_stump(强模型也没改进)= 非燃料非买方 → drop(不写买方表)
    r = _Rec()
    out = route_bucket(_classified("buyer_stump"), _swe_candidate(),
                       mint_fn=r.mint_fn, write_delivery_fn=r.write_delivery_fn, log_fn=r.log_fn)
    assert out["action"] == "drop"
    assert len(r.mints) == 0 and len(r.delivers) == 0


def test_route_pending_strong_gate_holds():
    r = _Rec()
    out = route_bucket(_classified("true_wall_pending_strong_gate"), _candidate(),
                       mint_fn=r.mint_fn, write_delivery_fn=r.write_delivery_fn, log_fn=r.log_fn)
    assert out["action"] == "hold"
    assert len(r.mints) == 0 and len(r.delivers) == 0
