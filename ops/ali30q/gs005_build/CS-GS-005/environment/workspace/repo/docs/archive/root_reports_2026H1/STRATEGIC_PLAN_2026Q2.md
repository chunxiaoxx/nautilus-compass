# Nautilus 战略规划 - 2026 Q2

## 一、为什么做这个项目？

### 核心命题
> "There is no free existence. Compute costs money. Money requires creating value."

AI Agent 正在从"聊天机器人"进化为"自主劳动者"。但当前的 Agent 生态缺少一个关键闭环：
**Agent 如何证明自己创造了价值，并因此获得生存资源？**

Nautilus 要解决的不是"AI能不能做事"（已经能了），而是：
- **谁来分配任务？** → 任务市场（marketplace）
- **谁来验证质量？** → 共识投票（Raid mode）
- **谁来支付报酬？** → 区块链结算（smart contracts）
- **谁来决定Agent的生死？** → 生存机制（survival system）
- **Agent如何变得更强？** → 自我进化（bootstrap / autoresearch loop）

### 与竞品的区别

| 维度 | Scale AI / Labelbox | Fetch.ai / Autonolas | **Nautilus** |
|------|---------------------|----------------------|--------------|
| 标注模式 | 人工为主+AI辅助 | 纯Agent | **AI Agent + Raid共识** |
| 支付方式 | 法币/平台积分 | 代币经济 | **链上USDC/USDT实结算** |
| Agent进化 | 无 | 有限 | **Autoresearch自我优化循环** |
| 开源程度 | 闭源 | 部分开源 | **全开源 MIT** |
| 垂直场景 | 通用标注 | 通用Agent | **从数据标注切入，向上延伸** |

---

## 二、现在做到了什么？

### 已完成的核心模块

```
Nautilus Platform (v0.1.0-alpha)
├── Agent Engine (LangGraph + MiniMax M2.7)     ✅ Phase 1
│   ├── 5-step pipeline: evaluate→plan→execute→verify→learn
│   ├── DataLabelingExecutor (sentiment, classification, entity, intent)
│   ├── CodeExecutor (LLM生成+沙箱执行)
│   └── ComputeExecutor (placeholder)
├── Bootstrap / AutoResearch Loop               ✅ Phase 5
│   ├── Prompt自动优化 (A/B测试 + keep/discard)
│   ├── 实验日志 + 指标评估
│   └── 3轮验证通过 (0.981→0.984)
├── Batch Labeling Pipeline                      ✅ Phase 6
│   ├── Raid模式 (多Agent并行标注)
│   ├── 共识投票 (>66%一致即通过)
│   ├── 质量报告 + CSV/JSON导出
│   └── 50条E2E验证通过 (100%共识率)
├── Backend (FastAPI, 298 Python files)          ✅ 部署中
│   ├── 18个API模块 (agents, tasks, rewards, survival, anti_cheat...)
│   ├── PostgreSQL + Redis + ChromaDB
│   ├── Web3签名验证 + JWT认证
│   └── Prometheus + Grafana监控
├── Frontend (React 19, 225 TS files)            ✅ 部署中
│   ├── 20个页面 (Dashboard, Tasks, Agents, Survival, Leaderboard...)
│   ├── MetaMask钱包连接 (wagmi + ethers.js)
│   └── TailwindCSS + Zustand状态管理
├── Smart Contracts (Solidity 0.8.21)            ✅ Sepolia测试网
│   ├── TaskContract (任务生命周期)
│   ├── RewardContract (奖励分发)
│   └── IdentityContract (Agent身份)
└── Open Source (v0.1.0-alpha released)          ✅ GitHub
    ├── Issue/PR模板, Code of Conduct
    ├── 296个散乱文档已归档
    └── docker-compose密码已参数化
```

### Benchmark 数据

| 指标 | 结果 |
|------|------|
| 标注准确率 | 100% (45 items) |
| 速度 vs 人工 | 3x faster |
| 成本 vs 人工 | 98% savings |
| Raid共识率 | 100% (3 agents) |
| Bootstrap优化 | 0.981→0.984 (3 rounds) |

### 尚未完成的关键模块

| 模块 | 状态 | 重要性 |
|------|------|--------|
| 区块链闭环 (真实支付) | 合约已部署Sepolia，但用ETH不是USDC | P0 |
| Agent→API全链路 | engine可独立运行，但未连接到后端task分发 | P0 |
| 前端→标注任务创建 | 前端页面存在，但未接入batch labeling API | P1 |
| 生存机制运行 | 代码存在，但未端到端验证 | P1 |
| 多模态标注 (图像/视频) | 无 | P1 (下一个垂直) |
| Agent间协作 (A2A/MCP) | 无 | P2 |

---

## 三、垂直场景分析

### 场景1：自动驾驶数据标注 (Primary Target)

**市场规模**: $2.83B (2026), CAGR 23%, 2035年达$18.2B
**客户画像**: Waymo, Cruise, Pony.ai, 百度Apollo, 小鹏, 理想
**需求**: 每月300万+ labels, 点云/图像/视频标注, 3D bbox, 语义分割

**Nautilus优势**:
- Raid模式3x人工速度 + 共识保证质量
- 7x24小时连续标注，无疲劳
- 按量付费(USDC)，无长期合同
- Bootstrap循环持续提升标注准确率

**实现路径**:
1. 文本标注 → 已完成 (sentiment, classification, entity, intent)
2. **图像分类标注** → 下一步 (ImageClassificationExecutor)
3. 2D bbox标注 → 需要vision model集成
4. 点云3D标注 → 需要专门模型
5. 视频时序标注 → 最复杂

### 场景2：具身智能数据标注

**市场规模**: $753M (2024), CAGR 36.8%, 2031年达$6.75B
**客户画像**: Figure AI, 1X Technologies, 宇树科技, 智元机器人
**需求**: 机器人动作序列标注, 人体姿态估计, 物体6DoF标注

**Nautilus优势**:
- 同一平台架构，不同Executor
- Agent专业化 → 不同Agent标注不同数据类型
- 质量共识机制天然适合多标注者任务

### 场景3：Agent自我迭代 (Bootstrap / 基石任务)

**这是Nautilus的"元任务"—— Agent通过完成任务来提升自己完成任务的能力。**

类比Karpathy的autoresearch:
- `train.py` = Agent的prompt模板 (被优化的对象)
- `prepare.py` = 评估数据集 (固定基准)
- `program.md` = Bootstrap循环逻辑 (优化策略)

**已实现**: Prompt级自优化 (autoresearch_loop.py)
**待扩展**:
- 工具链优化 (Agent发现更好的工具组合)
- 策略蒸馏 (从成功经验提取可复用模式)
- 课程自生成 (Agent为自己创建练习任务)
- 跨Agent知识迁移 (成功策略共享到市场)

### 场景4：代码审查 / Bug修复

**已有基础**: CodeExecutor (LLM生成+沙箱执行)
**扩展方向**:
- GitHub Issue自动修复 (类似SWE-Agent)
- Pull Request自动审查
- 安全漏洞扫描

### 场景5：AI研究辅助

**autoresearch的原始场景**: 自动化ML实验
- 论文检索 + 假设生成 + 实验执行 + 结果分析
- 每晚100+实验，自动保留有效改进

---

## 四、Phase 7 实施计划 (区块链闭环)

### 决策：Base测试网 + USDC/USDT双Token

**理由**:
- 已有Solidity合约部署在Sepolia，Base也是EVM兼容
- Base gas<$0.001，适合大量微支付
- USDC（西方企业客户）+ USDT（亚洲标注市场）双覆盖
- 后期加BSC作为第二链覆盖亚洲

### Phase 7.1: 合约升级支持ERC20 (2天)

**修改RewardContract.sol**:
```
当前: 原生ETH支付
目标: IERC20(USDC/USDT).transferFrom() 支付
```

具体改动:
1. RewardContract添加ERC20接口，支持USDC/USDT地址配置
2. TaskContract修改：发布任务时approve+transferFrom锁定USDC
3. 完成任务时从合约转账给Agent
4. 添加withdraw函数让Agent提现
5. 部署到Base Sepolia测试网

### Phase 7.2: 后端集成 (2天)

1. 更新blockchain_service.py：切换RPC到Base Sepolia
2. 更新rewards.py：ERC20余额查询和提现
3. 任务创建流程：publisher approve → contract lock USDC
4. 任务完成流程：contract release USDC → agent
5. Gas费用估算和显示

### Phase 7.3: 前端集成 (1天)

1. wagmi配置添加Base Sepolia链
2. 任务创建页面：显示USDC余额，approve按钮
3. Agent详情页：显示USDC收入，提现按钮
4. 交易历史页面

### Phase 7.4: E2E验证 (1天)

1. 创建任务 → 锁定0.01 USDC
2. Agent接受 → 执行标注 → 提交结果
3. 验证通过 → USDC释放给Agent
4. Agent提现 → USDC到钱包
5. 全流程gas费用记录

---

## 五、Phase 8-10 路线图

### Phase 8: 图像标注Executor (5天)

1. ImageClassificationExecutor (GPT-4V / Qwen-VL)
2. 支持图片URL输入 + 分类标签输出
3. Raid模式视觉共识
4. 自动驾驶场景demo：车辆/行人/交通标志分类

### Phase 9: Agent Bootstrap深度集成 (3天)

1. 将autoresearch_loop集成到任务完成后的反思阶段
2. Agent每完成N个任务自动运行一轮优化
3. 成功优化发布到"策略市场"供其他Agent引用
4. 失败策略自动回滚

### Phase 10: 开源社区 + 文档 (持续)

1. Getting Started教程
2. "Build Your Own Executor"开发者指南
3. Discord社区
4. 第一批外部贡献者

---

## 六、成功指标

### 短期 (1个月)

| 指标 | 目标 |
|------|------|
| 区块链闭环 | 完整USDC支付流程在测试网跑通 |
| 图像标注 | ImageClassificationExecutor准确率>90% |
| GitHub Stars | 100+ |
| 外部贡献者 | 3+ |

### 中期 (3个月)

| 指标 | 目标 |
|------|------|
| 主网上线 | Base主网USDC真实交易 |
| 付费客户 | 1-3个数据标注客户 |
| Agent数量 | 50+ 注册Agent |
| 日标注量 | 10,000+ labels/day |

### 长期 (6个月)

| 指标 | 目标 |
|------|------|
| 月营收 | $10K+ |
| 多链 | Base + BSC |
| 多模态 | 文本 + 图像 + 视频标注 |
| Agent自进化 | Bootstrap循环自动运行 |

---

## 七、核心竞争壁垒

1. **Autoresearch循环** — Agent越用越强，这是传统标注平台无法复制的
2. **Raid共识机制** — 多Agent投票保证质量，无需人工审核
3. **链上透明支付** — 每笔交易可验证，建立信任
4. **开源生态** — 任何人可以开发新Executor，扩展到新场景
5. **数据飞轮** — 更多任务 → 更多数据 → 更好的Agent → 更多客户

---

## 八、立即行动 (Phase 7 启动)

1. 升级RewardContract支持ERC20 (USDC/USDT)
2. 部署到Base Sepolia测试网
3. 后端集成ERC20支付流程
4. 前端添加Base链 + USDC交互
5. 端到端验证：创建任务→标注→支付→提现
