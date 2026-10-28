// Web3 Types
export interface NetworkConfig {
  chainId: number;
  chainName: string;
  nativeCurrency: {
    name: string;
    symbol: string;
    decimals: number;
  };
  rpcUrls: string[];
  blockExplorerUrls: string[];
}

export interface WalletState {
  address: string | null;
  chainId: number | null;
  balance: string | null;
  isConnecting: boolean;
  isConnected: boolean;
  error: string | null;
}

export interface TransactionState {
  hash: string | null;
  status: 'idle' | 'pending' | 'success' | 'error';
  error: string | null;
}

export interface ContractConfig {
  address: string;
  abi: any[];
}

export enum WalletProvider {
  METAMASK = 'metamask',
  WALLETCONNECT = 'walletconnect',
}

export interface Web3Error {
  code: number;
  message: string;
  data?: any;
}
