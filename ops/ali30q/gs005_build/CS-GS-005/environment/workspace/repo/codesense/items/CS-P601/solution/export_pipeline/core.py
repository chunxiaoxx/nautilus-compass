"""export_pipeline.core — 对账日报导出(金标实现)。"""
from __future__ import annotations

import hashlib
from pathlib import Path

REQUIRED = ("query", "out_dir", "export_id", "version")


def run_export(cfg: dict, db) -> dict:
    """执行日报导出流水线(§1-§3,以 §2 可靠性口径为准,§5 备注不采纳)。"""
    # §2 配置校验:缺键不执行任何步骤
    for k in REQUIRED:
        if k not in cfg:
            return {"ok": False, "reason": f"missing:{k}"}

    # §2 版本锁定:按快照键取数(禁取最新)
    rows = db.fetch(cfg["query"], cfg["version"])

    # §1 步骤2:格式化
    lines = [f"{row['id']},{row['amount']}" for row in rows]
    body = "\n".join(lines)

    # §1 步骤3:写文件对+校验和
    out_dir = Path(cfg["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    report = out_dir / "report.csv"
    try:
        with open(report, "w", encoding="utf-8") as f:
            f.write(body + ("\n" if body else ""))
        digest = hashlib.sha256((body + "\n").encode()).hexdigest()
        with open(out_dir / "report.csv.sha256", "w") as f:
            f.write(digest)
        # §2 成对一致校验
        with open(out_dir / "report.csv.sha256") as f:
            if f.read().strip() != digest:
                return {"ok": False, "reason": "write:sha_mismatch"}
    except OSError as e:
        return {"ok": False, "reason": f"write:{e}"}

    # §1 步骤4:登记(仅 1-3 全部成功后)
    try:
        reg = db.register(cfg["export_id"])
        if reg is False:  # §2 登记失败视为整次失败
            return {"ok": False, "reason": "register:rejected"}
    except Exception as e:
        return {"ok": False, "reason": f"register:{e}"}

    return {"ok": True, "file": report, "rows": len(rows)}
