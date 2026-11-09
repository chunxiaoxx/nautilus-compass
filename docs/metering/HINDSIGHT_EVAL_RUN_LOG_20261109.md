# hindsight 独立评测 · RUN LOG(2026-11-07)

- 冻结 commit: `bf554727`(冻结面 sha16 见 docs/metering/HINDSIGHT_EVAL_FREEZE_20261107.md)
- 数据集: /tmp/longmemeval_s.json · 278,025,796 B · sha16 `08d8dad4be43ee20` · 500 题
- 镜像: ghcr.io/vectorize-io/hindsight:latest · digest `sha256:19d0c08f3df79acac29384826419a1ca158129e81ec527cdcbd8c97ff4ef76da`
  (ghcr 直连停滞>45min → crane 走本机 clash 7890 拉同名同 digest tar → docker load;镜像内容未变)
- hindsight-client: 1.2.0 (PyPI)
- retain/subject/judge LLM: MiniMax-M3 @ https://api.minimax.chat/v1(V1.1 附录 §二)
- 部署: deploy.sh(provider=minimax·base_url 国内站·其余出厂默认·data volume hindsight-eval-data)

## 时间线(EST)

- 03:5x 数据集 HF 直连下载完成
- 04:0x 金库 key 甄别:OPENAI 401 · newapi 令牌失效 · ARK coding InvalidSubscription → V1.1 附录
- 04:1x 冻结 commit bf554727;V1.2 车道切换 commit 3dc12aa2(用户提供 qwen token-plan)
- 04:2x crane 代理拉镜像(digest 19d0c08f…)→ docker load → 部署 → 冒烟 SMOKE_PASS
- 05:0x retain 事故链(全部 infra fix·判据零变更·逐条 commit):
  1. `c4ad331e` haystack_dates 原生格式 422 → ISO 归一
  2. sync retain 52 条批 HTTP 响应挂死(服务端 578s 落库完成·客户端 45min 不返回)→ 8 项中
     7 bank 服务端全量落库实证后补记 done → `89768c2f` 改 retain_async+轮询
  3. `89768c2f` 后续:空会话 422(commit 并入下一条)· bank 内重复 session_id 400(15 bank×1
     条·内容逐字同)→ 去重修正
  4. `efdd7712` async 响应 operation_id 单数/operation_ids 复数双形——原代码只看复数致轮询
     空转,493 bank 全部秒标 done(记账失真)。实际提交已全部入服务端队列(pending 2066+
     槽位 10/10 满载)→ 不重提交,新增 verify 阶段以 DB 落库数收账
- 05:5x verify 启动:33/500 起步,服务端持续消化(Extract facts 吞吐 27-45 contents/min 口径)
- retain ETA ~9-13h(qwen3.8-max thinking 延迟为主因,服务端槽位默认 10 不调=公平性 §三.1)
- 06:0x 容器楔死#1(5min 零提取+1013 任务 assigned=0)→ 手动重启恢复(41/min)
- 06:1x verify 15min 停滞阈误报一次(批量落地节奏)→ 放宽 45min 重启
- 07:58 楔死#2 → 重启 + 自愈环上线(selfheal.sh:10min 零提取→自动重启→留痕,上限 12 次)
  · 楔死模式:qwen SSL 长连接被网关掐+重试风暴 → worker 槽位挂满不消化(与百炼 504 根修
    memory 同源的网关行为)。数据无损(PG 卷持久,队列续跑),仅 wall-clock 损失。
- 08:2x **V1.2 fallback 条款触发**:qwen 车道 retry_blocked=847 全队列退避停摆,重启两次
  不解(08:09 selfheal restart #1 后仍 0 提取)→ 服务端提取 LLM 切 MiniMax-M3
  @ api.minimax.chat(已验证 fallback),时点读数 verified=107/500。**为协议整洁全量
  重跑**:容器+PG 卷清空,107 个 qwen 提取 bank 弃用(弃用原因=混合提取配置不可比,
  单一配置重跑更严)——判据更严方向,合规。subject/judge 维持 qwen3.8-max(轻载稳定)。
  同批 adapter 修三件:op 轮询 async→REST 直询·base_url 落位·json import。
  MiniMax 实测吞吐 90 contents/min(qwen 27-45),ETA ~4.6h。
- 09:0x MiniMax token plan 撞 429 速率墙(3444 次/5min·sk-cp- 前缀=Token Plan key);
  qwen 侧 08:5x 也证实**月额度耗尽(重置 11-18 16:00 UTC)**。双车道同时枯竭。
- 09:4x 判别实验:新 bank 提交也不被认领 + 容器内 LLM 探测 429 → hindsight worker
  以 LLM 健康门控任务认领,槽位空闲是症状。
- 10:0x 用户拍板:**锁定 MiniMax token-plan 车道**(按量付费与 deepseek 恢复原协议两案
  均被否)。当前 key 仍在上限窗(可购积分补充/等重置)。resume.sh 自动复活链上线:
  key 每 10min 探测,一旦 200 → 容器切 MiniMax → retain(workers=4)自动续跑。
  挂起态:31/500 bank 已落库,runner/verify/selfheal 全部在岗等待。

