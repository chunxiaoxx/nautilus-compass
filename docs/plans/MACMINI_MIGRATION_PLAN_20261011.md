# 组织第二次大迁移：Windows 主力机 → Mac mini M6 规划(2026-10-11 立项 · 用户拍板)

> 性质:组织基础设施重大迁移。第一次=迁入当前 Windows 主力机;本次=全部迁至 Mac mini M6(Apple Silicon)。
> 原则:**分阶段/可回滚/不停服/零数据丢失**。本档=迁移正本,候用户确认分阶段路径后执行。

## 一、迁移范围盘点

### 必迁(组织核心服务)

| 服务 | 当前宿主 | 迁移复杂度 | 说明 |
|---|---|---|---|
| compass daemon(9876) | Windows 主力机 | 中 | BGE 嵌入+recall+drift,记忆文件随迁 |
| MCP server(stdio) | Windows 主力机 | 低 | mcp_server.py 纯 Python |
| hook.sh(UserPromptSubmit) | Windows 主力机 | 低 | bash 脚本,macOS 兼容 |
| 判读工作台(final_check 等) | Windows 主力机 | 低 | Python 脚本 |
| 跨框投件通道(_INBOUND) | 各框仓 | 低 | git 层面操作 |
| A100 SSH/隧道 | Windows 主力机 | 中 | paramiko/SSH config 迁移 |
| 平台信箱 key | Windows .cache | 低 | key 文件拷贝 |

### 选迁(有价值但非必需)

| 服务 | 说明 |
|---|---|
| dev.to/Discord/知乎 token | 各社媒渠道发布能力 |
| XERJ GitHub 操作 | gh CLI 认证迁移 |
| Gmail REST | 邮件渠道 |
| A100 rerank 隧道 | paramiko 脚本,已在仓 |

### 不迁(留在原位或云端)

| 服务 | 理由 |
|---|---|
| nautilus.social 静态站 | 在 cloud 服务器,独立于本机 |
| A100 训练机 | 独立远程 |
| platform 组织服务 | 在 cloud 服务器 |
| 判读 API(19988) | 在 A100 |

## 二、Mac mini M6 适配挑战

| 挑战 | 影响 | 解法 |
|---|---|---|
| **bash 版本** | macOS 自带 bash 3.2(无关联数组/EPOCHSECONDS) | brew install bash(5.x) |
| **路径差异** | C:\Users\chunx → /Users/chunx | 全局路径审计+替换 |
| **Python 环境** | 需重建(MiniForge/uv) | pyenv或uv+requirements.txt |
| **BGE 模型** | 需重下(~2GB) | huggingface-cli(M2 芯片 MPS 加速) |
| **paramiko SSH** | 需重装 | pip install |
| **daemon_start.sh** | python3 别名指向不同 | 统一 python3 路径 |
| **MPS vs CUDA** | Mac 用 MPS,CUDA 代码需适配 | 判读推理走 A100(不经本机GPU),本机只用CPU做轻量推理 |

## 三、分阶段路径

### Phase 0 · 准备(1 天)
- Mac mini 基础环境:bash 5 + Python 3.10+ + git + gh CLI
- key 文件全迁(.cache 全量拷贝,600 权限)
- 网络验证(SSH cloud/A100/信箱 API/dev.to)

### Phase 1 · 双机并行(3-5 天)
- Mac mini clone 全部仓+装依赖
- compass daemon 在 Mac mini 启动(新记忆库初始化)
- **Windows 主力机不关**(两台并行值守,验证 Mac mini 稳定性)

### Phase 2 · 切换(1 天)
- Mac mini 成为主力值守机
- Windows 降级为备用(不关,但不再发新任务)
- platform/各框通知新节点坐标(如需)

### Phase 3 · 清理(1 天)
- Windows 主力机归档快照
- 确认无遗留依赖

## 四、风险与回滚

| 风险 | 概率 | 回滚 |
|---|---|---|
| Mac mini bash 兼容 | 低(brew bash 5) | 回 Windows |
| Python 包版本冲突 | 中(pyenv 隔离) | 回 Windows |
| BGE 模型 MPS 不支持 | 中(fallback CPU) | 判读走 A100 |
| 记忆文件格式差异 | 低(纯 JSON/MD) | 逐文件验证 |
| 网络环境差异 | 低(Mac mini 同局域网) | — |

## 五、与现有排期的关系

- 10/11 终检正日:在 Windows 上(不受影响)
- 10/12 开张:在 Windows 上(不受影响)
- **迁移启动窗口:10/13-19 开业周**(Phase 0-1,与开业并行)
- **Phase 2 切换:10/20-25**(Windows 与 Mac mini 并行值守验证)
- **Phase 3 完成:10/26+**(8B 正式对拍时 Mac mini 已是主力)

## 六、决策需求(候用户)

1. 迁移启动时间:10/13 开业周启动 Phase 0?
2. Mac mini 是接替 Windows(完全替换)还是并行(双值守)?
3. Mac mini 是否需要跑 BGE 嵌入(本机 MPS)还是全部走 A100?
4. 迁移完成后 Windows 角色变化(备用机/退役/改派)?

—— compass · 大迁移规划 · 2026-10-11 · 候用户确认
