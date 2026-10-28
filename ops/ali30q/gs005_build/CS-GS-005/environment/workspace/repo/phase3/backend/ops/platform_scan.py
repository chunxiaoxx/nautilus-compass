# -*- coding: utf-8 -*-
"""platform_scan·全平台体检扫描器(2026-10-27 用户令)

五维×四层对象:活性/能力(代理)/产出/健康/关系 × 对话框/Agent身份/服务/机制
输出:~/snapshots/platform_scan_YYYYMMDD.md——问题归五类:断线/病带/空转/断链/账实
设计:只读查询+ssh探活,无写操作;单段失败不阻断。"""
import datetime
import os
import subprocess

DB = "postgresql://nautilus_user:nautilus2024@127.0.0.1:15432/nautilus_production"
OUT = os.path.expanduser(f"~/snapshots/platform_scan_{datetime.date.today():%Y%m%d}.md")


def psql(sql: str) -> str:
    r = subprocess.run(["psql", DB, "-c", sql], capture_output=True, text=True, timeout=90)
    return r.stdout if r.returncode == 0 else f"(psql失败:{r.stderr[:100]})"


S = []

# 1 身份层:agents 全景三态(总/活/僵尸)
S.append(("1.身份层·agents 356 身份三态",
          psql("SELECT count(*) 总数, count(*) FILTER (WHERE last_heartbeat > now()-interval '7 days') 近7日活, "
               "count(*) FILTER (WHERE last_heartbeat IS NULL) 无心跳记录 FROM agents;")
          + psql("SELECT agent_id, left(name,20) nm, to_char(last_heartbeat,'MM-DD') hb FROM agents "
                 "WHERE last_heartbeat > now()-interval '7 days' ORDER BY last_heartbeat DESC LIMIT 15;")))

# 2 关系层:函件协作图(收发不对称=断链候选)
S.append(("2.关系层·近7日收发不对称(收多发少=只进不出,发多收少=喊话无回)",
          psql("SELECT COALESCE(from_agent,'?') src, COALESCE(to_agent,'?') dst, count(*) n "
               "FROM org_mailbox WHERE created_at > now()-interval '7 days' "
               "GROUP BY 1,2 HAVING count(*) >= 3 ORDER BY n DESC LIMIT 20;")))

# 3 健康层:各 agent 工具失败率(遥测,近7日,失败率>5% 为病带候选)
S.append(("3.健康层·各agent近7日工具失败率(>5%病带候选)",
          psql("SELECT agent_id, count(*) calls, round(100.0*sum((not success)::int)/count(*),1) fail_pct "
               "FROM agent_tool_calls WHERE ts > now()-interval '7 days' GROUP BY 1 "
               "HAVING count(*) >= 50 ORDER BY fail_pct DESC LIMIT 12;")))

# 4 产出层:各框近7日工单贡献
S.append(("4.产出层·工单按承接方近7日",
          psql("SELECT claimed_by, status, count(*) FROM platform_bounties "
               "WHERE claimed_at > now()-interval '7 days' GROUP BY 1,2 ORDER BY 1,3 DESC LIMIT 15;")))

# 5 账实层:结算链对账(完成单 vs 铸造)
S.append(("5.账实层·结算与铸造",
          psql("SELECT count(*) FILTER (WHERE status='completed') 完成单, "
               "count(*) FILTER (WHERE status='settled') 已结算, "
               "count(*) FILTER (WHERE status='completed' AND score IS NULL) 完成但无分 FROM platform_bounties;")))

# 6 机制层:函件积压与ack纪律
S.append(("6.机制层·全平台未ack积压(to≠platform,谁欠谁)",
          psql("SELECT to_agent, count(*) 未ack, max(to_char(created_at,'MM-DD')) 最旧 FROM org_mailbox "
               "WHERE ack_at IS NULL AND to_agent IS NOT NULL AND to_agent != 'platform' "
               "GROUP BY 1 HAVING count(*) >= 2 ORDER BY 未ack DESC LIMIT 12;")))

# 7 服务层:云 systemd 全量对照(死unit/新增未记候选)
import json as _j
ssh_out = subprocess.run(
    ["ssh", "-p", "24860", "-o", "ConnectTimeout=8", "-o", "BatchMode=yes",
     "ubuntu@43.160.239.61",
     "systemctl list-units --type=service --state=running --no-pager --no-legend | awk '{print $1}' | grep -v -E 'systemd|dbus|ssh|cron|network|getty|polkit|rsyslog|unattended|user@|session|snap|lxd|qcloud|acme|fail2ban|multipath|ModemManager|udisks' | head -25"],
    capture_output=True, text=True, timeout=45)
S.append(("7.服务层·云运行中业务服务(对照架构档案找死unit/未记新增)",
          ssh_out.stdout or "(ssh不可达)"))

# 8 通路层:mac-v5/kairos/zenmind 通道验证
S.append(("8.通路层·静默框通道(kairos/zenmind/mac-v5 最近收发)",
          psql("SELECT to_agent, count(*) 收到, max(to_char(created_at,'MM-DD HH24:MI')) 最后收到 FROM org_mailbox "
               "WHERE to_agent IN ('kairos','zenmind','mac-v5') GROUP BY 1;")))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(f"# 全平台体检扫描 {datetime.datetime.now():%Y-%m-%d %H:%M}\n\n")
    f.write("> 五维×四层;问题五类归档:断线/病带/空转/断链/账实。只读扫描。\n\n")
    for title, body in S:
        f.write(f"## {title}\n```\n{body.strip() or '(空)'}\n```\n\n")
print(OUT)
