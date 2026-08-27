# 智星云 4090 跑分环境速配配方（2026-08-27 实战提炼）

> 首次部署实战耗时 ~50 分钟踩 8 坑；照本配方 **~12 分钟可复现**（模型已走 HF 缓存路径除外）。
> CLI 全量用法见 `~/nautilus-v5/ops/gpu_4090.md`（凭据 `~/.config/ai-galaxy-compute/credentials.json`）。

## 坑清单（按踩中顺序）

| # | 坑 | 修法 |
|---|---|---|
| 1 | 镜像无 python3-venv → `python3 -m venv` 必失败 | `wget bootstrap.pypa.io/get-pip.py && python3 get-pip.py --break-system-packages` |
| 2 | `pip install torch`（PyPI 最新 2.13）= **cu130** 变体，4090 实例驱动 550(CUDA12.4) → `cuda: False` | `pip3 install torch==2.6.0`（PyPI 上即 cu124 变体；pytorch.org CDN 被 blockelite 网关卡死勿用） |
| 3 | transformers 5.16.1 + sentence-transformers 6.0 组合炸 lazy import（`Could not import PreTrainedModel`，真因被吞） | 照抄云 VM 已验证组合：`transformers==5.2.0 tokenizers==0.22.2 sentence-transformers==5.2.3` |
| 4 | 真凶其实是系统 Pillow 老旧（缺 `Image.Resampling`）→ 强制 `python3 -c "import transformers.modeling_utils"` 才露真 traceback | `pip3 install -U pillow --break-system-packages`（12.3.0 实测过） |
| 5 | paramiko `exec_command('nohup ... &')` 子进程随 channel 关闭而死 | 一律 `setsid nohup ... < /dev/null &` |
| 6 | sftp 写远端脚本拼错文件名（deloy2.sh）→ 启动秒退且日志误导 | 启动前 `ls` 验证；或 `cat > 文件` 一次到位 |
| 7 | eval 脚本 import `~/.claude/plugins/nautilus-compass` 的 daemon——裸 clone 没有该目录 → `ModuleNotFoundError: daemon` | 77cbcc7 已修：插件目录不存在时回退 repo 根 |
| 8 | LOCOMO 部分 qa 无 `answer` 字段（adversarial 题无标准答案）→ KeyError | 77cbcc7 已修：`qa.get("answer","")` |

## 速配脚本（新实例从零到能跑）

```bash
# 1. pip（~1min）
wget -q https://bootstrap.pypa.io/get-pip.py && python3 get-pip.py -q --break-system-packages
# 2. torch cu124 + 组合（~15min 下载 5GB @32M）
pip3 install -q torch==2.6.0 sentence-transformers==5.2.3 transformers==5.2.0 tokenizers==0.22.2 rank-bm25 --no-cache-dir --break-system-packages
pip3 install -q -U pillow --break-system-packages
# 3. repo + 数据（S/M/LOCOMO，与下载并行）
git clone -q https://github.com/chunxiaoxx/nautilus-compass.git /root/nautilus-compass
cd /root/nautilus-compass/.cache
wget -q https://huggingface.co/datasets/xiaowu0162/LongMemEval/resolve/main/longmemeval_s -O longmem_s.json
wget -q https://huggingface.co/datasets/xiaowu0162/LongMemEval/resolve/main/longmemeval_m -O longmem_m.json
wget -q https://raw.githubusercontent.com/snap-research/locomo/main/data/locomo10.json -O locomo10.json
# 4. 跑（GPU）
ZMM_DEVICE=cuda ZMM_EMBEDDER_MODEL=BAAI/bge-m3 ZMM_LOCOMO_PATH=.cache/locomo10.json python3 tests/eval_locomo.py
```

- bge-m3 首次 HF 下载 ~2.3GB ≈ 12 分钟（32M 带宽）——**计入窗口预算**。
- 2h 窗口（¥3.37）装不下"部署+模型下载+LOCOMO+M 双臂"；要么租 3h（¥5），要么模型先下完再租。
- 到期即销毁（无续期命令）：**产物（jsonl/log）及时拉回**，别信实例常在。
- 实例被占时勿抢（GPU 协调护栏）：先 `instances` 看 status=1 的在跑谁的任务。
