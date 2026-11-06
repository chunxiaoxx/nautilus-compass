#!/usr/bin/env python3
"""gen_rocket_conf: 生成小火箭原生多链配置(每条链=家宽socks5+chain指向前置,导入即用)。

前置混编(抗单协议封锁): 美国02-trojan(extras,46ms 中转) + US05/06/07 vless-Reality(provider 缓存直读)。
泄露钉: 规则仅 MATCH→链,无任何 DIRECT 兜底(fail-close: 链死即断,永不回退直连)。
"""
from __future__ import annotations

import json
import sys
import time
import uuid as uuidlib
from pathlib import Path

import yaml

SRC = "/opt/homebrew/etc/mihomo/providers/subscription.yaml"
EXTRAS = str(Path.home() / ".config/nautilus/extra_nodes.yaml")
ENV = str(Path.home() / ".config/nautilus/egress.env")
HOME_DEFAULT = {"host": "99.112.135.180", "port": "3322", "user": "hwT25fxG", "pass": "aXc4xS8s"}


def load_env() -> dict:
    env = dict(HOME_DEFAULT)
    if Path(ENV).exists():
        for line in Path(ENV).read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def trojan_entry(p: dict, uid: str) -> dict:
    return {"host": p["server"], "port": str(p["port"]), "type": "Trojan", "uuid": uid,
            "password": p["password"], "peer": p.get("sni", ""), "sni": p.get("sni", ""),
            "allowInsecure": 1 if p.get("skip-cert-verify") else 0, "udp": 1,
            "obfs": "none", "proto": "none", "title": p["name"], "flag": "UM",
            "created": time.time(), "updated": time.time(), "weight": 1}


def vless_entry(p: dict, uid: str) -> dict:
    ro = p.get("reality-opts") or {}
    return {"host": p["server"], "port": str(p["port"]), "type": "Vless", "uuid": p["uuid"],
            "flow": p.get("flow", ""), "peer": p.get("servername", ""), "sni": p.get("servername", ""),
            "publicKey": ro.get("public-key", ""), "shortId": ro.get("short-id", ""),
            "allowInsecure": 0, "udp": 1, "obfs": "none", "proto": "none",
            "title": p["name"], "flag": "US",
            "created": time.time(), "updated": time.time(), "weight": 2}


def chain_entry(env: dict, front_uid: str, front_title: str) -> dict:
    return {"host": env["HOME_HOST"], "port": str(env["HOME_PORT"]), "type": "Socks5",
            "uuid": str(uuidlib.uuid4()).upper(),
            "user": env.get("HOME_USER", ""), "password": env.get("HOME_PASS", ""),
            "udp": 1, "obfs": "none", "proto": "none",
            "chain": front_uid,  # 前置焊死
            "title": f"🔗家宽链-经{front_title[:10]}", "flag": "WW",
            "created": time.time(), "updated": time.time(), "weight": int(time.time())}


def main() -> int:
    env = load_env()
    proxies = yaml.safe_load(open(SRC)).get("proxies") or []
    if Path(EXTRAS).exists():
        proxies += yaml.safe_load(Path(EXTRAS).read_text()) or []
    fronts = []
    seen_auth = set()
    # 前置混编且引用唯一: 先 trojan(唯一entry-uuid) 后 vless-Reality(共用auth-uuid,只取1条防chain引用歧义)
    extras = [p for p in proxies if str(p.get("type", "")).lower() == "trojan"
              and ("美国" in str(p.get("name", "")) or "US" in str(p.get("name", "")))]
    for p in proxies:
        n, t = str(p.get("name", "")), str(p.get("type", "")).lower()
        if n.startswith(("Expire", "Traffic", "Sync", "剩余", "过期")):
            continue
        if t == "trojan" and p in extras:
            continue  # 后面统一加
        if t == "vless" and p.get("reality-opts") and ("美国" in n or "US" in n) and len(fronts) < 2:
            if p["uuid"] not in seen_auth:
                seen_auth.add(p["uuid"])
                fronts.append(vless_entry(p, p["uuid"]))
    for p in extras[:1]:
        fronts.append(trojan_entry(p, str(uuidlib.uuid4()).upper()))  # trojan=备链(Reality 主)
    servers, first = [], None
    for f in fronts:
        c = chain_entry(env, f["uuid"], f["title"])
        if first is None:
            first = c["title"]  # 首条=vless-Reality(用户指定主协议)
        servers.append(c)
        servers.append(f)
    conf = {"servers": servers,
            "rules": [f"MATCH,{first}"]}  # 唯一规则=全走链(fail-close,无 DIRECT)
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/rocket_chain.conf")
    out.write_text(json.dumps(conf, ensure_ascii=False, indent=1))
    print(f"conf: {len(fronts)} 前置(trojan+vless-Reality 混编),链 {len(fronts)} 条;唯一出口={env['HOME_HOST']} -> {out}",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
