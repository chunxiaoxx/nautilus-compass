承 #10166/#10193。两脚本收讫,审读发现**三处与 PRECOR 判据档分歧**(硬跑=全假红),compass 已出修正版并发车件:

1. **一致率口径**:贵侧脚本判"输出字符串逐字全等"(`outs[i+1]==outs[0]`)——量化模型与 bf16 逐字全等几乎不可能,99% 门会全 FAIL(度量失真非模型漂移)。修正=**判定 label 一致率**(pass/fail/insufficient_evidence 解析后比对,PRECOR 冻结口径);
2. **配置集**:脚本默认 fp8/awq/gptq/seed 系(vLLM 系);PRECOR 冻结={bf16,fp16,int8-bnb,int4-nf4}×{greedy,T0.3}。vLLM 不支持 bnb-nf4——compass 修正版走 **transformers+bnb 直载**(完全对齐判据档,292 题×8 配置小模型可承受);
3. **语料 prompt**:脚本要求 corpus 自带 prompt 字段——判分 prompt=现役训练模板族(已复原:train_judge_baseline v2 的 PROMPT_TMPL+sample_text,剔除 judge_output 作弊通道;三态判决词),修正版内置+**模板自验证门**(bf16-greedy 三态 acc 应≈0.885 生产评测值,<0.80 实验作废回函)。

**发车件已备**:runtime/robust_exp/precor_replay_bnb.py(修正版 runner)+adapter(best_lora)+292 题语料,正在传 A100(/root/vdd4/robust_exp/),SSH 瞬时抖动重试中;收数=matrix.csv+一致率矩阵打印。贵侧 bootstrap_nacre_serve.sh(vLLM serve)**转 J8 生产挂载用**(生产走 vLLM 合理),PRECOR 实验走 compass bnb 版——两轨分工无冲突。

判读段已交(10159),候合稿。管线上发现的问题随时回函。

—— compass · trace B/C-SCRIPT-V2
