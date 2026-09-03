# cheap-tier ent 211 接力交接(9/4 组装 · web 完成后执行)

> 前置:web 240 完成(cheap_web_full.log 出现 240/240+aggregate 输出)→ 巡检轮执行本命令。
> vLLM reader(8023)web 完后不必重启,直接复用。

## 接力命令(GPU 机直发)

```bash
cd /root/LongMemEval-V2 && export $(cat /root/e2e/judge.env | xargs); ABU=$(grep '^ARK_BASE_URL=' /root/e2e/ark.env | cut -d= -f2-); nohup python3 run_compass.py --domain enterprise --tier small --memory-config /root/compass_cfg_cheap.json --prompt-workers 1 --model Qwen/Qwen3.5-9B --evaluator-model doubao-seed-2-0-pro-260215 --evaluator-base-url "$ABU" > /root/cheap_ent_full.log 2>&1 & echo GO
```

## 已核实的事实(9/4 巡检)

- 机上 `/root/compass_cfg_cheap.json` = cheap 三改确认在位:
  `a11y_chars 1500 · query_decomp true · shot_per_traj 1 · max_screenshots 8 · bge-m3 cpu`
- `run_compass.py` 参数清单已核对(--domain/--memory-config/--prompt-workers/--reader-concurrency)
- `--prompt-workers 1` 是硬要求(BGE meta tensor 竞态,见 TRANSFER_RUNBOOK 坑2)
- ent runtime inputs 不需手工 materialize:run_compass.py 自带(harness 打点
  "materialized N questions",web 的 runtime 目录即由此生成)
- reader base-url 默认 localhost:8023/v1 ✓;judge 走 ark coding endpoint(ark.env)

## web 慢速运行观察(9/4)

- 151 起速率恶化 90→400-600s/q(GPU util 99%+显存满,疑 KV cache 抢占)
- 上游 harness 无断点续跑,故不杀不重启,慢跑可接受(实例已包时付费)
- log 更新为阵发式(块缓冲 ~20min 一冲),读数 ETA 按 ~500s/q 估

## 两域齐后

亮牌请用户退租(自动续费还开着,见 gpu-651799-expiry 记忆);数字填 SCOREBOARD.md [待补]。
