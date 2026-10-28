import { useGasPrice, useBlockNumber, useNetwork } from '../hooks';
import { weiToGwei } from '../utils';

/**
 * Example: Network Status Component
 */
export function NetworkStatus() {
  const { gasPrice, maxFeePerGas, maxPriorityFeePerGas, isLoading: gasLoading } = useGasPrice();
  const { blockNumber, isLoading: blockLoading } = useBlockNumber();
  const { network, isLoading: networkLoading } = useNetwork();

  if (gasLoading || blockLoading || networkLoading) {
    return <div>Loading network status...</div>;
  }

  return (
    <div style={{ border: '1px solid #ccc', padding: '16px', borderRadius: '8px' }}>
      <h3>Network Status</h3>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
        <div>
          <strong>Network:</strong> {network?.name || 'Unknown'}
        </div>
        <div>
      <strong>Chain ID:</strong> {network?.chainId ? String(network.chainId) : 'N/A'}
        </div>
      <div>
          <strong>Block Number:</strong> {blockNumber ? Number(blockNumber).toLocaleString() : 'N/A'}
    </div>
      <div>
          <strong>Gas Price:</strong>{' '}
          {gasPrice ? `${weiToGwei(gasPrice)} Gwei` : 'N/A'}
        </div>
        {maxFeePerGas && maxFeePerGas > 0n ? (
          <div>
            <strong>Max Fee:</strong> {weiToGwei(maxFeePerGas)} Gwei
          </div>
        ) : null}
        {maxPriorityFeePerGas && maxPriorityFeePerGas > 0n ? (
          <div>
            <strong>Priority Fee:</strong> {weiToGwei(maxPriorityFeePerGas)} Gwei
        </div>
        ) : null}
      </div>
    </div>
  );
}
