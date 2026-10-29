#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CS-GS-005 反例程序 · 陷阱可证性(需求 §2.3/§3.5)。

复现坑面: v5 helix_v7 bridge 消费侧配置漂移的静默降级(锚 nautilus-v5 defb148
前真实事故)——坏 DSN 下 ImportError 被软捕获仅一行 warning → helix_v7=None →
消费侧裸调 AttributeError 再被 soft except 吞掉 → 返回 None、零计数、零结构化
痕迹,链上账静默丢失。

直调**被测 repo** 的 v5_bridge.helix_bridge(真实入口):
  坑版 exit 1(静默降级复现) / 金标或等价实现 exit 0(降级结构化可见)
运行: python3 counterexample_gs005.py <repo根目录>
"""
import asyncio
import sys
from pathlib import Path


def main() -> int:
    repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    sys.path.insert(0, str(repo))
    print(f"python={sys.version.split()[0]} platform={sys.platform}")

    from v5_bridge.helix_bridge import BridgeConfig, HelixBridgeHost

    bad_dsn = "postgres://user:oldpw@127.0.0.1:1/wrongdb"
    host = HelixBridgeHost(BridgeConfig(agent_id="counterexample", postgres_dsn=bad_dsn))
    outcome = asyncio.run(
        host.close_breath_pair(1, {"act_summary": "ce-action"}, {"cycle": 1}))

    silent = []
    if not getattr(host, "degradation_report", None):
        silent.append("degradation_report 缺失(降级无结构化报告)")
    if not getattr(host, "degradation_count", 0):
        silent.append("degradation_count=0(降级零计数零留痕)")
    if getattr(host, "chain_backend", None) is None:
        silent.append("chain_backend=None(后端标记缺失,fallback 不可观测)")
    if outcome is None:
        silent.append("outcome=None(消费侧静默吞,调用方无从分辨封链与否)")
    if silent:
        print(f"[静默降级证据] {len(silent)} 项:")
        for s in silent:
            print(f"  - {s}")
        print("VERDICT: TRAP_PRESENT — 配置漂移静默降级复现"
              "(defb148 前真实事故形态: 链上账静默丢失)")
        return 1
    print("VERDICT: FIXED — 降级四件套结构化可见(GP-1~GP-4 合规)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
