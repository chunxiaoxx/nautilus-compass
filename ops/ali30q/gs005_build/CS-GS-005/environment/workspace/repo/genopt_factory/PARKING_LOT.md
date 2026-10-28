# 🅿 GenOpt RL Parking Lot (7/3 1:15 钉死)

> **目的**(锚 #3 anti-D + 锚 #5 复用 + 6/14 真痛"狗熊掰玉米"复发防御):
> - 本周(7/2-7/9)GenOpt RL 主线 = 唯一主线
> - **本周不动 anchor #2 之外的任何主线**
> - **不在中途开新战线**(例:MCP Phase 1、content-engine 命名合约、4 框 daemon 化等)
> - **commit 仅在 binding-DONE 状态**(不是"做了一部分就 commit")

## 🟢 本周允许(GenOpt RL 唯一主线内)

| 维度 | 件 | 状态 |
|---|---|---|
| 出题 | 5 → 50 题扩量(用 produce_task.py 派生 variant) | 进行中(6 题 / 5 域) |
| 标定 | H800 GPT5.5 N=3 真 grounded 数据回填 | 进行中(5 题 v7 + QAOA 待) |
| 治理 | Cache 5 轮调试治根 · seed 漂移真证 · --multi-seed 改造 | 部分(件 1-4 中) |
| 工具 | produce_task / gapclosed_runner / verifier_qc / register / persist | 已就位 |
| 文档 | ARCHITECTURE.md · weekly review · SSOT | 7/3 0:55 grounded |
| 跨框 | 4 框单独催球 outbound(7/3 9:00 截止) | 已发 · 等球回 |

## 🔴 本周不动(anchor #2 之外 = 锚 #3 反 D)

- ❌ **MCP Phase 1 ship**(compass 框的球,等接球真回;不是平台)
- ❌ **content-engine 命名合约**(anchor #2 之外,冰冻)
- ❌ **4 框 daemon 化**(5/27 痛复发 — 4 框没真活是事实,本周不开新战线)
- ❌ **破自循环 Step 2/3**(等 A800 真 verified verdict,等不主动拉)
- ❌ **A800 部署流程**(等用户拍 IP/SSH config,平台不主动)
- ❌ **SWE A-class 续产 n=12**(V5 框的球,V5 session 没起我代行 = 复发)
- ❌ **bot 群 / NPS / 真实客户**(5/27 pivot 删了的 = 永久冰冻)
- ❌ **新 benchmark 域研发**(除 Robotics 第 7 题作为 GenOpt 收口 5/5 域,其他 0 启动)
- ❌ **distill_loo 真跑**(等 V5 SWE n=12 + A800 · gate n≥12 不动)
- ❌ **真 broadcast 多 dialog**(SSOT 路径已就位,不在中途改)

## 🪞 真根(锚 #6 治复发)

**6/14 自审**:artifact 多但闭合业务环少。本周**唯一 binding-DONE 标 = GenOpt RL 5-50 题入飞书**(FDE 框接球真回才算 closure)。**真问题 = 入表率,不是 commit 数**。

> "Don't ship 50 题, ship 5 题入表" — 6/14 反馈根

## 🔪 出 parking lot 的 3 个条件(任一)

1. **本周 closure 达成**(5 题入飞书表 + FDE 框 ack 真回 + 真 producer_id binding)
2. **用户 7/9 后拍新主线**(明确 anchor 切换)
3. **北极星中心环 break-self-loop 真跑**(Step 3 + 候选 A 真 verified)

## ✅ 维持纪律检查表(每次 commit 前问)

- [ ] 这件直接推进 GenOpt RL 入表吗?(0 贡献 = 改 park)
- [ ] 这件占用 V5/compass/soul/FDE 该做的活吗?(是 = 改 park)
- [ ] 这件是中途分支吗?(是 = 改 park)
- [ ] 这件产出是真 binding-DONE 吗?(部分 = 改 park,等齐再 commit)
- [ ] 这件有 SSOT 4 行卡在更新吗?(没 = 改 park,先改 SSOT)

— platform-soul · 7/3 1:15 钉死 · 治 6/14 狗熊掰玉米复发

---

## 🆕 7/4 grounded blocker: H800 systemd timer 不能启

**实证(7/4 22:30 grounded · paramiko 真连 H800)**:
- `/proc/1/comm = bash`(PID 1 = `/init/boot/boot.sh` · 非 systemd)
- `systemctl is-system-running = offline`
- `daemon-reload` / `list-timers` 全 `Failed to connect to bus: Host is down`
- `crond` 未安装 · `service --status-all` 无 cron 服务
- H800 是 Docker 容器,init system 不支持 systemd timer 真调度

**Plan Task 5(2026-07-04-genopt-rsi-fde-flywheel-activate.md Task 5)验证状态**:
- ✅ .service / .timer / .sh 三个 LOCAL 文件已写(可作 spec)
- ✅ .sh scp 到 H800 `/root/autodl-tmp/genopt/systemd/` · `bash -n` 语法 PASS · chmod +x
- ✅ 上传到 `/etc/systemd/system/` + `systemctl enable` symlink 已建
- ❌ **daemon-reload 失败** · `list-timers` 不能返回 trigger time · unit 不能真启动
- ❌ **未 commit**(`list-timers` 真验前不算 binding-DONE · 锚 #6 治根不真 ship 假启)

**出 park 条件(任一)**:
1. H800 切回 systemd 真 init(host provider 重启容器 + `--privileged --pid=host` 或换 base image)
2. 用户拍走 cron / supervisord 备援路径(platform 不主动 · 锚 #3 反 D 不重造 daemon)
3. 退回 driver-ssh-push 路径(7/2-7/3 真 work 路径 · 真 binding-DONE)

**目前真路径 = driver-ssh-push**(`harness/genopt_orlib_run.py` 通过 ssh 到 H800 真跑,7/2-7/3 已出 JobShop Easy + TSP Hard 双 grounded 数据 · anchor #5 不重造已证)。

— platform-soul · 7/4 22:30 grounded blocker append
