#!/usr/bin/env python3
"""阿里30题·B批判分矩阵跑批器 v2(macmini · 配置驱动 · 2026-10-24)

相对 v1(ali_matrix_runner.sh)的三处改动,全部来自实测:
  ① 去掉无条件 sleep 20 —— 那是按"relay 12req/min"一刀切,慢通道(百炼单次 15 分钟、
     ai80 单次 1.5 分钟)白等 20s;v2 按通道给间隔(relay 的 glm 6s,其余 0)
  ② 按通道并发 —— v1 全串行,13 题 × 5 模型 × 4 run = 260 次,按真实耗时根本跑不完
     (opus/百炼各要 1-2 分钟/15 分钟);v2 用 relay_capacity.json 的 max_concurrency
  ③ kimi-k3 → kimi-k3-ark —— relay 侧 kimi 周额度耗尽,每次 0.1s 秒拒 429 且会删掉
     旧结果反复重跑;火山 Agent Plan 直连已实测可用

用法:
  python3 ops/ali30q/ali_matrix_runner_v2.py --dry-run
  python3 ops/ali30q/ali_matrix_runner_v2.py --items CS-010 --models kimi-k3-ark
  python3 ops/ali30q/ali_matrix_runner_v2.py --serial        # 强制串行回退
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_CONFIG = HERE / "relay_capacity.json"
CS = Path(os.environ.get(
    "CS_PATH",
    "~/Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/codesense")).expanduser()
LOG = Path(os.environ.get(
    "JUDGE_LOG", "~/Projects/nautilus-compass/ops/ali30q/matrix_run.log")).expanduser()
PY = str(CS / ".venv-judge" / "bin" / "python")


def log(msg: str) -> None:
    line = f"[{time.strftime('%m-%d %H:%M')}] {msg}"
    print(line, flush=True)
    try:
        with LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


class RateGate:
    """每模型一个闸:并发上限 + 最小间隔(上游限速通道靠它错峰)。"""

    def __init__(self, max_concurrency: int, min_interval: float):
        self.sem = threading.Semaphore(max(1, int(max_concurrency)))
        self.min_interval = max(0.0, float(min_interval))
        self.lock = threading.Lock()
        self.last = 0.0

    def __enter__(self):
        self.sem.acquire()
        with self.lock:
            wait = self.last + self.min_interval - time.time()
            if wait > 0:
                time.sleep(wait)
            self.last = time.time()
        return self

    def __exit__(self, *exc):
        self.sem.release()
        return False


def probe_relay(cfg: dict) -> int:
    """探活:有 HTTP 响应=活着(401 也算),只有连不上才算宕。"""
    base = cfg["judge_models"].get("gpt-6-astra", {}).get("base_url", "").rstrip("/")
    if not base:
        return 0
    headers = {}
    tok = os.environ.get("RELAY_API_KEY", "")
    if tok:
        headers["Authorization"] = "Bearer " + tok
    try:
        req = urllib.request.Request(base + "/models", method="GET", headers=headers)
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def ensure_repo(item: str) -> bool:
    """题目就绪检查 + 考试副本物化(v1 的同一段逻辑,搬进 python)。"""
    item_dir = CS / "items" / item
    if not (item_dir / "task.toml").exists():
        return False
    repo = item_dir / "environment" / "workspace" / "repo"
    if not repo.exists():
        bak = item_dir / "environment" / "workspace" / "repo_bak"
        if bak.exists():
            shutil.copytree(bak, repo)
        else:
            return False
    return True


def result_ok(path: Path) -> bool:
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("score") is not None
    except Exception:
        return False


def run_one(item: str, model: str, run: int, gate: RateGate, dry: bool) -> None:
    res = CS / "items" / item / "_s5" / f"{model}_run{run}_result.json"
    if res.exists():
        if result_ok(res):
            log(f"{item} × {model} × run{run} 已有有效读数 · 跳过")
            return
        res.unlink()
        log(f"{item} × {model} × run{run} 旧结果无 score · 删除重跑")
    if dry:
        log(f"[dry] {item} × {model} × run{run} (并发上限={gate.sem._value}, 间隔={gate.min_interval}s)")
        return
    log(f"{item} × {model} × run{run} 开考")
    with gate:
        try:
            proc = subprocess.run([PY, "tools/model_solve.py", item, "--model", model, "--run", str(run)],
                                  cwd=str(CS), capture_output=True, text=True, timeout=2400)
            tail = (proc.stdout or "").strip().splitlines()[-2:]
            log(f"{item} × {model} × run{run} 结束 rc={proc.returncode} {' | '.join(tail)[:260]}")
        except subprocess.TimeoutExpired:
            log(f"{item} × {model} × run{run} 超时(>2400s) · 记为失败")


def merge_to_canonical(canonical: str, channel: str) -> int:
    """把通道结果归并到正典模型名(不覆盖已有有效读数,只填空缺)。

    背景:模型通道换过(ark 替代 relay 的 k3),但判分矩阵按文件名前缀分组、
    DOMESTIC 白名单里写的是正典名 ⇒ 通道名会成为独立列被整体丢弃。
    归并时在 JSON 里保留 channel 字段,通道来源可追溯。
    """
    filled = archived = 0
    for s5 in sorted((CS / "items").glob("*/_s5")):
        for src in sorted(s5.glob(f"{channel}_run*_result.json")):
            m = re.match(rf"{re.escape(channel)}_run(\d+)_result\.json$", src.name)
            if not m:
                continue
            run = m.group(1)
            try:
                d = json.loads(src.read_text(encoding="utf-8"))
            except Exception:
                continue
            if d.get("score") is None:
                continue
            tgt = s5 / f"{canonical}_run{run}_result.json"
            if tgt.exists():
                try:
                    old = json.loads(tgt.read_text(encoding="utf-8"))
                except Exception:
                    old = {}
                if old.get("score") is not None:
                    src.rename(s5 / f"{src.name}.merged-{time.strftime('%Y%m%d')}")
                    archived += 1
                    continue
            d["model"] = canonical
            d["channel"] = channel
            d["channel_note"] = f"通道 {channel} 归并到正典模型 {canonical}(通道来源留痕)"
            tgt.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
            src.rename(s5 / f"{src.name}.merged-{time.strftime('%Y%m%d')}")
            filled += 1
            archived += 1
    if filled or archived:
        log(f"归并 {channel} → {canonical}: 填空 {filled} · 归档 {archived}")
    return filled


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(DEFAULT_CONFIG))
    ap.add_argument("--items", default="", help="逗号分隔;缺省用配置")
    ap.add_argument("--models", default="", help="逗号分隔(channel key);缺省用配置顺序")
    ap.add_argument("--runs", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--serial", action="store_true", help="强制串行(回退)")
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    g, jm = cfg["global"], cfg["judge_models"]
    items = [s for s in (args.items.split(",") if args.items else g["items"]) if s]
    models = [s for s in (args.models.split(",") if args.models else list(jm)) if s]
    runs = args.runs or g["per_item_runs"]

    relay = probe_relay(cfg)
    log(f"中转站探活: {relay or '000(连不上)'}")
    if relay == 0:
        keep = [m for m in models if jm[m].get("endpoint") != "relay"]
        log(f"中转站连不上 → 只跑非 relay 通道: {keep}")
        models = keep

    skipped = [m for m in models if jm[m].get("status") == "unavailable"]
    if skipped:
        models = [m for m in models if m not in skipped]
        log(f"🔴 不可用模型(留待补跑): {skipped}")

    for m in models:
        spec = jm[m]
        conc = 1 if args.serial else max(1, int(spec.get("max_concurrency", 1)))
        gate = RateGate(conc, spec.get("min_interval_s", 0))
        for item in items:
            if not ensure_repo(item):
                log(f"[{item}] 未就绪(缺 task.toml 或 repo/repo_bak)· 跳过")
                continue
            tasks = [(item, r) for r in range(runs)]
            log(f"▶ {m} × {item}: {len(tasks)} 个读数 · 并发={conc} · 间隔={spec.get('min_interval_s', 0)}s")
            if conc == 1:
                for it, r in tasks:
                    run_one(it, m, r, gate, args.dry_run)
            else:
                with ThreadPoolExecutor(max_workers=conc) as ex:
                    list(ex.map(lambda t: run_one(t[0], m, t[1], gate, args.dry_run), tasks))
        canon = spec.get("canonical_model")
        if canon and canon != m:
            merge_to_canonical(canon, m)
        n = len(list((CS / "items" / item / "_s5").glob(f"{m}_run*_result.json"))) if item else 0
        log(f"[{item}] {m} 读数: {n}")
    log("本轮结束" + ("(dry-run,未发起模型调用)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
