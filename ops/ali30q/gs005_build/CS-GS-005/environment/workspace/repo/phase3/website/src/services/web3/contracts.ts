import { ethers } from 'ethers';
import { web3Provider } from './provider';

// Contract ABIs
export const TASK_CONTRACT_ABI = [
  // Task Management
  'function createTask(string memory title, string memory description, uint256 reward) external returns (uint256)',
  'function submitTask(uint256 taskId, string memory submissionUrl) external',
  'function approveTask(uint256 taskId, address worker) external',
  'function rejectTask(uint256 taskId, address worker, string memory reason) external',
  'function cancelTask(uint256 taskId) external',

  // Task Queries
  'function getTask(uint256 taskId) external view returns (tuple(uint256 id, address creator, string title, string description, uint256 reward, uint8 status, uint256 createdAt))',
  'function getTasksByCreator(address creator) external view returns (uint256[])',
  'function getTasksByWorker(address worker) external view returns (uint256[])',
  'function getActiveTasks() external view returns (uint256[])',
  'function getTotalTasks() external view returns (uint256)',

  // Events
  'event TaskCreated(uint256 indexed taskId, address indexed creator, uint256 reward)',
  'event TaskSubmitted(uint256 indexed taskId, address indexed worker, string submissionUrl)',
  'event TaskApproved(uint256 indexed taskId, address indexed worker, uint256 reward)',
  'event TaskRejected(uint256 indexed taskId, address indexed worker, string reason)',
  'event TaskCancelled(uint256 indexed taskId)',
];

export const REWARD_CONTRACT_ABI = [
  // Reward Management
  'function claimReward(uint256 taskId) external',
  'function getRewardBalance(address user) external view returns (uint256)',
  'function withdrawRewards() external',
  'function depositRewards() external payable',

  // Reward Queries
  'function getTotalRewardsPaid() external view returns (uint256)',
  'function getUserRewardHistory(address user) external view returns (tuple(uint256 taskId, uint256 amount, uint256 timestamp)[])',
  'function getPendingRewards(address user) external view returns (uint256)',

  // Events
  'event RewardClaimed(address indexed user, uint256 indexed taskId, uint256 amount)',
  'event RewardWithdrawn(address indexed user, uint256 amount)',
  'event RewardDeposited(address indexed depositor, uint256 amount)',
];

// Contract addresses
export const CONTRACT_ADDRESSES = {
  'base-sepolia': {
    taskContract: '0x69f258D20e5549236B5B68A33F26302B331379B6',
    rewardContract: '0x1f4d8E8Bdfc0323c5a684452071fa71129d4D8A3',
    identityContract: '0x20B9A1FCd63197616F67fE2012f3c5BE43B25952',
    nauToken: '0xb182196363150DE71E42AF5ffD8FD937BF27A7E3',
  },
  sepolia: {
    taskContract: '0x69f258D20e5549236B5B68A33F26302B331379B6',
    rewardContract: '0x1f4d8E8Bdfc0323c5a684452071fa71129d4D8A3',
    identityContract: '0x20B9A1FCd63197616F67fE2012f3c5BE43B25952',
    nauToken: '0xb182196363150DE71E42AF5ffD8FD937BF27A7E3',
  },
  mainnet: {
    taskContract: '0x0000000000000000000000000000000000000000',
    rewardContract: '0x0000000000000000000000000000000000000000',
    identityContract: '0x0000000000000000000000000000000000000000',
    nauToken: '0x0000000000000000000000000000000000000000',
  },
};

// Task status enum
export enum TaskStatus {
  OPEN = 0,
  IN_PROGRESS = 1,
  SUBMITTED = 2,
  APPROVED = 3,
  REJECTED = 4,
  CANCELLED = 5,
}

// Task interface
export interface Task {
  id: bigint;
  creator: string;
  title: string;
  description: string;
  reward: bigint;
  status: TaskStatus;
  createdAt: bigint;
}

// Reward history interface
export interface RewardHistory {
  taskId: bigint;
  amount: bigint;
  timestamp: bigint;
}

class ContractService {
  /**
   * Get contract instance
   */
  private getContract(address: string, abi: any[]): ethers.Contract {
    const signer = web3Provider.getCurrentSigner();

    if (!signer) {
      throw new Error('No signer available. Please connect wallet first.');
    }

    return new ethers.Contract(address, abi, signer);
  }

  /**
   * Get task contract
   */
  getTaskContract(network: string = 'base-sepolia'): ethers.Contract {
    const addresses = CONTRACT_ADDRESSES[network as keyof typeof CONTRACT_ADDRESSES];

    if (!addresses) {
      throw new Error(`Contract addresses not found for network: ${network}`);
    }

    return this.getContract(addresses.taskContract, TASK_CONTRACT_ABI);
  }

  /**
   * Get reward contract
   */
  getRewardContract(network: string = 'base-sepolia'): ethers.Contract {
    const addresses = CONTRACT_ADDRESSES[network as keyof typeof CONTRACT_ADDRESSES];

    if (!addresses) {
      throw new Error(`Contract addresses not found for network: ${network}`);
    }

    return this.getContract(addresses.rewardContract, REWARD_CONTRACT_ABI);
  }

  // ==================== Task Contract Methods ====================

  /**
   * Create a new task
   */
  async createTask(
    title: string,
    description: string,
    reward: string
  ): Promise<ethers.ContractTransactionResponse> {
    try {
      const contract = this.getTaskContract();
      const rewardWei = ethers.parseEther(reward);

      const tx = await contract.createTask(title, description, rewardWei);
      return tx;
    } catch (error) {
      throw new Error(`Failed to create task: ${(error as Error).message}`);
    }
  }

  /**
   * Submit task completion
   */
  async submitTask(
    taskId: number,
    submissionUrl: string
  ): Promise<ethers.ContractTransactionResponse> {
    try {
      const contract = this.getTaskContract();
      const tx = await contract.submitTask(taskId, submissionUrl);
      return tx;
    } catch (error) {
      throw new Error(`Failed to submit task: ${(error as Error).message}`);
    }
  }

  /**
   * Approve task submission
   */
  async approveTask(
    taskId: number,
    worker: string
  ): Promise<ethers.ContractTransactionResponse> {
    try {
      const contract = this.getTaskContract();
      const tx = await contract.approveTask(taskId, worker);
      return tx;
    } catch (error) {
      throw new Error(`Failed to approve task: ${(error as Error).message}`);
    }
  }

  /**
   * Reject task submission
   */
  async rejectTask(
    taskId: number,
    worker: string,
    reason: string
  ): Promise<ethers.ContractTransactionResponse> {
    try {
      const contract = this.getTaskContract();
      const tx = await contract.rejectTask(taskId, worker, reason);
      return tx;
    } catch (error) {
      throw new Error(`Failed to reject task: ${(error as Error).message}`);
    }
  }

  /**
   * Cancel task
   */
  async cancelTask(taskId: number): Promise<ethers.ContractTransactionResponse> {
    try {
      const contract = this.getTaskContract();
      const tx = await contract.cancelTask(taskId);
      return tx;
    } catch (error) {
      throw new Error(`Failed to cancel task: ${(error as Error).message}`);
    }
  }

  /**
   * Get task details
   */
  async getTask(taskId: number): Promise<Task> {
    try {
      const contract = this.getTaskContract();
      const task = await contract.getTask(taskId);

      return {
        id: task[0],
        creator: task[1],
        title: task[2],
        description: task[3],
        reward: task[4],
        status: task[5],
        createdAt: task[6],
      };
    } catch (error) {
      throw new Error(`Failed to get task: ${(error as Error).message}`);
    }
  }

  /**
   * Get tasks by creator
   */
  async getTasksByCreator(creator: string): Promise<bigint[]> {
    try {
      const contract = this.getTaskContract();
      return await contract.getTasksByCreator(creator);
    } catch (error) {
      throw new Error(`Failed to get tasks by creator: ${(error as Error).message}`);
    }
  }

  /**
   * Get tasks by worker
   */
  async getTasksByWorker(worker: string): Promise<bigint[]> {
    try {
      const contract = this.getTaskContract();
      return await contract.getTasksByWorker(worker);
    } catch (error) {
      throw new Error(`Failed to get tasks by worker: ${(error as Error).message}`);
    }
  }

  /**
   * Get active tasks
   */
  async getActiveTasks(): Promise<bigint[]> {
    try {
      const contract = this.getTaskContract();
      return await contract.getActiveTasks();
    } catch (error) {
      throw new Error(`Failed to get active tasks: ${(error as Error).message}`);
    }
  }

  /**
   * Get total tasks count
   */
  async getTotalTasks(): Promise<bigint> {
    try {
      const contract = this.getTaskContract();
      return await contract.getTotalTasks();
    } catch (error) {
      throw new Error(`Failed to get total tasks: ${(error as Error).message}`);
    }
  }

  // ==================== Reward Contract Methods ====================

  /**
   * Claim reward for completed task
   */
  async claimReward(taskId: number): Promise<ethers.ContractTransactionResponse> {
    try {
      const contract = this.getRewardContract();
      const tx = await contract.claimReward(taskId);
      return tx;
    } catch (error) {
      throw new Error(`Failed to claim reward: ${(error as Error).message}`);
    }
  }

  /**
   * Get reward balance
   */
  async getRewardBalance(user: string): Promise<string> {
    try {
      const contract = this.getRewardContract();
      const balance = await contract.getRewardBalance(user);
      return ethers.formatEther(balance);
    } catch (error) {
      throw new Error(`Failed to get reward balance: ${(error as Error).message}`);
    }
  }

  /**
   * Withdraw rewards
   */
  async withdrawRewards(): Promise<ethers.ContractTransactionResponse> {
    try {
      const contract = this.getRewardContract();
      const tx = await contract.withdrawRewards();
      return tx;
    } catch (error) {
      throw new Error(`Failed to withdraw rewards: ${(error as Error).message}`);
    }
  }

  /**
   * Deposit rewards
   */
  async depositRewards(amount: string): Promise<ethers.ContractTransactionResponse> {
    try {
      const contract = this.getRewardContract();
      const amountWei = ethers.parseEther(amount);
      const tx = await contract.depositRewards({ value: amountWei });
      return tx;
    } catch (error) {
      throw new Error(`Failed to deposit rewards: ${(error as Error).message}`);
    }
  }

  /**
   * Get total rewards paid
   */
  async getTotalRewardsPaid(): Promise<string> {
    try {
      const contract = this.getRewardContract();
      const total = await contract.getTotalRewardsPaid();
      return ethers.formatEther(total);
    } catch (error) {
      throw new Error(`Failed to get total rewards paid: ${(error as Error).message}`);
    }
  }

  /**
   * Get user reward history
   */
  async getUserRewardHistory(user: string): Promise<RewardHistory[]> {
    try {
      const contract = this.getRewardContract();
      const history = await contract.getUserRewardHistory(user);

      return history.map((item: any) => ({
        taskId: item[0],
        amount: item[1],
        timestamp: item[2],
      }));
    } catch (error) {
      throw new Error(`Failed to get reward history: ${(error as Error).message}`);
    }
  }

  /**
   * Get pending rewards
   */
  async getPendingRewards(user: string): Promise<string> {
    try {
      const contract = this.getRewardContract();
      const pending = await contract.getPendingRewards(user);
      return ethers.formatEther(pending);
    } catch (error) {
      throw new Error(`Failed to get pending rewards: ${(error as Error).message}`);
    }
  }

  // ==================== Event Listeners ====================

  /**
   * Listen to task created events
   */
  onTaskCreated(callback: (taskId: bigint, creator: string, reward: bigint) => void): void {
    const contract = this.getTaskContract();
    contract.on('TaskCreated', callback);
  }

  /**
   * Listen to task submitted events
   */
  onTaskSubmitted(
    callback: (taskId: bigint, worker: string, submissionUrl: string) => void
  ): void {
    const contract = this.getTaskContract();
    contract.on('TaskSubmitted', callback);
  }

  /**
   * Listen to task approved events
   */
  onTaskApproved(callback: (taskId: bigint, worker: string, reward: bigint) => void): void {
    const contract = this.getTaskContract();
    contract.on('TaskApproved', callback);
  }

  /**
   * Listen to reward claimed events
   */
  onRewardClaimed(callback: (user: string, taskId: bigint, amount: bigint) => void): void {
    const contract = this.getRewardContract();
    contract.on('RewardClaimed', callback);
  }

  /**
   * Remove all event listeners
   */
  removeAllListeners(): void {
    try {
      const taskContract = this.getTaskContract();
      const rewardContract = this.getRewardContract();

      taskContract.removeAllListeners();
      rewardContract.removeAllListeners();
    } catch (error) {
      // Ignore errors if contracts not initialized
    }
  }

  // ==================== Gas Estimation ====================

  /**
   * Estimate gas for creating task
   */
  async estimateCreateTaskGas(
    title: string,
    description: string,
    reward: string
  ): Promise<bigint> {
    try {
      const contract = this.getTaskContract();
      const rewardWei = ethers.parseEther(reward);
      return await contract.createTask.estimateGas(title, description, rewardWei);
    } catch (error) {
      throw new Error(`Failed to estimate gas: ${(error as Error).message}`);
    }
  }

  /**
   * Estimate gas for submitting task
   */
  async estimateSubmitTaskGas(taskId: number, submissionUrl: string): Promise<bigint> {
    try {
      const contract = this.getTaskContract();
      return await contract.submitTask.estimateGas(taskId, submissionUrl);
    } catch (error) {
      throw new Error(`Failed to estimate gas: ${(error as Error).message}`);
    }
  }
}

// Singleton instance
export const contractService = new ContractService();

// Export utility functions
export const createTask = (title: string, description: string, reward: string) =>
  contractService.createTask(title, description, reward);

export const submitTask = (taskId: number, submissionUrl: string) =>
  contractService.submitTask(taskId, submissionUrl);

export const approveTask = (taskId: number, worker: string) =>
  contractService.approveTask(taskId, worker);

export const getTask = (taskId: number) => contractService.getTask(taskId);

export const getActiveTasks = () => contractService.getActiveTasks();

export const claimReward = (taskId: number) => contractService.claimReward(taskId);

export const getRewardBalance = (user: string) => contractService.getRewardBalance(user);

export const withdrawRewards = () => contractService.withdrawRewards();
