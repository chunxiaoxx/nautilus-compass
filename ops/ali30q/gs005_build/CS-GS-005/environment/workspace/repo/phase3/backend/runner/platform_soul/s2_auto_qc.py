"""S2 webhook 入口 · FDE webhook 在 v06_派活 状态变「已提交」时 subprocess 调用。

薄包装:从 env 读 RGDK 配置 → 调现有 S2 runner(services.fde_qc_feedback_runner)。
不重写逻辑(复用 TDD green 的 sync_submissions)。

env(部署在 FDE 服务器·我引擎 app 凭据·我 bot 有 RGDK editor):
  FEISHU_APP_ID / FEISHU_APP_SECRET   我引擎 app(cli_aaa8e75d·bot ou_af25f91c... 授 RGDK editor)
  PLATFORM_BASE                       verdict-bus/dispatch(默认 https://nautilus.social)
  FDE_BASE_TOKEN                      RGDK base(RGDKbrtZ1aMcEOsZ2GcczeFknNg)
  PAIHUO_TABLE_ID                     v06_派活 table_id(FDE 建表后给)
  DRY_RUN                             可选·非空=dry-run
"""
from __future__ import annotations

import os
import sys


def main() -> None:
    from _env import load_sibling_env
    load_sibling_env()
    base = os.environ.get("PLATFORM_BASE", "https://nautilus.social")
    app_token = os.environ["FDE_BASE_TOKEN"]
    table_id = os.environ["PAIHUO_TABLE_ID"]
    argv = ["s2_auto_qc", "--base", base, "--app-token", app_token, "--table-id", table_id]
    if os.environ.get("DRY_RUN"):
        argv.append("--dry-run")
    sys.argv = argv
    from services.fde_qc_feedback_runner import main as runner_main
    runner_main()


if __name__ == "__main__":
    main()
