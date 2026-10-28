import { useEffect, useState } from 'react';
import { useContract } from '../hooks/useContract';
import { useWeb3 } from '../context';
import { formatEther } from '../provider';
import type { Task } from '../contracts';

/**
 * Example: Task List Component
 */
export function TaskList() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const { getActiveTasks, getTask, isLoading } = useContract();
  const { address } = useWeb3();

  useEffect(() => {
    loadTasks();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadTasks = async () => {
    try {
      const taskIds = await getActiveTasks();
      const taskDetails = await Promise.all(
        taskIds.map((id) => getTask(Number(id)))
      );
      setTasks(taskDetails.filter((task): task is Task => task !== null));
    } catch (error) {
      console.error('Failed to load tasks:', error);
    }
  };

  if (isLoading) {
    return <div>Loading tasks...</div>;
  }

  if (tasks.length === 0) {
    return <div>No active tasks found.</div>;
  }

  return (
    <div>
      <h2>Active Tasks</h2>
      <div>
        {tasks.map((task) => (
          <div key={String(task.id)} style={{ border: '1px solid #ccc', padding: '16px', margin: '8px 0' }}>
            <h3>{task.title}</h3>
            <p>{task.description}</p>
            <p>
              <strong>Reward:</strong> {formatEther(task.reward)} ETH
            </p>
            <p>
              <strong>Creator:</strong> {task.creator.slice(0, 6)}...{task.creator.slice(-4)}
            </p>
            <p>
              <strong>Status:</strong> {getStatusLabel(task.status)}
            </p>
            <p>
              <strong>Created:</strong> {new Date(Number(task.createdAt) * 1000).toLocaleDateString()}
            </p>
            {address && address.toLowerCase() !== task.creator.toLowerCase() && (
              <button>Apply for Task</button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function getStatusLabel(status: number): string {
  const labels = ['Open', 'In Progress', 'Submitted', 'Approved', 'Rejected', 'Cancelled'];
  return labels[status] || 'Unknown';
}
