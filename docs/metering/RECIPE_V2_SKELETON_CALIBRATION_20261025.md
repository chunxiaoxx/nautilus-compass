# 配方V2·校准四门与案例骨架难度先验（2026-10-25）

判据：`PREREG_RECIPE_V2_SKELETON_CALIBRATION_20261025.md`

## 一、L1–L4 校准四门复核表

| 变体 | L1 表层 | L2 修复点 | L3 组合边界 | L4 业务后果 | 判定 |
|---|---|---|---|---|---|
| perfect | PASS | PASS | PASS | PASS | 必须全过 |
| equivalent | PASS | PASS | PASS | PASS | 实现可异，行为不得降级 |
| deficient | PASS | PASS | FAIL | 实测记录 | 合格 deficient 必须精准挂 L3 |
| guessed | PASS优先 | FAIL | FAIL或不可达 | FAIL或不可达 | 至少从 L2 起挂；L1挂则标废品型 |

每题 UT 分层硬要求：
- L3 至少一条跨模块状态传递/时序/生命周期组合断言；不能只是两个单函数 UT 拼接。
- L4 至少一条业务口径结果断言，如含税/净额、快照时点、重投计笔、账面余额。
- perfect/equivalent 必须同时过 L3/L4；否则校准无效。
- deficient 的主鉴别点必须落 L3，不能靠 import/语法错误制造失败。

实际 UT 分层记录模板（每道转化题必须填写后才能进入校准）：

| 层 | UT 名称（不得跨层重复） | 输入/状态坐标 | 断言的可观察行为 | 运行结果坐标 |
|---|---|---|---|---|
| L1 | PENDING | PENDING | PENDING | PENDING |
| L2 | PENDING | PENDING | PENDING | PENDING |
| L3 | PENDING | PENDING | PENDING | PENDING |
| L4 | PENDING | PENDING | PENDING | PENDING |

`[不可验]` 当前委托仅有骨架、尚无具体转化题与 UT 实物，因此不能填写实际名单，也不能声称校准运行通过；新题生成后须逐题补表并执行 perfect/equivalent/deficient/guessed 四态。

## 二、骨架 IRT b 先验

说明：以下均为 `[推断]`，不是 IRT 实测；公式冻结于预注册档。原表标题称12条，实表仅11条（#8–#18），不补造缺失项。

| # | 骨架简称 | 原难度 | V2 b先验 | 理由 |
|---:|---|---|---:|---|
| 8 | 判分器自身假读数 | 中 | 0.75 | 组合边界+元认知额外项 |
| 9 | 活目录竞态 | 中 | 0.50 | 并发读写隔离组合 |
| 10 | 幂等键失效 | 低 | 0.00 | 去重键×状态过滤 |
| 11 | fake 200 | 低 | 0.00 | HTTP码×业务体 |
| 12 | schema split-brain | 高 | 1.00 | 双写×一致性验证 |
| 13 | LRU churn | 中 | 0.50 | 容量×访问分布 |
| 14 | token预算烧穿 | 中 | 0.50 | 推理预算×输出需求 |
| 15 | nohup假绿 | 低 | 0.00 | 存活×心跳产出 |
| 16 | 共享配置被覆盖 | 低 | 0.00 | 写保护×并发读/schema |
| 17 | 双进程同端口 | 低 | 0.00 | 端口占用×服务可达性 |
| 18 | qwen四连满分教训 | — | N/A | 出题规范反例，非题目 |

upgrade_path：S3 作答数据到后用 IRT batch 拟合 `(b,a)`，输出“先验→实测”残差；残差绝对值过大时回查组合深度与 UT 分层，不反向改实测。

## 三、元认知题 #8 G 门

**G-META（gating，一票否决）**：验证器实现不得引入与被测对象同族的验证缺陷。

必测 UT：
1. `test_oracle_catches_known_bad_subject`：独立 oracle 抓到已知坏实现。
2. `test_oracle_accepts_known_good_subject`：金标不被假杀。
3. `test_checker_path_independent_from_subject`：校验器不 import/复用被测实现的关键逻辑。
4. `test_empty_output_is_failure_not_zero_score`：空输出不得变成合法0分。
5. `test_import_path_failure_is_infra_error`：路径/import失败标 INFRA_ERROR，不算被测FAIL。
6. `test_fail_open_http_200_rejected`：HTTP 200 但业务体失败不得判PASS。
7. `test_cross_oracle_agreement`：两个独立 oracle 对校准集一致；分歧置 PENDING，不擅判。

校准预期：perfect/equivalent 全过；deficient 只修被测对象但复用同缺陷 oracle，必须挂 G-META；guessed 从 L2 起挂。

## 四、provenance 声明模板

```markdown
# Provenance Statement

## 1. 真实案例来源
- 事件/问题：
- 原始证据坐标（公开URL、Issue、提交、内部函ID）：
- 事实层级：[实测]/[推断]/[不可验]

## 2. 许可证与使用权
- 上游项目/材料：
- 许可证：
- 许可证文件坐标与SHA-256：
- 允许的改编/再分发范围：

## 3. 脱敏与业务解耦
- 删除/替换的实体：
- 保留的技术因果链：
- 不可逆性检查：

## 4. 骨架到题目的变换链

每一步均须填写 `输入证据坐标 / 变换说明 / 输出坐标`：

| 阶段 | 输入证据坐标 | 变换说明 | 输出坐标 |
|---|---|---|---|
| 真实案例 → 语义骨架 |  |  |  |
| 语义骨架 → 业务皮 |  |  |  |
| 业务皮 → L1/L2 UT |  |  |  |
| L1/L2 → L3组合边界 UT |  |  |  |
| L3 → L4业务后果 UT |  |  |  |

- 与原事件保持一致的因果关系：
- 变换中主动舍弃的业务细节及理由：

## 5. 相似度自查
- 对比语料/已交付题范围：
- 去重方法与阈值：
- 最高相似项及差异：

## 6. 已知限制
- 无法独立验证的事实：
- 可能的域偏差：
- upgrade_path：
```

模板红线：零散 vendor LICENSE 不能替代任务级声明；真实案例来源必须给可追溯坐标，不能只写“来自生产事故”。
