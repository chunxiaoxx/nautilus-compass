#!/usr/bin/env python3
"""状态栏 v3.1.0 自测:探针三级阴性对照 + 读数保持三例。全部用隔离的临时缓存/假 cwd,不碰线上缓存。

用法:python ops/hud_probe_selftest.py [--plugin <插件目录>] [--repo <compass 仓根>]
退出码 0 = 全部符合预期;非 0 = 有用例不符(逐条打印)。
"""
import argparse
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def strip(text):
    return ANSI.sub("", text or "")


def run_probe(plugin, cache, cwd, extra_env=None, mcp_json=None):
    env = dict(os.environ)
    env.pop("COMPASS_MCP_JSON", None)
    env.update(extra_env or {})
    if mcp_json:
        env["COMPASS_MCP_JSON"] = mcp_json
    proc = subprocess.run([sys.executable, os.path.join(plugin, "compass_hud_probe.py"), cache, cwd],
                          env=env, capture_output=True, timeout=90)
    if proc.returncode != 0:
        return {"state": "probe_exit_%d" % proc.returncode}
    tag = hashlib.md5(cwd.encode("utf-8", "replace")).hexdigest()[:8] if cwd else "nocwd"
    with open(cache, encoding="utf-8") as handle:
        return (json.load(handle) or {}).get(tag) or {}


def case_probe(plugin, repo, work):
    real = json.loads((pathlib.Path(repo) / ".mcp.json").read_text(encoding="utf-8"))
    real_url = real["mcpServers"]["nautilus-compass-cloud"]["url"]
    results = []

    empty = pathlib.Path(work) / "empty_cwd"
    empty.mkdir()
    # 回归:线上缓存是 v3.0.x 扁平旧格式(ts 的值是数字),首版 v3.1.0 探针在这里崩掉、不写结果。
    legacy = pathlib.Path(work) / "c0.json"
    legacy.write_text(json.dumps({"ts": 1795705100.316, "ok": False, "p95": 0, "ovl": False,
                                  "hits_today": 0}), encoding="utf-8")
    got = run_probe(plugin, str(legacy), str(empty))
    results.append(("探针·旧格式扁平缓存 → 迁移为分桶且不崩",
                    got.get("state") == "unconfigured", got.get("state")))
    got = run_probe(plugin, str(pathlib.Path(work) / "c1.json"), str(empty))
    results.append(("探针·未配置 → 报 unconfigured(不冒充未响应)",
                    got.get("state") == "unconfigured" and got.get("ok") is False, got.get("state")))

    bad_auth = pathlib.Path(work) / "bad_cwd"
    bad_auth.mkdir()
    (bad_auth / ".mcp.json").write_text(json.dumps({"mcpServers": {"nautilus-compass-cloud": {
        "type": "http", "url": real_url, "headers": {"Authorization": "Bearer invalid-token-for-selftest"}}}}), encoding="utf-8")
    got = run_probe(plugin, str(pathlib.Path(work) / "c2.json"), str(bad_auth))
    results.append(("探针·错令牌 → 报 auth", got.get("state") == "auth", got.get("state")))

    dead = pathlib.Path(work) / "dead_cwd"
    dead.mkdir()
    (dead / ".mcp.json").write_text(json.dumps({"mcpServers": {"nautilus-compass-cloud": {
        "type": "http", "url": "http://127.0.0.1:9/mcp/"}}}), encoding="utf-8")
    got = run_probe(plugin, str(pathlib.Path(work) / "c3.json"), str(dead))
    results.append(("探针·端点关闭 → 报 down", got.get("state") == "down", got.get("state")))

    got = run_probe(plugin, str(pathlib.Path(work) / "c4.json"), repo)
    results.append(("探针·真实配置 → ok,经 mcp-http",
                    got.get("ok") is True and got.get("via") == "mcp-http",
                    "%s/%s/%ss" % (got.get("state"), got.get("via"), got.get("latency_s"))))
    return results


def run_wrapper(python, plugin, payload, tag):
    spawn = os.path.join(os.path.expanduser("~"), ".claude", ".cache", "hud_out_cache.txt.%s.last_spawn" % tag)
    if os.path.exists(spawn):
        os.remove(spawn)
    # 该目录的 HUD 输出缓存若仍"新鲜"(<30s),wrapper 不会重渲染 → 上一例的画面会被误读成本例结果。
    hud_cache = os.path.join(os.path.expanduser("~"), ".claude", ".cache", "hud_out_cache.txt")
    if os.path.exists(hud_cache):
        with open(hud_cache, encoding="utf-8") as handle:
            data = json.load(handle)
        entry = data.get(payload["cwd"]) if isinstance(data, dict) else None
        if isinstance(entry, dict):
            data[payload["cwd"]] = dict(entry, ts=0)
            with open(hud_cache, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False)
    proc = subprocess.run([python, os.path.join(plugin, "compass_hud_wrapper.py")],
                          input=json.dumps(payload), capture_output=True, text=True,
                          encoding="utf-8", timeout=40)
    in_path = os.path.join(os.path.expanduser("~"), ".claude", ".cache", "hud_out_cache.txt.%s.in" % tag)
    time.sleep(2.5)  # 等 detached 的 node 刷新
    with open(in_path, encoding="utf-8") as handle:
        handed = json.loads(handle.read())
    hud_cache = os.path.join(os.path.expanduser("~"), ".claude", ".cache", "hud_out_cache.txt")
    rendered = ""
    if os.path.exists(hud_cache):
        with open(hud_cache, encoding="utf-8") as handle:
            entry = (json.load(handle).get(payload["cwd"]) or {})
        if time.time() - float(entry.get("ts", 0)) < 30:
            rendered = strip(entry.get("hud", ""))
    return strip(proc.stdout), handed, rendered


def case_hold(python, plugin):
    fake_cwd = r"C:\Users\chunx\hud_selftest_dir"
    tag = hashlib.md5(fake_cwd.encode("utf-8")).hexdigest()[:8]
    base = {"cwd": fake_cwd, "session_id": "selftest-session", "workspace": {"current_dir": fake_cwd},
            "model": {"id": "glm-5.4", "display_name": "glm-5.4"}}
    real_window = {"total_input_tokens": 297619, "total_output_tokens": 221, "context_window_size": 1000000,
                   "current_usage": {"input_tokens": 12179, "output_tokens": 221,
                                     "cache_creation_input_tokens": 0, "cache_read_input_tokens": 285440},
                   "used_percentage": 30, "remaining_percentage": 70}
    zero_window = {"total_input_tokens": 0, "total_output_tokens": 0, "context_window_size": 1000000,
                   "current_usage": {"input_tokens": 0, "output_tokens": 0,
                                     "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0},
                   "used_percentage": 0, "remaining_percentage": 100}
    results = []
    _, handed, rendered = run_wrapper(python, plugin, dict(base, context_window=real_window), tag)
    results.append(("读数保持·有效读数 → 原样交给状态栏(30%)",
                    handed["context_window"]["total_input_tokens"] == 297619 and "30%" in rendered, rendered[-26:]))
    _, handed, rendered = run_wrapper(python, plugin, dict(base, context_window=zero_window), tag)
    results.append(("读数保持·同会话零值样本 → 保持 30%",
                    handed["context_window"]["total_input_tokens"] == 297619 and "30%" in rendered, rendered[-26:]))
    other = dict(base, session_id="selftest-other-session")
    _, handed, rendered = run_wrapper(python, plugin, dict(other, context_window=zero_window), tag)
    results.append(("读数保持·新会话零值 → 放行(0%)",
                    handed["context_window"]["total_input_tokens"] == 0 and "0%" in rendered, rendered[-26:]))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugin", default=os.path.join(os.path.expanduser("~"), ".claude", "plugins", "nautilus-compass"))
    parser.add_argument("--repo", default=str(pathlib.Path(__file__).resolve().parents[1]))
    args = parser.parse_args()
    store_python = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Microsoft", "WindowsApps",
                                "PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0", "python.exe")
    python = store_python if os.path.exists(store_python) else sys.executable
    failed = 0
    with tempfile.TemporaryDirectory(prefix="hud_selftest_") as work:
        for name, ok, detail in case_probe(args.plugin, args.repo, work) + case_hold(python, args.plugin):
            failed += 0 if ok else 1
            print(json.dumps({"case": name, "pass": bool(ok), "detail": detail}, ensure_ascii=False))
    print(json.dumps({"failed": failed}, ensure_ascii=False))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
