import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { connectWeb3Auth, disconnectWeb3Auth } from '../lib/web3auth';

type WalletProvider = 'metamask' | 'web3auth' | null;

interface WalletState {
  address: string | null;
  balance: string;
  chainId: number | null;
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  provider: WalletProvider;
  idToken: string | null;
  userInfo: Record<string, unknown> | null;
}

interface WalletActions {
  connect: () => Promise<void>;
  connectWithWeb3Auth: () => Promise<void>;
  disconnect: () => void;
  switchChain: (chainId: number) => Promise<void>;
  updateBalance: (balance: string) => void;
  clearError: () => void;
}

type WalletStore = WalletState & WalletActions;

// Chain configurations
const SUPPORTED_CHAINS = {
  1: { name: 'Ethereum Mainnet', rpcUrl: 'https://eth.llamarpc.com' },
  5: { name: 'Goerli Testnet', rpcUrl: 'https://goerli.infura.io/v3/' },
  137: { name: 'Polygon Mainnet', rpcUrl: 'https://polygon-rpc.com' },
  80001: { name: 'Mumbai Testnet', rpcUrl: 'https://rpc-mumbai.maticvigil.com' },
};

// window.ethereum is declared once in src/services/web3/global.d.ts (single source).

export const useWalletStore = create<WalletStore>()(
  persist(
    (set, get) => ({
      // Initial state
      address: null,
      balance: '0',
      chainId: null,
      isConnected: false,
      isConnecting: false,
      error: null,
      provider: null,
      idToken: null,
      userInfo: null,

      // Web3Auth login (Google, GitHub, email → auto wallet)
      connectWithWeb3Auth: async () => {
        set({ isConnecting: true, error: null });
        try {
          const { address, idToken, userInfo } = await connectWeb3Auth();
          set({
            address,
            balance: '0',
            chainId: 84532, // Base Sepolia
            isConnected: true,
            isConnecting: false,
            provider: 'web3auth',
            idToken,
            userInfo,
            error: null,
          });
        } catch (error: any) {
          set({
            isConnecting: false,
            error: error.message || 'Web3Auth connection failed',
          });
          throw error;
        }
      },

      // Actions
      connect: async () => {
        if (!window.ethereum) {
          set({
            error: 'Please install MetaMask or another Web3 wallet',
            isConnecting: false,
          });
          throw new Error('No Web3 wallet detected');
        }

        set({ isConnecting: true, error: null });

        try {
          // Request account access
          const accounts = await window.ethereum.request({
            method: 'eth_requestAccounts',
          });

          if (!accounts || accounts.length === 0) {
            throw new Error('No accounts found');
          }

          const address = accounts[0];

          // Get chain ID
          const chainId = await window.ethereum.request({
            method: 'eth_chainId',
          });

          // Get balance
          const balanceHex = await window.ethereum.request({
            method: 'eth_getBalance',
            params: [address, 'latest'],
          });

          // Convert balance from hex to decimal (wei to ether)
          const balanceWei = parseInt(balanceHex, 16);
          const balanceEth = (balanceWei / 1e18).toFixed(4);

          set({
            address,
            balance: balanceEth,
            chainId: parseInt(chainId, 16),
            isConnected: true,
            isConnecting: false,
            provider: 'metamask',
            idToken: null,
            userInfo: null,
            error: null,
          });

          // Setup event listeners
          window.ethereum.on('accountsChanged', (accounts: string[]) => {
            if (accounts.length === 0) {
              get().disconnect();
            } else {
              set({ address: accounts[0] });
              // Update balance for new account
              get().connect();
            }
          });

          window.ethereum.on('chainChanged', (chainId: string) => {
            set({ chainId: parseInt(chainId, 16) });
            // Reload to avoid state inconsistencies
            window.location.reload();
          });

          window.ethereum.on('disconnect', () => {
            get().disconnect();
          });
        } catch (error: any) {
          const errorMessage = error.message || 'Failed to connect wallet';
          set({
            address: null,
            balance: '0',
            chainId: null,
            isConnected: false,
            isConnecting: false,
            error: errorMessage,
          });
          throw new Error(errorMessage);
        }
      },

      disconnect: () => {
        const { provider } = get();

        if (provider === 'web3auth') {
          disconnectWeb3Auth().catch(() => {});
        }

        // Remove MetaMask event listeners
        if (window.ethereum) {
          window.ethereum.removeAllListeners('accountsChanged');
          window.ethereum.removeAllListeners('chainChanged');
          window.ethereum.removeAllListeners('disconnect');
        }

        set({
          address: null,
          balance: '0',
          chainId: null,
          isConnected: false,
          isConnecting: false,
          provider: null,
          idToken: null,
          userInfo: null,
          error: null,
        });
      },

      switchChain: async (chainId: number) => {
        if (!window.ethereum) {
          throw new Error('No Web3 wallet detected');
        }

        const chainConfig = SUPPORTED_CHAINS[chainId as keyof typeof SUPPORTED_CHAINS];
        if (!chainConfig) {
          throw new Error('Unsupported chain');
        }

        set({ error: null });

        try {
          await window.ethereum.request({
            method: 'wallet_switchEthereumChain',
            params: [{ chainId: `0x${chainId.toString(16)}` }],
          });

          set({ chainId });
        } catch (error: any) {
          // This error code indicates that the chain has not been added to MetaMask
          if (error.code === 4902) {
            try {
              await window.ethereum.request({
                method: 'wallet_addEthereumChain',
                params: [
                  {
                    chainId: `0x${chainId.toString(16)}`,
                    chainName: chainConfig.name,
                    rpcUrls: [chainConfig.rpcUrl],
                  },
                ],
              });

              set({ chainId });
            } catch (addError: any) {
              const errorMessage = addError.message || 'Failed to add chain';
              set({ error: errorMessage });
              throw new Error(errorMessage);
            }
          } else {
            const errorMessage = error.message || 'Failed to switch chain';
            set({ error: errorMessage });
            throw new Error(errorMessage);
          }
        }
      },

      updateBalance: (balance: string) => {
        set({ balance });
      },

      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'wallet-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        address: state.address,
        chainId: state.chainId,
        isConnected: state.isConnected,
        provider: state.provider,
      }),
    }
  )
);
