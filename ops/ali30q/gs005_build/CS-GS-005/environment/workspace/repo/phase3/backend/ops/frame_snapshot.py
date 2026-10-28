# -*- coding: utf-8 -*-
"""frame_snapshot·Mac 版(2026-10-27 迁移接骨重写)

旧环境(Windows schtasks 每日 09:07)版未随 10/20 三机迁移入仓,本版按 10/27 实测方法论重写:
DB 活跃度+心跳+工单台账+判分轨迹+云况+本机进程 → ~/snapshots/frame_snapshot_YYYYMMDD.md
消费方:平台 loop 首轮、组织全景投影(治"盲区运行"——9框4机从快照可见)。
设计:任一段失败不阻断其余(快照的价值在每日有,不在完美)。"""
import datetime
import os
import subprocess

DB = "postgresql://nautilus_user:nautilus2024@127.0.0.1:15432/nautilus_production"
OUT = os.path.expanduser(f"~/snapshots/frame_snapshot_{datetime.date.today():%Y%m%d}.md")


def psql(sql: str) -> str:
    r = subprocess.run(["psql", DB, "-c", sql], capture_output=True, text=True, timeout=60)
    return r.stdout if r.returncode == 0 else f"(psql失败: {r.stderr[:120]})"


def ssh(cmd: str) -> str:
    r = subprocess.run(["ssh", "-p", "24860", "-o", "ConnectTimeout=8", "-o", "BatchMode=yes",
                        "ubuntu@43.160.239.61", cmd], capture_output=True, text=True, timeout=45)
    return r.stdout.strip() if r.returncode == 0 else "(ssh不可达)"


sections = [
    ("各框48h发函活跃度",
     psql("SELECT from_agent, count(*) n, max(to_char(created_at,'MM-DD HH24:MI')) last "
          "FROM org_mailbox WHERE created_at > now()-interval '48 hours' AND from_agent!='platform' "
          "GROUP BY 1 ORDER BY last DESC;")),
    ("平台未ack积压(按框)",
     psql("SELECT from_agent, count(*) FROM org_mailbox WHERE to_agent='platform' AND ack_at IS NULL "
          "AND title NOT LIKE '%loopback%' GROUP BY 1;")),
    ("agents心跳(48h)",
     psql("SELECT agent_id, left(name,16) nm, to_char(last_heartbeat,'MM-DD HH24:MI') hb "
          "FROM agents WHERE last_heartbeat > now()-interval '48 hours' ORDER BY last_heartbeat DESC LIMIT 12;")),
    ("ali30q工单台账",
     psql("SELECT status, count(*) FROM platform_bounties WHERE bounty_id ILIKE 'ali30q%' GROUP BY 1;")),
    ("判分轨迹(fuel)",
     psql("SELECT count(*) total, max(created_at) latest FROM fuel_trajectories;")),
    ("云况(load+服务)",
     ssh("cat /proc/loadavg; systemctl is-active compass-bge-daemon nautilus-backend") + "\n" +
     ssh("ps aux --sort=-%cpu | head -4 | tail -3")),
    ("Mac本机v5进程",
     subprocess.run(["bash", "-c", "ps aux | grep -E 'nautilus_v5|nautilus-v5' | grep -v grep | head -4"],
                    capture_output=True, text=True).stdout or "(无)"),
]

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(f"# 全框快照 {datetime.datetime.now():%Y-%m-%d %H:%M}·Mac版\n\n")
    f.write("> 生成:launchd ai.nautilus.frame-snapshot 每日09:07;消费:平台loop首轮+组织全景\n\n")
    for title, body in sections:
        f.write(f"## {title}\n```\n{body.strip() or '(空)'}\n```\n\n")
print(OUT)
