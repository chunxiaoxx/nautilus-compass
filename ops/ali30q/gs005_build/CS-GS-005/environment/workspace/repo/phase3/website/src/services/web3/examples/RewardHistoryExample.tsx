import { useEffect, useState } from 'react';
import { useContract } from '../hooks';
import { useWeb3 } from '../context';
import { formatEthAmount, formatRelativeTime } from '../utils';
import type { RewardHistory } from '../contracts';

/**
 * Example: Reward History Component
 */
export function RewardHistoryList() {
  const [history, setHistory] = useState<RewardHistory[]>([]);
  const { address } = useWeb3();
  const { getUserRewardHistory, isLoading } = useContract();

  useEffect(() => {
    if (address) {
      loadHistory();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [address]);

  const loadHistory = async () => {
    if (!address) return;

    try {
      const data = await getUserRewardHistory(address);
      setHistory(data);
    } catch (error) {
      console.error('Failed to load reward history:', error);
    }
  };

  if (!address) {
    return <div>Please connect your wallet to view reward history.</div>;
  }

  if (isLoading) {
    return <div>Loading reward history...</div>;
  }

  if (history.length === 0) {
    return <div>No reward history found.</div>;
  }

  return (
    <div>
      <h3>Reward History</h3>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ borderBottom: '2px solid #ccc' }}>
            <th style={{ padding: '8px', textAlign: 'left' }}>Task ID</th>
            <th style={{ padding: '8px', textAlign: 'left' }}>Amount</th>
            <th style={{ padding: '8px', textAlign: 'left' }}>Time</th>
          </tr>
        </thead>
        <tbody>
          {history.map((item, index) => (
            <tr key={index} style={{ borderBottom: '1px solid #eee' }}>
              <td style={{ padding: '8px' }}>#{String(item.taskId)}</td>
              <td style={{ padding: '8px' }}>{formatEthAmount(item.amount)} ETH</td>
       <td style={{ padding: '8px' }}>{formatRelativeTime(item.timestamp)}</td>
         </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
