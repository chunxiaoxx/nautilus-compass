#!/usr/bin/env python3
# statusLine 后台探针 v3.1.0 (2026-11-26) · 与 compass_hud_wrapper.py 配套
#
# wrapper 主流程零网络;缓存过期时最多 60s 派本脚本一次,结果写 hud_daemon_cache.json。
# v3.1.0 治"状态栏永远报记忆服务未响应":
#   ① v3.0.x 的 MCP 回退探测读 ~/.claude.json['mcpServers']['nautilus-compass'] 的 url
#      —— 那是本机 stdio 条目,没有 url;云端 MCP 的 url 在项目级 .mcp.json。
#      实测 2026-11-26:缓存恒为 ok=false,同一时刻公网 MCP 5/5 召回成功。
#      新:先探本机 daemon(有则沿用),否则按 cwd 向上找 .mcp.json 里的
#        COMPASS_MCP_SERVER_NAME(默认 nautilus-compass-cloud);COMPASS_MCP_JSON 可直接指定文件。
#   ② 状态分级:ok / slow(握手 > SLOW_S)/ down / auth(401,403)/ http_N / unconfigured。
#      没找到端点 = unconfigured,不再冒充"未响应"。
# 阴性对照:见 ops/hud_probe_selftest.py(未配置 / 错令牌 / 端点关闭 三种都必须各报其态)。
# 用法:python compass_hud_probe.py <cache_path> <cwd>
import hashlib
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.request

SERVER_NAME = os.environ.get("COMPASS_MCP_SERVER_NAME", "nautilus-compass-cloud")
DAEMON_PORT = int(os.environ.get("COMPASS_DAEMON_PORT", "9876"))
DAEMON_TIMEOUT_S = 2.0
MCP_TIMEOUT_S = 25.0
SLOW_S = 8.0


def _atomic_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(data, handle)
    os.replace(tmp, path)


def _write_result(path, cwd, result):
    """按 cwd 分桶写(v3.1.0):多窗口不同目录共用一份缓存会互相覆盖;过期条目顺手清掉。"""
    tag = hashlib.md5((cwd or "").encode("utf-8", "replace")).hexdigest()[:8] if cwd else "nocwd"
    try:
        with open(path, encoding="utf-8") as handle:
            loaded = json.load(handle)
        data = loaded if isinstance(loaded, dict) else {}
    except (OSError, ValueError):
        data = {}
    now = time.time()
    # 兼容 v3.0.x 的扁平旧格式(值是数字/布尔而非 dict):只保留本格式的未过期条目。
    kept = {k: v for k, v in data.items()
            if isinstance(v, dict) and now - float(v.get("ts", 0) or 0) < 86400}
    kept[tag] = result
    _atomic_json(path, kept)


def find_server(cwd):
    """按 cwd 向上找 .mcp.json 里的云端 MCP 条目;返回 (url, headers) 或 (None, None)。"""
    override = os.environ.get("COMPASS_MCP_JSON", "").strip()
    candidates = [override] if override else []
    directory = os.path.abspath(cwd) if cwd else ""
    for _ in range(6):
        if not directory:
            break
        candidates.append(os.path.join(directory, ".mcp.json"))
        parent = os.path.dirname(directory)
        if parent == directory:
            break
        directory = parent
    for path in candidates:
        if not path or not os.path.isfile(path):
            continue
        try:
            with open(path, encoding="utf-8") as handle:
                servers = (json.load(handle).get("mcpServers") or {})
        except (OSError, ValueError):
            continue
        entry = servers.get(SERVER_NAME)
        if isinstance(entry, dict) and entry.get("url"):
            return entry["url"], dict(entry.get("headers") or {})
    return None, None


def probe_daemon():
    """本机 daemon(有的机器在跑)。连不上返回 None;连上返回状态 dict。"""
    out = {"via": "daemon", "p95": 0, "ovl": False, "hits_today": 0}
    started = time.time()
    try:
        token = ""
        try:
            with open(os.path.expanduser("~/.claude/.cache/compass_daemon_token"), encoding="utf-8") as handle:
                token = handle.read().strip()
        except OSError:
            pass
        with socket.create_connection(("127.0.0.1", DAEMON_PORT), timeout=DAEMON_TIMEOUT_S) as sock:
            request = json.dumps({"action": "recall", "query": "ping", "top_k": 1, "scope": "project",
                                  "project": "C--Users-chunx", "token": token}) + "\n"
            sock.sendall(request.encode())
            buf = b""
            deadline = time.time() + 3.0
            while time.time() < deadline:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                buf += chunk
                try:
                    out["ok"] = bool(json.loads(buf.decode()).get("ok", False))
                    break
                except ValueError:
                    continue
            out.setdefault("ok", False)
        if out["ok"]:
            with socket.create_connection(("127.0.0.1", DAEMON_PORT), timeout=DAEMON_TIMEOUT_S) as sock:
                sock.sendall((json.dumps({"action": "status", "token": token}) + "\n").encode())
                status = json.loads(sock.recv(65536).decode())
            sliding = (status.get("recall") or {}).get("sliding_5min") or {}
            out["p95"] = sliding.get("p95_ms", 0)
            out["ovl"] = bool(sliding.get("overload_5min"))
    except (OSError, ValueError):
        return None
    out["state"] = "ok" if out["ok"] else "down"
    out["latency_s"] = round(time.time() - started, 2)
    return out


def probe_mcp(url, headers):
    """一次 initialize 往返。返回 (状态 dict, 秒)。"""
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-03-26", "capabilities": {},
        "clientInfo": {"name": "hud-probe", "version": "3.1"}}}).encode()
    sent = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    sent.update(headers)
    started = time.time()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=sent), timeout=MCP_TIMEOUT_S) as response:
            latency = time.time() - started
            if response.status == 200:
                return {"ok": True, "state": "slow" if latency > SLOW_S else "ok"}, latency
            return {"ok": False, "state": "http_%d" % response.status}, latency
    except urllib.error.HTTPError as error:
        return {"ok": False, "state": "auth" if error.code in (401, 403) else "http_%d" % error.code}, time.time() - started
    except Exception as error:  # 连接拒绝/超时/DNS/代理未起:对本机都是"够不着"
        return {"ok": False, "state": "down", "err": type(error).__name__}, time.time() - started


def hits_today(log_path):
    """今日召回数:verification_log 尾部 400KB(与 v3.0.9 口径一致)。"""
    try:
        with open(log_path, "rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            handle.seek(max(0, size - 400000))
            lines = handle.read().decode("utf-8", "replace").strip().splitlines()
        today = time.strftime("%Y-%m-%d")
        count = 0
        for line in lines:
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if record.get("top5") and str(record.get("ts", ""))[:10] == today:
                count += 1
        return count
    except OSError:
        return 0


def main(argv):
    if len(argv) < 3:
        return 2
    cache_path, cwd = argv[1], argv[2]
    out = {"ts": time.time(), "ok": False, "state": "unconfigured", "p95": 0, "ovl": False,
           "hits_today": 0, "latency_s": 0}
    try:
        local = probe_daemon()
        if local is not None:
            out.update(local)
        if not out["ok"]:
            url, headers = find_server(cwd)
            if url:
                result, latency = probe_mcp(url, headers)
                out.update(result)
                out["via"] = "mcp-http"
                out["latency_s"] = round(latency, 2)
            elif local is None:
                out["state"] = "unconfigured"
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                ".cache", "verification_log.jsonl")
        out["hits_today"] = hits_today(log_path)
    except Exception as error:  # 探针自身异常也不能让缓存停在旧值
        out.update({"ok": False, "state": "down", "err": type(error).__name__})
    _write_result(cache_path, cwd, out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
