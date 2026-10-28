"""S3 webhook 入口 · FDE webhook 在 v06_派活 状态变「已通过」时 subprocess 调用。

薄包装:从 env 读 RGDK(派活源)+ 我 Dx2qb(机密交付/结算)配置 → 调现有 S3 runner
(services.fde_delivery_runner)。不重写逻辑(复用 TDD green 的 sync_deliveries)。

🔴 机密隔离(charter §E):派活源=RGDK(我 bot 有 editor),买方交付内容+结算=我 Dx2qb
(我 app 主人·FDE 不读不写)。S3 把交付状态/应付镜像进 RGDK v06_交付总表(后续片)。

env:
  FEISHU_APP_ID / FEISHU_APP_SECRET   我引擎 app(写 RGDK 用我 bot·写 Dx2qb 用 app 主人权)
  PLATFORM_BASE                       verdict-bus 门(默认 https://nautilus.social)
  FDE_BASE_TOKEN / PAIHUO_TABLE_ID    RGDK + v06_派活(读已通过·写回已交付)
  DELIVER_APP_TOKEN                   我 Dx2qb(Dx2qb1fjhaJadSs0ZeMc0teVn49)
  DELIVER_TABLE_ID                    交付表(tblFkmEKTk4LIWJM)
  SETTLE_TABLE_ID                     结算表(tblFL7y3DejBQUvm)
  DRY_RUN                             可选
"""
from __future__ import annotations

import os
import sys


def main() -> None:
    from _env import load_sibling_env
    load_sibling_env()
    base = os.environ.get("PLATFORM_BASE", "https://nautilus.social")
    argv = [
        "s3_delivery_settlement", "--base", base,
        "--assign-app", os.environ["FDE_BASE_TOKEN"],
        "--assign-table", os.environ["PAIHUO_TABLE_ID"],
        "--deliver-app", os.environ.get("DELIVER_APP_TOKEN", "Dx2qb1fjhaJadSs0ZeMc0teVn49"),
        "--deliver-table", os.environ.get("DELIVER_TABLE_ID", "tblFkmEKTk4LIWJM"),
        "--settle-table", os.environ.get("SETTLE_TABLE_ID", "tblFL7y3DejBQUvm"),
    ]
    if os.environ.get("DRY_RUN"):
        argv.append("--dry-run")
    sys.argv = argv
    from services.fde_delivery_runner import main as runner_main
    runner_main()


if __name__ == "__main__":
    main()
