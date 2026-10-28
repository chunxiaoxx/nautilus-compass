# Phase 3 飞书应用运行契约

> 本文把已确认的第三期业务链路落实为两套飞书应用的运行边界。它是应用配置与
> 后端适配的验收依据，不包含密钥、Base 标识、原始验收材料或外部专家个人数据。

## 运行主链

```text
专家信息公开表单 / 题目预审公开表单
  -> Bitable 题目初始记录
  -> 智涌 Nautilus read-back / 题目自动 P0 / 受控写回
  -> 智涌导师向通过预审的专家发送不透明续办任务卡
  -> 同一任务卡打开受认证的交互证据续办页
  -> 智涌 Nautilus 创建并关联交互成果记录，read-back / 交互自动 P0 / 受控写回
  -> 买方反馈归一化并写回 Bitable
  -> eligible 脱敏投影
  -> V5 v3 事件与 manifest
  -> Compass 独立校验回执
  -> 智涌 Nautilus 受控写回 Bitable
```

飞书多维表格 read-back 是任务、审核、返修血缘和导出回执的唯一业务权威。任何
应用缓存、消息卡片回执、开发对话、截图或日志都不能覆盖该状态。

两阶段权威表为 `第三期专家`、`第三期题目预审`、`第三期交互成果`、`第三期审核与反馈`
和 `第三期导出与回执`。此前的单表入口仅保留为归档迁移来源，不得与上述链路并行接收生产任务。

## 应用分工

### 智涌 Nautilus

Nautilus 是唯一可以在表单初始写入之后发起业务字段变更的应用。它负责：

- 对表单记录做 Bitable read-back，绑定记录版本和幂等键；
- 运行题目和交互两道自动 P0，并写入状态、原因码、置信度、规则/模型版本和导师下一步；
- 仅在题目已 read-back 为 `eligible_for_interaction` 后，发放导师续办并在服务端创建题目、专家和交互成果之间的关联；
- 创建或更新关联审核记录，归一化买方反馈；
- 为导师生成专家本人范围内的脱敏投影；
- 在 V5/Compass 完成受控流程后，写回导出与回执状态。

Nautilus 不得把 `buyer_ready` 写成买方通过，不得绕过 Bitable read-back，也不得把
原始附件、对话、买方原文或身份发送给 V5、Compass 或导师。

### 智涌导师

导师是外部专家的常驻引导与咨询 Agent。它负责：

- 报名、培训、豆包办公任务操作说明和常见问题；
- 查询专家本人任务的可见状态；
- 按 P0 原因码给出返修陪跑与再次提交指引；
- 向通过题目预审的专家发送任务卡，并从同一任务卡续办交互证据提交；
- 使用版本化、脱敏的知识包回答质量问题。

题目预审通过时，导师投影只带短时、单次使用的不透明续办引用。它不是任务码，不暴露
Bitable `record_id`，也不要求专家选择数据表或匹配 UID。Nautilus 仅在服务端会话已绑定到
同一 `第三期专家`、续办未过期未消费且题目 read-back 仍为可交互时，创建 `第三期交互成果`
并写入题目、专家关系。重复卡片投递返回原结果；转发、跨专家、过期或已消费续办一律给出
通用恢复指引。

导师不直接读写 Bitable，不调用内部写入脚本，不查看其他专家数据、原始附件、原始
买方反馈、`revision_of`、最终 `verdict`、V5 或 Compass 内部信息。

## 事件与幂等

正式两阶段事件由 Bitable 创建后的受控元数据事件触发：

| 事件 | 触发来源 | Nautilus 允许动作 | 导师动作 |
| --- | --- | --- | --- |
| `question_created` | 题目预审公开表单创建记录后的 read-back | 绑定专家并将题目置入预审 | 仅发送题目已收到的通用提示 |
| `question_precheck_completed` | 题目自动 P0 完成 | 写入题目预审状态；通过时发放续办 | 按投影解释返修、阻断或开始豆包交互 |
| `interaction_submitted` | 受认证导师续办提交 | 创建受控交互关联并启动交互自动 P0 | 仅发送交互成果已收到的通用提示 |
| `qc_completed` | 交互自动 P0 完成 | 写入交互 P0、原因码和下一步 | 按投影解释下一步 |
| `repair_required` | 自动 P0 或买方反馈产生返修 | 保留前序记录，建立或核验 `revision_of` | 返修指导、提醒重新提交 |
| `buyer_feedback_recorded` | 受控买方反馈映射 read-back | 写入反馈类别与最终业务状态 | 只获得专家可用摘要 |
| `compass_receipt_recorded` | 已验签的 Compass 回执 | 核对绑定字段后写回导出回执 | 无 |

每个事件的幂等键由 `route + Bitable record_id + record_version` 派生。`source_event_id`
用于审计，不参与去重。任何写入必须记录该幂等键并 read-back；重试同一记录版本不得
产生第二条业务结果。

## 最小数据投影

### 导师投影

导师只接收：专家范围句柄、任务范围句柄、P0 路由、原因码、下一步、返修指引、返修
关联码、知识包版本与可选的 `human_interaction_ref_hash`。范围句柄是应用内部不透明引用，不是
Bitable `record_id`。

禁止携带：任何可识别个人身份资料、联系人、银行卡、Bitable 记录 ID、附件、截图、
对话原文、分享链接、日志内容、买方身份、买方原文或其他专家信息。

### V5 投影

V5 只在 `buyer_feedback_recorded` 已 read-back 且导出资格成立后接收：opaque
`task_id`、P0 状态、反馈类别代码、`Gold`/`Repair`、证据哈希与可选交互引用哈希。
资格必须同时核对任务、关联审核和导出记录的买方通过状态、最终 verdict、P0、脱敏和
返修血缘。V5 是 v3 事件/manifest 的唯一签名者，不读取 Base、不写业务状态。

Compass 只消费 V5 的签名 v3 事件和 manifest，独立校验后产生签名回执。Nautilus 必须
验证两端签名，并核对相同的 `task_id`、`event_id`、`payload_hash`、`manifest_hash` 与
导出记录，再用回执幂等键受控写回；任何一项不符均不写回。

### V5 到 Compass 的 v3 签名硬切换

这一节是 Core 对下游的唯一正式契约。它替代此前使用裸 64 位哈希、`task_*` 标识或
未签名 Compass 回执的预演协议；旧 fixture、旧提交和本地报告只能作为历史参考，不能
连接生产链路。

1. **入口资格**：只有 Core 从 Bitable read-back 判为 eligible 的脱敏投影可以交给 V5。
   V5 不把 `canonical_verified` 当作导出前提，也不读取 Bitable、表单、原始材料或开发
   对话。`canonical_verified` / `canonical_blocked` 是 Compass 回执被 Nautilus 验签后才可
   受控写回的业务结果。
2. **四元绑定**：每个 V5 产物和每个 Compass 回执必须逐字相同地携带
   `task_id`、`event_id`、`payload_hash`、`manifest_hash`。`task_id` 必须匹配
   `task_v3_[A-Za-z0-9_-]{1,80}`，不得包含 Bitable 记录标识、姓名、链接或业务原文；
   `event_id` 必须是非空、无空白字符的不透明标识。
3. **哈希格式**：`payload_hash`、`manifest_hash` 和 `receipt_hash` 一律写为
   `sha256:` 加 64 位小写十六进制。裸哈希、不同算法、URL、附件名或可逆业务内容均拒绝。
   `payload_hash` 计算自一个事件的脱敏 canonical JSON；`manifest_hash` 计算自不含
   `signature` 字段的 canonical manifest JSON；`receipt_hash` 计算自不含 `signature`
   的最小回执正文。canonical JSON 使用 UTF-8、键名升序、紧凑分隔符，禁止额外字段或
   字节重排。
4. **签名对象**：V5 使用已登记的 Ed25519 私钥对以下 UTF-8 字节序列做 detached
   signature：`fde.phase3.v3.v5-manifest`、US 分隔符、四元绑定。Compass 使用其已登记的
   Ed25519 私钥对 `fde.phase3.v3.compass-receipt`、US 分隔符、四元绑定、US 分隔符和
   `receipt_hash` 做 detached signature。每份产物都必须带可解析的 `signer_key_id` 和
   `signature`；Core 的信任库根据 key ID 验签，不能以文件名、聊天消息或“导入成功”替代。
5. **受控写回**：Nautilus 先验 V5 manifest，再验 Compass receipt，随后比较四元绑定和
   导出记录的 read-back。仅四项全部相同、两次验签均通过、回执幂等键未消费时，才写入
   `canonical_verified` / `canonical_blocked` 与导入状态。V5 与 Compass 不拥有任何
   Bitable 写权限。

V5 和 Compass 各自必须在自己的仓库提供同一组独立测试：被改动的 JSONL、被改动的
manifest、裸/错误哈希、缺失或未知签名键、无签名回执、错误四元绑定以及重复导入均须
fail closed。Core 在这些测试和首条 Bitable 资格记录均被独立核验前，不开启回执处理。

## 飞书配置验收清单

在开启生产事件前，逐项核验两应用的已发布版本和实际权限：

1. 智涌 Nautilus：机器人/消息卡片、事件订阅、服务端回调、Bitable 读写、附件元数据
   处理、自动化扩展绑定和失败日志可见性。
2. 智涌导师：机器人会话、消息卡片、专家身份绑定、只读投影接口、知识包版本读取和
   无权直连 Bitable 的权限边界。
3. Bitable：专家信息与题目预审两张表单可公开提交但不授予 Base 查看权限；交互成果不
   发布为广泛公开表单，只能由导师受认证续办页提交。Nautilus 的字段写入范围限定在五张
   第三期权威表；导师不保留广泛 Base 权限。续办状态、到期时间、签名键 ID 和回执幂等键
   均为内部字段。
4. 自动化：事件失败必须写入可追踪的 Bitable 审核/处理状态或受控技术日志，禁止以
   聊天消息作为重试队列。
5. 端到端演练：使用一条授权、脱敏的测试记录验证表单写入、P0、导师投影、返修码的
   身份/有效期/单次使用、返修血缘、V5 manifest 签名、Compass 回执签名和最终 Bitable
   read-back。

题目预审表单新增字段或修改公开问题时，先在明确维护窗口内取消共享，再补字段、更新问题、
read-back 并重新公开。交互成果的续办页在服务端契约、会话绑定和关系 read-back 完成前
始终保持不可用；中途失败时保持私有，不能继续接收不完整契约的提交。

当前仓库已提供本地运行契约和测试，但不代表上述飞书开发者后台配置、事件订阅或
生产处理器已经启用。上线前必须逐项 read-back 验证。

代码层现已预留受认证的 `POST /api/platform/fde/phase3/events` 与导师范围内的状态查询
入口；它们在没有注入签名校验、受控 Bitable 仓储、持久幂等存储和导师会话绑定前保持
不可用。API 不接受任意字段更新、原始聊天内容或客户端提供的 Bitable 记录标识替换。
