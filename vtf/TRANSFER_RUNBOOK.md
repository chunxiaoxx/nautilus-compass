# 数据搬迁 + LME-V2 首跑 Runbook(实例重租后执行,目标 ≤15min 开跑)

> 2026-08-29 立。前提:两台机均已停(用户主动停,数据在保留盘,无损失)。
> 上一窗口 rsync 未发出(上下文耗尽),重租后按本册执行,不要重新侦察。

## 重租时要回的信息(向用户要,或 `connect --include-sensitive` 自查)

- 新 GPU 机(镜像 v2608291059 + 100G 数据盘):IP / SSH 端口 / root 密码
- 旧盘机(8af0991f 盘,CPU 型即可):IP / SSH 端口 / root 密码

## 执行链(全在 Windows 本机驱动)

```bash
# 0. 指向新机(重租后端口密码必变)
export GPU_SSH_HOST=<新机IP> GPU_SSH_PORT=<端口> GPU_SSH_PW=<密码>

# 1. 打通 新机→旧机 key auth(幂等)
python vtf/link_machines.py <旧机IP> <旧机端口> <旧机密码>

# 2. 上传传输脚本并先跑 report(盘点双侧,不搬)
python vtf/gpu_ssh.py upload vtf/old_disk_transfer.sh /root/old_disk_transfer.sh
python vtf/gpu_ssh.py "OLD_HOST=<旧机IP> OLD_PORT=<旧机端口> bash /root/old_disk_transfer.sh report"

# 3. 确认 report 无 WARN 后正式搬(tar 落 /root/data,qwen 智能合并不回退)
python vtf/gpu_ssh.py "OLD_HOST=<旧机IP> OLD_PORT=<旧机端口> bash /root/old_disk_transfer.sh go"
#  ~6G tar + qwen 差额,内网带宽约 10-30MB/s,预计 10-25min;log 在 /root/transfer_logs/

# 4. Qwen 补齐(合并后若仍有 .incomplete,新机直连 HF 续传,32MB/s)
python vtf/gpu_ssh.py "cd /root && HF_ENDPOINT=https://hf-mirror.com hf download Qwen/Qwen3.5-9B --local-dir /root/data/models/qwen35-9b 2>&1 | tail -3"

# 5. 校验通过(index ALL_PRESENT + TAR_OK)后,提醒用户:旧盘机可退(钱包纪律)

# 6. LME-V2 收尾(prepare/validate/vLLM 8023,脚本已在机镜像里;若不在:upload vtf/lmev2_finish.sh)
python vtf/gpu_ssh.py "nohup bash /root/lmev2_finish.sh > /dev/null 2>&1 & echo LAUNCHED"
python vtf/gpu_ssh.py "tail -20 /tmp/finish.log"   # 轮询至 FINISH_DONE / VLLM_READY

# 7. small tier 首跑(judge 走 newapi glm,429 退避已在 eval 脚本里)
```

## 坑位提醒(已踩过)

- 新机根盘 91% 满(19G 余)——**tar/模型一律落 /root/data**,脚本已处理(symlink 进 repo)。
- rsync qwen 用"旧机更大才拉"逻辑,防新机已有进度被回退。
- 旧机重租后数据路径可能变(盘挂 /root 或 /root/data)——脚本自动探测两候选,report 模式先看。
- paramiko 后台链不 EOF:启动与查询分开两次调用(第 6 步已按此写)。
- 搬完立刻提醒退旧盘机——它是按小时计费的第二台实例。

## vLLM 版本矩阵(2026-08-30 定案 · PyPI metadata 硬数据,续租后直接照此装)

driver 550.127.05(CUDA 12.4)只能跑 cu12x build:
- vllm 0.27+/0.28 → torch 2.13.0(cu130)✗ `CUDA init: driver too old (found 12040)`
- vllm 0.20-0.26 → torch 2.11.0(cu13,nvidia-*-cu13 依赖实证)✗
- **vllm 0.18.1 → torch 2.10.0(cu128)✓ 唯一可行**(发布 2026-03-31,晚 Qwen3.5-9B 一个月,架构支持吻合)
- transformers 5.16.1 与 vllm 0.8.5 不兼容(`all_special_tokens_extended` 已移除)——勿降级 transformers,升 vllm

续租后直装(跳过 pip dry-run,GPU 机到 PyPI 慢,dry-run 曾卡 20min+):

```bash
python vtf/gpu_ssh.py "nohup bash -c 'pip install vllm==0.18.1 > /root/vllm018_install.log 2>&1; python3 -c \"import torch;print(torch.__version__,torch.cuda.is_available())\" >> /root/vllm018_install.log' > /dev/null 2>&1 & echo LAUNCHED"
python vtf/gpu_ssh.py "tail -5 /root/vllm018_install.log"   # 轮询至出现 True
```

装完(2.10.0 True)→ 直接跑步骤 6 的 `lmev2_finish.sh`(内含 vLLM 8023 起服务)。

## LME-V2 管线 smoke 全通定案(2026-08-30 · 六次迭代踩坑实录,续租后照此一键复跑)

烟测命令(1.5B smoke · 全链路绿 · aggregated_metrics 落盘实证):

```bash
# 1. vLLM 起服(32k context 是硬要求:harness reader 请求 max_tokens=20000)
python vtf/gpu_ssh.py "cd /root && nohup python3 -m vllm.entrypoints.openai.api_server --model /root/data/models/qwen25-1.5b --served-model-name qwen25-1.5b --port 8023 --max-model-len 32768 --gpu-memory-utilization 0.70 --enforce-eager > /tmp/vllm15b.log 2>&1 & echo UP"
# 2. judge env(ARK doubao;newapi 会被内容审查拦截,见坑3)
python vtf/gpu_ssh.py "ABU=\$(grep '^ARK_BASE_URL=' /root/e2e/ark.env | cut -d= -f2-); AKE=\$(grep '^ARK_API_KEY=' /root/e2e/ark.env | cut -d= -f2-); printf 'OPENAI_API_KEY=%s\n' \"\$AKE\" > /root/e2e/judge.env"
# 3. smoke 点火(--prompt-workers 1 是硬要求,见坑2)
python vtf/gpu_ssh.py "cd /root/LongMemEval-V2 && export \$(cat /root/e2e/judge.env | xargs); ABU=\$(grep '^ARK_BASE_URL=' /root/e2e/ark.env | cut -d= -f2-); nohup python3 run_compass.py --domain web --tier small --model qwen25-1.5b --prompt-workers 1 --evaluator-model doubao-seed-2-0-pro-260215 --evaluator-base-url \"\$ABU\" > /tmp/smoke15b.log 2>&1 & echo GO"
```

六个坑(每个都实测复现+修复验证):

1. **triton 编译炸 `Python.h: No such file or directory`**——vLLM 引擎起服即挂(与 eager 无关,triton 运行时必编 cuda_utils.c)。修:`apt-get install -y python3.10-dev`(~MB 级,秒装)。
2. **BGE meta tensor 竞态**——`SentenceTransformer` 在 **≥2 线程并发构造**时必报 `Cannot copy out of meta tensor`(torch 2.10+st 组合;主线程单发恒 OK,4 线程 100% 复现)。harness 默认 prompt-build 4 workers → 首题即挂。修:`--prompt-workers 1`(BGE 首次构造后进程内复用,串行只影响查询 embed,开销极小)。全量跑分片时每分片单进程即可。
3. **newapi judge 内容审查**——`PermissionDeniedError: Your request was blocked`:judge 端点对 LME-V2 web 域题干(模拟 reddit 帖)拦截;"reply OK" 短文本过、实际题干稳定 blocked(机上/本机一致)。修:judge 换 **ARK doubao-seed-2-0-pro-260215**(同一题干实测放行)。GLM-5.3-flash 仍是备选(newapi 恢复/换渠道时)。
4. **max_tokens 20000 > max_model_len**——vLLM 起 16384 时 reader 全 400,"Using empty response"→3 题空答案 0 分假完成。修:`--max-model-len 32768`(Qwen2.5 原生 32k)。
5. **显存分配**——48G 卡:vLLM 0.70(~34G)留 ~14G 给 compass bge-m3+系统;曾 0.85 时 bge 加载期紧张。1.5B 权重仅 3.1G,KV cache 充裕。
6. **openai SDK 过旧**——harness import `PromptCacheOptions` 需 openai≥某版,机上 2.24.0 报 ImportError。修:`pip install -U openai`(→3.6.0,纯 py 秒装;vllm 0.18.1 要求 ≥2.0.0 不冲突)。

smoke 结果(8/30):3 题 0 报错,Scoring 3/3,metrics 落盘(1.5B 0% 正确=预期,smoke 只验管线)。全量 451 题(web 240+enterprise 211)reader 换正式模型后续租再跑,参数除 --model 外全部照抄上面第 3 步。
