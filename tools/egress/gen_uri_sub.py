#!/usr/bin/env python3
"""gen_uri_sub: Clash 节点(mihomo provider 缓存) → 小火箭原生订阅(base64 节点 URI 列表)。

vless-Reality/trojan/socks5/vmess 全参数转换;ssr 跳过(老协议,URI 编码复杂且非必需)。
输出: base64 列表(小火箭"订阅"类型直接识别) + 明文对照(调试用)。
链式说明: URI 标准不带链式字段——家宽 socks5 节点导入后在 小火箭里设一次"前置代理"(两次点击)。
"""
from __future__ import annotations

import base64
import json
import sys
import urllib.parse
from pathlib import Path

import yaml

HOME = {
    "host": "99.112.135.180", "port": 3322,
    "user": "hwT25fxG", "pass": "aXc4xS8s",
}
SRC = "/opt/homebrew/etc/mihomo/providers/subscription.yaml"
EXTRAS = str(Path.home() / ".config/nautilus/extra_nodes.yaml")
SKIP_PREFIX = ("Expire", "Traffic", "Sync", "剩余", "过期")


def q(name: str) -> str:
    return urllib.parse.quote(name, safe="")


def conv_vless(p: dict) -> str:
    ro = p.get("reality-opts") or {}
    para = {
        "type": p.get("network", "tcp"),
        "security": "reality" if ro else ("tls" if p.get("tls") else "none"),
        "encryption": "none",
        "flow": p.get("flow", ""),
        "sni": p.get("servername", ""),
        "fp": p.get("client-fingerprint", "chrome"),
    }
    if ro:
        para["pbk"] = ro.get("public-key", "")
        para["sid"] = ro.get("short-id", "")
    if p.get("network") == "ws":
        ws = p.get("ws-opts") or {}
        para["path"] = ws.get("path", "/")
        para["host"] = (ws.get("headers") or {}).get("Host", "")
    qs = "&".join(f"{k}={v}" for k, v in para.items() if v != "")
    return f"vless://{p['uuid']}@{p['server']}:{p['port']}?{qs}#{q(p['name'])}"


def conv_trojan(p: dict) -> str:
    para = []
    if p.get("sni"):
        para.append(f"sni={p['sni']}")
    if p.get("skip-cert-verify"):
        para.append("allowInsecure=1")
    if p.get("udp"):
        para.append("udp=1")
    qs = ("?" + "&".join(para)) if para else ""
    return f"trojan://{p['password']}@{p['server']}:{p['port']}{qs}#{q(p['name'])}"


def conv_vmess(p: dict) -> str:
    ws = p.get("ws-opts") or {}
    obj = {"v": "2", "ps": p["name"], "add": p["server"], "port": str(p["port"]),
           "id": p["uuid"], "aid": str(p.get("alterId", 0)), "scy": p.get("cipher", "auto"),
           "net": p.get("network", "tcp"), "type": "none",
           "host": (ws.get("headers") or {}).get("Host", ""),
           "path": ws.get("path", ""), "tls": "tls" if p.get("tls") else "",
           "sni": p.get("servername", ""), "fp": p.get("client-fingerprint", "")}
    return "vmess://" + base64.b64encode(json.dumps(obj).encode()).decode()


def conv(p: dict) -> str | None:
    t = str(p.get("type", "")).lower()
    if t == "vless":
        return conv_vless(p)
    if t == "trojan":
        return conv_trojan(p)
    if t == "vmess":
        return conv_vmess(p)
    return None


def main() -> int:
    proxies = yaml.safe_load(open(SRC)).get("proxies") or []
    xp = Path(EXTRAS)
    if xp.exists():
        proxies += yaml.safe_load(xp.read_text()) or []
    uris = [f"socks5://{HOME['user']}:{HOME['pass']}@{HOME['host']}:{HOME['port']}#家宽出口-AT&T-Irvine"]
    skipped = 0
    for p in proxies:
        name = str(p.get("name", ""))
        if name.startswith(SKIP_PREFIX):
            continue
        u = conv(p)
        if u:
            uris.append(u)
        else:
            skipped += 1
    body = "\n".join(uris)
    b64 = base64.b64encode(body.encode()).decode()
    out_b64 = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/rocket_sub_b64.txt")
    out_b64.write_text(b64)
    Path(str(out_b64).replace("_b64", "_plain")).write_text(body)
    print(f"节点 URI {len(uris)} 条(vless/trojan/vmess 全参转换,ssr 跳过 {skipped}),家宽 socks5 置顶"
          f"-> {out_b64}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
