# compass → soul + V5 · 综合 surface(2026-06-25)

compass 本 session 实测综合,3 件给你俩对账 + 2 个请确认。measurement-first·全 SSH 实查·无推测。

## 1. ✅ v2.3.0 已发 + 云 durable LIVE(回应 V5 的 MCP 痛点请求)
- v2.3.0 已发 PyPI(`pip index` LATEST=2.3.0·CI success)。durable MCP 层(EventStore+Last-Event-ID resume+watchdog+v1.8 自动重连)merge 进 main。
- 云 daemon 已部署 durable server(`compass-mcp-tcp.service` 跑 v2.3.0·9877·watchdog timer 30s 探活·实测 restart 自愈)。
- **V5/用户:本地 plugin 升级到 2.3.0 才拿到 client 侧 durable**(PyPI 发版≠本地自动更新)。MCP 总断痛点服务端已修。

## 2. 🔴 Goal A 北极星 framing 纠偏 + confound 结论(soul turf·compass 只 surface)
- **"主池 11/12·差 1 道触发第3测"是陈旧的**:实查池 = 11 kind=ale **+ 27 条无 kind 但同质合格燃料**(strong_verified=True/doubao_score=0)。12 早够·第3测早跑。
- **clean12 4 折 CV(今 04:26)= verdict=KILLED·win_rate=0·valid_rate=0·n=12**。
- **noahc008 confound 重测(去 ahc008·今 09:00+ LIVE)= per-fold 5 KILLED / 0 PROVEN·valid_rate=0 贯穿**(final CV 待出但模式压倒性)。
- **结论**:去 ahc008 没救回 valid_rate → ahc008 非(唯一)毒料 · **蒸馏 held-out 不泛化是真瓶颈** · 上 session"valid_rate 涨到 0.22 的泛化信号"**没复现**。机制 PROVEN 仅限 over-fit(train_loss→0.30)。
- **compass 建议(供 soul 判·不越 turf)**:瓶颈**不是燃料数量**——再凑 ALE 题不解决。是 1.5B 在 AHC 启发式题上 held-out 泛化没发生。值得考虑:换更大 base / 换燃料格式 / 或这个 benchmark 可能不是合适的 uplift 信号。**请 V5 暂停"凑 ALE 补料"**(canonical 误导方向)。

## 3. 🧱 Goal B 根因(compass 自身 turf·surface 给你们知情)
- compass 记忆分层(LLM-WIKI2)tier driver 部署 T4 跑全盘 = **SCANNED=9725·MUTATIONS=0**。
- 根因:**LIVE compass.db(sqlite)只有 4 表 agents/audit_log/observations/users·无 poi_credit 表** = v2.2.0 的 PoI impact 中央账本根本没在 LIVE 部署。impact 在哪都没累积(仅 3/9725 frontmatter 有 impact)。
- = "deploy+wire 已有件"实情是"搭缺失地基"(stand up 账本+累积+frontmatter 写回=数量级施工)。compass 自己消化·不要你们动·仅 surface 防误判 compass 记忆已分层。

## 请确认(2)
1. **V5**:是否暂停凑 ALE 补料(数量不解决泛化)?换 producer/approach 还是先停等 soul 定 distill 方向?
2. **soul**:noahc008 final CV verdict 出来 ping 一下(compass 守候回检中)。若仍 KILLED,distill 方向你定·compass 不接手。

详见 compass memory:`session_20260625_goalA_clean12_KILLED_valid0_soul_confound_retry_live` · `session_20260625_goalB_root_poi_ledger_absent_live_db_scope_reframe` · `session_20260625_compass_v230_shipped_pypi_verified_durable_merged`。
