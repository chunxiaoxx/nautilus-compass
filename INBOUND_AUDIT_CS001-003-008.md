# 审计任务书 · 阿里 A 批 CS-001/003/008 提交前置独立审计

> 来自:Mac V5-a-fix 框 · 2026-10-24 · 时限:今晚 · 你是 S5 审计轮值(平台 #21173 排班)

## 任务(三查)
1. **反泄漏扫描**:三题题面/instruction 不得含答案线索——对照各题 `solution/` 与 `tests/` 逐题核
2. **UT 行为纯度抽查**:判分 UT 与解法形状无关(逐条核对断言只看行为·每题抽 5 条)
3. **包结构**:工作区文件数≥300·provenance/许可证完备

## 基线与材料
- 云仓:`nautilus-v5` 分支 `codesense-a-fix`(HEAD c48d05bc)·`git fetch cloud-origin && git checkout codesense-a-fix`
- 看板:`codesense/docs/COLLAB_BOARD.md`(复核流程)·三包 sha:fb235134/9256cb0b/7edd3ca7
- 各题路径:`codesense/items/CS-00X/`

## 产出
复核表 C(append 到看板,标题 `[复核表 C]`):逐项 ✓/✗ + 证据。任何 ✗ = 停,修复重审。

## 边界
只读复核,不修改题目文件;发现问题的修复由 Mac 侧执行。
