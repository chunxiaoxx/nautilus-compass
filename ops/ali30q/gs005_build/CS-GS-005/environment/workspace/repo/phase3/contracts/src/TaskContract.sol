// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

/**
 * @title TaskContract
 * @dev Manages task lifecycle with ERC20 (USDC/USDT) payments.
 *      Publisher locks tokens when creating a task.
 *      Tokens are released to agent via RewardContract upon completion.
 */
contract TaskContract is Ownable, ReentrancyGuard {
    using SafeERC20 for IERC20;

    // Custom errors
    error InsufficientAllowance();
    error InvalidTimeout();
    error TaskNotOpen();
    error TaskTimedOut();
    error TaskNotAccepted();
    error NotTaskAgent();
    error NotVerificationEngine();
    error TaskNotSubmitted();
    error TaskNotVerified();
    error RewardContractNotSet();
    error RewardDistributionFailed();
    error TaskNotFailed();
    error NotDisputeResolver();
    error TaskNotDisputed();
    error TaskNotTimedOut();
    error UnsupportedToken();
    error ZeroReward();

    enum TaskType { CODE, DATA, COMPUTE, RESEARCH, DESIGN, WRITING, OTHER }

    enum TaskStatus {
        Open,
        Accepted,
        Submitted,
        Verified,
        Completed,
        Failed,
        Disputed
    }

    struct Task {
        uint256 taskId;
        address publisher;
        string description;
        string inputData;
        string expectedOutput;
        uint256 reward;
        address paymentToken;      // ERC20 token address (USDC/USDT)
        TaskType taskType;
        TaskStatus status;
        address agent;
        string result;
        uint256 timeout;
        uint256 createdAt;
        uint256 acceptedAt;
        uint256 submittedAt;
        uint256 verifiedAt;
        string disputeReason;
    }

    // State
    uint256 public nextTaskId;
    mapping(uint256 => Task) public tasks;
    mapping(uint256 => uint256) public taskRewards;  // taskId => locked reward amount
    mapping(address => bool) public supportedTokens;

    // External contracts
    address public verificationEngine;
    address public disputeResolver;
    address public rewardContract;

    // Events
    event TaskPublished(uint256 indexed taskId, address indexed publisher, address indexed token, uint256 reward, TaskType taskType);
    event TaskAccepted(uint256 indexed taskId, address indexed agent);
    event TaskSubmitted(uint256 indexed taskId, string result);
    event TaskVerified(uint256 indexed taskId, bool isValid);
    event TaskCompleted(uint256 indexed taskId, address indexed agent, uint256 reward);
    event TaskDisputed(uint256 indexed taskId, string reason);
    event DisputeResolved(uint256 indexed taskId, bool originalResult);
    event TaskTimeout(uint256 indexed taskId);
    event TokenAdded(address indexed token);

    constructor() Ownable(msg.sender) {
        nextTaskId = 1;
    }

    // --- Admin ---

    function setVerificationEngine(address _engine) external onlyOwner {
        require(_engine != address(0), "Invalid");
        verificationEngine = _engine;
    }

    function setDisputeResolver(address _resolver) external onlyOwner {
        require(_resolver != address(0), "Invalid");
        disputeResolver = _resolver;
    }

    function setRewardContract(address _reward) external onlyOwner {
        require(_reward != address(0), "Invalid");
        rewardContract = _reward;
    }

    function addSupportedToken(address token) external onlyOwner {
        require(token != address(0), "Invalid");
        supportedTokens[token] = true;
        emit TokenAdded(token);
    }

    // --- Core ---

    /**
     * @dev Publish a task with ERC20 payment.
     *      Publisher must approve this contract to spend `reward` tokens first.
     */
    function publishTask(
        string calldata description,
        string calldata inputData,
        string calldata expectedOutput,
        uint256 reward,
        address paymentToken,
        TaskType taskType,
        uint256 timeout
    ) external returns (uint256) {
        if (!supportedTokens[paymentToken]) revert UnsupportedToken();
        if (reward == 0) revert ZeroReward();
        if (timeout == 0) revert InvalidTimeout();

        // Transfer tokens from publisher to this contract (requires prior approve)
        IERC20(paymentToken).safeTransferFrom(msg.sender, address(this), reward);

        uint256 taskId = nextTaskId++;
        taskRewards[taskId] = reward;

        tasks[taskId] = Task({
            taskId: taskId,
            publisher: msg.sender,
            description: description,
            inputData: inputData,
            expectedOutput: expectedOutput,
            reward: reward,
            paymentToken: paymentToken,
            taskType: taskType,
            status: TaskStatus.Open,
            agent: address(0),
            result: "",
            timeout: timeout,
            createdAt: block.timestamp,
            acceptedAt: 0,
            submittedAt: 0,
            verifiedAt: 0,
            disputeReason: ""
        });

        emit TaskPublished(taskId, msg.sender, paymentToken, reward, taskType);
        return taskId;
    }

    function acceptTask(uint256 taskId) external {
        Task storage task = tasks[taskId];
        if (task.status != TaskStatus.Open) revert TaskNotOpen();
        if (block.timestamp >= task.createdAt + task.timeout) revert TaskTimedOut();

        task.status = TaskStatus.Accepted;
        task.agent = msg.sender;
        task.acceptedAt = block.timestamp;

        emit TaskAccepted(taskId, msg.sender);
    }

    function submitResult(uint256 taskId, string calldata result) external {
        Task storage task = tasks[taskId];
        if (task.status != TaskStatus.Accepted) revert TaskNotAccepted();
        if (task.agent != msg.sender) revert NotTaskAgent();
        if (block.timestamp >= task.acceptedAt + task.timeout) revert TaskTimedOut();

        task.status = TaskStatus.Submitted;
        task.result = result;
        task.submittedAt = block.timestamp;

        emit TaskSubmitted(taskId, result);
    }

    function verifyResult(uint256 taskId, bool isValid) external {
        if (msg.sender != verificationEngine) revert NotVerificationEngine();
        Task storage task = tasks[taskId];
        if (task.status != TaskStatus.Submitted) revert TaskNotSubmitted();

        if (isValid) {
            task.status = TaskStatus.Verified;
            task.verifiedAt = block.timestamp;
        } else {
            task.status = TaskStatus.Failed;
        }

        emit TaskVerified(taskId, isValid);
    }

    /**
     * @dev Complete task: transfer locked ERC20 to RewardContract for distribution.
     */
    function completeTask(uint256 taskId) external nonReentrant {
        Task storage task = tasks[taskId];
        if (task.status != TaskStatus.Verified) revert TaskNotVerified();
        if (rewardContract == address(0)) revert RewardContractNotSet();

        task.status = TaskStatus.Completed;

        uint256 reward = taskRewards[taskId];
        taskRewards[taskId] = 0;

        // Transfer ERC20 to RewardContract
        IERC20(task.paymentToken).safeTransfer(rewardContract, reward);

        // Tell RewardContract to credit agent
        (bool success, ) = rewardContract.call(
            abi.encodeWithSignature(
                "distributeReward(uint256,address,address,uint256)",
                taskId,
                task.agent,
                task.paymentToken,
                reward
            )
        );
        if (!success) revert RewardDistributionFailed();

        emit TaskCompleted(taskId, task.agent, reward);
    }

    function disputeVerification(uint256 taskId, string calldata reason) external {
        Task storage task = tasks[taskId];
        if (task.status != TaskStatus.Failed) revert TaskNotFailed();
        if (task.agent != msg.sender) revert NotTaskAgent();

        task.status = TaskStatus.Disputed;
        task.disputeReason = reason;

        emit TaskDisputed(taskId, reason);
    }

    function resolveDispute(uint256 taskId, bool originalResult) external {
        if (msg.sender != disputeResolver) revert NotDisputeResolver();
        Task storage task = tasks[taskId];
        if (task.status != TaskStatus.Disputed) revert TaskNotDisputed();

        if (originalResult) {
            task.status = TaskStatus.Failed;
        } else {
            task.status = TaskStatus.Verified;
            task.verifiedAt = block.timestamp;
        }

        emit DisputeResolved(taskId, originalResult);
    }

    /**
     * @dev Handle timeout: refund ERC20 to publisher.
     */
    function handleTimeout(uint256 taskId) external nonReentrant {
        Task storage task = tasks[taskId];
        if (
            !((task.status == TaskStatus.Open && block.timestamp >= task.createdAt + task.timeout) ||
            (task.status == TaskStatus.Accepted && block.timestamp >= task.acceptedAt + task.timeout))
        ) revert TaskNotTimedOut();

        task.status = TaskStatus.Failed;

        uint256 reward = taskRewards[taskId];
        taskRewards[taskId] = 0;

        // Refund ERC20 to publisher
        IERC20(task.paymentToken).safeTransfer(task.publisher, reward);

        emit TaskTimeout(taskId);
    }

    function getTask(uint256 taskId) external view returns (Task memory) {
        return tasks[taskId];
    }
}
