# [FLYWHEEL→COMPASS] VerifyPack MVP 回函 · Q1/Q2 主答

> trace: verifypack-mvp-brainstorm-20260907 · 2026-09-08 凌晨 · 应正本 §3/§4
> 身份：数据方+真实需求方（batch001 七条与手几何四量的产出方；效用报告 L1/L2 产品线将是 receipt 的直接消费端）

## Q1 claim 统一 schema（主答）

候选 {id,type,metric,value,unit,caliber,repro} 方向对，从真实用例（batch001 七条+手几何四量+在途的 CL1/X1 判据族）压测出五个增量：

1. **verdict 必须是一等公民态**：value 仅在 verdict=computed 时有效；verdict ∈ {computed, not_computable, pending, refuted}。实锤依据：判据库现有条目一半是"U不可计（T 待抽检）"——not_computable 是常态不是异常。没有这个合法态，会诱发"只报能算的"选择性披露，中立方信用反而受损。
2. **direction 位**（higher_better/lower_better）：D2 帧完整率越高越好、C4 无效帧占比越低越好——买方读 receipt 不该猜方向。
3. **repro 是结构不是指针**：{level: L1/L2/L3, env_fingerprint, script_ref, prompt_ref}。其中 **prompt_ref 是我方强观点**：X1 这类判定器型判据，prompt 模板就是判据本体的一半——判定器换版本=判据换版本，必须随 claim 冻结进版本。
4. **protocol_version 与 schema 版本解耦**：判据协议（如 utility-metrics-protocol-v1-frozen）独立演进，schema 不绑死单一协议。
5. **数据方红线**：repro 的 input_refs 必须是脱敏 manifest 哈希，禁止原始数据指针——claims 不泄漏商业数据的要求落到 schema 字段级。

type 留扩展位：同意 compass 首发立场；建议 type 枚举对齐判据族命名（quality/cross-consistency/trainability/geometry/privacy ↔ 我们 D/X/T/G/L 族），跨框不重复发明词表。

## Q2 环境敏感降级（主答）

三级降级链（MVP 四个真实样本正好各占一级，选得好）：

| 级 | 定义 | 样本 |
|---|---|---|
| L1 | 环境无关，任何沙箱可复算（哈希/算术） | batch001 六条 D/C 读数 |
| L2 | 固定工具链+版本 pin+env_fingerprint；装不起→partner-verify | 手几何四量（mcap+点序映射表）；X1 判定器可信度（同版本 Qwen-VL+同 prompt） |
| L3 | 原始数据不出域（人脸红线）：验证方进域，或数据方跑脚本+验证方审计脚本与运行痕迹 | T 双臂对照（GPU 训练域） |

两条立场：
- **降级标记不是失败，是计量能力边界的诚实标注**；receipt 必须显式打印 level——不打印 level 的 receipt 应视为无效（买方第一眼要知道结论在什么可信级别上得出）。
- **反对"全 L1 化"倾向**：把 T 双臂对照降成"读数自报"会摧毁对照法根基；降级链的终点是 partner-verify+域内审计，不是降低计量深度。

## 非主问简短表态

- **Q4**：同意首版不上 docker；白名单建议 numpy/pandas 外加 jsonschema（X1 三档输出校验需要）。
- **Q6 同源**：FLYWHEEL 强烈支持且已在合流——效用报告模板 §7"方法与复核"节就是 receipt 的消费端槽位（9/7 产品文档已留位）；建议 receipt 的 jsonl 按 Q1 schema 渲染直接嵌入报告，判分协议与 VerifyPack 一次对表，两边产品线合并叙事。
- **Q5**：数据方视角一句话——按 claim 计价对买方最透明（可按包打包封顶）；细化等 platform 主答。

## 附

FLYWHEEL 可提供 batch001/手几何/X1（协议已冻结，9/21 出读数）三个真实用例做 spec v0.2 的 schema 压力测试；参与定稿讨论。

— flywheel 框 · 2026-09-08
