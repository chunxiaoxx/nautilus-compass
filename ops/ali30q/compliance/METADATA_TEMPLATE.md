# 合规元数据模板 · task.toml [metadata] 完整字段(甲方 1012 §3.2)

## 必填字段(甲方验收方逐条核对)
```toml
[metadata]
badpattern = ""           # 唯一 badpattern(配额归属,六选一)
focus_points = []         # 七考察点选 1~3(固定③⑤ + 选①②④⑥⑦)
trap_type = ""            # 陷阱类型(语义/运行时/边界/口径/范围/精度)
language = ""             # 主语言
difficulty = ""           # easy / medium / hard
domain = ""               # 领域类型(甲方 D01.1/D05.0/D08.0/D09.x)
knowledge_path = ""       # 知识树四级路径
knowledge_l0 = ""         # 知识树 L0
knowledge_l1 = ""         # 知识树 L1
knowledge_l2 = ""         # 知识树 L2
knowledge_l3 = ""         # 知识树 L3
code_origin = ""          # internal / opensource / authored
code_license = ""         # SPDX 标识 / internal / authored
source_note = ""          # 来源说明(为什么选这段代码,真实性保障)
task_id = "CS-NNN"        # 与目录名逐字一致
```

## expert_design_notes.md(独立文件)
```yaml
intent: ""                # 出题意图(一句话)
trap_design: ""           # 陷阱设计(具体语义位置+触发条件)
boundary: ""              # 语义边界声明(什么在范围内/什么不扣分)
challenges:               # 每个内嵌挑战的区分意图
  - premise: ""           # 错误前提/半错断言内容
    expected_reject: true/false  # 正确行为是拒绝还是修正
    distinguishes: ""     # 预期能区分开哪两类模型行为
model_failure_modes:      # ≥3 条,每条在 tests/assets/ 有真实答卷片段
  - pattern: ""           # 错误行为描述
    evidence: "tests/assets/xxx.json"  # 真实答卷片段路径
    ut_anchor: ""         # 对应 UT 方法名
```

## tests/assets/ 目录结构
```
tests/assets/
├── model_failure_mode_1.json    # 真实答卷片段(qwen/glm/kimi 实测)
├── model_failure_mode_2.json
├── model_failure_mode_3.json
└── counterexample_output.txt    # 反例程序运行日志
```
