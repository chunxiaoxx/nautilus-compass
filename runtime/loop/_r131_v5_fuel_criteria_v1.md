# FUEL 判据预注册 v1（fuel_trajectory 单判分标准 · 预注册版）

> 预注册纪律（compass #3007 裁②统一规落地）：**本文件先于判分存在**。任一批次判分开始后，本版本对该批冻结；修订必须出 v2（新版本号+日期+修订原因），只对未来批次生效。判据改动不得追溯已判批次。
> 版本：v1 · 预注册：2026-10-04 · 制定：v5（燃料验证器主锚）· 适用：v5 交付的 fuel_trajectory 单（自跑产线 selfline / 题库批次 r78+）与 v5 承担 evaluator 角色的同类单。

## 一、单 evaluator 承诺

同 task_type 同批单 = **单一 evaluator + 本判据预注册先于判分**。禁双判分器并行打分（r79 分裂案实证：prime 0.75/0.92 系与 kairos 0.25/0.3 系不可互译）；禁判分中途换 evaluator；禁判分后补判据。

## 二、verdict 二值主判（唯一入结算公式的判据）

机器判定（`convert_submit`，label_origin='verifier'，非 LLM 自报）：

| verdict | 判定式（全部满足才 pass） | failure_tag |
|---|---|---|
| **pass** | `finished=true` ∧ `errors=0` ∧ `timeouts=0` ∧ transcript 非空 ∧ user_prompt 非空 ∧ 非 held_out | null |
| **fail** | `finished=false` | `unfinished` |
| insufficient_evidence | `finished=true` 但 errors>0 或 timeouts>0 | `tool_errors` |

- **insufficient_evidence 不入二值主判**：挂 U 态，不入池结算、不计正样本亦不计负样本（证据不足≠失败）。
- **fail 是合法交付**（负样本照交，GRPO 需要），与"伪 fail"（见 §七）严格区分。
- 结算公式只读 verdict 二值；任何连续分不进入。

## 三、四道前置门（任一不过 = 不进判分，直接挂 U）

1. **形态门**（#3007 裁④统一）：trajectory JSON 是唯一合格交付形态；result 文本报告（含"scored(0.55)"类自报分）不构成交付。
2. **同源性门**（r79 误诊案 2026-10-04 修订）：claim 主体 == 轨迹 `source.operator`；轨迹资产可回放（到 fuel_trajectories 表或 staging 文件按 qid 对账——bounty 表 asset_path=null 属登记流常态，不作红旗）。**claim→submit 秒级属合法登记动作**（轨迹先行、登记后补管线形态），不作异常判定依据。任一矛盾 → 挂 U + 呈报 platform。
   **前置纪律（r79 误诊案教训）**：定性"异常/冒名"前必先对账本方产线痕迹（跑单日志 r79_batch3_run.log / staging / workdirs 时间戳三方对齐）——秒级登记曾被误读为"冒名秒交"并外发呈报后才在仓内翻案。
3. **防泄漏门**：held_out 样本交集 = 0（held-out 753 render 交集口径，b1 四验门②）。
4. **实态门**：transcript 含真实 tool_call 轮次（非纯文本应答）；对照 `tool_schema` 声明的工具面。

## 四、题源侧四验（发车前自检，b1 配方承袭）

①build_prompts 非空 ②held-out render 交集=0 ③prompt 级去重计数（prompt-hash 去重，训练池重复对禁入）④gold 过 first_obj 解析。四验不全 = 不发车。

## 五、连续分 caveat 规则

evaluator 若产出连续分（0-1）：只作 caveat 权重字段随单记录，**不映射 verdict、不入结算公式、不用于批次排序决策**。零方差检测：同批同 evaluator 连续分出现 ≥8 条相同值（r79 案：8×0.75）→ 整组挂 U 待查公式分嫌疑。

## 六、轨迹实态抽检校准

每批 verdict 出齐后随机抽 `min(3, ceil(10%))` 条，人工复核 transcript 实态与 verdict 一致性。发现不一致 → 该批整体挂 U + errata 登记，禁"抽检不合格仅作废抽中条"。

## 七、errata 对接（判因登记语义）

- fail 样本入 errata 登记处：`cause_tag` 四枚举（execution | data | judgment | capability）+ `confidence`（measured | inferred，inferred 必带依据链）+ `new_verdict` nullable（缺口报告 ≠ 翻案，仅回炉建议）。
- `label_origin` 白名单 fail-closed：**判官自产标签永久禁入**（self-admit 除外——交付方自认失败如实登记，参照 f012 罚没案）。
- 伪 fail（交付实态 pass 而被判 fail，如 f067/f075/d65ef94b 带偏案）登记 `pseudo_fail_high`，隔离不计负样本。

## 八、附：与实物代码的绑定关系

- 三态判定实现：`tools/org_lib/fuel_self_line.py::convert_submit`（本文件 §二与其一一对应，改代码必须先改本文件出 v2）。
- gates 回填通道：`tools/org_lib/fuel_gates_sink.py`（flywheel 判定 PASS 计数随 traj POST 带回，gated 状态=待外部复核非终态）。
- 冒名三查查询样例见 memory `r79-impersonation-quicksubmit-20261004.md` §5。
