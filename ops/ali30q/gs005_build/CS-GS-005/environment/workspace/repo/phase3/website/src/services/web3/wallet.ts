import { ethers } from 'ethers';
import { web3Provider, NETWORKS } from './provider';
import { WalletProvider } from './types';
import type { NetworkConfig, Web3Error } from './types';

// Wallet event listeners
type WalletEventListener = (data: any) => void;

class WalletService {
  private listeners: Map<string, Set<WalletEventListener>> = new Map();

  /**
   * Connect wallet with specified provider
   */
  async connectWallet(provider: WalletProvider = WalletProvider.METAMASK): Promise<string> {
    try {
      if (provider === WalletProvider.METAMASK) {
        return await this.connectMetaMask();
      } else if (provider === WalletProvider.WALLETCONNECT) {
        return await this.connectWalletConnect();
      }

      throw new Error(`Unsupported wallet provider: ${provider}`);
    } catch (error) {
      throw this.handleWalletError(error);
    }
  }

  /**
   * Connect MetaMask wallet
   */
  private async connectMetaMask(): Promise<string> {
    if (typeof window === 'undefined' || !window.ethereum) {
      throw new Error('MetaMask is not installed. Please install MetaMask extension.');
    }

    try {
      // Initialize provider
      await web3Provider.initializeProvider();

      // Request account access
      const accounts = await window.ethereum.request({
        method: 'eth_requestAccounts',
      });

      if (!accounts || accounts.length === 0) {
        throw new Error('No accounts found. Please unlock MetaMask.');
      }

      const address = accounts[0];

      // Setup event listeners
      this.setupMetaMaskListeners();

      return address;
    } catch (error: any) {
      if (error.code === 4001) {
        throw new Error('User rejected the connection request.');
      }
      throw error;
    }
  }

  /**
   * Connect WalletConnect (placeholder for future implementation)
   */
  private async connectWalletConnect(): Promise<string> {
    throw new Error('WalletConnect integration coming soon.');
  }

  /**
   * Disconnect wallet
   */
  async disconnectWallet(): Promise<void> {
    try {
      // Clear listeners
      this.removeAllListeners();

      // Reset provider
      web3Provider.reset();

      // Emit disconnect event
      this.emit('disconnect', null);
    } catch (error) {
      throw this.handleWalletError(error);
    }
  }

  /**
   * Get connected wallet address
   */
  async getAddress(): Promise<string | null> {
    try {
      const signer = await web3Provider.getSigner();
      return await signer.getAddress();
    } catch (error) {
      return null;
    }
  }

  /**
   * Get wallet balance
   */
  async getBalance(address?: string): Promise<string> {
    try {
      const provider = web3Provider.getProvider();
      const targetAddress = address || (await this.getAddress());

      if (!targetAddress) {
        throw new Error('No wallet address available.');
      }

      const balance = await provider.getBalance(targetAddress);
      return ethers.formatEther(balance);
    } catch (error) {
      throw this.handleWalletError(error);
    }
  }

  /**
   * Switch to specified network
   */
  async switchNetwork(networkKey: string): Promise<void> {
    if (!window.ethereum) {
      throw new Error('No Web3 provider found.');
    }

    const network = NETWORKS[networkKey];
    if (!network) {
      throw new Error(`Network configuration not found: ${networkKey}`);
    }

    try {
      // Try to switch to the network
      await window.ethereum.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: `0x${network.chainId.toString(16)}` }],
      });

      web3Provider.setCurrentNetwork(networkKey);
      this.emit('networkChanged', network.chainId);
    } catch (error: any) {
      // Network not added to MetaMask
      if (error.code === 4902) {
        await this.addNetwork(network);
      } else {
        throw this.handleWalletError(error);
      }
    }
  }

  /**
   * Add network to MetaMask
   */
  private async addNetwork(network: NetworkConfig): Promise<void> {
    if (!window.ethereum) {
      throw new Error('No Web3 provider found.');
    }

    try {
      await window.ethereum.request({
        method: 'wallet_addEthereumChain',
        params: [
          {
            chainId: `0x${network.chainId.toString(16)}`,
            chainName: network.chainName,
            nativeCurrency: network.nativeCurrency,
            rpcUrls: network.rpcUrls,
            blockExplorerUrls: network.blockExplorerUrls,
          },
        ],
      });

      this.emit('networkAdded', network.chainId);
    } catch (error) {
      throw this.handleWalletError(error);
    }
  }

  /**
   * Get current chain ID
   */
  async getChainId(): Promise<number> {
    try {
      const network = await web3Provider.getNetwork();
      return Number(network.chainId);
    } catch (error) {
      throw this.handleWalletError(error);
    }
  }

  /**
   * Sign message
   */
  async signMessage(message: string): Promise<string> {
    try {
      const signer = await web3Provider.getSigner();
      return await signer.signMessage(message);
    } catch (error: any) {
      if (error.code === 4001) {
        throw new Error('User rejected the signature request.');
      }
      throw this.handleWalletError(error);
    }
  }

  /**
   * Verify signed message
   */
  verifyMessage(message: string, signature: string): string {
    try {
      return ethers.verifyMessage(message, signature);
    } catch (error) {
      throw new Error(`Failed to verify message: ${(error as Error).message}`);
    }
  }

  /**
   * Check if wallet is connected
   */
  async isConnected(): Promise<boolean> {
    try {
      const address = await this.getAddress();
      return address !== null;
    } catch (error) {
      return false;
    }
  }

  /**
   * Setup MetaMask event listeners
   */
  private setupMetaMaskListeners(): void {
    if (!window.ethereum) return;

    // Account changed
    window.ethereum.on('accountsChanged', (accounts: string[]) => {
      if (accounts.length === 0) {
        this.disconnectWallet();
      } else {
        this.emit('accountsChanged', accounts[0]);
      }
    });

    // Chain changed
    window.ethereum.on('chainChanged', (chainId: string) => {
      const chainIdNumber = parseInt(chainId, 16);
      this.emit('chainChanged', chainIdNumber);
      // Reload page on chain change (recommended by MetaMask)
      window.location.reload();
    });

    // Disconnect
    window.ethereum.on('disconnect', (error: any) => {
      this.emit('disconnect', error);
      this.disconnectWallet();
    });
  }

  /**
   * Add event listener
   */
  on(event: string, listener: WalletEventListener): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(listener);
  }

  /**
   * Remove event listener
   */
  off(event: string, listener: WalletEventListener): void {
    const eventListeners = this.listeners.get(event);
    if (eventListeners) {
      eventListeners.delete(listener);
    }
  }

  /**
   * Emit event
   */
  private emit(event: string, data: any): void {
    const eventListeners = this.listeners.get(event);
    if (eventListeners) {
      eventListeners.forEach((listener) => listener(data));
    }
  }

  /**
   * Remove all listeners
   */
  private removeAllListeners(): void {
    this.listeners.clear();

    if (window.ethereum) {
      window.ethereum.removeAllListeners();
    }
  }

  /**
   * Handle wallet errors
   */
  private handleWalletError(error: any): Error {
    const web3Error = error as Web3Error;

    // User rejected request
    if (web3Error.code === 4001) {
      return new Error('User rejected the request.');
    }

    // Unauthorized
    if (web3Error.code === 4100) {
      return new Error('The requested method is not authorized.');
    }

    // Unsupported method
    if (web3Error.code === 4200) {
      return new Error('The requested method is not supported.');
    }

    // Disconnected
    if (web3Error.code === 4900) {
      return new Error('The provider is disconnected from all chains.');
    }

    // Chain disconnected
    if (web3Error.code === 4901) {
      return new Error('The provider is disconnected from the specified chain.');
    }

    return new Error(web3Error.message || 'An unknown wallet error occurred.');
  }
}

// Singleton instance
export const walletService = new WalletService();

// Export utility functions
export const connectWallet = (provider?: WalletProvider) =>
  walletService.connectWallet(provider);

export const disconnectWallet = () => walletService.disconnectWallet();

export const getAddress = () => walletService.getAddress();

export const getBalance = (address?: string) => walletService.getBalance(address);

export const switchNetwork = (network: string) => walletService.switchNetwork(network);

export const getChainId = () => walletService.getChainId();

export const signMessage = (message: string) => walletService.signMessage(message);

export const verifyMessage = (message: string, signature: string) =>
  walletService.verifyMessage(message, signature);

export const isConnected = () => walletService.isConnected();
