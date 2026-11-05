#!/usr/bin/env python3
"""出口质量探针套件 · NET_EGRESS_ORGSELF V2 §1.4 判据的工具化。

五探针: 出口IP(v4/v6)/分层时延/DNS解析路径/UDP-DNS通达/QUIC试探。
用法: egress_probe.py [--label 名字] [--out dir]  → egress_report_<ts>.json
判据(§1.4 预注册): 7天IP不变≥95%(跨日累积)/时延P50不劣于基线/逐段行为有记录。
本工具只测不判(单次读数),跨日累积判读由面板评测模块做。
"""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import time
from pathlib import Path

TARGETS = ["https://www.baidu.com", "https://api.chunxiao.wang", "https://www.google.com"]
IP_CHECKS = {
    "v4": "https://api.ipify.org",
    "v6": "https://api6.ipify.org",
}
DNS_PROBE_HOST = "8.8.8.8"  # UDP 53 通达性探针(经隧道则验证 UDP 被承载)


def run(cmd: list[str], timeout: int = 15) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT"


def curl(url: str, extra: list[str] | None = None, timeout: int = 15) -> dict:
    cmd = ["curl", "-s", "-o", "/dev/null", "--max-time", str(timeout),
           "-w", "%{http_code} %{time_namelookup} %{time_connect} %{time_appconnect} %{time_starttransfer} %{time_total}"]
    if extra:
        cmd += extra
    cmd.append(url)
    rc, out = run(cmd, timeout + 5)
    parts = out.split()
    if rc != 0 or len(parts) < 6:
        return {"ok": False, "rc": rc, "raw": out[:80]}
    code, dns, tcp, tls, ttfb, total = parts[:6]
    return {"ok": True, "http": code, "dns_s": float(dns), "tcp_s": float(tcp),
            "tls_s": float(tls), "ttfb_s": float(ttfb), "total_s": float(total)}


def probe_exit_ip() -> dict:
    out = {}
    for ver, url in IP_CHECKS.items():
        rc, body = run(["curl", "-s", "--max-time", "10", url])
        out[ver] = body[:60] if rc == 0 and body else f"FAIL(rc={rc})"
    return out


def probe_timing() -> dict:
    rows = {}
    for t in TARGETS:
        rows[t] = curl(t)
    p50 = sorted(r["ttfb_s"] for r in rows.values() if r.get("ok"))
    return {"targets": rows, "ttfb_p50_s": p50[len(p50) // 2] if p50 else None}


def probe_dns() -> dict:
    """DNS 走向: 系统解析 vs 直问外部 DNS,出口侧解析器一致性由 ipinfo 判。"""
    rc, body = run(["curl", "-s", "--max-time", "10", "https://ipinfo.io/json"])
    resolver_city = ""
    try:
        resolver_city = json.loads(body).get("city", "")
    except json.JSONDecodeError:
        pass
    sys_rc, sys_ip = run(["sh", "-c", "dscacheutil -q host -a name example.com | awk '/ip_address/{print $2; exit}'"])
    return {"egress_geoloc_city": resolver_city, "system_resolves": bool(sys_ip), "raw": body[:100] if rc else ""}


def probe_udp_dns() -> dict:
    """经当前出口向 8.8.8.8:53 发 UDP 查询——通=UDP 被全链路承载。"""
    rc, out = run(["dig", f"@{DNS_PROBE_HOST}", "example.com", "+time=5", "+tries=1", "+short"])
    return {"udp_dns_ok": rc == 0 and bool(out), "answer": out[:60]}


def probe_quic() -> dict:
    """QUIC 试探: curl 无 http3 时降级记录不可验,不冒充。"""
    rc, out = run(["curl", "-sV"], 5)
    has_h3 = "HTTP3" in out
    if not has_h3:
        return {"quic": "[不可验] 本机 curl 无 HTTP3 支持"}
    rc2, _ = run(["curl", "-s", "-o", "/dev/null", "--http3-only", "--max-time", "10", "https://www.google.com"])
    return {"quic": "OK" if rc2 == 0 else f"FAIL(rc={rc2})"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", default="unlabeled-exit")
    parser.add_argument("--out", default="runtime/egress_reports")
    args = parser.parse_args()

    report = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "label": args.label,
        "exit_ip": probe_exit_ip(),
        "timing": probe_timing(),
        "dns": probe_dns(),
        "udp_dns": probe_udp_dns(),
        "quic": probe_quic(),
    }
    out_dir = Path(args.out).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"egress_{args.label}_{time.strftime('%Y%m%d_%H%M')}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1))
    print(f"\n-> {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
