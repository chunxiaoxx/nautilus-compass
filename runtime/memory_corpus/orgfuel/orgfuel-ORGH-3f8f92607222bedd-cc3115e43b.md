---
name: orgfuel-ORGH-3f8f92607222bedd-cc3115e43b
description: "commit 9f6c8221f8ed 2026-07-16 feat(fde): BioMysteryBench 出题"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-3f8f92607222bedd
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 9f6c8221f8ed 2026-07-16
feat(fde): BioMysteryBench 出题脚手架(验证器+格式规范)
甲方外部新需求·生物信息学反向推理 benchmark。本轮建格式/验证器脚手架:
- bmb_validator.py: 把买方 §3/§4/§5 验收门译成代码(REJECT: 缺列/id不配zip/
  zip坏/域名超14白名单/human_solvable≠yes/答案泄露; WARN: 难度/工具/格式)。
  --selftest 过 + 买方真实样例 qes1 实测 0 REJECT + 泄露负例被抓。
- README.md: 格式规范+验收门+用法+诚实下一步(bio工具环境+真解验证待做)。
- problems_template.csv: 干净起点。

红线: 内容需真数据/真专家, AI 不得凭空造; 交付前须真解验证唯一答案+难度。

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
