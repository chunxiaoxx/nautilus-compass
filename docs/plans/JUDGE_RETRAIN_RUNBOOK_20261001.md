# 判分器定期重训 Runbook(A100 40G · 2026-10-01 备就)

> 用户 9/30 批:语料越攒越多→定期重训判分器;每次先申报/先定判据/后动手。
> 与 v5(agent 框)/flywheel(飞轮框)融合:语料活水=飞轮产出+errata gold,判分器输出=v5 三门判定。

## 一 · 触发条件(满足其一)

1. errata gold / 新 labelled 语料净增 **≥50 条**(对照 manifest.json counts.labelled=1454 基线)
2. 距上次训练 **≥14 天**(双周节奏,即使语料未达标——防遗忘/漂移)
3. 现役判分器在线上被判据抽查抓到退化(抽检 acc < 85%)

## 二 · 每次重训的固定规矩(P2v2 全流程复用)

1. **申报**:platform 函(承宪章 40/30/30,模板=runtime/mail_p2v2_charter_report_20260930.md 改)
2. **判据预注册**:J1-J7 沿 docs/metering/P2_JUDGE_TRAINING_PREREG_20260930.md,
   只许加严;新增语料必须 qid 分组防泄漏重切三折(禁复用旧 split——新题混入即泄漏)
3. **训练→读数原样落盘→拉回→判定→通报**(红灯如实报,不调参救读数)

## 三 · A100 40G 现成环境(2026-10-01 实测)

- 连接:`.cache/gpu_a100.env`(双线 223.109.239.30/180.127.11.167:23236,root)
- 全套就位:torch 2.6.0+cu126 / transformers 4.57.6 / peft 0.13.2 / bnb 0.50.2 / modelscope
- 我们部署件(sha256 三折已验与本地一致):
  - /root/runtime/verdict_corpus/split_{train,dev,test}.jsonl(1162/143/149)
  - /root/tools/train_judge_lora.py(MODEL_ID 现指 modelscope 本地路径,重训前改回或重下)
  - /root/runtime/judge_lora/(上一轮产物)
- 模型缓存:Qwen3-1.7B 在 /root/.cache/modelscope(HF 直连/hf-mirror 大文件断流,一律走 modelscope)

## 四 · 与 v5/飞轮共用纪律(🔴 必读)

- **这台机 = v5 框 E6 训练机**(/root/vdd+vdd2:ego_open100k_t1 15G/nanjev_ckpt 14G/
  e6 18G/agibot/genrobot 数据),E6 GRPO 训练在跑时**绝不抢 GPU**
- (GOALS W1:E5 达 30 条即首批 POST 1562,E6 训练是 v5 施工图主线)
- 我们的判分器训练 <1h/<¥2,窗口=E6 空档;开跑前必查 `nvidia-smi` 显存占用 <10%
- 训练脚本无需改超参(判据零放宽);40G 富余显存留给 E6 共存,不升 batch

## 五 · 语料活水管道(增量入库路径)

| 来源 | 现状 | 入库动作 |
|---|---|---|
| unlabelled_v0.jsonl | 47 条 | 人工/三门判分升 labelled 后并入 |
| v5 errata gold | 挑战窗/errata 登记处(18890)活水 | exporter v1.3 加源 |
| E5 三门轨迹 | 33 条已过门(e5_gates_first33) | 判定样本→labelled(专家复核后) |
| F15 meta-judge 三供应商 | 8 条 | 持续积累 |
| BC1 考生判分 | 首考生=M1 信号 | 判绩账→语料(脱敏) |

## 六 · 命令速查(全流程 <1h)

```bash
# 1) 上传新三折(本地切好后)
python -c "import paramiko; ..."  # sftp.put → /root/runtime/verdict_corpus/
# 2) 训练(setsid 后台,日志 /root/runtime/judge_lora/run.log)
(setsid bash -c 'python3 /root/tools/train_judge_lora.py && echo DONE' > .../run.log 2>&1 &)
# 3) 监控(p2v2_monitor.py 改 LOG 路径即可)
# 4) 拉回(p2v2_pullback.py)+ 判据判定 + 通报函
```
