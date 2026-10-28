import { useState } from 'react';
import { useContract } from '../hooks/useContract';
import { useTransaction } from '../hooks/useTransaction';

/**
 * Example: Create Task Form Component
 */
export function CreateTaskForm() {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [reward, setReward] = useState('');

  const { createTask, estimateCreateTaskGas } = useContract();
  const { executeTransaction, status, hash, error } = useTransaction();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!title || !description || !reward) {
      alert('Please fill in all fields');
      return;
    }

    try {
      // Estimate gas first
      const gasEstimate = await estimateCreateTaskGas(title, description, reward);
      console.log('Estimated gas:', String(gasEstimate));

      // Execute transaction
      const receipt = await executeTransaction(async () => {
        return await createTask(title, description, reward);
      });

      if (receipt) {
        alert(`Task created successfully! Transaction: ${receipt.hash}`);
        // Reset form
        setTitle('');
        setDescription('');
        setReward('');
      }
    } catch (error) {
      console.error('Failed to create task:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="title">Task Title</label>
        <input
          id="title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Enter task title"
          required
        />
      </div>

      <div>
        <label htmlFor="description">Description</label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Enter task description"
          rows={4}
          required
        />
      </div>

      <div>
        <label htmlFor="reward">Reward (ETH)</label>
        <input
          id="reward"
          type="number"
          step="0.01"
          min="0"
          value={reward}
          onChange={(e) => setReward(e.target.value)}
          placeholder="0.1"
          required
        />
      </div>

      <button type="submit" disabled={status === 'pending'}>
        {status === 'pending' ? 'Creating Task...' : 'Create Task'}
      </button>

      {status === 'pending' && hash && (
        <p>Transaction submitted: {hash.slice(0, 10)}...</p>
      )}

      {status === 'success' && <p style={{ color: 'green' }}>Task created successfully!</p>}

      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
    </form>
  );
}
