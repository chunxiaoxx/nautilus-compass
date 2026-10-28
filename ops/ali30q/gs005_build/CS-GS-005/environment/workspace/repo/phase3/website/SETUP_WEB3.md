# Web3 Integration Setup Guide

## Installation

Install the required dependency:

```bash
npm install ethers@^6.13.0
```

## Quick Start

### 1. Wrap your app with Web3Provider

```tsx
// src/main.tsx or src/App.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { Web3Provider } from './services/web3';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Web3Provider>
      <App />
    </Web3Provider>
  </React.StrictMode>
);
```

### 2. Use Web3 hooks in your components

```tsx
import { useWeb3, useContract, useTransaction } from './services/web3';

function MyComponent() {
  const { address, isConnected, connect } = useWeb3();
  const { createTask } = useContract();
  const { executeTransaction } = useTransaction();

  // Your component logic
}
```

## Configuration

### Update Contract Addresses

Before using the contracts, update the addresses in:
`src/services/web3/contracts.ts`

```typescript
export const CONTRACT_ADDRESSES = {
  sepolia: {
    taskContract: '0xYourTaskContractAddress',
    rewardContract: '0xYourRewardContractAddress',
  },
};
```

### Update RPC URLs (Optional)

Add your Infura or Alchemy API keys in:
`src/services/web3/provider.ts`

```typescript
rpcUrls: [
  'https://sepolia.infura.io/v3/YOUR_INFURA_KEY',
  'https://rpc.sepolia.org',
],
```

## File Structure

```
src/services/web3/
├── provider.ts              # Web3 provider configuration
├── wallet.ts                # Wallet connection logic
├── contracts.ts             # Smart contract interactions
├── types.ts                 # TypeScript types
├── utils.ts                 # Utility functions
├── global.d.ts              # Global type declarations
├── index.ts                 # Main exports
├── hooks/
│   ├── useWallet.ts         # Wallet management hook
│   ├── useContract.ts       # Contract interaction hook
│   ├── useTransaction.ts    # Transaction management hook
│   ├── useWeb3Utils.ts      # Utility hooks (gas, block, network)
│   └── index.ts
├── context/
│   ├── Web3Context.tsx      # React context provider
│   └── index.ts
├── components/
│   ├── WalletConnectButton.tsx
│   ├── CreateTaskForm.tsx
│   ├── TaskList.tsx
│   ├── RewardDashboard.tsx
│   └── index.ts
├── examples/
│   ├── AppExample.tsx
│   ├── SubmitTaskExample.tsx
│   ├── NetworkStatusExample.tsx
│   ├── RewardHistoryExample.tsx
│   └── index.ts
└── README.md
```

## Usage Examples

See the `examples/` directory for complete component examples:

- **AppExample.tsx** - Full app integration
- **SubmitTaskExample.tsx** - Task submission form
- **NetworkStatusExample.tsx** - Network status display
- **RewardHistoryExample.tsx** - Reward history list

## Testing

1. Install MetaMask browser extension
2. Switch to Sepolia testnet
3. Get test ETH from Sepolia faucet
4. Update contract addresses
5. Run `npm run dev`
6. Test wallet connection and transactions

## Next Steps

1. Deploy smart contracts to Sepolia testnet
2. Update contract addresses in `contracts.ts`
3. Test all functionality with MetaMask
4. Integrate components into your app
5. Add error handling and loading states
6. Implement event listeners for real-time updates

## Support

For detailed documentation, see:
- `src/services/web3/README.md` - Complete API documentation
- `src/services/web3/examples/` - Working code examples
