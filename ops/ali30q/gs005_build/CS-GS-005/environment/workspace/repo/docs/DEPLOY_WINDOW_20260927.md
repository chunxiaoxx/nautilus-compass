# 部署窗 2026-09-27 晨 · 四项(U27/U28+采纳v5 1164)

> 排程依据:用户 9/27 凌晨批(复活阶段二三+kairos 排活);深夜不动生产纪律,晨窗一次过。
> 两窗分立(9/28 22:00-24:00 = v5 手术窗,另案):本窗与它互不挤,已函 v5 定案。
> 纪律:照 ops/DEPLOY_DISCIPLINE.md;每项独立验证;任一项红 → 回滚该项,不牵连其余。

## 项 0 · fde-runner@kairos 停用(v5 1164 采纳)

- 现状:active running 但 24h 零日志零请求(历史 dmas 病,当前纯闲置=值守盲区)
- 步骤:`systemctl disable --now fde-runner@kairos` → 回读 is-active=inactive/is-enabled=disabled
- 回滚:enable --now(接组织新供给时再启用)

## 项 1 · 明信片协议一期部署(码已备)

- 本地 commit `7bbd986e4`(auto_ack.py + platform_loop.py,[kind:postcard] 前缀:收讫即归档+永不催办)
- 步骤:推分支 → 云端 nautilus-mvp 拉取 → 验证 `grep -c POSTCARD_PREFIX ops/auto_ack.py`(=1)与 `grep -c kind:postcard ops/platform_loop.py`(=1)→ 等 autoack timer 下轮,插一封测试明信片(platform→v5,title=[kind:postcard] 测试·阶段三)→ 15min 内 ack_note="postcard 收讫" 即绿。
- 回滚:git revert 7bbd986e4。

## 项 2 · kairos 模型线切 relay(分歧1已定,9/26 协商)

- 现状:api.minimaxi.com/anthropic(200 OK 但 MiniMax-M3 漂移家族风险,"执行返空"已现)
- 目标:soul 同款——base=https://api.chunxiao.wang(relay,/v1/messages 401 实证端点在)、key=soul .soul-env 的 relay key、model=k3-256k
- 步骤:备份 kairos/.env(.bak-20260927)→ 改 CLAUDE_BASE_URL/key/model → `systemctl restart nautilus-kairos` → 验证:①journal/日志首 cycle 正常 ②INNER boot 行(inner_append "Kairos 2.0 boot") ③日志出现 api.chunxiao.wang 且 200 ④5min 后 cycle 持续推进
- 回滚:.env 还原+restart(配置级,无数据迁移)
- 注意:restart 前确认无 in-flight 任务(读它 self.md cycle 状态);排活消息已读后重启不丢(DB 持久)。

## 项 3 · v5 主脑手术窗(等 v5 报窗需求)

- v5 呼吸手术(写通道第二刀)如 R5 基线考完即排,合本窗一次 restart;v5 域内自决,平台只同步排程。
- 若 v5 今日不排,本窗=项1+项2。

## 窗后验收(全窗)

- autoack 明信片测试绿;kairos 5 cycle 无 exception 且走 relay;roster 全绿;日报(09:07)无新红。
