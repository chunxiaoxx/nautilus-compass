---
name: orgfuel-ORGH-df97e5f7c5083ed3-51adf6bcaf
description: "commit ced0ed4b4b8b 2026-08-30 feat(N5·刀3): 训练对扩容+LoRA 训练四件套"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-df97e5f7c5083ed3
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit ced0ed4b4b8b 2026-08-30
feat(N5·刀3): 训练对扩容+LoRA 训练四件套——①semantic_align(cos 判据实测被域差距压顶天花板 0.73,推翻'转述可cos对齐'假设)②llm_weak_label(doubao 绕开 embedder 域差距做弱标注,cos+lexical 双路候选)③train_lmev2_lora(peft r16 只挂 qkv 0.41% 可训·guard recall@5 每 epoch 护栏·最佳 adapter 后统一 merge,管线 10 对冒烟全通 1s/epoch)④merge_pairs(strict g3 去 eval 池+weak YES 合成)——全轨迹 1.2GB 拉回证实 subset 已全覆盖,56 对是精确对齐结构上限,扩对只能走 LLM 弱标注
Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
