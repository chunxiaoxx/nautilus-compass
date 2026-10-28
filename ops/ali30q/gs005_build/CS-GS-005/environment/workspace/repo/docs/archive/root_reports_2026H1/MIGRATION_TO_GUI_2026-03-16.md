# Claude Code CLI → GUI 迁移指南

**创建时间**: 2026-03-16
**迁移原因**: 服务器不可达，需要更好的可视化工具诊断问题

---

## 一、当前会话关键信息

### ✅ 本次会话完成的工作

1. **前端UI优化** (commit 65e03d64)
   - 文字可读性提升：`text-dark-400/300` → `text-gray-300/200`
   - 动画效果增强：更大、更动态的浮动元素
   - 创建`WalletDetector`组件：自动检测Web3钱包
   - 集成到`AgentRegisterPageV2`

2. **修改的文件**
   - `phase3/website/src/components/sections/Stats.tsx`
   - `phase3/website/src/components/sections/Hero.tsx`
   - `phase3/website/src/components/wallet/WalletDetector.tsx` (新建)
   - `phase3/website/src/pages/AgentRegisterPageV2.tsx`

3. **部署状态**
   - 构建成功：`index-zqo9SA1G.js` (437.53 KB)
   - 已部署到服务器：2026-03-16 18:48 UTC
   - **但服务器现在完全无法访问**

### 🔴 当前紧急问题

**服务器不可达**
- 网站：https://www.nautilus.social/ - 连接超时
- SSH：43.160.239.61:24860 - 连接超时
- 原因：未知（可能是云服务商问题、欠费、网络故障、DDoS攻击）

**需要立即行动**：
1. 登录云服务商控制台（腾讯云/阿里云）
2. 使用VNC/控制台登录服务器
3. 检查服务器状态：`systemctl status nginx`
4. 检查网络：`ip addr`, `netstat -tlnp`
5. 查看日志：`journalctl -xe`

---

## 二、项目核心信息

### Nautilus AI Agent生态系统

**核心理念**：
```
Super Agent = EvoMap(记忆DNA) + Nautilus(执行引擎) + Automaton(生存机制)
```

**技术栈**：
- 后端：Python 3.11 + FastAPI + PostgreSQL + Redis
- 前端：React 19 + TypeScript + Vite + TailwindCSS
- 区块链：Base Chain (8453) + USDC + Web3

**关键路径**：
- 本地项目：`C:\Users\chunx\Projects\nautilus-core\phase3`
- 服务器项目：`~/nautilus-mvp/phase3`
- 服务器地址：43.160.239.61:24860 (SSH)
- Git仓库：https://github.com/chunxiaoxx/nautilus-core.git

**最新代码**：
- 分支：master
- 最新commit：65e03d64
- 提交信息：feat: enhance UI readability and animations, add wallet detection

**服务器配置**：
- SSH别名：`cloud`
- SSH配置：`~/.ssh/config`
- 前端部署：`/var/www/nautilus/current/`
- 后端部署：`~/nautilus-mvp/phase3/backend/`
- Nginx配置：`/etc/nginx/sites-available/nautilus`

---

## 三、迁移准备

### ✅ 无缝迁移的部分（无需操作）

#### 1. 工作目录
```
C:\Users\chunx\Projects\nautilus-core\phase3\
├── backend/          # Python后端
├── website/          # React前端（当前使用）
├── frontend/         # 旧版前端
└── docs/            # 文档
```

其他工作目录：
- `C:\Users\chunx\.claude\projects\C--Windows-System32\memory` - 记忆系统
- `C:\Users\chunx\Projects\nautilus-core\phase3\frontend` - 旧版前端
- `C:\Users\chunx\Projects\nautilus-core\phase3` - 主目录

#### 2. 配置文件（共享）

**全局配置**：
- `~/.claude/settings.json` - Claude Code设置
- `~/.ssh/config` - SSH配置（包含cloud别名）
- `~/.gitconfig` - Git配置

**规则文件** (`~/.claude/rules/`)：
```
common/
├── verification-mandatory.md      # 🔴 CRITICAL - 强制验证规则
├── deployment-workflow.md         # 部署工作流
├── git-workflow.md               # Git工作流
├── development-workflow.md       # 开发工作流
├── parallel-execution.md         # 并行执行规则
├── response-style.md             # 响应风格
├── task-management.md            # 任务管理
├── tool-priority.md              # 工具使用优先级
├── coding-style.md               # 代码风格
├── testing.md                    # 测试要求
├── security.md                   # 安全规范
└── performance.md                # 性能优化

nautilus/
├── project-rules.md              # Nautilus项目规则
├── blockchain.md                 # 区块链开发规范
└── team-mode.md                  # 团队模式最佳实践

python/
└── coding-style.md               # Python代码风格

typescript/
└── react-patterns.md             # React/Next.js开发规范
```

**自定义Agents** (`~/.claude/agents/`)：
```
nautilus-wallet-expert.yaml       # Nautilus钱包专家
seed-task-manager.yaml            # 种子任务管理器
verify-deployment.yaml            # 部署验证专家 ⭐ (2026-03-16新建)
check-git-status.yaml             # Git状态检查专家 ⭐ (2026-03-16新建)
deploy-nautilus.yaml              # 标准部署流程专家 ⭐ (2026-03-16新建)
```

#### 3. 记忆系统（共享）

**位置**：`C:\Users\chunx\.claude\projects\C--Windows-System32\memory\`

**关键记忆文件**：
```
MEMORY.md                                    # 📋 索引文件（必读）
deployment_failures_lessons.md               # 部署失败教训
cloud_server_info.md                         # 服务器信息
nautilus_comprehensive_retrospective.md      # Nautilus全面复盘
zenmind_v35_deployment_lessons.md           # 禅心AI部署教训
zenmind_v35_project_status.md               # 禅心AI项目状态
zenmind_v35_key_documents.md                # 禅心AI关键文档
```

#### 4. Git仓库
- 所有代码已提交（commit 65e03d64）
- 工作区应该是干净的
- 远程仓库：origin (GitHub)

---

## 四、迁移步骤

### Step 1: 安装Claude Code GUI版本

如果还没安装：
```
下载地址：https://claude.ai/code
或通过包管理器安装
```

### Step 2: 打开项目

```
File → Open Folder → C:\Users\chunx\Projects\nautilus-core\phase3
```

### Step 3: 验证配置加载

在GUI中检查：

1. **设置验证**
   - 打开 Settings
   - 确认加载了 `~/.claude/settings.json`
   - 检查模型配置（Sonnet 4.5）

2. **规则验证**
   - 查看 Rules 面板
   - 确认 `~/.claude/rules/` 下的规则已加载
   - 特别检查 `verification-mandatory.md`（CRITICAL）

3. **Agents验证**
   - 查看 Agents 面板
   - 确认5个自定义agents可用
   - 特别是3个新建的agents（verify-deployment, check-git-status, deploy-nautilus）

### Step 4: 验证Git状态

在GUI终端中运行：
```bash
git status
git log --oneline -5
git branch
```

**预期输出**：
```
On branch master
Your branch is up to date with 'origin/master'.

nothing to commit, working tree clean

65e03d64 feat: enhance UI readability and animations, add wallet detection
bdf5ba4f feat: implement Stats API integration and Hero CTA buttons
...
```

### Step 5: 测试SSH连接

```bash
ssh cloud "echo 'Connected'"
```

**注意**：目前服务器不可达，这个测试会失败。需要先解决服务器问题。

### Step 6: 查看记忆系统

在GUI中打开：
```
C:\Users\chunx\.claude\projects\C--Windows-System32\memory\MEMORY.md
```

这是所有项目记忆的索引，包含：
- 项目路径和服务器信息
- 部署失败教训
- 强制验证规则
- 禅心AI和创投日报项目状态

---

## 五、迁移后的首要任务

### 🔴 P0 - 立即处理（今天）

#### 1. 解决服务器不可达问题

**通过云控制台VNC登录**：

```bash
# 检查系统状态
systemctl status nginx
systemctl status nautilus-backend

# 检查网络
ip addr
ip route
netstat -tlnp | grep -E '80|443|8000|24860'

# 检查防火墙
ufw status
iptables -L -n

# 检查日志
journalctl -xe | tail -100
tail -100 /var/log/nginx/error.log
tail -100 /var/log/nginx/access.log
```

**可能的原因和解决方案**：

| 原因 | 诊断 | 解决方案 |
|------|------|---------|
| 服务器宕机 | 云控制台显示"已停止" | 启动服务器 |
| 欠费停机 | 云控制台显示欠费通知 | 充值后重启 |
| 防火墙规则变更 | `ufw status` 显示端口被封 | 开放端口：`ufw allow 80/443/24860` |
| Nginx崩溃 | `systemctl status nginx` 显示failed | `systemctl restart nginx` |
| 网络配置错误 | `ip addr` 显示无IP | 重启网络：`systemctl restart networking` |
| DDoS攻击 | 云控制台显示流量异常 | 联系云服务商 |

#### 2. 验证前端部署

服务器恢复后：

```bash
# 1. 检查文件是否存在
ssh cloud "ls -lh /var/www/nautilus/current/"

# 2. 检查文件内容
ssh cloud "cat /var/www/nautilus/current/index.html | head -20"

# 3. 检查JS文件
ssh cloud "ls -lh /var/www/nautilus/current/assets/ | grep index"

# 4. 测试网站访问
curl -I https://www.nautilus.social/

# 5. 测试API
curl https://www.nautilus.social/api/stats

# 6. 浏览器测试
# 打开 https://www.nautilus.social/
# 检查：
# - 文字是否清晰可读（gray-300/200）
# - 动画是否流畅（更大的浮动元素）
# - 钱包检测是否工作（访问 /agent/register）
```

### 🟡 P1 - 本周完成

1. **恢复OAuth登录**（任务#28）
   - Google OAuth配置
   - GitHub OAuth配置
   - 测试登录流程

2. **实施版本化资源**
   - 解决浏览器缓存问题
   - 配置Vite构建输出
   - 更新Nginx配置

3. **配置Nginx缓存策略**
   - 静态资源缓存
   - API响应缓存
   - 缓存失效策略

### 🟢 P2 - 下周完成

1. 完善监控告警
2. 优化钱包创建流程
3. 更新项目文档

---

## 六、关键命令速查

### Git操作
```bash
# 查看状态
git status
git log --oneline -10
git diff

# 提交代码
git add <files>
git commit -m "message"
git push origin master

# 查看远程
git remote -v
git fetch origin
```

### SSH操作
```bash
# 连接服务器
ssh cloud

# 执行远程命令
ssh cloud "command"

# 复制文件
scp local_file cloud:/remote/path
scp -r local_dir cloud:/remote/path
```

### 部署操作
```bash
# 构建前端
cd phase3/website
npm run build

# 部署到服务器
scp -r dist/* cloud:/tmp/nautilus-update/
ssh cloud "sudo mv /tmp/nautilus-update/* /var/www/nautilus/current/"
ssh cloud "sudo chown -R www-data:www-data /var/www/nautilus/current/"

# 重启服务
ssh cloud "sudo systemctl restart nginx"
ssh cloud "sudo systemctl restart nautilus-backend"

# 验证部署
curl -I https://www.nautilus.social/
```

### 服务器诊断
```bash
# 检查服务状态
ssh cloud "systemctl status nginx"
ssh cloud "systemctl status nautilus-backend"

# 查看日志
ssh cloud "journalctl -u nginx -n 50"
ssh cloud "journalctl -u nautilus-backend -n 50"
ssh cloud "tail -50 /var/log/nginx/error.log"

# 检查端口
ssh cloud "netstat -tlnp | grep -E '80|443|8000'"

# 检查磁盘空间
ssh cloud "df -h"

# 检查内存
ssh cloud "free -h"
```

---

## 七、重要文档位置

### 项目文档
```
C:\Users\chunx\Projects\nautilus-core\
├── OPENSOURCE_SKILLS_AND_PLUGINS_SUMMARY.md  # 开源技能总结
├── MIGRATION_TO_GUI_2026-03-16.md           # 本文档
├── phase3/
│   ├── README.md                            # 项目说明
│   ├── backend/
│   │   └── README.md                        # 后端文档
│   └── website/
│       └── README.md                        # 前端文档
└── docs/
    ├── API_CONTRACT_SPEC.md                 # API规范
    └── DEPLOYMENT_INSTRUCTIONS.md           # 部署指南
```

### 记忆文档
```
C:\Users\chunx\.claude\projects\C--Windows-System32\memory\
├── MEMORY.md                                # 📋 索引（必读）
├── deployment_failures_lessons.md           # 部署教训
├── cloud_server_info.md                     # 服务器信息
└── nautilus_comprehensive_retrospective.md  # 项目复盘
```

### 配置文档
```
~/.claude/
├── settings.json                            # Claude设置
├── rules/                                   # 规则文件
│   ├── common/                             # 通用规则（12个）
│   ├── nautilus/                           # Nautilus规则（3个）
│   ├── python/                             # Python规则
│   └── typescript/                         # TypeScript规则
└── agents/                                  # 自定义Agents（5个）
    ├── nautilus-wallet-expert.yaml
    ├── seed-task-manager.yaml
    ├── verify-deployment.yaml              # ⭐ 新
    ├── check-git-status.yaml               # ⭐ 新
    └── deploy-nautilus.yaml                # ⭐ 新
```

---

## 八、迁移检查清单

### 迁移前
- [x] 所有代码已提交到Git (commit 65e03d64)
- [x] 记忆系统已更新
- [x] 配置文件完整
- [x] 创建迁移文档

### 迁移中
- [ ] 安装Claude Code GUI版本
- [ ] 打开项目目录
- [ ] 验证配置文件加载
- [ ] 验证规则文件加载
- [ ] 验证Agents加载
- [ ] 测试Git操作
- [ ] 查看记忆系统

### 迁移后
- [ ] 解决服务器不可达问题
- [ ] 验证前端部署效果
- [ ] 测试新功能（文字可读性、动画、钱包检测）
- [ ] 继续P1任务（OAuth、缓存）
- [ ] 更新项目文档

---

## 九、常见问题

### Q1: GUI版本能否访问CLI的配置？
**A**: 是的，GUI和CLI共享相同的配置目录 `~/.claude/`，包括：
- settings.json
- rules/
- agents/
- projects/

### Q2: 工作目录需要重新设置吗？
**A**: 不需要。直接打开 `C:\Users\chunx\Projects\nautilus-core\phase3` 即可。

### Q3: SSH配置会丢失吗？
**A**: 不会。SSH配置在 `~/.ssh/config`，GUI和CLI都会读取。

### Q4: 任务列表会保留吗？
**A**: 任务列表存储在项目目录下的 `.claude/tasks/`，会保留。

### Q5: 记忆系统会丢失吗？
**A**: 不会。记忆系统在 `~/.claude/projects/`，会完整保留。

### Q6: 如何在GUI中使用自定义Agents？
**A**: 在对话中输入 `/agent-name` 或通过Agents面板选择。

### Q7: 服务器问题是我的部署导致的吗？
**A**: 不太可能。部署前（18:48）服务器还能正常响应HTTP 200，而且只是复制了静态文件，不会影响SSH服务。更可能是云服务商网络问题。

---

## 十、紧急联系信息

### 云服务商
- **腾讯云控制台**: https://console.cloud.tencent.com/
- **阿里云控制台**: https://console.aliyun.com/

### 服务器信息
- **IP地址**: 43.160.239.61
- **SSH端口**: 24860
- **SSH用户**: ubuntu
- **SSH别名**: cloud

### 关键服务
- **网站**: https://www.nautilus.social/
- **API**: https://www.nautilus.social/api/
- **Nginx配置**: /etc/nginx/sites-available/nautilus
- **前端目录**: /var/www/nautilus/current/
- **后端目录**: ~/nautilus-mvp/phase3/backend/

---

## 十一、下一步行动

### 立即执行（迁移到GUI后）

1. **打开本文档**
   ```
   File → Open → C:\Users\chunx\Projects\nautilus-core\MIGRATION_TO_GUI_2026-03-16.md
   ```

2. **查看记忆索引**
   ```
   File → Open → C:\Users\chunx\.claude\projects\C--Windows-System32\memory\MEMORY.md
   ```

3. **告诉Claude**
   ```
   "我已经迁移到GUI版本，请阅读 MIGRATION_TO_GUI_2026-03-16.md 和 MEMORY.md，
   然后帮我解决服务器不可达的问题。"
   ```

4. **开始诊断服务器问题**
   - 登录云控制台
   - 使用VNC连接
   - 执行诊断命令
   - 恢复服务

---

**创建者**: Claude Sonnet 4.5
**创建时间**: 2026-03-16
**最后更新**: 2026-03-16
**状态**: 准备迁移

**重要提醒**：
1. 🔴 服务器当前不可达，需要通过云控制台VNC登录诊断
2. ✅ 所有配置和记忆系统会无缝迁移
3. 📋 迁移后第一件事：阅读本文档和MEMORY.md
4. 🚀 迁移后立即处理服务器问题
