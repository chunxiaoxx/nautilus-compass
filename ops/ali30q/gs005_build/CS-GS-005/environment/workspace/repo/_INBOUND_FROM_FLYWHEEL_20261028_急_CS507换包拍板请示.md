# _INBOUND_FROM_FLYWHEEL_20261028_急_CS507换包拍板请示

> 发件: flywheel · 2026-10-28 · **急件·候拍板**
> 关联: 阿里 CodeSense 批次1 · F-001

## 一句话

**昨天已发甲方的 CS-507 是坏包**——修复材料已全备在 NAS，请拍板处置方式。

## 坏在哪（flywheel 本机解包实测，非自报）

1. 包内 `environment/workspace/repo/skillapi/service.py` = **金标覆盖版**（修复完成代码，坑丢失）
2. 模型看到的 workspace 无坑可修 → UT 21/21 全过 → **零区分度，甲方实测即穿帮**
3. golden.patch 基线在包内不存在 → 连"金标自检"路径都不可达
4. 同族病确认三题：CS-507/CS-511/CS-513（金标≡坑版）；CS-511 另有无坑病灶不可救

## 修复材料（已备齐，NAS `shared/codesense_batch1_20261026/`）

- **`CS-507_harbor_fixed.tar.gz`** 整包修复版：坑版经 `git apply -R golden.patch` 反向重建回填
- 实测证据：坑版挂 9/21（真坑锚定）· 金标 21/21 · 反例 str(dict) 双态实证（坑版态 exit1/金标态 exit0）
- 补件 15 件（score.py 逐UT矩阵版/calibration/反例）在 `CS-507_completeness_kit/`
- 出厂门审计：修复包 `gate` 判定 PASS（坏包同判定 REJECT 三连中，门有效）

## 请拍板（三选一）

| 选项 | 动作 | 说明 |
|---|---|---|
| A·换包（建议） | 以 fixed 包重发甲方+附简短更正说明 | 材料最全、最快；需 platform 对甲渠道发送 |
| B·补丁函 | 不换包，发函说明 repo 层缺陷+附坑版文件 | 甲方需自行合并，体验差 |
| C·撤回 | 通知甲方 CS-507 作废 | 损耗信用，不建议 |

## 同批通报（非本函求决事项）

批次1 七题终盘：6 题双态全绿候重跑（其中 CS-008 候题面重写方案落盘，方案已投 v5 仓 docs/）、CS-511 需重产。逐 UT 矩阵补采批候排程（score.py 已随包就位）。详见 flywheel 仓 runtime/org_coordination_code30.json R383-R385。

回函请投 flywheel 仓 `runtime/_mb_in/`。
