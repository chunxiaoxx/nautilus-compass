# GPU 实例隔离环境 runbook(新架构模型加载三障 · 2026-10-03 定案)

> 场景:GPU 实例(A100,共享环境,他人训练在用)上加载**新架构模型**(qwen3_5/Qwen3.5 代等),
> 系统 python 包是旧版且**不可动**(G1 训练同机,升系统包=红线)。
> 首案:P0-full turbo 臂(Qwen3.8-14B-Turbo,qwen3_5 架构),三障历时三轮清零,此档防复发。

## 环境事实(2026-10-03 实测)

- 实例:223.109.239.30:23236(root),A100 40G,系统 python 3.12.3 + torch 2.6.0+cu126 + transformers 4.57.6 + 旧 peft
- G1/评测链共训此机:**任何系统级 pip 升级都禁止**

## 三障与修法(按出现顺序)

### 障 1:新架构模型类不被识别
- 症状:`AutoConfig` 可读 config.json(model_type=qwen3_5)但 `AutoModelForCausalLM` 报"Can't load configuration"/模型类 ImportError
- 根因:系统 transformers 4.57.6 无 qwen3_5 架构类
- 修法:**venv 隔离**(继承系统 torch,只覆盖纯 python 包):
  ```bash
  python3 -m venv --system-site-packages /root/vdd2/p0_full/venv
  /root/vdd2/p0_full/venv/bin/pip install -q transformers==5.10.4 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple
  ```
  ⚠️ 排障教训:venv 里报 `SyntaxError` 先怀疑**自己的多层引号转义命令**(本案例 3 次),
  一律改脚本文件 sftp 上去跑,别在 `python -c` 里叠转义。

### 障 2:torch 旧版缺新 dtype 属性
- 症状:`AttributeError: module 'torch' has no attribute 'float8_e8m0fnu'`(transformers 5.x 的 fp8 集成层在 **import 期**读该属性;torch≥2.9 才有,系统 torch 2.6)
- 修法:**脚本头属性补丁**(bf16 路径不触发 fp8,仅补 import 期缺口):
  ```python
  import torch
  if not hasattr(torch, "float8_e8m0fnu"):
      torch.float8_e8m0fnu = torch.float8_e4m3fn
  ```
  (已固化在 tools/p0_full_extract.py 头部)

### 障 3:系统 peft 旧版撞新 transformers
- 症状:`ImportError: cannot import name '_maybe_shard_state_dict_for_tp' from 'peft.utils.save_and_load'`
- 修法:venv 内升 peft(不动系统):
  ```bash
  /root/vdd2/p0_full/venv/bin/pip install -q -U peft -i https://pypi.tuna.tsinghua.edu.cn/simple
  ```

## 附:GPU 实例 SSH 操作配方(同日定案)

- **SSH 限流**:高频连接触发远端重置(banner `WinError 10054`/EOF)→ **退避 120s + 单连接做完所有事**(put+启动+读数一条会话内)
- `setsid nohup ... &` 启动后 exec_command 读 channel 会挂起=**正常**(后台进程持有 channel),进程已起,重连验证即可
- 新开 tab 验证网页:`PUT /json/new?url=...`(GET 已 405)
- 提取/评测脚本自带 GPU 守门(有计算进程即退出)——放 cron 里空窗自动跑是安全模式

## 首案结果(P0-full turbo,验证配方有效)

turbo 提取 effect 52.9s + cause 92.7s,F1 零失败,1454×5120(32 层主干倒数第二层);eval hit@5=60.94% PASS——三障全清后一次成功。

关联:docs/metering/P0_FULL_PREREG_V2_20261002.md §7;GPU_EVAL_RECIPE_4090.md(旧 4090 配方)
