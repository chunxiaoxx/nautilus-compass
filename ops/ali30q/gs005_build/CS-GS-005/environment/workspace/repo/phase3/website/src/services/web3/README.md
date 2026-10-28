# Web3 Integration

Complete Web3 blockchain integration for Nautilus website using Ethers.js 6.x.

## Installation

```bash
npm install ethers@^6.0.0
```

## Structure

```
src/services/web3/
├── provider.ts          # Web3 Provider configuration
├── wallet.ts            # Wallet connection and management
├── contracts.ts         # Smart contract interactions
├── types.ts             # TypeScript type definitions
├── global.d.ts          # Global type declarations
├── hooks/
│   ├── useWallet.ts     # Wallet hook
│   ├── useContract.ts   # Contract interaction hook
│   ├── useTransaction.ts # Transaction management hook
│   └── index.ts         # Hooks exports
└── index.ts             # Main exports
```

## Features

### Provider (provider.ts)
- Ethers.js 6.x provider initialization
- Network configuration (Sepolia testnet, Mainnet)
- Provider management and utilities
- Gas price and fee data retrieval
- Transaction confirmation tracking

### Wallet (wallet.ts)
- MetaMask connection
- WalletConnect support (placeholder)
- Network switching
- Balance retrieval
- Message signing and verification
- Event listeners for account/network changes
- Comprehensive error handling

### Contracts (contracts.ts)
- Task contract interactions
  - Create, submit, approve, reject, cancel tasks
  - Query tasks by creator, worker, or status
- Reward contract interactions
  - Claim, withdraw, deposit rewards
  - Query reward balances and history
- Event listeners for contract events
- Gas estimation for transactions
- Type-safe contract interfaces

### Hooks

#### useWallet
```typescript
const {
  address,
  chainId,
  balance,
  isConnecting,
  isConnected,
  error,
  connect,
  disconnect,
  switchNetwork,
  refreshBalance,
  signMessage,
} = useWallet();
```

#### useContract
```typescript
const {
  isLoading,
  error,
  createTask,
  submitTask,
  approveTask,
  getTask,
  getActiveTasks,
  claimReward,
  getRewardBalance,
  withdrawRewards,
  estimateCreateTaskGas,
} = useContract('sepolia');
```

#### useTransaction
```typescript
const {
  hash,
  status,
  error,
  executeTransaction,
  waitForTransaction,
  reset,
  getReceipt,
} = useTransaction();
```

## Usage Examples

### Connect Wallet
```typescript
import { useWallet, WalletProvider } from '@/services/web3';

function WalletButton() {
  const { isConnected, address, connect, disconnect } = useWallet();

  const handleConnect = async () => {
    try {
      await connect(WalletProvider.METAMASK);
    } catch (error) {
      console.error('Failed to connect:', error);
    }
  };

  return (
    <button onClick={isConnected ? disconnect : handleConnect}>
      {isConnected ? `${address?.slice(0, 6)}...${address?.slice(-4)}` : 'Connect Wallet'}
    </button>
  );
}
```

### Create Task
```typescript
import { useContract, useTransaction } from '@/services/web3';

function CreateTaskForm() {
  const { createTask, estimateCreateTaskGas } = useContract();
  const { executeTransaction, status } = useTransaction();

  const handleSubmit = async (title: string, description: string, reward: string) => {
    try {
      // Estimate gas first
      const gasEstimate = await estimateCreateTaskGas(title, description, reward);
      console.log('Estimated gas:', gasEstimate.toString());

      // Execute transaction
      const receipt = await executeTransaction(() =>
        createTask(title, description, reward)
      );

      if (receipt) {
        console.log('Task created:', receipt.hash);
      }
    } catch (error) {
      console.error('Failed to create task:', error);
    }
  };

  return (
    <form onSubmit={(e) => {
      e.preventDefault();
      const formData = new FormData(e.currentTarget);
      handleSubmit(
        formData.get('title') as string,
        formData.get('description') as string,
        formData.get('reward') as string
      );
    }}>
      <input name="title" placeholder="Task title" required />
      <textarea name="description" placeholder="Description" required />
      <input name="reward" type="number" step="0.01" placeholder="Reward (ETH)" required />
      <button type="submit" disabled={status === 'pending'}>
        {status === 'pending' ? 'Creating...' : 'Create Task'}
      </button>
    </form>
  );
}
```

### Get Active Tasks
```typescript
import { useContract } from '@/services/web3';
import { useEffect, useState } from 'react';

function TaskList() {
  const { getActiveTasks, getTask } = useContract();
  const [tasks, setTasks] = useState([]);

  useEffect(() => {
    const loadTasks = async () => {
      const taskIds = await getActiveTasks();
      const taskDetails = await Promise.all(
        taskIds.map(id => getTask(Number(id)))
      );
      setTasks(taskDetails.filter(Boolean));
    };

    loadTasks();
  }, []);

  return (
    <div>
      {tasks.map(task => (
        <div key={task.id.toString()}>
          <h3>{task.title}</h3>
          <p>{task.description}</p>
          <p>Reward: {ethers.formatEther(task.reward)} ETH</p>
        </div>
      ))}
    </div>
  );
}
```

### Claim Reward
```typescript
import { useContract, useTransaction } from '@/services/web3';

function ClaimRewardButton({ taskId }: { taskId: number }) {
  const { claimReward } = useContract();
  const { executeTransaction, status } = useTransaction();

  const handleClaim = async () => {
    try {
      const receipt = await executeTransaction(() => claimReward(taskId));
      if (receipt) {
        console.log('Reward claimed:', receipt.hash);
      }
    } catch (error) {
      console.error('Failed to claim reward:', error);
    }
  };

  return (
    <button onClick={handleClaim} disabled={status === 'pending'}>
      {status === 'pending' ? 'Claiming...' : 'Claim Reward'}
    </button>
  );
}
```

## Configuration

### Update Contract Addresses

Edit `contracts.ts` and replace placeholder addresses:

```typescript
export const CONTRACT_ADDRESSES = {
  sepolia: {
    taskContract: '0xYourTaskContractAddress',
    rewardContract: '0xYourRewardContractAddress',
  },
  mainnet: {
    taskContract: '0xYourTaskContractAddress',
    rewardContract: '0xYourRewardContractAddress',
  },
};
```

### Update RPC URLs

Edit `provider.ts` and add your Infura/Alchemy keys:

```typescript
export const NETWORKS: Record<string, NetworkConfig> = {
  sepolia: {
    rpcUrls: [
      'https://sepolia.infura.io/v3/YOUR_INFURA_KEY',
      'https://rpc.sepolia.org',
    ],
    // ...
  },
};
```

## Error Handling

All functions include comprehensive error handling:

- User rejection errors (code 4001)
- Insufficient funds errors
- Gas estimation failures
- Network errors
- Transaction revert errors

Errors are parsed and returned with user-friendly messages.

## Security Considerations

1. **Never hardcode private keys** - Always use wallet providers
2. **Validate all inputs** - Check addresses, amounts, and parameters
3. **Estimate gas before transactions** - Prevent failed transactions
4. **Handle errors gracefully** - Provide clear feedback to users
5. **Use testnet first** - Test thoroughly on Sepolia before mainnet

## TypeScript Support

Full TypeScript support with:
- Strict type checking
- Interface definitions for all data structures
- Type-safe contract interactions
- Autocomplete for all functions

## Testing

Before deploying:

1. Test wallet connection on Sepolia testnet
2. Test all contract interactions with test ETH
3. Verify gas estimation accuracy
4. Test error handling scenarios
5. Test network switching functionality

## Next Steps

1. Deploy smart contracts to Sepolia testnet
2. Update contract addresses in `contracts.ts`
3. Add your RPC provider keys in `provider.ts`
4. Test all functionality with MetaMask
5. Implement WalletConnect support (optional)
6. Add transaction history persistence (optional)
7. Implement event listeners for real-time updates (optional)
