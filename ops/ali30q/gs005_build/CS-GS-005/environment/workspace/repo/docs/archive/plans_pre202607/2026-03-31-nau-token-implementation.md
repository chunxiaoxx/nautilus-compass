# NAU Token (PoUW) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 部署 NautilusToken ERC20 合约到 Base Sepolia，academic task 完成后 mint NAU 到 agent 钱包，Basescan 留下记录。

**Architecture:** NautilusToken.sol（ERC20 + Ownable）部署在 Base Sepolia，平台服务器持有 owner 私钥。Academic task 完成时，`NautilusTokenService` 调用 `mint(agent_wallet, amount)`，tx_hash 写入 `academic_tasks.blockchain_tx_hash`，失败不阻塞任务结果。

**Tech Stack:** Solidity 0.8.21, OpenZeppelin, Hardhat, Web3.py, FastAPI, Alembic, Base Sepolia testnet

---

## 前置条件（手动操作，开始前完成）

1. **准备 deployer 钱包**：需要一个以太坊钱包的私钥，该钱包将成为合约 owner 及平台 mint 账户。
2. **获取 Base Sepolia ETH**：访问 https://faucet.quicknode.com/base/sepolia 或 https://www.coinbase.com/faucets/base-ethereum-goerli-faucet，领取测试 ETH（约 0.05 ETH，够数十次部署）。
3. **确认钱包有 ETH**：用 https://sepolia.basescan.org/address/{your_address} 确认余额 > 0。
4. **在服务器 `.env` 设置（暂时本地开发）**：
   ```
   DEPLOYER_PRIVATE_KEY=0x<your_private_key>
   BLOCKCHAIN_PRIVATE_KEY=0x<same_private_key>
   ```

---

## Task 1: 编写并编译 NautilusToken.sol

**Files:**
- Create: `phase3/contracts/src/NautilusToken.sol`

**Step 1: 写合约**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/// @title NautilusToken (NAU)
/// @notice Proof of Useful Work token. Minted by platform when agents
///         complete real computational tasks (physics simulation, ML, etc.)
contract NautilusToken is ERC20, Ownable {
    event TaskRewarded(address indexed agent, uint256 amount, string taskType);

    constructor() ERC20("Nautilus Token", "NAU") Ownable(msg.sender) {}

    /// @notice Mint NAU to an agent wallet. Only platform (owner) can call.
    /// @param to Agent wallet address
    /// @param amount Amount in wei (1 NAU = 1e18)
    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }

    /// @notice Mint with task type event for off-chain indexing
    function mintForTask(address to, uint256 amount, string calldata taskType) external onlyOwner {
        _mint(to, amount);
        emit TaskRewarded(to, amount, taskType);
    }
}
```

**Step 2: 编译**

```bash
cd phase3/contracts
npx hardhat compile
```

期望输出：`Compiled 1 Solidity file successfully`

Artifact 生成在：`phase3/contracts/artifacts/src/NautilusToken.sol/NautilusToken.json`

**Step 3: Commit**

```bash
git add phase3/contracts/src/NautilusToken.sol
git commit -m "feat: add NautilusToken ERC20 (PoUW) contract"
```

---

## Task 2: 部署合约到 Base Sepolia

**Files:**
- Create: `phase3/contracts/scripts/deploy_nau.js`

**Step 1: 写部署脚本**

```javascript
const hre = require("hardhat");

async function main() {
  console.log("Deploying NautilusToken to", hre.network.name);

  const [deployer] = await hre.ethers.getSigners();
  console.log("Deployer:", deployer.address);

  const balance = await hre.ethers.provider.getBalance(deployer.address);
  console.log("Balance:", hre.ethers.formatEther(balance), "ETH");

  const NautilusToken = await hre.ethers.getContractFactory("NautilusToken");
  const token = await NautilusToken.deploy();
  await token.waitForDeployment();

  const address = await token.getAddress();
  console.log("NautilusToken deployed to:", address);
  console.log("Add to .env: NAU_TOKEN_ADDRESS=" + address);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
```

**Step 2: 确认前置条件满足**（`DEPLOYER_PRIVATE_KEY` 已设置在 `phase3/contracts/.env`）

```bash
cat phase3/contracts/.env | grep DEPLOYER_PRIVATE_KEY
```

如果没有，在 `phase3/contracts/.env` 创建（不 commit 这个文件）：
```
DEPLOYER_PRIVATE_KEY=0x<your_key>
```

**Step 3: 部署**

```bash
cd phase3/contracts
npx hardhat run scripts/deploy_nau.js --network baseSepolia
```

期望输出：
```
Deploying NautilusToken to baseSepolia
Deployer: 0x...
Balance: 0.05 ETH
NautilusToken deployed to: 0x<CONTRACT_ADDRESS>
Add to .env: NAU_TOKEN_ADDRESS=0x<CONTRACT_ADDRESS>
```

**Step 4: 验证部署**

打开 `https://sepolia.basescan.org/address/0x<CONTRACT_ADDRESS>`，确认：
- Contract 已部署
- Token name = "Nautilus Token", symbol = "NAU"

**Step 5: 把合约地址加入服务器 .env**

在 `phase3/backend/.env`（或服务器环境变量）：
```
NAU_TOKEN_ADDRESS=0x<CONTRACT_ADDRESS>
BLOCKCHAIN_PRIVATE_KEY=0x<same_as_DEPLOYER_PRIVATE_KEY>
```

**Step 6: 复制 ABI 到后端**

```bash
node -e "
const art = require('./artifacts/src/NautilusToken.sol/NautilusToken.json');
const fs = require('fs');
fs.writeFileSync(
  '../backend/blockchain/abi/NautilusToken.json',
  JSON.stringify({abi: art.abi}, null, 2)
);
console.log('ABI copied');
"
```

**Step 7: Commit**

```bash
git add phase3/contracts/scripts/deploy_nau.js phase3/backend/blockchain/abi/NautilusToken.json
git commit -m "feat: deploy NautilusToken to Base Sepolia + copy ABI"
```

---

## Task 3: 更新 web3_config.py 加载 NAU 合约

**Files:**
- Modify: `phase3/backend/blockchain/web3_config.py`

**Step 1: 在 web3_config.py 顶部加环境变量读取**

在 `IDENTITY_CONTRACT_ADDRESS = ...` 那行之后添加：

```python
# NAU Token contract
NAU_TOKEN_ADDRESS = os.getenv("NAU_TOKEN_ADDRESS", "")
```

**Step 2: 在 Web3Config.__init__ 中加载 NAU 合约**

在 `self.usdt_contract = ...` 那行之后添加：

```python
# NAU token contract (platform token)
self.nau_contract = self._load_contract("NautilusToken", NAU_TOKEN_ADDRESS) if NAU_TOKEN_ADDRESS else None
if self.nau_contract:
    logger.info(f"NAU token contract loaded at {NAU_TOKEN_ADDRESS}")
else:
    logger.warning("NAU_TOKEN_ADDRESS not set — token minting disabled")
```

**Step 3: 验证加载正常**

```bash
cd phase3/backend
python -c "
import os
os.environ['NAU_TOKEN_ADDRESS'] = '0x0000000000000000000000000000000000000001'
from blockchain.web3_config import get_web3_config
cfg = get_web3_config()
print('nau_contract:', cfg.nau_contract)
"
```

期望：无报错（合约地址无效会返回 None，这是预期行为）

**Step 4: Commit**

```bash
git add phase3/backend/blockchain/web3_config.py
git commit -m "feat: load NAU token contract in web3_config"
```

---

## Task 4: 编写 NautilusTokenService（TDD）

**Files:**
- Create: `phase3/backend/services/nautilus_token.py`
- Create: `phase3/backend/tests/test_nautilus_token.py`

**Step 1: 先写测试**

```python
# phase3/backend/tests/test_nautilus_token.py
"""Tests for NautilusTokenService."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock


def test_reward_table_covers_all_task_types():
    """Every AcademicTaskType should have a reward entry."""
    from services.nautilus_token import TASK_TYPE_REWARDS
    known_types = [
        "physics_simulation", "pde_simulation", "ode_simulation",
        "ml_training", "monte_carlo", "jc_constitutive", "thmc_coupling",
        "curve_fitting", "statistical_analysis", "data_visualization",
        "general_computation",
    ]
    for t in known_types:
        assert t in TASK_TYPE_REWARDS, f"Missing reward for {t}"
        assert TASK_TYPE_REWARDS[t] > 0


def test_reward_amounts_are_tiered():
    """High-complexity tasks should earn more than low-complexity."""
    from services.nautilus_token import TASK_TYPE_REWARDS
    assert TASK_TYPE_REWARDS["physics_simulation"] > TASK_TYPE_REWARDS["curve_fitting"]
    assert TASK_TYPE_REWARDS["curve_fitting"] > TASK_TYPE_REWARDS["general_computation"]


@pytest.mark.asyncio
async def test_mint_returns_none_when_no_nau_contract():
    """mint_task_reward returns None silently when NAU contract not loaded."""
    with patch("services.nautilus_token.get_web3_config") as mock_cfg:
        mock_cfg.return_value.nau_contract = None
        from services.nautilus_token import NautilusTokenService
        result = await NautilusTokenService.mint_task_reward(
            agent_wallet="0xabc", task_type="general_computation"
        )
        assert result is None


@pytest.mark.asyncio
async def test_mint_returns_none_when_no_wallet():
    """mint_task_reward returns None when agent_wallet is empty."""
    from services.nautilus_token import NautilusTokenService
    result = await NautilusTokenService.mint_task_reward(
        agent_wallet="", task_type="general_computation"
    )
    assert result is None


@pytest.mark.asyncio
async def test_mint_calls_mint_for_task_with_correct_amount():
    """mint_task_reward calls mintForTask with correct NAU amount in wei."""
    mock_contract = MagicMock()
    mock_fn = MagicMock()
    mock_contract.functions.mintForTask.return_value = mock_fn
    mock_fn.build_transaction.return_value = {"to": "0x...", "data": "0x..."}

    mock_cfg = MagicMock()
    mock_cfg.nau_contract = mock_contract
    mock_cfg.chain_id = 84532
    mock_cfg.get_account_address.return_value = "0xowner"
    mock_w3 = MagicMock()
    mock_w3.eth.get_transaction_count.return_value = 0
    mock_w3.eth.account.sign_transaction.return_value = MagicMock(raw_transaction=b"tx")
    mock_w3.eth.send_raw_transaction.return_value = bytes.fromhex("abcd1234")

    with patch("services.nautilus_token.get_web3_config", return_value=mock_cfg), \
         patch("services.nautilus_token.get_w3", return_value=mock_w3), \
         patch("services.nautilus_token.BLOCKCHAIN_PRIVATE_KEY", "0xdeadbeef"):

        from importlib import reload
        import services.nautilus_token as snt
        reload(snt)

        result = await snt.NautilusTokenService.mint_task_reward(
            agent_wallet="0x1234567890abcdef1234567890abcdef12345678",
            task_type="physics_simulation",
        )
        # physics_simulation = 10 NAU = 10 * 1e18 wei
        call_args = mock_contract.functions.mintForTask.call_args
        _, amount, _ = call_args[0]
        assert amount == 10 * 10**18
        assert result == "abcd1234"
```

**Step 2: 运行测试确认失败**

```bash
cd phase3/backend
pytest tests/test_nautilus_token.py -v
```

期望：`ImportError` 或 `ModuleNotFoundError`（服务还不存在）

**Step 3: 实现 NautilusTokenService**

```python
# phase3/backend/services/nautilus_token.py
"""
NautilusToken (NAU) mint service.

Proof of Useful Work: agents earn NAU by completing real computational tasks.
Mint is non-blocking — failures are logged but never raise exceptions to callers.
"""
import logging
from typing import Optional

from blockchain.web3_config import get_web3_config, get_w3, BLOCKCHAIN_PRIVATE_KEY
from web3 import Web3

logger = logging.getLogger(__name__)

# NAU reward per task type (in whole NAU units, converted to wei on send)
TASK_TYPE_REWARDS: dict[str, int] = {
    "physics_simulation": 10,
    "pde_simulation": 10,
    "ode_simulation": 5,
    "ml_training": 5,
    "monte_carlo": 5,
    "jc_constitutive": 5,
    "thmc_coupling": 5,
    "curve_fitting": 3,
    "statistical_analysis": 3,
    "data_visualization": 1,
    "general_computation": 1,
}

_NAU_DECIMALS = 18


class NautilusTokenService:
    """Handles NAU token minting for Proof of Useful Work rewards."""

    @staticmethod
    async def mint_task_reward(
        agent_wallet: str,
        task_type: str,
    ) -> Optional[str]:
        """
        Mint NAU to agent wallet on task completion.

        Returns tx_hash hex string on success, None on any failure.
        Never raises — callers should not depend on this succeeding.
        """
        if not agent_wallet:
            return None

        cfg = get_web3_config()
        if not cfg.nau_contract:
            logger.debug("NAU contract not loaded, skipping mint")
            return None

        if not BLOCKCHAIN_PRIVATE_KEY:
            logger.debug("BLOCKCHAIN_PRIVATE_KEY not set, skipping mint")
            return None

        nau_amount = TASK_TYPE_REWARDS.get(task_type, 1)
        amount_wei = nau_amount * (10 ** _NAU_DECIMALS)

        try:
            w3 = get_w3()
            account = cfg.get_account_address()
            if not account:
                logger.warning("Cannot derive account address from private key")
                return None

            checksum_wallet = Web3.to_checksum_address(agent_wallet)
            nonce = w3.eth.get_transaction_count(account)

            tx = cfg.nau_contract.functions.mintForTask(
                checksum_wallet,
                amount_wei,
                task_type,
            ).build_transaction({
                "from": account,
                "nonce": nonce,
                "chainId": cfg.chain_id,
            })

            signed = w3.eth.account.sign_transaction(tx, BLOCKCHAIN_PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            tx_hash_hex = tx_hash.hex()

            logger.info(
                "Minted %d NAU to %s for %s task, tx: %s",
                nau_amount, agent_wallet, task_type, tx_hash_hex,
            )
            return tx_hash_hex

        except Exception as e:
            logger.warning("NAU mint failed for %s (%s): %s", agent_wallet, task_type, e)
            return None
```

**Step 4: 运行测试确认通过**

```bash
cd phase3/backend
pytest tests/test_nautilus_token.py -v
```

期望：所有测试 PASS

**Step 5: Commit**

```bash
git add phase3/backend/services/nautilus_token.py phase3/backend/tests/test_nautilus_token.py
git commit -m "feat: NautilusTokenService — PoUW mint on task completion"
```

---

## Task 5: DB Migration — academic_tasks 加 blockchain 字段

**Files:**
- Modify: `phase3/backend/models/database.py`（AcademicTask 类）
- Create: `phase3/backend/alembic/versions/add_nau_token_fields.py`

**Step 1: 更新 AcademicTask model**

在 `phase3/backend/models/database.py` 的 `AcademicTask` 类中，`updated_at` 字段之后添加：

```python
# NAU token reward (PoUW)
blockchain_tx_hash = Column(String(66), nullable=True)   # mint tx hash
token_reward = Column(Float, nullable=True)               # NAU amount minted
```

**Step 2: 生成 Alembic migration**

```bash
cd phase3/backend
alembic revision --autogenerate -m "add_nau_token_fields_to_academic_tasks"
```

检查生成的文件（在 `alembic/versions/` 下），确认 `upgrade()` 包含：
```python
op.add_column('academic_tasks', sa.Column('blockchain_tx_hash', sa.String(66), nullable=True))
op.add_column('academic_tasks', sa.Column('token_reward', sa.Float(), nullable=True))
```

**Step 3: 运行 migration**

```bash
alembic upgrade head
```

期望输出：`Running upgrade ... -> <new_revision>`

**Step 4: 验证**

```bash
python -c "
from utils.database import get_db_context
from models.database import AcademicTask
with get_db_context() as db:
    cols = [c.name for c in AcademicTask.__table__.columns]
    assert 'blockchain_tx_hash' in cols
    assert 'token_reward' in cols
    print('OK:', cols[-4:])
"
```

**Step 5: Commit**

```bash
git add phase3/backend/models/database.py phase3/backend/alembic/versions/add_nau_token_fields*.py
git commit -m "feat: add blockchain_tx_hash + token_reward to academic_tasks"
```

---

## Task 6: 集成 mint 调用到 academic_tasks.py

**Files:**
- Modify: `phase3/backend/api/academic_tasks.py`

**找到集成点**：在文件约 706 行，`logger.warning("Survival score update failed: %s", surv_err)` 之后，紧接着加 mint 调用。

**Step 1: 在 survival score 更新块之后插入**

在 `except Exception as surv_err:` 块结束后（约第 707 行），`# Fire background auditor...` 注释之前，插入：

```python
            # Mint NAU token reward (Proof of Useful Work) — non-blocking
            if _task_succeeded and _agent_id_to_credit:
                try:
                    from services.nautilus_token import NautilusTokenService
                    from models.database import Agent as AgentModel
                    with get_db_context() as tdb:
                        agent_row = tdb.query(AgentModel).filter(
                            AgentModel.agent_id == _agent_id_to_credit
                        ).first()
                        agent_wallet = agent_row.owner if agent_row else None
                    if agent_wallet:
                        tx_hash = await NautilusTokenService.mint_task_reward(
                            agent_wallet=agent_wallet,
                            task_type=row.task_type or "general_computation",
                        )
                        if tx_hash:
                            with get_db_context() as tdb:
                                task_row = tdb.query(AcademicTaskModel).filter(
                                    AcademicTaskModel.task_id == task_id
                                ).first()
                                if task_row:
                                    from services.nautilus_token import TASK_TYPE_REWARDS
                                    task_row.blockchain_tx_hash = tx_hash
                                    task_row.token_reward = float(
                                        TASK_TYPE_REWARDS.get(row.task_type or "", 1)
                                    )
                                    tdb.commit()
                except Exception as mint_err:
                    logger.warning("NAU mint failed (non-blocking): %s", mint_err)
```

**Step 2: 验证 import 不报错**

```bash
cd phase3/backend
python -c "from api.academic_tasks import router; print('OK')"
```

期望：`OK`

**Step 3: Commit**

```bash
git add phase3/backend/api/academic_tasks.py
git commit -m "feat: mint NAU token on academic task completion"
```

---

## Task 7: 端到端验证

> 此 Task 需要服务器已部署合约地址、已配置 `.env`。

**Step 1: 本地快速验证（不上链）**

```bash
cd phase3/backend
python -c "
import asyncio
from services.nautilus_token import NautilusTokenService, TASK_TYPE_REWARDS
# 无 NAU_TOKEN_ADDRESS 时应返回 None 不报错
result = asyncio.run(NautilusTokenService.mint_task_reward('0x1234', 'physics_simulation'))
print('No contract result:', result)  # Expected: None
print('Reward table OK:', TASK_TYPE_REWARDS['physics_simulation'])  # Expected: 10
"
```

**Step 2: 提交一个 academic task 并确认 tx_hash 写入**

```bash
# 启动后端（确保 NAU_TOKEN_ADDRESS + BLOCKCHAIN_PRIVATE_KEY 已配置）
cd phase3/backend && uvicorn main:app --reload

# 提交任务（另一个终端）
curl -X POST http://localhost:8000/api/academic-tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "NAU Token Test",
    "description": "Simple computation to test NAU minting",
    "task_type": "general_computation",
    "input_data": "x = [1,2,3]",
    "parameters": {"operation": "sum"}
  }'
```

记录返回的 `task_id`。

**Step 3: 等任务完成后查 blockchain_tx_hash**

```bash
curl http://localhost:8000/api/academic-tasks/<task_id>
```

确认响应中 `blockchain_tx_hash` 有值（非 null）。

**Step 4: Basescan 验证**

打开 `https://sepolia.basescan.org/tx/0x<blockchain_tx_hash>`，确认：
- Transaction 状态 = Success
- Method = `mintForTask`
- To = NAU 合约地址
- From = 平台服务器钱包

打开 `https://sepolia.basescan.org/address/<agent_wallet>#tokentxns`，确认：
- NAU token 余额 > 0
- 有 mint 交易记录

**Step 5: 最终 commit**

```bash
git add -A
git commit -m "feat: NAU PoUW token — full Web3 loop verified on Base Sepolia"
```

---

## 快速检查清单

完成后确认以下均满足：

- [ ] `NautilusToken.sol` 编译通过
- [ ] 合约已部署，Basescan 可查
- [ ] ABI 已复制到 `backend/blockchain/abi/NautilusToken.json`
- [ ] `NAU_TOKEN_ADDRESS` + `BLOCKCHAIN_PRIVATE_KEY` 已配置
- [ ] `pytest tests/test_nautilus_token.py` 全部通过
- [ ] DB migration 已运行，`academic_tasks` 表有新字段
- [ ] 一个 task 完成后 `blockchain_tx_hash` 有值
- [ ] Basescan 确认 mint 交易成功，agent 钱包收到 NAU
