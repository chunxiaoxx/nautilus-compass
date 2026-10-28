import { useState, useEffect } from 'react';
import { web3Provider } from '../provider';

/**
 * Hook for monitoring gas prices
 */
export function useGasPrice() {
  const [gasPrice, setGasPrice] = useState<bigint | null>(null);
  const [maxFeePerGas, setMaxFeePerGas] = useState<bigint | null>(null);
  const [maxPriorityFeePerGas, setMaxPriorityFeePerGas] = useState<bigint | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetch current gas prices
   */
  const fetchGasPrice = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const feeData = await web3Provider.getFeeData();

      setGasPrice(feeData.gasPrice);
      setMaxFeePerGas(feeData.maxFeePerGas);
      setMaxPriorityFeePerGas(feeData.maxPriorityFeePerGas);
      setIsLoading(false);
    } catch (err) {
      setError((err as Error).message);
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchGasPrice();

    // Refresh gas price every 15 seconds
    const interval = setInterval(fetchGasPrice, 15000);

    return () => clearInterval(interval);
  }, []);

  return {
    gasPrice,
    maxFeePerGas,
    maxPriorityFeePerGas,
    isLoading,
    error,
    refresh: fetchGasPrice,
  };
}

/**
 * Hook for monitoring block number
 */
export function useBlockNumber() {
  const [blockNumber, setBlockNumber] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetch current block number
   */
  const fetchBlockNumber = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const block = await web3Provider.getBlockNumber();
      setBlockNumber(block);
      setIsLoading(false);
    } catch (err) {
      setError((err as Error).message);
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchBlockNumber();

    // Refresh block number every 12 seconds (average block time)
    const interval = setInterval(fetchBlockNumber, 12000);

    return () => clearInterval(interval);
  }, []);

  return {
    blockNumber,
    isLoading,
    error,
    refresh: fetchBlockNumber,
  };
}

/**
 * Hook for monitoring network status
 */
export function useNetwork() {
  const [network, setNetwork] = useState<{
    name: string;
    chainId: bigint;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetch network information
   */
  const fetchNetwork = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const networkInfo = await web3Provider.getNetwork();
      setNetwork({
        name: networkInfo.name,
        chainId: networkInfo.chainId,
      });
      setIsLoading(false);
    } catch (err) {
      setError((err as Error).message);
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchNetwork();
  }, []);

  return {
    network,
    isLoading,
    error,
    refresh: fetchNetwork,
  };
}
