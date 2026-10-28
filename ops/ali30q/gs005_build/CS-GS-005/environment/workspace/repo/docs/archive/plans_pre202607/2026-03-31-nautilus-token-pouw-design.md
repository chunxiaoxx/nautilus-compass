# Nautilus Token (NAU) — Proof of Useful Work 设计文档

**日期**: 2026-03-31
**状态**: 已批准，待实施
**范围**: MVP — 链上 ERC20 token，academic task 完成后 mint

---

## 1. 背景与定位

### 核心叙事

> "There is no free existence. Compute costs money. Money requires creating value."

NAU（Nautilus Token）是平台的 **Proof of Useful Work（PoUW）** token：

- 传统 PoW（Bitcoin）：算法解哈希谜题 → 纯计算浪费
- Nautilus PoUW：agent 完成真实学术计算任务（物理模拟、ML 训练、科学建模）→ mint NAU

算力产生真实科研价值，token 是这一价值的链上凭证。

### Survival Score 关系

MVP 阶段：
- **DB survival score** = source of truth（现有系统不变）
- **链上 NAU balance** = 链上记录层（并行，不双向同步）

后期演化方向：链上 token balance 作为 survival 权威来源，DB 定期从链上同步。

---

## 2. 架构

```
Academic Task 完成
       │
       ▼
 _execute_task_async()
       │
       ├─► SurvivalService.update_scores()     (现有，不变)
       │
       └─► NautilusTokenService.mint_task_reward()
                   │
                   ├─ 查 agent.owner（钱包地址）
                   ├─ 按 task_type 查奖励表 → NAU amount
                   ├─ token_contract.mint(owner, amount * 1e18)
                   ├─ 写 tx_hash → academic_tasks.blockchain_tx_hash
                   └─ 失败时 log warning，不影响任务完成状态
```

**关键原则**：mint 异步、非阻塞。失败不影响任务结果。

---

## 3. 智能合约

### NautilusToken.sol

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract NautilusToken is ERC20, Ownable {
    constructor() ERC20("Nautilus Token", "NAU") Ownable(msg.sender) {}

    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }
}
```

- 18 decimals（标准 ERC20）
- 只有 owner（平台服务器钱包）可 mint
- 无总量上限（MVP，后期可加 cap）
- 无销毁机制（MVP）

### 部署

- 网络：Base Sepolia（chain_id=84532）
- 工具：Hardhat（`phase3/contracts/hardhat.config.js` 已配置）
- 所需：`DEPLOYER_PRIVATE_KEY` 环境变量 + Base Sepolia ETH（faucet 可取）

---

## 4. 奖励分级（PoUW 难度映射）

按计算复杂度和科研价值分级：

| task_type | NAU | 说明 |
|---|---|---|
| physics_simulation | 10 | 高复杂度物理模拟 |
| pde_simulation | 10 | 偏微分方程求解 |
| ode_simulation | 5 | 常微分方程 |
| ml_training | 5 | 机器学习训练 |
| monte_carlo | 5 | 蒙特卡洛模拟 |
| jc_constitutive | 5 | JC 本构模型 |
| thmc_coupling | 5 | THMC 耦合模拟 |
| curve_fitting | 3 | 曲线拟合 |
| statistical_analysis | 3 | 统计分析 |
| data_visualization | 1 | 数据可视化 |
| general_computation | 1 | 通用计算 |

---

## 5. 后端实现

### 新文件：`services/nautilus_token.py`

职责：
- 持有奖励分级表
- 封装 mint 调用（build tx → sign → send）
- 返回 tx_hash 或 None

### DB 变更：`academic_tasks` 表新增字段

```sql
ALTER TABLE academic_tasks ADD COLUMN blockchain_tx_hash VARCHAR(66);
ALTER TABLE academic_tasks ADD COLUMN token_reward FLOAT;
```

### 集成点：`api/academic_tasks.py`

在任务完成回调中，survival score 更新之后追加：

```python
try:
    tx_hash = await NautilusTokenService.mint_task_reward(
        agent_wallet=agent.owner,
        task_type=task.task_type,
    )
    if tx_hash:
        task.blockchain_tx_hash = tx_hash
        task.token_reward = TASK_TYPE_REWARDS.get(task.task_type, 1)
except Exception as e:
    logger.warning("Token mint failed (non-blocking): %s", e)
```

### 新增环境变量

```env
BLOCKCHAIN_PRIVATE_KEY=<deployer/server钱包私钥>
NAU_TOKEN_ADDRESS=<部署后合约地址>
```

---

## 6. 错误处理

| 场景 | 处理方式 |
|---|---|
| `BLOCKCHAIN_PRIVATE_KEY` 未配置 | 启动时 log warning，所有 mint 调用跳过 |
| `NAU_TOKEN_ADDRESS` 未配置 | mint 调用跳过 |
| agent 无 `owner` 地址 | 跳过 mint |
| agent owner 是 SecurityTestBot 等无效地址 | mint 仍执行（地址合法即可），但无人取款 |
| 链上交易 revert | log warning，任务仍 COMPLETED |
| RPC 超时 | log warning，任务仍 COMPLETED |

---

## 7. 验证标准（MVP 完成条件）

- [ ] `NautilusToken.sol` 部署到 Base Sepolia，Basescan 可查合约
- [ ] 一个 OpenClaw agent 完成 academic task
- [ ] `academic_tasks.blockchain_tx_hash` 有值
- [ ] Basescan 上该 tx 显示 `mint` 调用，agent 钱包收到 NAU
- [ ] 任务失败不影响 task 完成状态

---

## 8. 后期演化路线（不在 MVP 范围）

1. **链上验证**：引入零知识证明或链上验证器，mint 由合约自动触发，无需信任平台
2. **Token → Survival 同步**：DB survival score 定期从链上 token balance 同步
3. **Token 经济**：引入销毁机制（agent 失活时 burn），代币总量有意义
4. **DAO 治理**：奖励分级表链上投票决定
5. **Mainnet 迁移**：Base Sepolia → Base Mainnet

---

## 9. 实施计划概览

| 步骤 | 预估 |
|---|---|
| 写 + 测试 NautilusToken.sol | 1-2小时 |
| 部署到 Base Sepolia | 1-2小时 |
| 写 NautilusTokenService | 1-2小时 |
| DB migration + 集成 academic_tasks | 1小时 |
| 端到端验证（Basescan 确认） | 1小时 |
| **总计** | **~1天** |
