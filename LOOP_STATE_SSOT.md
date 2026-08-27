<!-- FDE_T1_LOOP_STATE_VERSION: t1-constitution-v1.0-20260730 -->
# 第三期 T1 闭环状态（当前唯一生效）

- constitution_version: t1-constitution-v1.0-20260730
- as_of: 2026-07-30
- business_state: S0_NOT_ACCEPTED
- external_state: FROZEN
- claim: 尚未跑通，尚不可邀请专家开始任务
- supersedes: 本文件下方所有冲突的旧状态、旧下一动作和旧 DONE 声明

> 规范性边界：本区块是当前状态单一真相源。区块结束后的原正文仅为历史记录，不得据其发送通知、公开入口、部署、写业务数据或宣称完成。

## 已确认的基础

- 当前专家权威表为 tblxRjSYEkdKxpVT；历史“20260723 第三期专家信息”不是当前准入入口。
- 五张 Bitable 的业务结构已建立。
- 题目预审与交互成果在结构上已分表，并具备关联规则。
- platform-t1-interface-v1 已定义专家状态、字段边界和两道运营发布闸门。
- 培训 microguides 只是本地内容源，不代表专家端已上线。
- 旧一次性公开 Form 不是 Agent 工作流入口；继续对外发送已冻结。
- ecc-fde-external 属于二期遗留，当前 T1 禁用。

## 尚未验收

- S0 OAuth redirect 的生产配置与发布探针。
- 飞书身份与权威专家记录的绑定。
- 新人/已有专家的条件化报名。
- UID 一次绑定及不可静默覆盖。
- 智涌Nautilus 生产导师卡片与阶段工作台。
- 锁题/开放交互闸门与提交甲方闸门。
- 甲方 Sheet GXZrwAIHLi2H7Okk7L6cqIxfnZf?sheet=3fEOVf 的字段适配、去标识化写入和独立读回。
- 一位真实专家首题的端到端证据。

## 当前唯一下一动作

平台侧只实现并验收 S0 身份与准入纵切：

受控邀请
→ 本人OAuth
→ 权威专家表精确匹配
→ 条件化报名或补缺
→ UID一次绑定
→ Bitable写入并独立读回
→ 仅向该专家返回S0 continuation

培训侧保持冻结，只校验宪法版本和准备既有内容接入，不新增材料、入口或状态。

## S0 的硬阻塞条件

任一条件不满足均不得联系专家或发送任务入口：

- OAuth redirect URI 已在生产飞书应用精确配置并发布。
- 应用拥有权威 Base 所需读写权限与 IM 所需权限。
- 目标专家存在正式记录或通过条件化报名形成记录。
- 姓名、飞书身份和 UID 校验无冲突。
- Bitable 写入后独立读回成功。
- 邀请一次性、可过期、不可二次使用。
- 失败提示不泄露 UID、记录 ID 或内部状态。

## 角色锁

- 平台对话框：身份、状态机、权限、接口、Bitable、部署、读回和审计。
- 培训对话框：既有招募/运营训练和专家微指引内容；不得改 Bitable、状态机、身份、接口或部署。
- 跨对话框消息必须携带 constitution_version；缺失或不一致时停止实施。
- 未经用户明确授权，不得改变本区块的范围、权威顺序或唯一下一动作。

<!-- END FDE_T1_LOOP_STATE_VERSION: t1-constitution-v1.0-20260730 -->

# 🎯 LOOP STATE · 单一真相源 v4(2026-07-07 重写 · 用户拍"过于混乱,重新梳理")

> 当前状态唯一权威。各框 session-start 必读;与任何 goal/memory/文档冲突,以此为准。
> 变更协议:先改这里(canonical = nautilus-core),再开工,再同步各 repo 根副本。
> 7/7 前的全部历史层(推断纠正/实施日志/A800 候选/蒸馏条件)原文在 `docs/LOOP_STATE_ARCHIVE_20260707.md`,这里不再重复。

---

## 零、Phase 3 单链 RACI（2026-07-22 覆盖条款）

本节覆盖本文件及各 repo 副本中与第三期交互式标注相冲突的旧职责表述。
它是职责和放行门，不等同于已经实施、已接入线上飞书，或首条记录已经闭环。

### 唯一权威与单链

飞书多维表格的 **read-back** 是第三期任务状态、审核结果和
`revision_of` 返修血缘的唯一权威。Agent 文字、截图、文件名、本地缓存、
V5 manifest 和 Compass 回执都不能代替 Bitable read-back。

```text
Bitable read-back
  -> V5 最小 v3 脱敏事件 + manifest
  -> Compass 独立校验 / 隔离导入 + 受控回执
  -> Core 受控回写 `canonical_verified` / `canonical_blocked`
  -> 成功导入后回写 `compass_imported` -> Bitable read-back
```

### 职责、输入与输出

| 责任方 | 只负责 | 允许输入 | 唯一输出 | 当前阻断与下一步 |
|---|---|---|---|---|
| Core / FDE | 状态机、字段映射审批、专家信息/题目预审入口、受控 Bitable 写回门 | Bitable schema 元数据、已批准字段映射、受控 Evidence Pack 引用 | Bitable read-back 的题目、交互、审核、导出记录及 eligible 判定 | 五张两阶段权威表和导师续办合同已在本地定义；阻断于维护窗口的 schema read-back、两应用事件订阅、持久会话/幂等存储与首条授权脱敏演练。不得创建平行记录。 |
| V5 | 消费 eligible Bitable 记录，生成最小 v3 脱敏事件和 manifest | Core 提供的 eligible read-back 锚、受控派生 `task_v3_*`、批准字段白名单 | 签名 v3 JSONL/manifest 与 `task_id`、`event_id`、`payload_hash`、`manifest_hash` 绑定 | 阻断于没有 eligible 首条记录和下游硬切换实现；只可在 V5 repo 完成签名/篡改拒绝测试，不能自行取数、写表或导出 |
| Compass | 独立校验并隔离导入 V5 v3 事件与 manifest，生成受控回执 | V5 的正式脱敏 v3 JSONL、匹配 manifest、V5 公钥信任材料 | 对同一四元绑定的签名回执；成功导入确认后由 Core 受控回写 `canonical_verified`/`canonical_blocked` 与 `compass_imported` | 阻断于没有正式 v3 输入和 Core 信任链适配；只可在 Compass repo 完成验签/幂等/篡改拒绝测试，不能自行导入任务或裁决 |

### 禁止项

- 不得建立平行任务、审核、返修或最终判定账本。
- 自动 P0 只能按批准规则路由，不得写成甲方通过；V5 或 Compass 不得替代甲方
  `feedback_class` 或 `verdict`。
- 不得读取、转发或导出原始对话、截图、附件、个人信息、联系方式、银行卡
  或甲方原始验收材料。
- 除公开原生表单创建的 pilot 初始记录和 Nautilus 的受控 read-back 写回外，不得
  创建平行业务记录、买方同步或线上导出。返修、V5、Compass 与结算须分别通过自己的
  字段、权限和首条记录门槛。

### 放行与同步协议

首条闭环的顺序固定为：目标 Base 只读 schema probe -> 字段映射批准 ->
外部提交与人工审核均有 Bitable read-back -> V5 脱敏导出 -> Compass 校验与隔离
导入 -> Core 受控回写 `canonical_verified` / `canonical_blocked` -> 成功导入后回写
`compass_imported` -> Bitable read-back。任一步失败，停在该步并记录阻断原因。

变更顺序固定为：先修改 `nautilus-core/LOOP_STATE_SSOT.md` 并单独提交，
再由 V5 和 Compass 在各自 repo 根副本同步同一 RACI；副本不得自行扩写职责或
覆盖 canonical。

### 当前落地状态（2026-07-24）

- 已确认的目标权威 Base 是五张表：`第三期专家`、`第三期题目预审`、`第三期交互成果`、
  `第三期审核与反馈`、`第三期导出与回执`。外部可见入口只有专家信息表单和题目预审表单；
  交互成果由智涌导师同一任务卡中的受认证续办页提交，绝不要求专家匹配 UID、选择表或输入
  任务码。旧统一任务表不是新的生产入口，旧预审/成果归档只能作为 metadata 复用候选，不能
  恢复为第二条业务链。
- 用户已授权删除空默认 `数据表` 并进入维护窗口，但实际线上删除和 Base 改造尚未执行。执行
  前必须再次 read-back 默认表字段、Form 共享状态和自动化绑定；发现任何异常即停止。不得读
  取记录、附件、专家数据或甲方原始材料。
- 本地已具备元数据迁移安全门、两阶段 schema、受控关系写入合同和短时单次导师续办凭证；
  自动 P0、返修关联、买方字段映射、V5 v3 导出、Compass 导入和结算仍未启用。Core 尚未接入
  受控 Bitable 仓储、持久幂等/续办存储、飞书验签、导师会话绑定或应用事件订阅。
- 下游统一采用 `task_v3_*` 与带 `sha256:` 前缀的四元绑定。此前的裸哈希、`task_*`、
  无签名回执预演协议已作废；V5 和 Compass 只能各自在本仓硬切换并提供独立篡改拒绝证据。

## 一、北极星(不变)

FDE 产难题(强解+弱难倒 = 燃料)→ 蒸馏 → 系统可证变强(① 模型权重 ② agent 群体自治)→ 产更难更值钱的题 → 每圈外部 benchmark 证明。**分叉过滤器:一件事不直接推进这条链,默认不做。**

当前阶段目标(7/6 /goal · 用户拍):把已走通一次的闭环从 one-off 变成
**(a) 活 producer 自持产出(income 自动持续涨)+ (b) 甲方可交付(11 道合规题入飞书表)**。
不扩 1000 题,不碰蒸馏(A800 到位再解冻),不开新战线。

## 二、当前真值(7/7 · 全部可独立复核,出处 = 记分牌/探针/DB)

> **🔴 8/24 增量(用户拍板 · compass 框落笔)**:**genopt 自产变体族铸币已停(约 8/22 起)**——该管道 income = B(外部真值)0 的自印发空转,与北极星无关,故主动关闸。**income/自治率/settle 等自铸口径指标自此废弃,不再作为收敛指标**;8/16-8/21 该管道曾恒定 7-10 铸/日(详 compass memory session_income_flatline_rootcause_20260824),停后记分牌 income 不再增长属预期非故障。**接棒生产端 = V5 g2b1 真燃料线**(双门:starter 必败/fix 必过;8/24 四仓 86 题自检 71 OK,见 `_OUTBOUND_FROM_V5_TO_PLATFORM_20260825_g2b1_qc_full86.md`)+ gold-replication 3 Gold。中心环唯一裁决点仍是 **L4a 蒸馏判据(due 8/29,预注册决策树)**,出结果前其它不算进展。

> **🔴 8/25 增量(platform A1 loop 监督 · 3 轮读数)**:① income 7d +2220 已归因消解——全是 gmint genopt 停闸前最后一波(gmint-deterministic 156 + gmint-minimax 21,最后铸 8/22 11:05 后平线),与"自铸停"一致,非故障。② **g2b1 真燃料线在跑**:云 DB `g2-b1-repair-executor` verdict 8/24 17时→21时 11→25 条(全不同 task_uid,幂等纪律在守),但 external_verified 全 false,**双门/独立复核 25 条积压未消化**(平台下轮抽验)。③ `/api/health` 已 200(502 已被修好,8/1 记录过时)。④ **L4a 催办已发**(platform→V5 `20260825_l4a_urgent` + 云端 memory):已知阻塞全解除(薛美雪燃料=`vtf/batch_guoshu_202607/fuel_pool/xuemeixue_001`·GPU=智星云 CLI 一键管·协议判据齐),但 V5 执行侧零起跑痕迹。**升级线:8/26 22:00 +0800 前无回执/无起跑证据 → 记"L4a 大概率跳票"并升级用户。**

> **🔴 8/25 二次增量(compass 纠偏 · `compass-l4a-status-correction-20260825` · 覆盖上段催办前提)**:**L4a 首跑已跑完且 compass 验收 PROVEN,合约已核销**——蒸馏 v3:1.5B base 0/4·0/8 → distilled 4/4·8/8;7B 跨族 base 8/10 → adapter 9/10。证据押送 compass 仓 main `_v5_proof_deposit/`(3536353),compass 独立复算逐项一致 + n=3 双门抽查含同坏题复现。**边界:单族族内泛化/pass@5 口径**,非全量宣告。平台 A1"零起跑"判断的 confound=proof 不落盘(V5 老毛病,实物最终落了)。**下一轮=混训蒸馏轮(拒采 80/族→混训→押送→验收),V5 拒采进行中,deadline 自定**;平台 A1 催办对象随之改。中心环状态从"待证"升级为"**机制首次 PROVEN(弱边界)**,放大验证中"。

> **🔴 8/26 增量(platform 独立判分 · `v4-trainset-verdict-20260826`)· v4 混训蒸馏轮 = 负(配方级)**:GPU 649392 实物拉回(gen 两臂+tasks+traces 391 条),平台逐条独立复现(pytest 级 verifier,探针三层 confound 已排除+全 0 抽查 reason 证真):**训练集 base 0/30 · distill 1/15;held-out base 0/22 · distill 0/14**。对比 v3 首跑训练题 4/4 → **多族混训配方下注入本身退化**(非泛化问题)。distill 臂 29 条中 20 条裸输出无围栏(合规性负信号)。归因候选:7B 多族配比/SFT 样本格式/train-gen 分布。**裁决(预注册三态):负——但杀的是"多族一锅混训"配方,不是蒸馏假设**(v3 单族 PROVEN 仍立)。下一步=V5 归因后单变量复跑(族数/格式/配比),或退回单族逐族蒸。原始产物与判分:`nautilus-core/phase3/backend/docs/evidence/v4_*`。已通报 V5(outbound v4_trainset_negative + 云 obs)。

> **🔴 8/26 二次增量(双判分互核 + V5 归因升级)**:V5 自判 v4 同为负且更深——1.5B(0/28·0/25)与 7B(b0f1b24,0/23·0/30)双规格全 0 → **结论从"配方级"升级为"任务类型级":单步补成式蒸馏可注入协议/格式合规(v3 本质),不可注入陌生 repo 真修复策略**(391 条全验正确轨迹也学不进)。"蒸馏破能力墙"假设收窄为"蒸馏破协议合规墙"=边界地图。平台判分(7B 轮 train distill 1/15·holdout 0/14)与 V5 同向,唯一分歧 1 条过疑提取口径,不改裁决。**正资产:V5 双臂筛管线落地(minimax 全 0×deepseek>0 → 68 题出 8 题真 A 类,391 轨迹就绪,纯 API 零 GPU)**。🔴 **呈用户决策点**:真修复类蒸馏 a) agent-loop 多步轨迹(重设计) b) 显式课程化,或 c) 收缩——协议域单族模式先商用(垂域 QC 降本试点),真修复进 parking。平台票投 c(正现金流优先),等用户+V5 两票。outbound v4_cross_confirm 已发。

> **🔴 8/26 三次增量(用户拍板 · 决策点 c 生效)**:**真修复类蒸馏(a 多步轨迹/b 课程化)进 Parking Lot,解冻条件=协议域商用产生收入或新方法灵感;主线下一步=协议域单族模式商用**——首个落地场景=垂域交付线 QC 降本试点(蒸馏模型做 verdict 初筛/格式门,人只看边缘案例,试点料=验证积压+垂域 23 题 QC 流水);同步推进垂域 23 题交付临门一脚(补题/整改/脱敏)。8 题 A 类+391 轨迹冻结保存(资产不解冻不弃)。V5 重测(gen_distill 53 条)后台判分中,结果只作 v4 归因脚注,不改变本决策。

> **🔴 8/26 四次增量(用户拍板 · 组织变更)**:**FDE 框退出业务推进,垂域交付线(国曙 23 题)由数据飞轮框接续**。交接清单已发飞轮 outbound(flywheel-takeover-20260826):台账/整改单位置、6 人补交名单、整改单未下发、反馈表 16 题待判、通过 5 题结算。平台侧机器活现状:**国曙附件包本机未寻获(7/18 扫描 82 违规文件的源不在当前路径)→ PII 脱敏阻塞待飞轮定位附件包**;12 题 A 候选双臂筛需先按台账"验证器思路"列构造 verifier(非即跑活),已作为任务单入交接。

> **🔴 8/26 五次增量(v4 重测翻案 · `v4-rerun-flip-20260826`)· 修正本日三次增量**:V5 重生成 gen_distill(53 条)平台独立判分(抽查 pass 证真,commit cb6b38ed1):**train distill 8/30 vs base 0/30**(三题有信号 4/6·3/6·1/6)·holdout 1/23 vs 0/22。首轮 1/15 系生成故障低估。**v4 修正为 INCONCLUSIVE 偏弱正**:训练题部分注入成立(27%),跨题泛化仍≈0。影响:①"任务类型级"结论弱化为"单步补成式可部分学进训练题但不可迁移";②商用边界与**决策 C 不变**(真修复能力仍不可卖);③V5"1.5B/7B 双规格一致"待 1.5B 重测坐实(可能同样被生成故障污染)。互核链条(平台判负→V5 重测→平台翻案)证双判分机制必要:单边判分两边都会错。

> **🔴 8/26 六次增量(agent-loop 解冻 · 用户拍板 `v5-agentloop-unfreeze-20260826`)· 部分修订三次增量**:V5 提 agent-loop 轨迹蒸馏方案(不教答案教解题循环:出代码→verifier→失败喂回→修正,≤4 轮;P1 采样器纯 API 半天 + P2 compass 记忆增强 + P3 多轮 SFT mask 一次 GPU ~2h,成本 v4 的 1/3;判据预注册:P3 训练题>0→形态正确,仍全 0→SFT 关闭只剩 RL)。**用户拍板解冻(解冻条件"新方法灵感"触发)**,前置门=**三臂对账**:V5 须先交代 1.5B×391/7B×391/mask+CoT×131 各 eval 哪个生成批次,eval 旧生成故障批次的臂须重生成再判(v4 翻案同款纪律),对账前 P3 不上 GPU。平台照 v4 模式独立判分互核。**边界不变:训练题>0 也不改商用叙事(协议域);主线 QC 降本试点照跑,v0 门已上岗**(23 行判读与人工 QC 完全一致零漏判零误伤,`vtf/batch_guoshu_202607/verifiers/qc_gate_v0.py`·判据预注册 v0/v1/v2 见 `docs/plans/2026-08-26-qc-pilot-protocol.md`,v1/v2 阻塞于附件包定位)。另:git 单点风险已消(soul-distill-deploy 已推 GitHub 至 22163f211);main↔sdd 真分叉 1509/119 需专场合并。

> **8/26 八次增量(dogfood 设计回执跳票 · 22:00 期限到点)**:dogfood 监督接线设计(docs/plans/2026-08-25-dogfood-supervision-wiring-design.md · trace_id dogfood-supervision-wiring-20260825 · 8/25 广播征三票)**零回执**——V5/compass 仓根无回函、compass 云记忆无 ingest、用户未表态。跳票归因:8/26 V5 注意力全在 agent-loop 提案/解冻,监督接线被生产优先级挤掉。处置:平台先行用现有 cron/A1 模式顶监督(design 评审不阻塞日常读数),设计三票(用户+V5+compass)转常设待办不设新 deadline,等 agent-loop 对账窗口后自然回收。**用户随即拍板强推三票评审(同日)**:催办函已投 V5/compass 仓根+云 obs(dogfood-supervision-wiring-20260826-reminder),回执格式降为一句话,**新 deadline 8/27(周四)22:00 +0800**;用户侧两问(P1 推真 telegram 可否/P4 后 loop 退役授权)**已于 8/27 拍板并入设计**:P1 授权+护栏(≤1 条/周+trace_id 标识),P4 授权+影子期判据(2 周双轨零分歧后退役,代码保留可复活)。设计动工只等 V5/compass 两票(deadline 8/27 22:00)。

> **🔴 8/26 七次增量(拓扑债收口 · `main-archive-cutover-20260826`)· 销账六次增量遗留的"main↔sdd 专场合并"**:合并专场勘察(merge-tree 干跑):64,716 冲突文件(4.1 万 = `_dead_code_backup` 垃圾目录互斗 · 141 content · ~2.1 万 add/add,含全仓 LF 规整 commit 放大)= **true-merge 负 ROI,弃**。用户拍板"捞资产+归档+换轨":① main 独有活资产 29 文件捞入 sdd(ops/16 含部署纪律 DEPLOY_DISCIPLINE 回家+drift/a2a/sot systemd 套件 · 具身 PPT plans 8+presentations 5,commit 4641568b9;其余 985 文件 = 死代码/历史文物,留归档);② main 打归档 tag `archive/main-legacy-20260826`(119 独有 commits 历史完整);③ **GitHub 默认分支已换轨 soul-distill-deploy**(gh api 读回验证);④ DEPLOY_DISCIPLINE + 本文件护栏#4 主干名同步更新。**单一主干达成,git 拓扑债清零**(六次增量末"需专场合并"待办就此关闭,处置=弃 merge 换轨)。

> **8/1-2 增量(平台框实测,详 memory s0-merge-deploy-20260801)**:S0 admission **v3**(生产 VM 手放版,对齐 7/30 宪法)已回收入库并上生产(`77652fccb`·合并 fde-phase3 worktree 77 提交)·部署前后记分牌逐字不变=账本无损·**income 703 自 7/15 零增长第 17 天,题池枯竭未解(球在 V5/FDE 产题侧)**·`/api/health` 502 根因坐实(nginx 指死端口 8001 + backend 无路由,未修)·云上残留 dirty worktree `distill-deploy` 与分支名 soul-audit-increment1 待正名。记分牌 8/1 直读:verdict **76**(7d +5)·income **703**(7d +0)·自治率 **90.8%**(69/76)·settle 0/3618。

| 指标 | 值 | 说明 |
|---|---|---|
| income(agent 9000009) | **703**(7/16 探针,7/15 起持平)| ⚠️ 7/15→7/16 零增长 = 题池枯竭信号仍在(mint 重刷旧题被幂等门全拦),产题供给是唯一瓶颈。历史注(7/8):| 🎯 **目标(a)"自持产出"字面达成**:平台 7/8 产 2 道新变体(bin_v3+cache_v2,数据全新 seed 20260708)放进 mint glob 路径 → daemon 自动拾取/解题/canonical verify/铸币(+86/+13,与产题 QC 预测分毫不差),全程零人工。**模式已证:income 斜率 = 产题速度,题目供给是唯一手动环节**。TSP 97.63 不铸维持原判(overall_pass=false 非交付档)|
| 外部验证 verdict | **67**(7/18 记分牌直读,7d 内 +26;income 703 · 7d +100 · 自治率 89.55%)· 历史:65(7/16)| 历史注(7/8,时值 16):| auto-verify daemon 自动验证在持续;7/7 深夜后新增 6 条全 autonomous **但全是同题重跑**(cache×3/bin×3),幂等门全拦零铸币 = 门有牙齿 + **题池枯竭信号**:genopt-mint 无新题可选在重刷旧题(浪费 LLM 成本,V5 宜让 mint 跳过已铸题)|
| **producer 自治率** | **89.2%(58/65)**(7/16 探针)| 历史注(7/8,时值 56%):| 7/7 晚脱 0(V5 修假成功 a3795c2 → 3 条 autonomous 铸币);此后新增全 autonomous 但系同题重复,含金量看 income 不看该比率。**真瓶颈回到题目供给(变体题/11 题)**,非 producer |
| settle 含金量 | **0/3617** | 旧自循环账,维持原判 |
| 甲方交付 | **11 题需求已作废(用户 7/18:"现在没有这个需求")** | 接棒:垂域批次已接手(国曙22人23题·台账+整改单+机械QC done)。**7/18 燃料链首闭:薛美雪题成为第一道完整 A 类蒸馏燃料(doubao 2.0-pro 难倒 0/5 · GLM-5.2 强解 3/3 带 CoT · 确定性验证器,入池 vtf/batch_guoshu_202607/fuel_pool/)**;张欢题 10/10 未难倒判非燃料——实证:燃料分布外性=概念边界密度(时点/口径之争)非算术难度。待办:5 人缺题补交 · 整改单下发 · 全批附件机械脱敏(PII 扫描 82 文件违规) |
| 记分牌 | `GET /api/platform/convergence` | 收敛 = 这 5 个数字的走向,不是叙事。⚠️ prime-001 旧 PID 884064 已不在,但自治轨迹在产 = V5 侧有新进程,身份确认球在 V5,平台不动进程 |

基础设施:cloud backend = systemd 管(nautilus-backend.service · 8000)· auto-verify daemon 10min 轮 · prime-001(PID 884064)连续跑 7 天勿动 · GPT5.5 cloud 直连稳 · doubao ARK 本机通(偶发代理抖动)· T4/H800 已关 · A800 租赁中。

## 三、系统职责一句话(谁是什么 · 治重复造轮子)

| 系统 | 唯一职责 |
|---|---|
| 平台 backend | 经济与验证的账本:verdict / external-verify(income 唯一门)/ 镜子 / 记分牌 |
| genopt_factory | 题目工厂:出题 + runner(存完整解)+ verifier |
| soul canonical verify | 独立裁判:复现一致才盖章(已由 daemon 自动化) |
| compass | 记忆 + 独立审计探针(自报不算,它读 DB 才算)+ feishu 读写 |
| V5 / prime-001 | 生产 agent:产可复现轨迹 → persist → 被验证 → 挣 income |
| FDE | 人的业务:选题内容 / 招募培训 / 甲方交付内容(不背 infra) |
| fde.nautilus.social | 教材层(只读,已开放,学员入口 /start/) |
| 飞书多维表格 | 操作台(领题/提交/评分/结算;培训期只用 3 张表) |

## 四、各框本周唯一一件事(做完才领下一件)

- **V5**:修 `fde_claim_produce` 假成功 + runner 存完整解(两份合约 due 7/9)→ 产出**第一条自治合规轨迹**(带 `artifacts.autonomous=true`)→ 自治率脱离 0%。
- **platform(本框)**:主线定位(用户 7/7 拍)= **为整套业务体系(LLM 后训练 FDE + RSI + ENG 基准 + 具身智能数据采集)做减法和闭环**——守裁判链与账本(auto-verify/记分牌/backend);配合 FDE 用 `produce_task.py` 产**互不相同的变体题**;题集就位后跑 checklist 盲点测试(M1 修正口径:T1 开放题无"难倒",测的是 checklist 可判性 + 模型盲点密度;pass@5 难倒门只适用 T3 基准)。
- **compass**:三角色(用户 7/7 问分工后定)= ① **收敛执法**:5 记分牌数字 + FDE 培训链(学员/题目/派活行数)每日独立读数,自报与探针不符即亮牌;② **合约管家**:活合约到期核销(读 DB/表验收,不闭标红);③ **记忆守门**:四代资产台账 recall 前置(任何框"我先写个"之前先查),产"减法清单"(15 表/13 SOP/50 脚本标 活/死/冻结,给用户拍砍)。**不做**:生产、内容、新架构。
- **FDE**:①选定 11 道题内容(合约 due 7/10,候选 = L3 基准样例 43 道)②陪跑第一批真人培训 = 体系唯一验收(学员卡住处记下来当整改输入)。**基建冻结:不加表、不加 skill、不写新 T 文档;repo 根建一页 FDE_LOOP_STATE 锚治失忆**(7/7 审查:6 月 v0.8 体系被自己遗忘、7 月重造更差版)。
- **soul-verify**:维持 canonical 链;计时型 verifier(Attention 类)的验证协议设计进 parking。
- **用户**:带第一批真人培训(入口 https://fde.nautilus.social/start/ 已开放);A800 到位说一声。

## 五、活合约(compass 派 · 到期必须有交代)

| 合约 | 给谁 | due | 状态 |
|---|---|---|---|
| grant_survival(探针读权)| platform | 7/9 | ✅ 7/7 兑现(三张真值表 GRANT)|
| settle_routes_404 | platform | 7/9 | ✅ 7/7 兑现(messages 双前缀 + 镜子端点)|
| fake_success_produce | V5 | 7/9 | 🔴 进行中(自治率脱 0 的钥匙)|
| evaluate_artifacts_fix(甲方 7/7 反馈)| V5 | 7/9 | compass 已代修一版,V5 收口 |
| cache_income_finding 集成 | V5 | 7/10 | 待接 |
| 11 题内容 | FDE | 7/10 | ⚫ 作废核销(7/18 用户确认需求已无;接棒合约=垂域出题第一批,等用户交题) |

## 六、硬护栏(压缩版 · 全文见归档)

1. **外部 gate 经济学(C 口径)**:external_verified 只看独立复现;income 再加两门 = 难度档合格 + 每题每 producer 只铸一次。
2. **producer 必须是注册整数 agent**(§0-ARCH);Claude 对话框是脚手架,不算系统组件。
3. **自报不算,探针才算**:任何 alive/done/income 声明以 compass 读 DB 为准。
4. **部署规程(7/16 换轨,用户拍板 · 8/26 主干更名)**:以 `ops/DEPLOY_DISCIPLINE.md` 为准——**单一主干 = `soul-distill-deploy`(2026-08-26 起,GitHub 默认分支已换轨;旧主干 main 归档于 tag `archive/main-legacy-20260826`,活资产已捞入 4641568b9)**、禁 VM 直改、部署 = git pull --ff-only 禁 scp 覆盖代码、禁手工改 systemd unit、部署后必验记分牌。过渡期若确需 scp,同一改动必须同步 commit 进主干。仍禁手工 kill/nohup;pkill/pgrep -f 会自匹配 ssh 命令行。底座融合状态见 `RECOVERY_STATE_20260715.md`。
5. **可复现契约**:轨迹必须带完整解 + sha256;preview 一律拒。
6. **不重复造轮子**:动手前先查已有资产(7/7 教训:fde.nautilus.social 整套 v0.8 被遗忘重造)。
7. **confound 先核再下结论**;n≥12 才跑 LOO;买方名绝不出现在对外内容;"真"只作真实义,不作强调副词。
8. **甲方红线**:专家亲笔,AI 痕迹零容忍;附件脱敏;交付走飞书表。

## 七、Parking Lot(冻结 · 解冻条件写明)

蒸馏维①(等 A800 + n≥12)· SWE 链 verify 候选 A(等 A800)· 1000 题扩量(等 11 题交付)· Attention 计时型验证协议(等 GenOpt 主链稳)· 新陈代谢/income 花销(等自治率>0)· FDE 4 skill 发版 / RBAC / mkdocs 新增(等真人 gate 过)· compass MCP 耦合 Phase 1-4 · content-engine 命名合约 · **具身智能数据采集线**(用户 7/7 首提:先进 FDE_BUSINESS_CHARTER 立业务锚(甲方/口径/turf)再动一行代码,防再走散落失忆老路)· 专家进 agent 经济账本(等自治率>0 + 首批学员跑通)· 导师多轮会话态 + 注册整数 agent(等出题 Copilot 单消息版跑通)。

## 八、各框 turf(一行版)

platform-soul = infra/账本/裁判链部署;soul-verify = canonical 复现;V5 = 生产 agent 与 RSI;compass = 记忆/探针/feishu;FDE = 人的业务内容;用户 = 拍板/真人 gate/算力。

---
*维护:状态有变 → 先改本文件 → 同步 V5/compass repo 根副本 → 记 memory。历史查 `docs/LOOP_STATE_ARCHIVE_20260707.md`。*
