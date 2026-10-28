# Phase 3 Feishu Asset Registry

**Purpose:** Register existing Feishu assets that Phase 3 may reuse. This is an
implementation boundary, not a credential inventory, buyer-data catalogue, or
proof that production configuration is live.

## Reuse decision

复用现有的智涌 Nautilus 作为唯一业务字段写入应用，复用智涌导师作为外部专家的全程引导
Agent，复用现有 Bitable 自动化扩展作为受限触发器。不得为同一业务再创建第二个写入应用、
第二个状态账本或独立专家任务入口。

## Asset register

| Asset or boundary | Current status | Phase 3 reuse rule |
| --- | --- | --- |
| 智涌 Nautilus 自建应用 | reusable, runtime not verified | 仅它可在原生表单初始写入后进行 Bitable 业务字段更新；需逐项 read-back 已发布版本、权限、回调、自动化扩展和失败日志。 |
| 智涌导师自建应用 | reusable, runtime not verified | 用于报名、培训、状态查询、导师续办和返修陪跑；无广泛 Base 权限，只消费专家范围内的脱敏投影。 |
| Bitable 自动化扩展 | reusable, binding not verified | 仅触发已批准的元数据事件；不计算或写入 P0、反馈类别或 `verdict`。 |
| 受控凭据来源 | available, not inventoried here | 只在批准的短时探测或操作中加载；不得打印、复制、提交或写入本文。 |
| 五张权威表 | local schema ready, online read-back pending | `第三期专家`、`第三期题目预审`、`第三期交互成果`、`第三期审核与反馈`、`第三期导出与回执` 是唯一业务状态锚。 |
| 两张原生公开表单 | design ready, online acceptance pending | 只公开专家信息与题目预审；持链接者可提交但不授予 Base 查看权限。 |
| 导师续办 | local API contract ready, runtime not verified | 只有题目 read-back 为 `eligible_for_interaction` 后才向认证专家会话签发；交互成果不能公开自由填写。 |
| 归档表与旧表单 | retain for audit, not runnable | 保留用于追溯；不绑定自动化、不作为入口、不恢复公开。 |
| V5/Compass 后段 | contract ready, production frozen | 只消费符合资格的签名脱敏投影；待独立验证与授权演练后再开启。 |

## 当前冻结

线上尚未形成五表、两张原生公开表单、两应用、自动化扩展及持久运行时依赖的独立
read-back 证据。自动 P0、买方同步、V5 导出、Compass 导入和结算均保持关闭，直到
[飞书绑定 Runbook](FDE_PHASE3_FEISHU_BINDING_RUNBOOK.md) 的每个门槛完成。

## Information exclusions

本文不得包含应用 ID、secret、token、Base 或记录标识、个人姓名、专家资料、买方内容、
原始验收材料或其副本。Schema 探测与 Skill 文档同样不读取这些内容。
