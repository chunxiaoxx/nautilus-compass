// Web3 Provider
export { web3Provider, NETWORKS, DEFAULT_NETWORK } from './provider';
export { formatEther, parseEther, formatUnits, parseUnits, isAddress, getAddress } from './provider';

// Wallet Service
export { walletService } from './wallet';
export { connectWallet, disconnectWallet, getBalance, switchNetwork, getChainId, signMessage, verifyMessage, isConnected } from './wallet';

// Contract Service
export { contractService, TaskStatus, CONTRACT_ADDRESSES } from './contracts';
export { TASK_CONTRACT_ABI, REWARD_CONTRACT_ABI } from './contracts';
export { createTask, submitTask, approveTask, getTask, getActiveTasks, claimReward, getRewardBalance, withdrawRewards } from './contracts';
export type { Task, RewardHistory } from './contracts';

// Hooks
export { useWallet, useContract, useTransaction, useTransactionHistory } from './hooks';
export { useGasPrice, useBlockNumber, useNetwork } from './hooks';

// Context
export { Web3Provider, useWeb3 } from './context';

// Components
export { WalletConnectButton, RewardDashboard, TaskList, CreateTaskForm } from './components';

// Utils
export * from './utils';

// Types
export type { NetworkConfig, WalletState, TransactionState, ContractConfig, Web3Error } from './types';
export { WalletProvider as WalletProviderEnum } from './types';
