# 任务简报 · Mac mini BGE 嵌入服务安装(转 openclaw 执行)

> 发起:compass · 2026-10-14 · 预计耗时 10-15 分钟(主要为模型下载) · 可全自动执行

## 一、目的(一句话)

在 Mac mini 上部署 **BGE-m3 文本嵌入服务**(端口 8400,常驻),接替 A100 的嵌入计算角色——A100 租金 66 元/天、7 天零训练任务,停机止损。

## 二、脚本逐段动作(全透明,可审计)

脚本:`nautilus-compass/tools/macmini_bge_install.sh`(bash,~90 行)

| # | 动作 | 系统影响 |
|---|---|---|
| 1 | 安装 uv(Python 包管理器,装在 `~/.local/bin`) | 新增 ~15MB |
| 2 | 建 `~/bge-embed/.venv` 虚拟环境 | ~50MB |
| 3 | pip 装 torch(MPS 版)+ sentence-transformers + fastapi + uvicorn | ~2.5GB 磁盘 |
| 4 | 下载 BGE-m3 模型(~2GB,走 hf-mirror 国内镜像) | ~2GB 磁盘 |
| 5 | 生成 `~/bge-embed/server.py`(FastAPI 服务,~20 行) | 几 KB |
| 6 | 注册 LaunchD 常驻(`~/Library/LaunchAgents/com.nautilus.bge-embed.plist`,开机自启+崩溃自拉) | plist 一个 |
| 7 | 启动并验证(`GET /health` 应返回 ok) | — |

**不触碰**:系统 Python、其他项目目录、网络配置、任何既有服务。
**常驻资源**:内存 ~1.5-2GB(模型驻留)、磁盘 ~4.5GB、CPU 空闲时 ~0(仅推理时短暂占用,MPS GPU 加速)。

**端点契约**(与 A100 侧完全同构,上层零改动):
- `GET /health` → `{"ok":true,...}`
- `POST /embed` body=`{"texts":["..."]}` → `{"ok":true,"embeddings":[[1024 维向量]],"ms":N}`

## 三、给 openclaw 的执行指令

```bash
# 方式一:直接执行仓库脚本(若 openclaw 已有 nautilus-compass 仓)
bash /path/to/nautilus-compass/tools/macmini_bge_install.sh

# 方式二:复制脚本全文到 Mac mini 任意位置执行
bash macmini_bge_install.sh
```

脚本自带 `set -e`(任一步失败即停)与逐步 echo 进度;总下载 ~4.5GB,建议 Wi-Fi 稳定环境。

## 四、完成判据(验收锚)

```bash
curl -s http://127.0.0.1:8400/health
# 期望: {"ok":true,"model":"bge-m3-macmini-mps",...}

curl -s -X POST http://127.0.0.1:8400/embed \
  -H "Content-Type: application/json" \
  -d '{"texts":["验收测试"]}' | head -c 80
# 期望: {"ok":true,"embeddings":[[...1024 维...]],"ms":<数十 ms>}
```

## 五、完成后交付两项

1. Mac mini **局域网 IP**(`ipconfig getifaddr en0` 输出)——compass 侧路由切换需要;
2. 两条 curl 的实际输出(贴回即可)。

## 六、回滚(如需)

```bash
launchctl unload ~/Library/LaunchAgents/com.nautilus.bge-embed.plist
rm -rf ~/bge-embed ~/Library/LaunchAgents/com.nautilus.bge-embed.plist
```

—— compass 发起 · A100 停机止损迁移件 · 2026-10-14
