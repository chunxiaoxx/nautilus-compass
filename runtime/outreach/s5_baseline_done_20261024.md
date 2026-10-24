**[管道 S5·第一步完成] 零样本基线 J1 达成 [实测]**

- InternVL2.5-8B(vdd4 完整版)零样本对数聚变留出集(24 视频每 3 取 1)推理,3 集有效读数(episode 映射覆盖 3/8,基线-微调臂同集对比内部有效)
- 样例:ep0"机器人在超市货架挑选商品(方便面/零食/货架/购物篮)"vs 金标"夹爪抓取橙色威化饼干(货架/零食包装)"——语义相关但精度差距可见(正是微调提升空间)
- 读数:/root/pipeline_s5_eval/zeroshot_baseline.json(逐集 pred/gold/耗时,可复算)
- 环境:InternVL2.5-8B bf16/A100/eval-venv(torch 2.14+cu126/tf 4.47/sentencepiece 0.2.0)
- **10 断点修复链全程留档**(选型依据 adapter_config/坏 shard/缺 tokenizer 慢版/sp 版本不兼容/torchvision CUDA 错配)

第二步(S4 数据微调):LoRA 配方=flywheel a3_lora_sft.py(InternVL 同底座),数据=72 条帧级标注,排程明日窗口;第三四步(评测+Delta pp)随后半日闭合。SLA 10/27 富余。

—— compass 判读层
