#!/usr/bin/env python3
"""gen_sub: 拉取 Clash 订阅 → 注入"VPN前置+家宽SOCKS5出口"链式节点 → 输出合并 YAML(自用)。

用法(依赖 pyyaml,走 uv 临时环境):
  uv run --with pyyaml python3 tools/egress/gen_sub.py

配置: ~/.config/nautilus/egress.env (0600,不进仓,模板见 egress.env.example):
  SUB_URL=https://xxx?target=clash      # 你的订阅(也可用 SUB_URL_FILE=本地yaml路径测试)
  HOME_HOST=/HOME_PORT/HOME_USER/HOME_PASS  # 家宽 SOCKS5
  PREPROXY_NAME=                         # 可选:指定前置 VPN 节点名;缺省自动选订阅里第一个可用节点
  OUT=                                   # 可选:输出路径;缺省 ~/.config/nautilus/out/merged_sub.yaml(0600)

注意:
- 输出文件含明文凭据——只放本地或自己的服务器,绝不进 git;
- dialer-proxy 链式为 mihomo/Clash Meta 特性;不支持链式的客户端(部分版本小火箭)会忽略链,
  故同时输出裸 socks5 节点兜底;
- 上传到你自己域名的随机长路径 HTTPS URL 后,小火箭/Clash 填该 URL 导入。
"""
from __future__ import annotations

import os
import re
import stat
import sys
from pathlib import Path

import yaml

ENV_PATH = Path.home() / ".config/nautilus/egress.env"
DEFAULT_OUT = Path.home() / ".config/nautilus/out/merged_sub.yaml"
CHAIN_NODE = "us-home-exit"
CHAIN_GROUP = "美国家宽链"
PLAIN_NODE = "us-home-direct"

USABLE_PREPROXY = ("ss", "vmess", "trojan", "vless", "hysteria2", "tuic", "ssr", "socks5", "http")


def load_env() -> dict:
    if not ENV_PATH.exists():
        sys.exit(f"缺配置 {ENV_PATH}(模板: tools/egress/egress.env.example)")
    if (ENV_PATH.stat().st_mode & 0o777) != 0o600:
        os.chmod(ENV_PATH, 0o600)
    env = {}
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
    missing = [k for k in ("HOME_HOST", "HOME_PORT") if not env.get(k)]
    if missing:
        sys.exit(f"配置缺 {missing}")
    if not (env.get("SUB_URL") or env.get("SUB_URL_FILE")):
        sys.exit("配置缺 SUB_URL 或 SUB_URL_FILE")
    return env


def fetch_sub(env: dict) -> str:
    if env.get("SUB_URL_FILE"):
        return Path(env["SUB_URL_FILE"]).read_text(encoding="utf-8")
    import urllib.request
    req = urllib.request.Request(env["SUB_URL"], headers={"User-Agent": "clash-verge/1.6"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def pick_preproxy(proxies: list[dict], want: str | None) -> str:
    if want:
        names = {p.get("name") for p in proxies}
        if want not in names:
            sys.exit(f"PREPROXY_NAME={want} 不在订阅节点里;可选: {sorted(names)[:10]}...")
        return want
    for p in proxies:
        if str(p.get("type", "")).lower() in USABLE_PREPROXY:
            return p["name"]
    sys.exit("订阅里没有可用作前置的节点")


def main() -> int:
    env = load_env()
    raw = fetch_sub(env)
    if "proxies:" not in raw:
        sys.exit("订阅内容不像 Clash YAML(无 proxies:)——检查 SUB_URL 的 target=clash 参数")
    cfg = yaml.safe_load(raw)
    proxies = cfg.get("proxies") or []
    if not proxies:
        sys.exit("订阅 proxies 为空")

    pre_name = pick_preproxy(proxies, env.get("PREPROXY_NAME") or None)
    home = {
        "name": CHAIN_NODE,
        "type": "socks5",
        "server": env["HOME_HOST"],
        "port": int(env["HOME_PORT"]),
        "udp": True,
        "dialer-proxy": pre_name,  # mihomo/Clash Meta: 跨境段走订阅节点加密
    }
    home_plain = {
        "name": PLAIN_NODE,
        "type": "socks5",
        "server": env["HOME_HOST"],
        "port": int(env["HOME_PORT"]),
        "udp": True,
    }
    for key in ("username", "password"):
        if env.get(key.upper()) or env.get(key):
            home[key] = home_plain[key] = env.get(key.upper()) or env[key]

    cfg["proxies"] = [home, home_plain] + proxies
    groups = cfg.setdefault("proxy-groups", [])
    groups.insert(0, {
        "name": CHAIN_GROUP,
        "type": "select",
        "proxies": [CHAIN_NODE, PLAIN_NODE, pre_name],
    })

    out = Path(env.get("OUT") or DEFAULT_OUT)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
    os.chmod(out, 0o600)
    print(f"OK: {len(proxies)} 订阅节点 + 链式节点(前置={pre_name}) -> {out}", file=sys.stderr)
    print(f"上传到自有域名随机长路径后,小火箭/Clash 订阅填该 URL;选组 [{CHAIN_GROUP}]", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
