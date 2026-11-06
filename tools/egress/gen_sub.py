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
    real = [p for p in proxies
            if not str(p.get("name", "")).startswith(("Expire", "Traffic", "Sync", "剩余", "过期"))
            and str(p.get("type", "")).lower() in USABLE_PREPROXY]
    if not real:
        sys.exit("订阅里没有可用作前置的节点")
    # 链式最短路径: 优先美国节点做前置(机场节点→同国家宽出口,少绕一洲)
    for p in real:
        if "美国" in str(p.get("name", "")) or "US" in str(p.get("name", "")):
            return p["name"]
    return real[0]["name"]


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
    home_plain = {
        "name": PLAIN_NODE,
        "type": "socks5",
        "server": env["HOME_HOST"],
        "port": int(env["HOME_PORT"]),
        "udp": True,
    }
    # 附加节点(如小火箭切片的中转 trojan,凭据在 EXTRA_NODES_FILE,不进仓)
    extras_path = env.get("EXTRA_NODES_FILE")
    extras = []
    if extras_path and Path(extras_path).exists():
        extras = yaml.safe_load(Path(extras_path).read_text(encoding="utf-8")) or []
        existing = {p.get("name") for p in proxies}
        extras = [e for e in extras if isinstance(e, dict) and e.get("name") not in existing]
        proxies = proxies + extras
    # 多前置链: 机场节点池含死键,给最多 4 条链择活;附加节点优先(用户手动指定=首选)
    real = [p for p in proxies
            if not str(p.get("name", "")).startswith(("Expire", "Traffic", "Sync", "剩余", "过期"))
            and str(p.get("type", "")).lower() in USABLE_PREPROXY]
    us_pool = [p["name"] for p in real if "美国" in str(p.get("name", "")) or "US" in str(p.get("name", ""))]
    extra_names = [e["name"] for e in extras]
    us_nodes = (extra_names + [n for n in us_pool if n not in extra_names])[:4] or [pre_name]
    chain_nodes = []
    for i, pn in enumerate(us_nodes):
        n = dict(home_plain)
        n["name"] = CHAIN_NODE if i == 0 else f"{CHAIN_NODE}-via{pn[:12]}"
        n["dialer-proxy"] = pn
        chain_nodes.append(n)
    for key in ("username", "password"):
        if env.get(key.upper()) or env.get(key):
            home_plain[key] = env.get(key.upper()) or env[key]
            for cn in chain_nodes:
                cn[key] = home_plain[key]

    cfg["proxies"] = chain_nodes + [home_plain] + proxies
    groups = cfg.setdefault("proxy-groups", [])
    auto_group = f"{CHAIN_GROUP}-自动"
    groups.insert(0, {
        "name": CHAIN_GROUP,
        "type": "select",
        "proxies": [auto_group] + [c["name"] for c in chain_nodes] + [PLAIN_NODE],
    })
    groups.insert(1, {
        "name": auto_group,
        "type": "fallback",
        "proxies": [c["name"] for c in chain_nodes],
        "url": f"http://nautilus.social/api/egress-check?expect={env['HOME_HOST']}",
        "interval": 300,
    })

    out = Path(env.get("OUT") or DEFAULT_OUT)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
    os.chmod(out, 0o600)
    print(f"OK: {len(proxies)} 订阅节点 + 链式节点(前置={pre_name}) -> {out}", file=sys.stderr)

    token = env.get("DEPLOY_TOKEN") or (Path.home() / ".config/nautilus/sub_token.txt").read_text().strip() if (Path.home() / ".config/nautilus/sub_token.txt").exists() else env.get("DEPLOY_TOKEN")
    if token:
        import subprocess
        remote = f"cloud:/var/www/subs/{token}/clash.yaml"
        r = subprocess.run(["scp", "-q", str(out), remote], timeout=60)
        if r.returncode == 0:
            print(f"已部署: https://nautilus.social/subs/{token}/clash.yaml (小火箭/Clash 填此 URL,选组 [{CHAIN_GROUP}])", file=sys.stderr)
        else:
            print(f"scp 部署失败(rc={r.returncode}),文件在本地 {out},手动上传 {remote}", file=sys.stderr)
    else:
        print(f"上传到自有域名随机长路径后,小火箭/Clash 订阅填该 URL;选组 [{CHAIN_GROUP}]", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
