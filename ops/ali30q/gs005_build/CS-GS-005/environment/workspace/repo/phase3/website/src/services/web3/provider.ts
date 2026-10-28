import { ethers } from 'ethers';
import type { NetworkConfig } from './types';

// Network configurations
export const NETWORKS: Record<string, NetworkConfig> = {
  'base-sepolia': {
    chainId: 84532,
    chainName: 'Base Sepolia',
    nativeCurrency: {
      name: 'Ethereum',
      symbol: 'ETH',
      decimals: 18,
    },
    rpcUrls: [
      'https://sepolia.base.org',
      'https://base-sepolia-rpc.publicnode.com',
    ],
    blockExplorerUrls: ['https://sepolia.basescan.org'],
  },
  'base-mainnet': {
    chainId: 8453,
    chainName: 'Base',
    nativeCurrency: {
      name: 'Ethereum',
      symbol: 'ETH',
      decimals: 18,
    },
    rpcUrls: [
      'https://mainnet.base.org',
      'https://base-rpc.publicnode.com',
    ],
    blockExplorerUrls: ['https://basescan.org'],
  },
};

// Default network
export const DEFAULT_NETWORK = 'base-sepolia';

class Web3Provider {
  private provider: ethers.BrowserProvider | null = null;
  private signer: ethers.Signer | null = null;
  private currentNetwork: string = DEFAULT_NETWORK;

  /**
   * Initialize provider with MetaMask or other injected wallet
   */
  async initializeProvider(): Promise<ethers.BrowserProvider> {
    if (typeof window === 'undefined' || !window.ethereum) {
      throw new Error('No Web3 provider found. Please install MetaMask.');
    }

    try {
      this.provider = new ethers.BrowserProvider(window.ethereum);
      return this.provider;
    } catch (error) {
      throw new Error(`Failed to initialize provider: ${(error as Error).message}`);
    }
  }

  /**
   * Get current provider instance
   */
  getProvider(): ethers.BrowserProvider {
    if (!this.provider) {
      throw new Error('Provider not initialized. Call initializeProvider() first.');
    }
    return this.provider;
  }

  /**
   * Get signer for transactions
   */
  async getSigner(): Promise<ethers.Signer> {
    const provider = this.getProvider();

    try {
      this.signer = await provider.getSigner();
      return this.signer;
    } catch (error) {
      throw new Error(`Failed to get signer: ${(error as Error).message}`);
    }
  }

  /**
   * Get current signer instance
   */
  getCurrentSigner(): ethers.Signer | null {
    return this.signer;
  }

  /**
   * Get network configuration
   */
  getNetworkConfig(network?: string): NetworkConfig {
    const networkKey = network || this.currentNetwork;
    const config = NETWORKS[networkKey];

    if (!config) {
      throw new Error(`Network configuration not found for: ${networkKey}`);
    }

    return config;
  }

  /**
   * Set current network
   */
  setCurrentNetwork(network: string): void {
    if (!NETWORKS[network]) {
      throw new Error(`Invalid network: ${network}`);
    }
    this.currentNetwork = network;
  }

  /**
   * Get current network
   */
  getCurrentNetwork(): string {
    return this.currentNetwork;
  }

  /**
   * Get network details from provider
   */
  async getNetwork(): Promise<ethers.Network> {
    const provider = this.getProvider();

    try {
      return await provider.getNetwork();
    } catch (error) {
      throw new Error(`Failed to get network: ${(error as Error).message}`);
    }
  }

  /**
   * Get block number
   */
  async getBlockNumber(): Promise<number> {
    const provider = this.getProvider();

    try {
      return await provider.getBlockNumber();
    } catch (error) {
      throw new Error(`Failed to get block number: ${(error as Error).message}`);
    }
  }

  /**
   * Get gas price
   */
  async getGasPrice(): Promise<bigint> {
    const provider = this.getProvider();

    try {
      const feeData = await provider.getFeeData();
      return feeData.gasPrice || 0n;
    } catch (error) {
      throw new Error(`Failed to get gas price: ${(error as Error).message}`);
    }
  }

  /**
   * Get fee data (EIP-1559)
   */
  async getFeeData(): Promise<ethers.FeeData> {
    const provider = this.getProvider();

    try {
      return await provider.getFeeData();
    } catch (error) {
      throw new Error(`Failed to get fee data: ${(error as Error).message}`);
    }
  }

  /**
   * Wait for transaction confirmation
   */
  async waitForTransaction(
    txHash: string,
    confirmations: number = 1
  ): Promise<ethers.TransactionReceipt | null> {
    const provider = this.getProvider();

    try {
      return await provider.waitForTransaction(txHash, confirmations);
    } catch (error) {
      throw new Error(`Failed to wait for transaction: ${(error as Error).message}`);
    }
  }

  /**
   * Reset provider state
   */
  reset(): void {
    this.provider = null;
    this.signer = null;
    this.currentNetwork = DEFAULT_NETWORK;
  }
}

// Singleton instance
export const web3Provider = new Web3Provider();

// Utility functions
export const formatEther = (value: bigint): string => {
  return ethers.formatEther(value);
};

export const parseEther = (value: string): bigint => {
  return ethers.parseEther(value);
};

export const formatUnits = (value: bigint, decimals: number): string => {
  return ethers.formatUnits(value, decimals);
};

export const parseUnits = (value: string, decimals: number): bigint => {
  return ethers.parseUnits(value, decimals);
};

export const isAddress = (address: string): boolean => {
  return ethers.isAddress(address);
};

export const getAddress = (address: string): string => {
  return ethers.getAddress(address);
};
