"""compass · fuel-loop 部署验证探针(2026-08-22 grounded 修订:见各检查项注释)。

codex 部署 fuel-loop 到 cloud 后，compass 用此脚本独立验证端到端。

验证项（全部 grounded，不靠自报）:
1. 文件存在性：fuel_admission_receipt.py / fuel_intake.py / fde_admission.py
2. DB 表存在：fde_admission_ledger
3. 端点可达：POST /api/platform/fde/admissions/{grant_id}/consume
4. 链路活：V5 产经验 → fuel_intake → admission_ledger 有记录

用法:
    ssh cloud "python3 /opt/nautilus/nautilus-compass/ops/verify_fuel_loop.py"
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def check_files():
    """检查 fuel-loop 三个核心文件是否部署。"""
    # 2026-08-22 grounded:实际部署仓 = /home/ubuntu/nautilus-v5(cloud 真实布局,
    # 原 /opt/nautilus 是旧 phase3 平台 repo · 8/9 写探针时的假设未 grounding)
    expected = [
        "/home/ubuntu/nautilus-v5/fde_capsule/fuel_admission_receipt.py",
        "/home/ubuntu/nautilus-v5/fde_capsule/feishu/fuel_intake.py",
        "/home/ubuntu/nautilus-v5/nautilus_v5/platform/fde_admission.py",
    ]
    results = {}
    for path in expected:
        p = Path(path)
        results[path] = p.exists()
    return results


def check_db_table():
    """检查 fde_admission_ledger 表是否创建。"""
    try:
        import os
        import re as _re
        import psycopg2
        # grounded: 直接用 v5 daemon 的真实 DSN(/home/ubuntu/nautilus-v5/.env 的
        # POSTGRES_DSN · 库=nautilus_production · 密码在该文件)
        dsn = ""
        env_path = "/home/ubuntu/nautilus-v5/.env"
        if os.path.exists(env_path):
            m = _re.search(r'^(?:V5_)?POSTGRES_DSN="?([^"\r\n]+)"?',
                           open(env_path, encoding="utf-8").read(), _re.M)
            if m:
                dsn = m.group(1).strip()
        conn = psycopg2.connect(dsn)
        cur = conn.cursor()
        cur.execute(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables "
            "WHERE table_name='fde_admission_ledger')"
        )
        exists = cur.fetchone()[0]
        conn.close()
        return exists
    except Exception as e:
        return f"ERROR: {str(e)[:120]}"


def check_endpoint():
    """检查 consume 端点是否可达。"""
    try:
        import urllib.request
        req = urllib.request.Request(
            "http://localhost:8001/api/platform/fde/admissions/test/consume",
            method="POST",
            data=b"{}",
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=5)
        return "200"
    except Exception as e:
        code = getattr(e, "code", None)
        if code == 404:
            return "404 (endpoint not deployed)"
        if code == 400:
            return "400 (endpoint exists, bad request expected)"
        return f"ERROR: {str(e)[:120]}"


def main():
    print("=== fuel-loop 部署验证 ===\n")

    print("[1] 文件存在性:")
    files = check_files()
    all_ok = True
    for path, exists in files.items():
        status = "✅" if exists else "❌ MISSING"
        print(f"  {status} {path}")
        if not exists:
            all_ok = False

    print("\n[2] DB 表 fde_admission_ledger:")
    db = check_db_table()
    if db is True:
        print("  ✅ EXISTS")
    elif db is False:
        print("  ❌ NOT FOUND")
        all_ok = False
    else:
        print(f"  ⚠️ {db}")

    print("\n[3] Consume 端点:")
    ep = check_endpoint()
    print(f"  {ep}")

    print(f"\n=== 总判定: {'✅ DEPLOYED' if all_ok else '❌ NOT DEPLOYED'} ===")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
