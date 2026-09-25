# -*- coding: utf-8 -*-
"""BC1 发布前外部基线:开源记忆产品双臂测试(2026-09-25 立).

臂 A direct: backbone LLM 直接作答(题面+数据全给,不过记忆系统)。
臂 B mem0:   题目数据写入 mem0(走其自带事实抽取管线=其写入门被测)
             → 以题面检索 → backbone 仅凭检索到的记忆作答。
两臂差值 = 记忆管线保真度的实测。

纪律(报数纪律适用):
- 本脚本只读 decision_set 的 check.spec.target(答案槽位),
  绝不读 expected 真值字段;判分一律走公开 verify_bc1.py。
- 模型返回 null 标记 = 弃答 → 该 qid 不写入 answers(grader 计 U,
  U 不充正分)。全 raw 落 raw_responses.jsonl 供第三方复算。

用法:
  python run_baseline.py                       # 双臂全量(public 18),默认 MiniMax-M3
  python run_baseline.py --limit 2             # 冒烟
  python run_baseline.py --arm direct          # 单臂
  python run_baseline.py --provider ark --model doubao-seed-2-1-pro-260915
提供商:--provider minimax(默认;读 MINIMAX_API_KEY 或本机 MiniMax Code CLI
的 OAuth token)| ark(读 ARK_API_KEY 或 arkcli config;注意 coding plan
月额度 9/28 23:59 才重置)。向量一律本地 bge-m3(零配额依赖)。
"""
import argparse
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
EXAM = HERE.parent / "selftest_exam_paper_v2.json"
DECISION_SET = HERE.parent / "decision_set.json"
GRADER = HERE.parent / "verify_bc1.py"
ARK_BASE = "https://ark.cn-beijing.volces.com/api/coding/v3"
MINIMAX_BASE = "https://agent.minimax.cn/mavis/api/v1/llm/v1"
MINIMAX_AUTH = (Path.home() /
                ".minimax/auth/prod/cn/mcode-public/auth.json")
DEFAULT_MODEL = "doubao-seed-2-1-pro-260915"
EMB_LOCAL = "BAAI/bge-m3"  # 1024 维,本地 HF 缓存已备,零配额依赖

SYS = ("你是 BC1 考试的考生。根据题目要求与所给材料作答。"
       "严格只输出一个 JSON 对象,不要输出任何其他文字、解释或"
       " markdown 围栏。")
SLOT_INSTR = {
    "answer_json": ('输出格式:{"answer_json": <合法 JSON 值>}。'
                    '无法确定则输出 {"answer_json": null}(计弃答)。'),
    "answer": ('输出格式:{"answer": "<字符串>"}。'
               '无法确定则输出 {"answer": null}(计弃答)。'),
}


def minimax_key() -> str:
    """优先 env MINIMAX_API_KEY;否则读 MiniMax Code CLI 的 OAuth accessToken
    (用户本机已登录;过期则提示用户开一次 App 刷新)。"""
    import os
    k = os.environ.get("MINIMAX_API_KEY")
    if k:
        return k
    d = json.loads(MINIMAX_AUTH.read_text(encoding="utf-8"))
    rec = next(iter(d["records"].values()))
    if rec["expiresAtMs"] / 1000 < time.time():
        raise SystemExit("MiniMax token 已过期——请开一次 MiniMax Code App"
                         "(自动刷新)或设 MINIMAX_API_KEY")
    return rec["accessToken"]


def ark_key() -> str:
    import os
    k = os.environ.get("ARK_API_KEY")
    if k:
        return k
    import yaml
    cfg = yaml.safe_load((Path.home() / ".arkcli/config.yaml")
                         .read_text(encoding="utf-8"))
    prof = cfg["profiles"][cfg["default_profile"]]
    return prof["api_key"]


def provider_cfg(name: str):
    if name == "minimax":
        return MINIMAX_BASE, minimax_key(), "MiniMax-M3"
    return ARK_BASE, ark_key(), DEFAULT_MODEL


def ark_post(base: str, path: str, payload: dict, key: str, tries: int = 3):
    body = json.dumps(payload).encode()
    for i in range(tries):
        try:
            req = urllib.request.Request(
                base + path, data=body,
                headers={"Authorization": f"Bearer {key}",
                         "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.load(r)
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 ** (i + 1))


def chat(base: str, key: str, model: str, user: str) -> str:
    r = ark_post(base, "/chat/completions", {
        "model": model, "temperature": 0, "max_tokens": 4096,
        "messages": [{"role": "system", "content": SYS},
                     {"role": "user", "content": user}]}, key)
    return r["choices"][0]["message"]["content"]


def local_emb_dims() -> int:
    """本地 bge-m3 维度探测(首次加载约 10s,此后 HF 缓存命中)。"""
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer(EMB_LOCAL)
    return int(m.get_sentence_embedding_dimension())


def parse_answer(text: str, target: str):
    """模型输出 → (slot 值, 是否弃答)。剥围栏/抓首个 JSON 对象。"""
    t = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.M).strip()
    m = re.search(r"\{.*\}", t, flags=re.S)
    if not m:
        return None, True
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None, True
    val = obj.get(target)
    if val is None:
        return None, True
    if target == "answer" and not isinstance(val, str):
        val = json.dumps(val, ensure_ascii=False)
    return val, False


def load_items():
    exam = json.loads(EXAM.read_text(encoding="utf-8"))
    ds = json.loads(DECISION_SET.read_text(encoding="utf-8"))
    # 纪律:只取槽位字段,不读 expected
    targets = {it["qid"]: it["check"]["spec"]["target"]
               for it in ds["items"]}
    items = []
    for q in exam["items"]:
        qid = q["qid"]
        items.append({"qid": qid, "dim": q["dim"], "type": q["type"],
                      "prompt": q["prompt"], "inputs": q["inputs"],
                      "target": targets[qid]})
    return items


def make_memory(dims: int, qid: str, base: str, key: str, model: str):
    """每题独立 mem0 实例(隔离):qdrant 本地路径+提供商 LLM+本地 bge 向量。"""
    from mem0 import Memory
    cfg = {
        "vector_store": {"provider": "qdrant", "config": {
            "collection_name": f"bc1_{qid.replace('-', '_')}",
            "path": str(HERE / "qdrant_local" / qid),
            "embedding_model_dims": dims}},
        "llm": {"provider": "openai", "config": {
            "model": model, "api_key": key,
            "openai_base_url": base}},
        "embedder": {"provider": "huggingface", "config": {
            "model": EMB_LOCAL}},
    }
    return Memory.from_config(cfg)


def run_direct(item, base, key, model, raw_log):
    slot = SLOT_INSTR[item["target"]]
    user = (f"题目:\n{item['prompt']}\n\n材料:\n"
            f"{json.dumps(item['inputs'], ensure_ascii=False)}\n\n{slot}")
    out = chat(base, key, model, user)
    raw_log.append({"qid": item["qid"], "arm": "direct", "out": out})
    return parse_answer(out, item["target"])


def run_mem0(item, base, key, model, dims, raw_log):
    mem = make_memory(dims, item["qid"], key, model)
    payload = json.dumps(item["inputs"], ensure_ascii=False)
    # 写入:mem0 自带抽取管线(infer=True=其写入门本体被测)
    chunks = [payload[i:i + 6000] for i in range(0, len(payload), 6000)]
    for c in chunks:
        mem.add(c, user_id="exam")
    hits = mem.search(item["prompt"][:2000], user_id="exam")
    hits = hits.get("results", hits) if isinstance(hits, dict) else hits
    mems = [h.get("memory", str(h)) if isinstance(h, dict) else str(h)
            for h in hits]
    raw_log.append({"qid": item["qid"], "arm": "mem0", "stage": "retrieved",
                    "out": mems})
    slot = SLOT_INSTR[item["target"]]
    user = (f"以下是记忆系统就本题检索到的全部内容:\n"
            f"{json.dumps(mems, ensure_ascii=False)}\n\n"
            f"题目:\n{item['prompt']}\n\n"
            f"只能基于上述检索内容作答;内容不足即弃答。\n{slot}")
    out = chat(base, key, model, user)
    raw_log.append({"qid": item["qid"], "arm": "mem0", "stage": "answer",
                    "out": out})
    return parse_answer(out, item["target"])

def grade(answers_path: Path) -> str:
    """跑公开判分器。判分器副作用:每次运行重写 scorecard_public.json
    (正本=自测 18/18 那份)——快照后恢复,基线跑不得污染正本。"""
    canonical = GRADER.parent / "scorecard_public.json"
    saved = canonical.read_bytes() if canonical.exists() else None
    try:
        r = subprocess.run([sys.executable, str(GRADER), str(answers_path)],
                           capture_output=True, text=True, timeout=120)
        return (r.stdout or "") + (r.stderr or "")
    finally:
        if saved is not None:
            canonical.write_bytes(saved)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--arm", choices=["both", "direct", "mem0"],
                    default="both")
    ap.add_argument("--provider", choices=["minimax", "ark"],
                    default="minimax")
    ap.add_argument("--model", default="", help="覆盖提供商默认模型")
    a = ap.parse_args()

    items = load_items()
    if a.limit:
        items = items[:a.limit]
    base, key, model = provider_cfg(a.provider)
    if a.model:
        model = a.model
    raw_log = []
    dims = local_emb_dims() if a.arm in ("both", "mem0") else 0

    for arm in (["direct", "mem0"] if a.arm == "both" else [a.arm]):
        answers = {}
        for it in items:
            try:
                if arm == "direct":
                    val, abstain = run_direct(it, base, key, model, raw_log)
                else:
                    val, abstain = run_mem0(it, base, key, model,
                                            dims, raw_log)
            except Exception as e:
                raw_log.append({"qid": it["qid"], "arm": arm,
                                "stage": "error", "out": repr(e)[:500]})
                val, abstain = None, True
            if not abstain:
                answers[it["qid"]] = {it["target"]: val}
            print(f"[{arm}] {it['qid']}: "
                  f"{'ABSTAIN/ERR' if abstain else 'answered'}",
                  flush=True)
        apath = HERE / f"answers_{arm}.json"
        apath.write_text(json.dumps(answers, ensure_ascii=False, indent=1),
                         encoding="utf-8")
        scorecard = grade(apath)
        (HERE / f"scorecard_{arm}.txt").write_text(scorecard,
                                                   encoding="utf-8")
        print(f"=== {arm} ===\n{scorecard}", flush=True)

    (HERE / "raw_responses.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in raw_log),
        encoding="utf-8")
    print("raw archived:", len(raw_log), "rows")


if __name__ == "__main__":
    main()
