import { useState } from 'react';
import { useContract, useTransaction } from '../hooks';
import { useWeb3 } from '../context';

/**
 * Example: Submit Task Component
 */
export function SubmitTaskForm({ taskId }: { taskId: number }) {
  const [submissionUrl, setSubmissionUrl] = useState('');
  const { submitTask } = useContract();
  const { executeTransaction, status, error } = useTransaction();
  const { address } = useWeb3();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!submissionUrl) {
      alert('Please enter submission URL');
      return;
    }

    try {
      const receipt = await executeTransaction(async () => {
        return await submitTask(taskId, submissionUrl);
      });

      if (receipt) {
        alert('Task submitted successfully!');
        setSubmissionUrl('');
      }
    } catch (error) {
      console.error('Failed to submit task:', error);
    }
  };

  if (!address) {
    return <div>Please connect your wallet to submit tasks.</div>;
  }

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="submissionUrl">Submission URL</label>
        <input
          id="submissionUrl"
          type="url"
          value={submissionUrl}
          onChange={(e) => setSubmissionUrl(e.target.value)}
          placeholder="https://github.com/your-repo/pull/123"
          required
        />
      </div>

      <button type="submit" disabled={status === 'pending'}>
        {status === 'pending' ? 'Submitting...' : 'Submit Task'}
      </button>

      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
    </form>
  );
}
