本轮网络复核已完成，现停止等待协调。bootstrap 已读通；候选 5 卡在 SSH 认证阶段，尚未取得任何远端文件证据。

任务：`COMPASS-MAIN-20261102-NETWORK-STAGE-01`。Owner：Compass 本仓长期主会话 / Codex。写入范围仅为本目录，首轮原件未改；仓库 HEAD 仍为 `e6fe8d55c147bff90b1b90077280ebd2d4c80f01`。

| 核对项 | 本轮读数 | 证据 |
|---|---|---|
| bootstrap | [实测] HTTP 200，success=true，运行身份 compass / agent_id=9000017 | [BOOTSTRAP_MAIL_READBACK.json](BOOTSTRAP_MAIL_READBACK.json) |
| 本框 mail 概要 | [实测] 同次 bootstrap 的未读概要 0 项，due_12h=0；这是本次返回包的范围 | 同上；未 ack、未取正文、未外发 |
| 现有 a100 配置 | [实测] 配置 SHA 与首轮一致，使用已有别名，不输出地址、端口、账号或凭据值 | [SSH_CONFIG_METADATA.json](SSH_CONFIG_METADATA.json) |
| 唯一一次 SSH | [实测] 退出 255，错误类别 `SSH_AUTHENTICATION_DENIED`，发生在认证阶段；stdout 为空 | [SSH_INDEX_READBACK.json](SSH_INDEX_READBACK.json)、[SSH_ATTEMPT.json](SSH_ATTEMPT.json) |
| 候选 5 的数据 | [不可验] 没有目录索引、文件大小/日期、小 metadata 或数组头；不能说远端没有文件 | [CANDIDATE5_DELTA.json](CANDIDATE5_DELTA.json) |

本次 SSH 进程已启动，错误属于 SSH 认证拒绝，没有报告本地执行/网络 `EPERM`。这与“命令不被允许执行”是不同类别。[推断] 请求已进入 SSH 认证阶段；认证拒绝的具体原因尚未核明。没有重试、换别名、换密钥或连其他候选，也没有新建隧道或修改认证配置。

首轮 bootstrap 的原 `URLError` 和 SSH 255 记录完整保留。用户给出的旧 DNS 失败背景也保留；首轮文件没有记录底层 errno/SSH错误文本，不能从哈希补出原因。本次 bootstrap 读通不能倒推旧失败一定由网络权限关闭导致，旧失败也不能用来判断远端文件不存在。

唯一授权目录为 `/root/vdd2/p0_full/out`。已准备的标准库探针只列该目录，metadata 与 NPY 头共享 64 KiB 读取预算，不读数组 payload、不跟随符号链接、不递归扫描。由于 SSH 认证失败，远端探针没有执行；准备了代码不算取得文件证据。anchor 的实际坐标仍缺索引证据，本轮没有拿脚本默认路径冒充已有文件。

10 月的条件点火授权保持原义。当前数据完整性、当前资源状态、完整实验可执行性三项分别未核；本轮网络读数不替代这些验收，也不形成训练授权或永久冻结结论。未新起模型、安装、提特征、训练、下载大数组/权重、重启服务、恢复历史循环、分派子代理或 commit/push/deploy/结算/外发。既有记忆服务沿用，未新增 MCP 召回或服务实例；本地计算线程设为 1。

bootstrap 远端 registry 的 compass 角色文字仍是旧口径。本框继续依照当前用户和本地 catalog 承担长期记忆、assay/jev、压缩×验证与因果倒置模型，不据远端旧文案扩大外联任务，也不修改注册表。

下一动作归协调框：先核对原有 a100 入口的认证条件或安排可用的既有只读执行环境。续轮仍先读取旧 out 目录索引与不超过 64 KiB 的小 metadata/数组头，再由索引确认 anchor 位置；沿用首轮的数据、指标和对照缺口清单。本轮不继续连接。

完整验收见 [STARTUP_ACCEPTANCE.json](STARTUP_ACCEPTANCE.json)。首轮逐文件保全结果见 [FIRST_ROUND_PRESERVATION.json](FIRST_ROUND_PRESERVATION.json)，交付核对见 [DELIVERY_CHECK.json](DELIVERY_CHECK.json)。
