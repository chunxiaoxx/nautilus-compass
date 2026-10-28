import { ethers } from 'ethers';

/**
 * Format address to short form
 */
export function formatAddress(address: string, startLength: number = 6, endLength: number = 4): string {
  if (!address) return '';
  return `${address.slice(0, startLength)}...${address.slice(-endLength)}`;
}

/**
 * Format ETH amount with specified decimals
 */
export function formatEthAmount(amount: bigint | string, decimals: number = 4): string {
  const ethAmount = typeof amount === 'string' ? amount : ethers.formatEther(amount);
  return parseFloat(ethAmount).toFixed(decimals);
}

/**
 * Parse ETH amount to wei
 */
export function parseEthAmount(amount: string): bigint {
  try {
    return ethers.parseEther(amount);
  } catch (error) {
    throw new Error('Invalid ETH amount');
  }
}

/**
 * Validate Ethereum address
 */
export function isValidAddress(address: string): boolean {
  return ethers.isAddress(address);
}

/**
 * Get checksum address
 */
export function getChecksumAddress(address: string): string {
  try {
    return ethers.getAddress(address);
  } catch (error) {
    throw new Error('Invalid address');
  }
}

/**
 * Format transaction hash
 */
export function formatTxHash(hash: string, length: number = 10): string {
  if (!hash) return '';
  return `${hash.slice(0, length)}...`;
}

/**
 * Get explorer URL for address
 */
export function getExplorerAddressUrl(address: string, chainId: number): string {
  const explorers: Record<number, string> = {
    1: 'https://etherscan.io/address',
    11155111: 'https://sepolia.etherscan.io/address',
  };

  const baseUrl = explorers[chainId] || explorers[1];
  return `${baseUrl}/${address}`;
}

/**
 * Get explorer URL for transaction
 */
export function getExplorerTxUrl(txHash: string, chainId: number): string {
  const explorers: Record<number, string> = {
    1: 'https://etherscan.io/tx',
    11155111: 'https://sepolia.etherscan.io/tx',
  };

  const baseUrl = explorers[chainId] || explorers[1];
  return `${baseUrl}/${txHash}`;
}

/**
 * Calculate gas cost in ETH
 */
export function calculateGasCost(gasUsed: bigint, gasPrice: bigint): string {
  const cost = gasUsed * gasPrice;
  return ethers.formatEther(cost);
}

/**
 * Format timestamp to readable date
 */
export function formatTimestamp(timestamp: bigint | number): string {
  const date = new Date(Number(timestamp) * 1000);
  return date.toLocaleString();
}

/**
 * Format relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(timestamp: bigint | number): string {
  const now = Date.now();
  const then = Number(timestamp) * 1000;
  const diff = now - then;

  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
  if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
  if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
  return `${seconds} second${seconds > 1 ? 's' : ''} ago`;
}

/**
 * Wait for specified milliseconds
 */
export function wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Retry function with exponential backoff
 */
export async function retry<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> {
  let lastError: Error;

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;
      if (i < maxRetries - 1) {
        await wait(delay * Math.pow(2, i));
      }
    }
  }

  throw lastError!;
}

/**
 * Truncate string to specified length
 */
export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return `${str.slice(0, maxLength)}...`;
}

/**
 * Convert wei to gwei
 */
export function weiToGwei(wei: bigint): string {
  return ethers.formatUnits(wei, 'gwei');
}

/**
 * Convert gwei to wei
 */
export function gweiToWei(gwei: string): bigint {
  return ethers.parseUnits(gwei, 'gwei');
}

/**
 * Check if transaction is pending
 */
export function isTransactionPending(status: string): boolean {
  return status === 'pending';
}

/**
 * Check if transaction is successful
 */
export function isTransactionSuccess(status: string): boolean {
  return status === 'success';
}

/**
 * Check if transaction failed
 */
export function isTransactionFailed(status: string): boolean {
  return status === 'error';
}

/**
 * Get network name from chain ID
 */
export function getNetworkName(chainId: number): string {
  const networks: Record<number, string> = {
    1: 'Ethereum Mainnet',
    11155111: 'Sepolia Testnet',
    5: 'Goerli Testnet',
    137: 'Polygon Mainnet',
    80001: 'Mumbai Testnet',
  };

  return networks[chainId] || `Unknown Network (${chainId})`;
}

/**
 * Check if network is testnet
 */
export function isTestnet(chainId: number): boolean {
  const testnets = [11155111, 5, 80001];
  return testnets.includes(chainId);
}
