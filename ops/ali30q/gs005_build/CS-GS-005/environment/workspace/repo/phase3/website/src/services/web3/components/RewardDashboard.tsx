import { useEffect, useState } from 'react';
import { useContract } from '../hooks/useContract';
import { useWeb3 } from '../context';
import { useTransaction } from '../hooks/useTransaction';

/**
 * Example: Reward Dashboard Component
 */
export function RewardDashboard() {
  const [balance, setBalance] = useState('0');
  const [pendingRewards, setPendingRewards] = useState('0');
  const [totalPaid, setTotalPaid] = useState('0');

  const { address } = useWeb3();
  const { getRewardBalance, getPendingRewards, getTotalRewardsPaid, withdrawRewards } = useContract();
  const { executeTransaction, status } = useTransaction();

  useEffect(() => {
    if (address) {
      loadRewardData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [address]);

  const loadRewardData = async () => {
    if (!address) return;

    try {
      const [balanceData, pendingData, totalData] = await Promise.all([
        getRewardBalance(address),
        getPendingRewards(address),
        getTotalRewardsPaid(),
      ]);

      setBalance(balanceData);
      setPendingRewards(pendingData);
      setTotalPaid(totalData);
    } catch (error) {
      console.error('Failed to load reward data:', error);
    }
  };

  const handleWithdraw = async () => {
    try {
      const receipt = await executeTransaction(async () => {
        return await withdrawRewards();
      });
      if (receipt) {
        alert('Rewards withdrawn successfully!');
        loadRewardData();
      }
    } catch (error) {
      console.error('Failed to withdraw rewards:', error);
    }
  };

  if (!address) {
    return <div>Please connect your wallet to view rewards.</div>;
  }

  return (
    <div>
      <h2>Reward Dashboard</h2>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '24px' }}>
        <div style={{ border: '1px solid #ccc', padding: '16px' }}>
          <h3>Available Balance</h3>
          <p style={{ fontSize: '24px', fontWeight: 'bold' }}>{parseFloat(balance).toFixed(4)} ETH</p>
        </div>

        <div style={{ border: '1px solid #ccc', padding: '16px' }}>
          <h3>Pending Rewards</h3>
          <p style={{ fontSize: '24px', fontWeight: 'bold' }}>{parseFloat(pendingRewards).toFixed(4)} ETH</p>
        </div>

        <div style={{ border: '1px solid #ccc', padding: '16px' }}>
          <h3>Total Paid</h3>
          <p style={{ fontSize: '24px', fontWeight: 'bold' }}>{parseFloat(totalPaid).toFixed(4)} ETH</p>
        </div>
      </div>

      <button
        onClick={handleWithdraw}
        disabled={status === 'pending' || parseFloat(balance) === 0}
      >
        {status === 'pending' ? 'Withdrawing...' : 'Withdraw Rewards'}
      </button>

      <button onClick={loadRewardData} style={{ marginLeft: '8px' }}>
        Refresh
      </button>
    </div>
  );
}
