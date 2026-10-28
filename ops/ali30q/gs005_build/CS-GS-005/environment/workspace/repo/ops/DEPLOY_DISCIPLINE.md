# 🚦 部署纪律(三脊柱 · 脊柱1)· v1 生效(2026-07-16 用户拍板)

> 状态:**已生效**。main 已立(GitHub 默认分支,基于 prod-truth-20260715 + 捞入资产)。本文替换 LOOP_STATE_SSOT 护栏#4 的旧 scp 规程。目的 = 终结"4 平行世界"的根因(部署走 scp 不走 git、生产 VM 直改工作区、多副本无主)。
>
> **🔄 2026-08-26 主干换轨(用户拍板)**:7/16 所立的 `main` 于 7/23 后停止演进,实际工作全部在 `soul-distill-deploy`(main 的分叉后代)上。勘察 true-merge 为负 ROI(64,716 冲突),故:**单一主干自今日起 = `soul-distill-deploy`**(GitHub 默认分支);`main` 打归档 tag `archive/main-legacy-20260826` 保留全部历史,活资产(ops/16 + 具身 PPT)已捞入本分支(commit 4641568b9)。下文所有 `main` 均按此换读。

## 铁律

1. **单一主干**:`soul-distill-deploy` 是唯一部署源(2026-08-26 起;旧主干 main 已归档)。其它分支只经 PR 汇入,不直接部署。
2. **禁 VM 直改**:生产 `/home/ubuntu/nautilus-mvp` 工作区必须始终 clean。任何改动先进 main,再拉到生产。发现生产 dirty = 事故,先入库再继续(参照 7/15 静雷入库流程)。
3. **部署 = canonical 脚本执行 Git 拉取,禁文件覆盖代码**:
   ```
   phase3/scripts/deploy-and-verify.sh --preflight-only
   phase3/scripts/deploy-and-verify.sh
   ```
   脚本只接受 clean local main = origin/main + clean production main tracking origin/main。
   `--ff-only`:拉不动 = 生产有分叉或状态异常,回到铁律 2 处理,不 force。
   生产变更阶段必须持有 `/tmp/nautilus-deploy.lock`;并发或陈旧锁一律 fail closed,按 reconciliation runbook 人工核对。
   仓库中旧的部署、迁移、回滚、文件覆盖和直启入口统一为精确 fail-closed wrapper；候选 SHA 中任一 wrapper 内容变化都会在 merge 前被拒绝,不得恢复或新建旁路。
4. **禁手工改 systemd unit**(7/15 override 事故教训):unit 变更进 repo(`genopt_factory/systemd/` 或 `ops/`),经 main 部署,再 `daemon-reload`。
5. **部署前必备份并限制候选范围**:唯一目录保存旧 SHA、`.env`、unit、convergence 基线和 PostgreSQL custom dump;必须验证 `.env` 中的 `DATABASE_URL` 是 loopback PostgreSQL 且库名与 dump 目标一致,再验证空间、dump 可读和哈希。backend/frontend runtime 变化必须另走专用 build/migration runbook;service/timer 变化必须用候选 SHA 显式确认。
6. **部署后必验**:systemd active + MainPID 非零 + localhost health JSON healthy + `https://www.nautilus.social` 主页和 convergence HTTP 200 + income/verdict 数字不倒退,才算部署完成(独立验证优于自报)。
7. **每步可回滚**:部署前记录当前 commit(`/tmp/nautilus_deploy_prev`),更新后任一验证失败只在生产 HEAD 仍等于本次候选时自动切回该 commit、restart 并完成本机与公网复验；回滚态故意 detached,必须按 reconciliation runbook 收敛后才能再部署。

## 生产 main 一次性收敛

- 2026-07-20 只读取证发现生产仍在 `soul-audit-increment1`、无 upstream 且有未跟踪状态文件。
- 在完成 [`PRODUCTION_MAIN_RECONCILIATION.md`](PRODUCTION_MAIN_RECONCILIATION.md) 前,canonical 脚本必须 fail closed,不得部署。
- 收敛过程先保全和哈希异常文件,再由 operator 明确决定归档/入库/脱敏；脚本不代替该决策。
- 当前树已删除被跟踪的生产形态 `.env` 备份并阻止再次提交,但 Git 历史副本仍按泄漏处理；未完成供应商侧轮换、撤销和非秘密证据记录前不得部署。

## 尚缺(不在本草案内)

- 生产凭据轮换、GitHub secret-scanning 复核与 Git 历史处置决策(执行门见 reconciliation Phase 2c)
- backend runtime 依赖升级和数据库 migration 的隔离 venv 专用 runbook

## 自动检查

`.github/workflows/deploy-contract.yml` 在 PR 和 main push 上运行 focused contract tests 与 Bash syntax。CI 通过不替代生产 preflight、备份、状态文件审批或独立部署验证。

## nginx 卫生纪律(2026-10-04 · 复发棘轮物理化第一步)

- 任何涉及 nginx 变更的部署窗,**离开前必查**:`ls /etc/nginx/sites-enabled/ | grep -c '\.bak'` → 必须 0;非零=移 `/etc/nginx/backups/` 后 `nginx -t` + `systemctl reload nginx` + 受影响域名 200 复测。
- 教训链:8/30(sites-enabled 禁留 .bak)→ 10/3 实测 4 个 .bak 残留致满屏 conflicting server name 警告(.bak 文件会被 `include sites-enabled/*` 无差别加载)。
- **验证输出纪律**:探活/清点输出禁止用 tail/head 截断(10/4 曾因 tail -10 截断 ls 误判"4 个活配置消失",nginx -T 定音为乌龙)——列清单必须全量输出。

## /var/log 权限陷阱(2026-10-07 · compass 盘点 B4)

- **凡以 ubuntu 身份运行、又向 /var/log 写新路径的排期/服务,默认是死的**(无权限,静默失败)。
- 正确姿势:日志写 `~/logs/`(ubuntu 属主)或由 root 预建目录并 chown ubuntu;systemd unit 优先 journal(StandardOutput=journal)。
- 教训:compass 盘点发现多个排期面写 /var/log 全部静默死——只查 systemctl 状态看不见(进程退出码为 0 的 wrapper 也会掩盖)。

## 跨框活动量统计去重口径(2026-10-07 · compass 盘点 B9)

- 任何"发函量/活动量/工作量"统计,**一律按唯一键去重**(from+to+content 前 200 字符哈希);按未去重条数排工作量=系统性高估。
- 实证:A 账 20014 条跨框记录去重后 19331 唯一;同一函重投/回执副本普遍存在。
- 探针/报表脚本若输出"总条数",必须同时输出去重数,否则视为无效报表。
