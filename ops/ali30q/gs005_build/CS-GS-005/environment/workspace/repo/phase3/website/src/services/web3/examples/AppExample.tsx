import { Web3Provider } from '../context';
import { WalletConnectButton } from '../components/WalletConnectButton';
import { CreateTaskForm } from '../components/CreateTaskForm';
import { TaskList } from '../components/TaskList';
import { RewardDashboard } from '../components/RewardDashboard';

/**
 * Example App Integration
 *
 * This demonstrates how to integrate the Web3 services into your application.
 */
function App() {
  return (
    <Web3Provider>
      <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
        <header style={{ marginBottom: '40px' }}>
          <h1>Nautilus - Web3 Task Platform</h1>
          <WalletConnectButton />
        </header>

        <main>
          <section style={{ marginBottom: '40px' }}>
            <h2>Create New Task</h2>
            <CreateTaskForm />
          </section>

          <section style={{ marginBottom: '40px' }}>
            <TaskList />
          </section>

          <section>
            <RewardDashboard />
          </section>
        </main>
      </div>
    </Web3Provider>
  );
}

export default App;
