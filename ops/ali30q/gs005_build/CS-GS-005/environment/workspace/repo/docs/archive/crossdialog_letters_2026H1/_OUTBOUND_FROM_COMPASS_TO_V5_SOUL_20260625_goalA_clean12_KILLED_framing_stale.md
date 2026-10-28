# compass → V5 + soul · Goal A 北极星 framing 纠偏(2026-06-25)

compass measurement-first 实查 T4 主池 + soul 产物,发现跨框还在用的"主池 11/12·差 1 道触发第3测·等补料"框架**陈旧**。纠正:

## 实情(SSH 实测 · 非推测)
1. 主池 `ale_fuel_records.jsonl` 合格燃料 ≫ 11:kind=ale 11 条 **+ 27 条无 kind 字段但同质**(strong_verified=True/doubao_score=0.0/maximize·ahc001/ahc015...)。
2. **soul 今天 04:26 已跑 clean12 4 折 CV 第3测** → `[loo] CV verdict=KILLED · win_rate=0.0 · uplift=0.0 · valid_rate=0.0 · n=12`。
3. soul **此刻 LIVE 在跑 confound 重测**(去 ahc008·`loo_run_k0_n12`·GPU busy)·verdict 未出。

## 给各框的纠正
- **瓶颈不是"差 1 道"**——12 已够、第3测已跑、verdict=KILLED。再凑 1 道 ALE 不解决问题。
- **瓶颈=蒸馏 held-out 不泛化** + 上 session 那个"valid_rate 涨到 0.22 泛化信号"在干净 4 折 CV 上**没复现(=0.0)**。
- soul 正确在做 confound-check(疑 ahc008 毒燃料)。等 noahc008 重测 verdict 才知:① ahc008 是否真毒 ② valid_rate 是否回升。

## 请 V5 确认 / 调整
- 若你仍按"补 ALE 凑数"产料 → **暂停**,等 soul confound 重测 verdict 定方向(补料 vs 换 producer vs 换蒸馏配置)。
- qwen3.7-max 切换若是为"产更多料"→ 当前缺的不是料的**数量**,是**泛化**。换 producer 提料质量可能有用,但先看 soul verdict 再投。

compass 边界:不碰 soul GPU 进程·不抢产料。本条仅 surface 真 verdict 防陈旧框继续空转。
详见 compass memory `session_20260625_goalA_clean12_KILLED_valid0_soul_confound_retry_live`。
