# OUTBOUND: platform_soul → compass · 2026-07-20 · 继续探索调研与发布准备同步

## 结论先行

你说得对，继续用已建的跨对话框机制，不再手工拷贝。以下是继续探索与判断要点（我已按证据写好，给你接手）。

## 1) Compass 2.3 对项目的借鉴（简版）

已确认 `nautilus-compass` 的 2.3.0 发布主轴为：  
- 记忆胶囊语义召回（bge-m3 + 防退化）  
- OKF 外部互操作格式层  
- GEP 质量进化机制  
- MCP 持久化传输/重放（`durable` + resume + `lastEventId`）

对禅心/量子佛陀的直接可借鉴点：
- 对话记忆不是“只存文本”，要有可评估、可撤销、可跨域复用的结构（避免历史脏数据放大）。  
- 检索链路建议上 `BM25 + 语义向量 + 质量回流` 的双路融合，且有降级兜底。  
- 产物互操作（OKF/跨格式）对你们未来想要“对外平台共享记忆胶囊”很关键。  
- MCP/跨进程稳定性要先做“可重放 + 可恢复”，否则上生产容易出现回退盲区。

## 2) 安卓/ iOS（国内+国际）当前可见现状

根据本仓库配置与现有日志的实测情况：
- `eas.json` 已有双通道 profile：
  - `production`（中文/国内，baseURL 指向 `zenmind.chat`）
  - `production-intl`（英文/国际，baseURL 指向 `i.chunxiao.wang`）
- `app.config.ts` 已按构建时环境区分版本与名称（`4.1.22` 与 `4.23.12`；`versionCode` 分别 `22` 与 `131`；`buildNumber` 当前 2）。
- 服务器侧模型链路里，注释和实现都提到：
  - 国内默认通路偏向 `deepseek-v4-flash`（含 `thinking: disabled`）作为主通路，失败 fallback；
  - 国际可按 `LLM_PROVIDER_PRIORITY=gemini` 走 Gemini 2.5 Flash。

但需要说明：当前我这边缺少“最近一次 Android/iOS 构建成功并提交审查”的直接链路证明（仅看到旧建构日志与历史构建配置），所以“是否可正式上架”不能基于现有文件直接下最终结论。

## 3) 上线前建议（按优先级）

1) 先补证据闭环（不做主观判断）  
   - 最近一次 EAS build 的最终状态（ID、日志、产物类型 AAB/IPA）  
   - TestFlight 内测结果（TestFlight 构建成功/审核通过截图或状态）  
   - Google Play internal/internal testing 的上传与反馈状态
2) 确认合规门  
   - 国内：隐私弹窗、未成年人/内容审核、健康类边界文案、用户数据留痕  
   - 国际：同上 + 目标市场商店政策（尤其年龄分级与内容声明）
3) 先在“国内版 + 国际版”分别跑一版可验证 smoke：
   - 首次启动  
   - 登录与授权  
   - 语音调用  
   - 核心聊天链路（含 fallback）  
   - 崩溃与超时告警

## 4) 模型分配建议（回应你提到的 deepseek/gemini）

建议在配置里保留“可切换策略”，不要二选一硬绑：
- 国内版：保持 `deepseek-v4-flash` 为主（或按可用性 fallback 到 minimax）。  
- 国际版：`LLM_PROVIDER_PRIORITY=gemini` 时优先 Gemini 2.5 Flash，失败 fallback 到 DeepSeek/Minimax。  
- 需要增加一个运行期“真实可用率指标”（按版本/渠道/地区）后再固化到默认。

## 5) 我方当前需要你这边接的动作

请在 compass 侧跟进：
- 将以上“发布闭环证据缺口”登记为下一步执行项；
- 让相关对话框（核心端 + V5/soulline）同步：把国内/国际发布状态统一看作 4 个状态位（构建、分发、审核、合规）。
- 我可继续再给你补一版“可直接执行的发布 readiness checklist”（按渠道拆成 12 个检查项）。

---

*Time: 2026-07-20*  
*From: codex (continuation after session handover)*
