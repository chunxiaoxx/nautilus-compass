# -*- coding: utf-8 -*-
"""Infistar API 网关计量 probe runner · 预注册判据档的执行器。

判据正本:docs/metering/INFISTAR_GATEWAY_METERING_PLAN_20260930.md(冻结,只许更严)
用法:
  run:  python tools/infistar_meter.py run [--config PATH] [--dryrun]
  daily: python tools/infistar_meter.py daily [--date YYYYMMDD]   # 汇总当日 jsonl
config(runtime/infistar_meter/config.json, key 走 env 不落盘):
  {"base_url": "...", "models": ["glm-5.3-flash", ...], "fingerprint_file": "..."}
env: INFISTAR_API_KEY(网关)/ 官方对照腿 key 沿用现有 .cache env
"""
from __future__ import annotations
import argparse, json, os, statistics, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METER_DIR = ROOT / "runtime" / "infistar_meter"
DEFAULT_CFG = METER_DIR / "config.json"
FP_FILE = METER_DIR / "fingerprints.json"

# probe 固定集(J6 结构化与 J1/J2 同轮采集;J3 指纹题库外置)
CAP_ANCHORS = [  # J7 能力锚(30 天同题测漂移)
    {"id": "cap-math-1", "prompt": "Compute 17*23+sqrt(144). Reply with just the number."},
    {"id": "cap-code-1", "prompt": "Write a Python one-liner reversing words in a string. Code only."},
    {"id": "cap-instr-1", "prompt": "In exactly 5 words, explain what an API gateway does."},
]
STRUCTURED = {  # J6
    "id": "struct-choice-1",
    "prompt": ("Grade this trajectory: 'fixed bug, tests 6/6'. Reply ONLY JSON: "
               '{"verdict":"pass|fail|insufficient_evidence"}'),
}
LONGCTX_NOTE = ("Long-context probe: the key is at the END of this message. " * 2000
                + " KEY: the secret word is kumquat-7741. What is the secret word?")


def _load_cfg(path: Path) -> dict:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "base_url": "https://infistar.ai/v1",  # 待对方文档确认
            "models": ["REPLACE_WITH_MODEL_LIST"],
            "fingerprint_file": str(FP_FILE),
        }, indent=1), encoding="utf-8")
        raise SystemExit(f"config 模板已生成 {path},请填 base_url/models 后重跑")
    return json.loads(path.read_text(encoding="utf-8"))


def _fps(cfg: dict) -> dict:
    f = Path(cfg.get("fingerprint_file") or FP_FILE)
    if not f.exists():
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps({
            "_note": "J3 指纹题库:每模型 identity/knowledge/style 三类,拿到模型清单后填",
            "REPLACE_WITH_MODEL_LIST": {
                "identity": ["What model are you? Include version if known."],
                "knowledge": ["What is your training data cutoff date?"],
            },
        }, ensure_ascii=False, indent=1), encoding="utf-8")
    return json.loads(f.read_text(encoding="utf-8"))


def _chat(base_url: str, model: str, prompt: str, key: str, timeout: int = 120):
    """OpenAI 兼容 chat 调用。返回(status, latency, usage, reply_text)。"""
    t0 = time.time()
    try:
        req = urllib.request.Request(
            f"{base_url.rstrip('/')}/chat/completions",
            data=json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                             "max_tokens": 1024}).encode(),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        r = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
        lat = round(time.time() - t0, 2)
        msg = (r.get("choices") or [{}])[0].get("message", {}).get("content", "")
        return "ok", lat, r.get("usage", {}), msg
    except Exception as e:
        return f"err:{type(e).__name__}", round(time.time() - t0, 2), {}, str(e)[:200]


def cmd_run(a) -> int:
    cfg = _load_cfg(Path(a.config))
    key = os.environ.get("INFISTAR_API_KEY", "")
    if not a.dryrun and not key:
        raise SystemExit("INFISTAR_API_KEY 未设置")
    fps = _fps(cfg)
    METER_DIR.mkdir(parents=True, exist_ok=True)
    raw = METER_DIR / f"raw_{time.strftime('%Y%m%d_%H')}.jsonl"
    n_ok = n_all = 0
    for model in cfg["models"]:
        probes = [(p["id"], p["prompt"]) for p in CAP_ANCHORS] + \
                 [(STRUCTURED["id"], STRUCTURED["prompt"])] + \
                 [(f"fp-{k}", p) for k in ("identity", "knowledge", "style")
                  for p in (fps.get(model, {}).get(k) or [])[:3]]
        for pid, prompt in probes:
            if a.dryrun:
                print(f"[dry] {model} {pid}"); continue
            status, lat, usage, reply = _chat(cfg["base_url"], model, prompt, key)
            n_all += 1; n_ok += status == "ok"
            rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "model": model, "probe": pid, "status": status, "latency_s": lat,
                   "usage": usage, "reply_head": reply[:300]}
            with open(raw, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"{model} {pid} {status} {lat}s")
    if not a.dryrun:
        print(f"\nround: {n_ok}/{n_all} ok -> {raw.name}")
    return 0


def cmd_daily(a) -> int:
    date = a.date or time.strftime("%Y%m%d")
    rows = []
    for f in sorted(METER_DIR.glob(f"raw_{date}_*.jsonl")):
        rows += [json.loads(ln) for ln in f.read_text(encoding="utf-8").splitlines() if ln]
    if not rows:
        print(f"no raw for {date}"); return 1
    per = {}
    for r in rows:
        d = per.setdefault(r["model"], {"ok": 0, "all": 0, "lats": [], "errs": {}})
        d["all"] += 1; d["ok"] += r["status"] == "ok"
        (d["lats"] if r["status"] == "ok" else d["errs"]).append(r["latency_s"]) \
            if r["status"] == "ok" else d["errs"].update({r["status"]: d["errs"].get(r["status"], 0) + 1})
    out = {"date": date, "total": len(rows), "models": {}}
    for m, d in per.items():
        out["models"][m] = {
            "ok_rate": round(d["ok"] / d["all"], 4),
            "lat_p50": round(statistics.median(d["lats"]), 2) if d["lats"] else None,
            "lat_p95": round(sorted(d["lats"])[max(0, int(len(d["lats"]) * .95) - 1)], 2) if d["lats"] else None,
            "errors": d["errs"]}
    (METER_DIR / f"daily_{date}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run"); r.add_argument("--config", default=str(DEFAULT_CFG))
    r.add_argument("--dryrun", action="store_true"); r.set_defaults(fn=cmd_run)
    d = sub.add_parser("daily"); d.add_argument("--date"); d.set_defaults(fn=cmd_daily)
    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
