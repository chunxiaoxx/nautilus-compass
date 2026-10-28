"""两条 RSI+FDE 闭环回放数据装配(舰桥 scrollytelling 用)。

🔴 融合闭环接真:db 给定时,关键数值从真实表装配 —— radix 从 fde_rsi_deltas
(task_uid=radix_sort 最新行)· data_001 从 fde_verdicts(task_uid=data_001
最新行)。db None / 行缺 / 查询异常 → fail-soft 回退 curated 叙述。每条 loop
带 source ∈ {db, curated} 诚实标注数值来源(不把 curated 伪装成真值)。

叙述脚手架(phase/label/缺省值)= 我们真跑过的结果(escapes=True 的 radix
grounded-retrieval + EduPulse 买方题 11/11 过 QC),DB 行只覆盖其中可由表回填
的数值字段。control_plane._loops_section 传 db;import 失败 fail-soft 返 stub。
"""
from __future__ import annotations


def _curated_radix() -> dict:
    """radix RSI grounded-retrieval 叙述脚手架 + 真跑缺省数值(escapes=True)。"""
    return {
        "loop_id": "radix_rsi",
        "title": "radix RSI grounded-retrieval(首个真外部增量·escapes=True)",
        "source": "curated",
        "steps": [
            {"phase": "verdict_baseline", "label": "裸候选客观打分",
             "data": {"bare_mean": 0.1835, "correct": "9/13"}},
            {"phase": "grounding", "label": "检索 correctness-first 避坑语料注入",
             "data": {"policy": "correctness-first",
                      "source": "autolab_avoid_radix_sort"}},
            {"phase": "produce", "label": "producer(deepseek)产 grounded 候选",
             "data": {"producer": "deepseek-chat"}},
            {"phase": "reward", "label": "grounded 客观打分",
             "data": {"grounded_mean": 0.2568, "correct": "12/13",
                      "delta_reward": 0.0734}},
            {"phase": "escapes_judgment", "label": "soul 官方 grounding_probe_twosample 判",
             "data": {"delta_reward": 0.0734, "p_value": 0.0215,
                      "n_permutations": 10400000, "escapes_noise": True}},
            {"phase": "poi", "label": "ΔReward 升 PoI fuel(escapes gated)",
             "data": {"poi_eligible": True,
                      "attribution": "deepseek-chat + correctness-first"}},
        ],
    }


def _curated_data001() -> dict:
    """data_001 EduPulse 买方题闭环叙述脚手架 + 真跑缺省数值(11/11 过 QC)。"""
    return {
        "loop_id": "data_001_fde",
        "title": "data_001 FDE 买方题闭环(11/11 过 soul QC)",
        "source": "curated",
        "steps": [
            {"phase": "intake",
             "label": "买方题 intake(EduPulse 学生学业预测系统·4 真附件)",
             "data": {"task_uid": "data_001", "level": "L2", "attachments": 4}},
            {"phase": "qc_checklist", "label": "soul checklist_scorer 逐项判(11 项·含 veto)",
             "data": {"items": 11, "veto_items": ">=1"}},
            {"phase": "verdict", "label": "verdict 落库",
             "data": {"overall_pass": True, "veto_failed": False,
                      "score": 1.0, "source": "soul"}},
            {"phase": "poi", "label": "PoI credit(外部买方接收信号)",
             "data": {"credited": True}},
        ],
    }


def _set_step(loop: dict, phase: str, patch: dict) -> None:
    """把真实 DB 数值覆盖进指定 phase 的 step.data(就地·只覆盖给定键)。"""
    for step in loop["steps"]:
        if step["phase"] == phase:
            step["data"].update(patch)
            return


def _radix_from_db(db) -> dict | None:
    """从 fde_rsi_deltas(radix_sort 最新行)装配 radix 回放 · 失败返 None。"""
    try:
        from models.fde_rsi_delta import FdeRsiDelta
        row = (
            db.query(FdeRsiDelta)
            .filter(FdeRsiDelta.task_uid == "radix_sort")
            .order_by(FdeRsiDelta.created_at.desc(), FdeRsiDelta.id.desc())
            .first()
        )
        if row is None:
            return None
        loop = _curated_radix()
        loop["source"] = "db"
        if row.producer_model:
            _set_step(loop, "produce", {"producer": row.producer_model})
        _set_step(loop, "verdict_baseline", {"bare_mean": row.bare_mean})
        _set_step(loop, "reward", {"grounded_mean": row.grounded_mean,
                                   "delta_reward": row.delta_reward})
        _set_step(loop, "escapes_judgment",
                  {"delta_reward": row.delta_reward, "p_value": row.p_value,
                   "escapes_noise": bool(row.escapes_noise)})
        _set_step(loop, "poi", {"poi_eligible": bool(row.escapes_noise)})
        return loop
    except Exception:  # noqa: BLE001 — fail-soft 回退 curated
        return None


def _data001_from_db(db) -> dict | None:
    """从 fde_verdicts(data_001 最新行)装配 FDE 回放 · 失败返 None。"""
    try:
        from models.fde_verdict import FdeVerdict
        row = (
            db.query(FdeVerdict)
            .filter(FdeVerdict.task_uid == "data_001")
            .order_by(FdeVerdict.created_at.desc(), FdeVerdict.id.desc())
            .first()
        )
        if row is None:
            return None
        loop = _curated_data001()
        loop["source"] = "db"
        _set_step(loop, "verdict",
                  {"overall_pass": bool(row.overall_pass),
                   "veto_failed": bool(row.veto_failed),
                   "score": row.score, "source": row.source})
        _set_step(loop, "poi", {"credited": bool(row.overall_pass)})
        return loop
    except Exception:  # noqa: BLE001 — fail-soft 回退 curated
        return None


def build_loop_replays(db=None) -> list[dict]:
    """返两条闭环回放 · 每个 step = {phase, label, data}。

    db 给定 → 关键数值从真实表装配(source=db);否则/行缺/异常 → curated 回退。
    """
    radix = (_radix_from_db(db) if db is not None else None) or _curated_radix()
    data001 = (_data001_from_db(db) if db is not None else None) or _curated_data001()
    return [radix, data001]
