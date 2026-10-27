# 中转站运维变更清单（OPS CHANGELOG）

> 范围：manus 上的 new-api（api.chunxiao.wang）渠道/路由/守护体系
> 格式：每条 = 时间 · 变更 · 验证 · 回滚指针
> 配套：`relay_alert.sh`（告警）、`relay_zhipu_guard.sh`（ch1 守卫 cron）、`backups/`（DB 备份链）

---

## 2026-10-25

### 19:5x · 400 溢出路复发 → 根治（ch13 只留 flash）
- **复发**：18:39-19:46 持续 400。机制（日志实录）：`ch4 429(12/min) → 重试:4->13 → ark glm-5.3 纯文本+图 → 400`。14:5x 的"降优先级"只是把洞从主路挪到溢出路；且 400 是硬失败（客户端不像 429 那样自动重试）。
- **根治**：ch13 摘除 `glm-5.3`/`glm-5.3[1M]`（abilities+models），只留 `glm-5.3-flash`（ark 支持图）。溢出改走 ch1 官方（官方 glm-5.3 非 flash 带图实测 200）。
- **验证**：三档带图全 200；20 并发打满 20/20 全 200（溢出落 ch1×5），400 归零。
- **判据**：①腿必须能吃该模型名的所有请求形态（文本+图）；②降优先级不根治，摘除纯文本腿才是；③改完必须做打满限速的溢出测试。

### 14:5x · 修复多模态 400（glm-5.3[1M] 带图）【注:此法后被 19:5x 条取代】
- **症状**：客户（Claude Code，`/v1/messages?beta=true`）6 次 400 `Model only support text input`（14:11-14:22）。
- **根因**：ch13(ark-glm) 的 `glm-5.3-flash` 支持多模态，但 `glm-5.3` 与 `glm-5.3[1M]`（mapping→glm-5.3）是**纯文本**；两者 pri 0 高于第三方的 -5，客户带图请求先撞 ch13 → ark 拒收，400 不换腿。
- **变更**：ch13 的 `glm-5.3` 与 `glm-5.3[1M]` ability **priority 0 → -8**（排到支持多模态的 ch4/ch5 之后）；`glm-5.3-flash` 保持 0（ark 实测支持图）。
- **验证**：`[1M]+带图` → 200 落 ch4；20 发/分钟打满限速 → **20/20 全 200 客户端零失败**（内部 ch4 429×14 + ch5 429×7 全被自动换腿吸收，ch13 承接 26 次）；修复后 400 归零。
- **能力矩阵实测**（带图）：ark glm-5.3/5.3-air ❌纯文本；ark glm-5.3-flash ✅；ark kimi-k3 ✅；07211996 glm-5.3 ✅；官方 glm-5.3-flash ✅；ai80 claude ✅。
- **回滚**：abilities priority 改回 0 即可（无 DB 备份需求，纯 ability 行）。

### 13:5x · 新增 ch13 ark-glm（glm 第三条腿）
- **变更**：新增渠道 `ark-glm`（type=1，base=`https://ark.cn-beijing.volces.com/api/plan`，key=ARK_AGENT_KEY），models=`glm-5.3,glm-5.3-flash,glm-5.3[1M]`，mapping 仅 `[1M]→glm-5.3`，**priority 0**，abilities 3 行。
- **动机**：07211996 有**站级 12 req/min 硬墙**（ch4/ch5 两把 key 共享同一限速池，实测 18 发/min 交替两 key → 每 key 9/min 即被拒）；ark 火山 Agent Plan 的 glm 实测 **8 并发 8/8 全通**，不受该墙约束。
- **验证**：经中转站并发 glm-5.3-flash **12 并发 12/12 全 200**（扩容前 14 并发 → 5 次 429）；落点 ch13×20 / ch4×8 / ch5×8。
- ⚠️ **base_url 拼接规则**：OpenAI 类型渠道 base **不带 `/v1`**（new-api 拼成 `…/api/plan/v1/chat/completions`）；写带 `/v1` 会被剥尾 → 404。

### 13:5x · 新增 ch12 ark-kimi（k3 替代腿）
- **变更**：新增渠道 `ark-kimi`（同 base），models=`k3,k3-256k`，mapping→`kimi-k3`，priority 0，abilities 2 行。
- **动机**：relay 的 kimi-k3 周额度耗尽（36 次调用全 429、0.1s 秒拒，且幂等逻辑删旧结果反复重跑）。
- **验证**：k3 / k3-256k 各 200 落 ch12；ark kimi 并发 5/5 全通（10 并发 1×429）。

### 09:0x-09:2x · 修复客户 503（claude-sonnet-4-5 无渠道）
- **症状**：11 次 503 `No available channel for model claude-sonnet-4-5`（来源 123.149.34.153）。
- **根因**：ch6 的 models 只有**点号版** `claude-sonnet-4.5`（靠 mapping 转横杠），abilities 按"请求写的名字"索引 → 横杠名查不到渠道 → 直接 503。
- **变更**：ch6 models 补 `claude-sonnet-4-5` + abilities 加一行（pri 0）。
- **验证**：e2e 200 落 ch6；此后 503 该模型归零。
- **教训**：**aliases 必须同时进 models + abilities**，只有 model_mapping 不够。

### 09:0x · ch3 补 MiniMax-M3[1M] 别名
- 桌面旧档位名 `MiniMax-M3[1M]` 在中转站不存在（503 model_not_found）。ch3 models 补名 + mapping→`MiniMax-M3` + abilities 加行（pri 20）。e2e 200。

### 08:5x-09:0x · guard v5：ch1 常驻不摘除（策略反转）
- **症状**：glm 四腿全断（官方窗口耗尽 + 第三方 12/min + ch2 周额度 + ch3 封顶），客户端 429 直接崩，"不会自动切换负载均衡"。
- **根因**：guard v4 在官方窗口耗尽时把 ch1 **静音**（status=2 + abilities=0 + models=''）→ **唯一可切的兜底腿被摘出路由池**。静音并不减少客户可见失败（其他腿断时客户照样失败），只让日志少几行。
- **变更**：`relay_zhipu_guard.sh` v5 —— ch1 **常驻池中**（pri -10 最后试），窗口耗尽只记录+飞书告警不改库；窗口重置自动可用，无需恢复动作。
- **验证**：v5 幂等（二次运行"已在池中·无需动作"）；ch1 直测 200（窗口重置后）；官方腿自动接住限速溢出。
- **回滚**：`relay_zhipu_guard.sh.bak-20261025-v4`。
- **教训**：静音/摘腿是最后手段；先问"能不能加腿/换腿"。多腿 + 自动换腿 > 降并发/降重试。

### 08:4x · judge-ark-text 专用令牌（已停用，留档）
- 组隔离方案（abilities.group=`ark-text` + 专用令牌）被证伪：new-api 令牌 group **不支持逗号多组**（`default,ark-text` → 403），且分组校验依赖用户所属分组（补 GroupRatio 仍 403）。令牌 id=25 已 status=2 停用；`GroupRatio['ark-text']=1` 保留无害。

---

### 20:3x · 🔴 第三次计费兜底坑：claude-sonnet-4-5 别名漏倍率（已修账）
- **发现**：ai80 卖家账单"昨天 claude-sonnet-4-5 737 次 · $69.28"；我方内账同模型同日 736 次（gaoguan-02）记了 **$8,830.30 —— 虚高 127 倍**。
- **根因**：09:1x 修复 claude-sonnet-4-5 别名时只补了 models+abilities，**漏了 ModelRatio/CompletionRatio 键** → 静默落 37.5 未知兜底（68 倍超收，与 10-15 gpt 腿、10-21 [1M] 别名同族，第三次）。样本行对拍：37.5 兜底算=2206050 ✓ 吻合实测 quota。
- **修复**：①补 ModelRatio=2.5 / CompletionRatio=5 ②回扫当日 736 行 logs.quota 按正确倍率重算：**$8,830.30 → $115.45**（抽样首行对拍精确吻合）。
- **经济账**：内账 $115.45 vs ai80 成本 $69.28 → 毛利 1.67×，定价合理。
- 🔴 **判据（第三次，升格为清单）**：加模型别名 = **四件套缺一不可**：models + abilities + ModelRatio + CompletionRatio。缺失不报错、静默落兜底，只在真实流量进账后从账单显形。修复别名后必须**回扫当天账单**。

## 2026-10-27

### 18:2x · glm 主力档补回第三腿：ch13(ark) 用 flash 接回 glm-5.3[1M]
- **症状**：用户报"glm 又额度用完了"。实测 18:14：`glm-5.3[1M]` 当时只有两条腿 —— ch4/ch5（**同一 07211996 站、两把 key 共享一个 12/min 池**）+ ch1 官方（5h 窗口）；**ch13(ark) 整体不在 glm-5.3/[1M] 池里**（10-25 19:5x 为根治多模态 400 洞主动摘除）⇒ 深对话撞 12/min 硬墙。
- **新实测依据**：ark **glm-5.3-flash 真实窗口也达 ~1M**（400K/700K/900K 全 200，1.05M 才 400）**且支持多模态** ⇒ 能同时满足"深+带图"，是补腿的最优解（ark 纯文本 glm-5.3 仍不接，避免 400 洞复发）。
- **变更**：ch13 models 加 `glm-5.3[1M]`；**mapping `[1M] → glm-5.3-flash`**（不是纯文本 glm-5.3）；abilities 加一行 pri 0。
- **验证**：纯文本 [1M] 200 落 ch13；[1M]+带图 200 落 ch13（ark flash 吃图）；**12 并发 [1M] 全部 200**（落点 ch13×14 / ch5×4 / ch4×2，第三方仅零星），内部零 429 零 400；glm-5.3 非 1M 档回归正常。
- 🔴 **判据**：一条腿被摘除前，先问"有没有等价替代腿"——ark 纯文本 glm 被摘时，**同站的 flash 既是多模态安全、又同窗口档位**，是零代价替代；先量 flash 的窗口再决定摘不摘。
- 🔴 **站级共享池的辨识**：ch4/ch5 是**同一站两把 key 共享一个限速池**（18 发/min 交替两把、每把 9/min 即被拒）⇒ "两条腿同时用完"往往实为"一条腿的两个 key"。

## 2026-10-26

### 15:0x · 补 glm-5.3-flash[1M] 别名（四件套正确示范，macmini OPUS 档解锁）
- macmini settings 的 OPUS 档 = `glm-5.3-flash[1M]`（该名中转站原不存在 → 503）。按**四件套**补齐：ch13/ch4/ch5/ch1 四腿 models+mapping（→glm-5.3-flash）+ abilities（pri 镜像 flash：0/-5/-5/-10）+ ModelRatio/CompletionRatio=0.0548/3.5（镜像 flash 档）。
- 验证：e2e 200 落 ch13；计费生效；全站 37.5 兜底保持 0。此条是"别名四件套"判据的正确执行样例（对比 09:1x 与 20:3x 两次漏键反例）。

### 12:2x · ch10/ch11 百炼 key 轮换（旧套餐过期 → 新套餐新 key）
- **背景**：百炼 Token Plan 月配额耗尽（bl CLI 报 "1-month quota exhausted"），用户 10-25 夜开通新套餐（新 key 尾 83YA，与 macmini `~/.bailian/config.json` 的 bl CLI key 同值）。
- **变更**：ch10/ch11 key 更新为新 key（热写+restart）。旧 key（尾 A7gQ）随旧套餐失效被上游 401。
- **验证**：新 key 直测百炼 compatible-mode 200；e2e `bl-qwen3.8-max` 经中转站 200 落 ch10。
- 🔴 **判据**：百炼套餐续期/新购**必须同步 ch10/ch11 的 key**（key 真源 = macmini `~/.bailian/config.json` 的 api_key）；判据 = ch10/ch11 401 "Invalid API-key" 出现即查套餐/key 同步。

### 00:5x · 判分批失败谱盘点 + "600s 网关线"判决（详见 10-25 19:5x 条）
- qwen 真堵点 = 百炼**月配额**（非 600s、非 5h 窗口，三层不同限制）；600s@504 只在已废弃的 qwen3.8max-direct 渠道。
- macmini DNS 间歇事件（11:10-11:15，5 分钟窗，glm5.3-anthropic 48 连败 Errno 8，嫌疑 Tailscale MagicDNS）已自愈；加固选项 = /etc/hosts 加 `115.159.62.192 api.chunxiao.wang`（需 macmini sudo，未执行）。

## 2026-10-24

### 21:4x · guard v4 → 策略演进起点（ch1 三道保险静音）
- 背景：官方 5h 窗口耗尽时 ch1 被 12/min 墙挤压反复 429（一小时 312 次），v4 采用"静音"消除放大。**10-25 被证伪并反转为 v5 常驻**（见上）。
- 附带产出：`ch1_profile.json`（原始模型面快照，恢复数据源）、热写+restart 流程（替代 stop+推库，规避 WAL 竞态回滚）。

### 16:27 · ch1 官方智谱 key 接回（用户供新 key）
- ch1 = open.bigmodel.cn/api/anthropic，**priority -10 兜底位**；models 8 个 + mapping 补 `[1M]→glm-5.3` + abilities 8 行 enabled。
- 验证：新 key 直测官方 200；e2e 公网域名 200 落 ch4（优先级生效）。
- 备份：`data/one-api.db.bak-20261024-ch1-zhipukey`。

### 15:05 · 恢复 new-api 容器（500 事故收尾）
- 容器被手动 stop 后 73 分钟未拉起（restart=always 对手动 stop 不生效）→ 全站 500。`docker start` 恢复。
- **relay_alert.sh 增强**：容器存活检查 + 自动拉起 + `MAINTENANCE.lock` 维护锁 + `ALERT_DRYRUN` 测试模式（备份 `.bak-20261024-autostart`）。
- 🔴 运维铁律：**改库流程 `stop→改→start` 必须在同一 ssh 会话原子执行**，中断即全站 500；exit=0+SIGTERM=人为 stop，别往崩溃/OOM 查。

### 15:2x · v5-brain llm_client.py 5xx 冷却（cloud ~/nautilus-v5）
- `chat_with_fallback` 兜底 except 补 5xx 签名 → 复用 `_quota_cooling` 指数退避（429/401 早有护栏，5xx 零登记 = 停机期每 ~10s 白打全链）。备份 `.bak-20261024-5xxcooldown`。

---

## 当前渠道拓扑（2026-10-25 15:00）

| 渠道 | 上游 | priority | 多模态 | 并发能力 | 定位 |
|---|---|---|---|---|---|
| ch13 ark-glm | 火山 Agent Plan | **0** | ✅（flash）/ ❌（5.3/[1M] 纯文本） | 8 并发全通 | glm 主力 |
| ch12 ark-kimi | 火山 Agent Plan | 0 | ✅ | 5-9 并发 | k3 主力 |
| ch6 ai80-claude | code.ai80.vip | 0 | ✅ | **1（串行，并发即 499）** | claude 系 |
| ch4/ch5 07211996 | 第三方智谱中转 | -5 | ✅ | **站级 12 req/min 共享** | glm 余量 |
| ch1 zhipu-glm | 官方智谱 | -10（常驻） | ✅（flash 实测） | 5h 窗口制 | glm 兜底 |
| ch3 minimax / ch2 kimi | 官方直连 | 20 / 0 | — | 订阅额度制 | MiniMax/kimi |
| ch7 qixuw / ch9 vertex / ch10-11 bailian | 各上游 | 5-10 | — | — | gpt/gemini/百炼 |

**判决记录**：07211996 的 12/min 是**站级共享**（18 发/min 交替两把 key，每 key 9/min 即被拒）——两把 key 不能叠加容量。

## 备份指针

| 变更 | 备份 |
|---|---|
| ch1 key 接回(10-24) | `data/one-api.db.bak-20261024-ch1-zhipukey` |
| ch1 三道保险静音(10-24) | `data/one-api.db.bak-20261024-ch1-disable` |
| guard v4→v5(10-25) | `relay_zhipu_guard.sh.bak-20261025-v4` |
| ch1 写回常驻(10-25) | `backups/one-api_20261025_090024_ch1-restore.db` |
| ark 补跑基线(10-24) | `backups/one-api_20261024_214704_ch1-enable.db` |
| macmini models_channels.json | `codesense/tools/models_channels.json.bak-20261024-mt` |
| 每日自动 | `backup_db.sh` 04:15（留 14 份）+ 05:20 异地推 cloud（留 7 份） |

## 运维判据（本轮沉淀）

1. 加腿前先量**能力矩阵**（尤其多模态）——同一模型名在不同腿上能力不同，按**腿**分优先级。
2. 一个纯文本上游被多个别名（[1M] 类后缀）mapping 时，**每个别名都要同批降优先级**，漏一个就是复发源。
3. aliases 要同时进 **models + abilities**，只有 model_mapping 不够。
4. OpenAI 类型渠道 base_url **不带 `/v1`**（new-api 拼 `/v1/chat/completions`；带 `/v1` 被剥尾 → 404）。
5. 改库用**不停机热写 + docker restart**（stop+推库有 WAL 竞态回滚风险）；中断的 stop→start 会全站 500。
6. 探活语义：**有 HTTP 响应=活着**（401 也算），连不上才算宕。
7. 限流对策优先级：**加腿/换腿 > 排队 > 限流**；限制是最后手段。
