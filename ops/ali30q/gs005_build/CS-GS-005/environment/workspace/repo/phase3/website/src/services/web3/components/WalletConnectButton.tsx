import { useWeb3 } from '../context';
import { WalletProvider } from '../types';

/**
 * Example: Wallet Connect Button Component
 */
export function WalletConnectButton() {
  const { isConnected, isConnecting, address, balance, error, connect, disconnect } = useWeb3();

  const handleConnect = async () => {
    try {
      await connect(WalletProvider.METAMASK);
    } catch (error) {
      console.error('Failed to connect wallet:', error);
    }
  };

  if (isConnecting) {
    return <button disabled>Connecting...</button>;
  }

  if (isConnected && address) {
    return (
      <div>
        <div>
          <span>Address: {address.slice(0, 6)}...{address.slice(-4)}</span>
          <span>Balance: {balance ? parseFloat(balance).toFixed(4) : '0'} ETH</span>
        </div>
        <button onClick={disconnect}>Disconnect</button>
      </div>
    );
  }

  return (
    <div>
      <button onClick={handleConnect}>Connect Wallet</button>
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </div>
  );
}
