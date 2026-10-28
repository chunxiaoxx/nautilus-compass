// Global type declarations for Web3
declare global {
  interface Window {
    ethereum?: {
      isMetaMask?: boolean;
      isCoinbaseWallet?: boolean;
      request: (args: { method: string; params?: any[] }) => Promise<any>;
      on: (event: string, callback: (...args: any[]) => void) => void;
      removeListener: (event: string, callback: (...args: any[]) => void) => void;
      removeAllListeners: (event?: string) => void;
      // wallet providers inject extra flags/methods (isRabby, providers[], …)
      [key: string]: any;
    };
  }
}

export {};
