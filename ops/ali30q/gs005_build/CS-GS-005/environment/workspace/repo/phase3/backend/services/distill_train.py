"""齿轮⑦ 蒸馏训练/eval 纯逻辑(2026-06-22)· 中心环终点(从没跑过的硬事)。

无 torch/GPU 依赖·本地可 TDD。真训练/推理在 scripts/distill_qlora.py / distill_eval.py
(import torch/peft·on T4·gated)。本模块 = SFT 格式化 + 分数 delta + 证/杀判定逻辑。

可证伪判据(北极星 forcing function):蒸馏 7B held-out 分数 vs base 7B。
win_rate_vs_base 显著 > 0.5 + 正 uplift = 蒸馏破墙(PROVEN);≤0.5 = KILLED;中间/小样本 = INCONCLUSIVE。
"""
from __future__ import annotations

from typing import Optional

_SFT_TEMPLATE = (
    "### Instruction:\n{instruction}\n\n"
    "### Problem:\n{input}\n\n"
    "### Solution:\n{output}"
)


def format_sft_example(sample: dict) -> str:
    """蒸馏样本(instruction/input/output)→ SFT 训练文本(目标解在末尾)。"""
    return _SFT_TEMPLATE.format(
        instruction=(sample.get("instruction") or "").strip(),
        input=(sample.get("input") or "").strip(),
        output=(sample.get("output") or "").strip(),
    )


def build_sft_texts(rows: list[dict]) -> list[str]:
    """A 类燃料 jsonl rows → SFT 训练文本列表。"""
    return [format_sft_example(r) for r in rows]


_EPS = 1e-9
_NEAR_FRAC = 0.8   # distilled 达 base 的 ≥80% = "接近"(部分泛化探测·6/23 加)


def compute_score_delta(per_task: list[dict]) -> dict:
    """held-out per-task 分数(distilled/base/doubao)→ 增量度量(连续·ALE 友好)。

    per_task 每项:``{task_id, distilled, base, doubao}``(连续分数)。
    win_rate = 蒸馏严格高于对照的题占比;mean_rel_uplift = 相对 base 的平均相对提升。

    🔴 graded 信号(6/23 加·held-out KILLED 教训):binary win_rate 把"distilled 产垃圾
    0 分"和"distilled 产有效但分低"都记成 0,看不出早期/部分泛化趋势。补 3 个连续信号:
    - ``distilled_valid_rate``:distilled 产出有效解(分>0)的题占比 = 最早泛化信号
      (held-out KILLED 时=0 → distilled 啥都没产;若后续 run 它涨 → 开始泛化·即便 win<0.6)。
    - ``base_valid_rate``:base 同口径(对照·题本身可解性)。
    - ``near_base_rate``:在 base>0 的题里·distilled 达 base ≥80% 的占比 = 部分泛化
      (接近 base 但没赢·binary 漏掉)。无 base>0 题 → 0。
    """
    n = len(per_task)
    if n == 0:
        return {"n": 0, "win_rate_vs_base": 0.0, "win_rate_vs_doubao": 0.0,
                "mean_rel_uplift_vs_base": 0.0,
                "distilled_mean": 0.0, "base_mean": 0.0, "doubao_mean": 0.0,
                "distilled_valid_rate": 0.0, "base_valid_rate": 0.0, "near_base_rate": 0.0}

    wins_base = wins_doubao = 0
    d_valid = b_valid = near = base_pos = 0
    rel_uplifts = []
    sd = sb = sdb = 0.0
    for t in per_task:
        d = float(t.get("distilled") or 0.0)
        b = float(t.get("base") or 0.0)
        db = float(t.get("doubao") or 0.0)
        sd += d; sb += b; sdb += db
        if d > b:
            wins_base += 1
        if d > db:
            wins_doubao += 1
        if d > 0:
            d_valid += 1
        if b > 0:
            b_valid += 1
            base_pos += 1
            if d >= b * _NEAR_FRAC:          # 接近或超过 base(仅 base>0 题有意义)
                near += 1
        rel_uplifts.append((d - b) / max(abs(b), _EPS))

    return {
        "n": n,
        "win_rate_vs_base": round(wins_base / n, 4),
        "win_rate_vs_doubao": round(wins_doubao / n, 4),
        "mean_rel_uplift_vs_base": round(sum(rel_uplifts) / n, 4),
        "distilled_mean": round(sd / n, 4),
        "base_mean": round(sb / n, 4),
        "doubao_mean": round(sdb / n, 4),
        "distilled_valid_rate": round(d_valid / n, 4),
        "base_valid_rate": round(b_valid / n, 4),
        "near_base_rate": round(near / base_pos, 4) if base_pos else 0.0,
    }


def prove_or_kill_verdict(
    delta: dict,
    min_win_rate: float = 0.6,
    min_uplift: float = 0.05,
    min_n: int = 20,
) -> str:
    """forcing function 决策门:PROVEN / KILLED / INCONCLUSIVE(诚实·不被小样本骗)。"""
    if delta.get("n", 0) < min_n:
        return "INCONCLUSIVE"
    win = delta.get("win_rate_vs_base", 0.0)
    uplift = delta.get("mean_rel_uplift_vs_base", 0.0)
    if win >= min_win_rate and uplift >= min_uplift:
        return "PROVEN"
    if win <= 0.5:
        return "KILLED"
    return "INCONCLUSIVE"


# ── held-out 设计(首证·从 A 类 split·同分布甜点题) ──────────────────────

def split_train_heldout(samples: list[dict], heldout_frac: float = 0.3,
                        min_heldout: int = 3, max_heldout: int = 6):
    """A 类燃料 → (train, held_out)。首证 held-out 用同分布甜点题(非难题=测不出 delta)。

    确定性(按 meta.task_id 排序·可复现·非随机)。held-out 数 = clamp(round(frac·n),
    [min,max])·至少留 1 train。~12 A 类 → 8 train + 4 held-out。
    🔴 首证小样本:held-out 4-6 条 = 方向性证据(看 delta 正负)·非严格统计显著·
    distill_eval --min-n 应=held-out 数·PROVEN 需后续扩量确认。
    """
    srt = sorted(samples, key=lambda s: s.get("meta", {}).get("task_id", ""))
    n = len(srt)
    n_held = max(min_heldout, min(max_heldout, round(n * heldout_frac)))
    n_held = min(n_held, max(0, n - 1))    # 至少留 1 train
    return srt[n_held:], srt[:n_held]      # train, held_out


def held_out_eval_record(sample: dict) -> dict:
    """A 类 sample(instruction/input/output/meta)→ distill_eval held-out 格式。

    held-out 用 A 类题本身(problem=input·doubao_score 从 meta)·测 distilled vs base
    在这些甜点题上谁分高(base 部分会·distilled 学了 A 类应更会=delta 显蒸馏效果)。
    """
    meta = sample.get("meta", {})
    return {
        "task_id": meta.get("task_id"),
        "kind": meta.get("kind") or meta.get("benchmark") or "ale",
        "problem_statement": sample.get("input", ""),
        "doubao_score": float(meta.get("doubao_score") or 0.0),
    }


# ── LOO / k-fold 交叉验证(稀缺 A 类燃料榨干 held-out 信号·方向 B 立即解锁) ──

def cv_folds(samples: list[dict], k: Optional[int] = None):
    """LOO / k-fold 交叉验证折——稀缺料下从 N 道 A 类榨出 N(或 k)个 held-out 评测。

    单 split(50/50)只给 1 个 held-out 评测、且浪费一半料训练;CV 让每道题都既当过
    训练又当过 held-out·N 折聚合 = 信号强 N 倍(scarce-fuel 首证关键)。

    k=None → leave-one-out(k=N·每折留 1·最大信号·N 次重训最贵)。
    k=int  → k-fold(每折留 ~N/k·k 次重训·折中成本)。
    跨步分配(``srt[i::k]``)→ 折均衡 + 每样本恰好被留出一次。确定性(按 meta.task_id 排序)。
    返回 ``[(train, held), ...]``。N<2 → ``[]``(无法 CV)。

    🔴 成本:每折一次完整重训(QLoRA)。LOO N=6 ≈ 6 次重训。首证可先 k=3 折中·
    确认方向后再 LOO 加精度。
    """
    srt = sorted(samples, key=lambda s: s.get("meta", {}).get("task_id", ""))
    n = len(srt)
    if n < 2:
        return []
    k = n if k is None else max(2, min(k, n))
    folds = []
    for i in range(k):
        held = srt[i::k]                                   # 跨步取·均衡
        train = [s for j, s in enumerate(srt) if j % k != i]
        if held and train:
            folds.append((train, held))
    return folds


def aggregate_cv_results(fold_results: list[list[dict]]) -> dict:
    """各折 held-out per_task 结果 → 合并 → 整体 delta(N 个 held-out 评测聚合)。

    fold_results: ``[[per_task_row,...], ...]``(每折 distill_eval 的 held-out 评测行)。
    LOO 下 N 折共 N 个评测聚合 → ``prove_or_kill_verdict`` 的 n 自然达标(单 split 达不到)。
    """
    flat = [row for fold in fold_results for row in (fold or [])]
    return compute_score_delta(flat)
