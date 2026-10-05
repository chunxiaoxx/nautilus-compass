# -*- coding: utf-8 -*-
"""L3 正榜 Round 1 B 臂 runner(max_steps=50 判据演进版(mini-swe-agent 2.4.6 @ release a83fcae82d2a)。

双臂同题源:runtime/loop/_r181_board30/tasks.json(board30,Verified 分层 n=30,ENV 行题面)。
配置钉死(L3_HARNESS_BOARD_ROUND1_PREREG 采样参数第 5 条):temperature=0/top_p=1,
step_limit=50 双臂同(R177 smoke 预算信号+用户拍板 10/5);wall 3600s(随步数预算同步放宽,披露项);模板=mini 官方 config/default.yaml 原文(harness 本体,不改动)。
环境:LocalEnvironment(cwd=r81 worktree 池 checkout,与 A 臂同 repo 同 base_commit)。
smoke 不出 resolved%(判分=正榜独立工序);产物=轨迹+final patch+退出状态。

用法: %TEMP%/mini_venv/Scripts/python.exe b_runner.py [n题]
"""
import json
import os
import sys
import time
from pathlib import Path

# 网关=127.0.0.1 本地直连;socks 代理 env 会毁 litellm 底层 httpx(缺 socksio,第 N 次复发)
for _k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
    os.environ.pop(_k, None)
os.environ["NO_PROXY"] = "*"

BASE = Path(__file__).resolve().parent
POOL = Path("C:/Users/chunx/nautilus-v5/tools/uni_agent_bridge/e5_repos")
import minisweagent  # noqa: E402
from minisweagent.agents.default import AgentConfig, DefaultAgent  # noqa: E402
from minisweagent.environments.local import (  # noqa: E402
    LocalEnvironment,
    LocalEnvironmentConfig,
)
from minisweagent.models.litellm_model import LitellmModel  # noqa: E402
import yaml  # noqa: E402

sys.path.insert(0, "C:/Users/chunx/nautilus-v5/tools/uni_agent_bridge")
from r81_env import collect_final_patch, ensure_worktree  # noqa: E402

DEFAULT_YAML = Path(minisweagent.__file__).parent / "config" / "default.yaml"


def run_one(t, agent_yaml):
    idx = t["idx"]
    outdir = BASE / "board_b" / f"task_{idx}"
    outdir.mkdir(parents=True, exist_ok=True)
    wt = ensure_worktree(
        {"repo": t["repo"], "base_commit": t["base_commit"], "expect": "patch"},
        POOL, f"l3r1b_{idx}",
    )
    if wt is None:
        rec = {"idx": idx, "instance_id": t["instance_id"], "status": "deferred_env_fail"}
        (outdir / "result.json").write_text(
            json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[B {idx}] {t['instance_id']} deferred_env_fail", flush=True)
        return rec
    env = LocalEnvironment(
        config_class=LocalEnvironmentConfig, cwd=str(wt),
        env={"PAGER": "cat", "MANPAGER": "cat", "LESS": "-R",
             "PIP_PROGRESS_BAR": "off", "TQDM_DISABLE": "1"},
        timeout=300,
    )
    model = LitellmModel(
        model_name="openai/nautilus-v5",
        model_kwargs={"api_base": "http://127.0.0.1:18001/v1",
                      "api_key": "vb-local-truth",
                      "temperature": 0, "top_p": 1},
        cost_tracking="ignore_errors",
    )
    agent = DefaultAgent(
        model=model, env=env, config_class=AgentConfig,
        system_template=agent_yaml["system_template"],
        instance_template=agent_yaml["instance_template"],
        step_limit=50, cost_limit=0.0,
        wall_time_limit_seconds=3600,
        output_path=str(outdir / "trajectory.json"),
    )
    t0 = time.time()
    err = ""
    extra = {}
    try:
        extra = agent.run(task=t["task_text"])
    except Exception as ex:  # noqa: BLE001 — 单题失败不塌整批
        err = f"{type(ex).__name__}: {ex}"
    patch = collect_final_patch(wt)
    rec = {
        "idx": idx, "instance_id": t["instance_id"],
        "wall_s": round(time.time() - t0, 1),
        "exit_status": extra.get("exit_status", "") if extra else "",
        "n_model_calls": agent.n_calls,
        "cost": round(agent.cost, 4),
        "patch_nonempty": bool(patch), "patch_chars": len(patch),
        "exit_error": err[:300],
        "status": "ok" if not err else "error",
    }
    (outdir / "result.json").write_text(
        json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    (outdir / "patch.diff").write_text(patch, encoding="utf-8")
    print(f"[B {idx}] {t['instance_id']} {rec['status']} "
          f"exit={rec['exit_status'] or 'EXC'} wall={rec['wall_s']}s "
          f"steps={rec['n_model_calls']} patch={rec['patch_chars']}ch {err[:80]}",
          flush=True)
    return rec


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 10
    tasks = json.loads((BASE / "tasks.json").read_text(encoding="utf-8"))[:n]
    agent_yaml = yaml.safe_load(DEFAULT_YAML.read_text(encoding="utf-8"))["agent"]
    print(f"B-arm round1 start: {len(tasks)} tasks, template={DEFAULT_YAML.name}", flush=True)
    for t in tasks:
        run_one(t, agent_yaml)
    print("B-arm round1 done", flush=True)


if __name__ == "__main__":
    main()
