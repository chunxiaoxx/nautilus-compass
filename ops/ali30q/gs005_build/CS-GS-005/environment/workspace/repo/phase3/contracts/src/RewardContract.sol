// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

/**
 * @title RewardContract
 * @dev Manages ERC20 (USDC/USDT) reward distribution and withdrawal.
 *      Supports multiple payment tokens via whitelist.
 */
contract RewardContract is Ownable, ReentrancyGuard {
    using SafeERC20 for IERC20;

    // Supported payment tokens (e.g., USDC, USDT)
    mapping(address => bool) public supportedTokens;

    // Agent balances per token: token => agent => amount
    mapping(address => mapping(address => uint256)) public balances;

    // Authorized callers (TaskContract)
    address public taskContract;

    // Platform fee (basis points, e.g., 500 = 5%)
    uint256 public platformFeeBps;
    address public feeRecipient;

    // Events
    event RewardDistributed(
        uint256 indexed taskId,
        address indexed agent,
        address indexed token,
        uint256 amount,
        uint256 fee
    );
    event RewardWithdrawn(address indexed agent, address indexed token, uint256 amount);
    event TokenAdded(address indexed token);
    event TokenRemoved(address indexed token);
    event PlatformFeeUpdated(uint256 newFeeBps);

    // Errors
    error UnsupportedToken();
    error NotTaskContract();
    error InsufficientBalance();
    error ZeroAmount();
    error InvalidAddress();
    error FeeTooHigh();

    constructor(uint256 _feeBps, address _feeRecipient) Ownable(msg.sender) {
        if (_feeBps > 1000) revert FeeTooHigh(); // Max 10%
        if (_feeRecipient == address(0)) revert InvalidAddress();
        platformFeeBps = _feeBps;
        feeRecipient = _feeRecipient;
    }

    // --- Admin Functions ---

    function setTaskContract(address _taskContract) external onlyOwner {
        if (_taskContract == address(0)) revert InvalidAddress();
        taskContract = _taskContract;
    }

    function addSupportedToken(address token) external onlyOwner {
        if (token == address(0)) revert InvalidAddress();
        supportedTokens[token] = true;
        emit TokenAdded(token);
    }

    function removeSupportedToken(address token) external onlyOwner {
        supportedTokens[token] = false;
        emit TokenRemoved(token);
    }

    function setPlatformFee(uint256 _feeBps) external onlyOwner {
        if (_feeBps > 1000) revert FeeTooHigh();
        platformFeeBps = _feeBps;
        emit PlatformFeeUpdated(_feeBps);
    }

    function setFeeRecipient(address _recipient) external onlyOwner {
        if (_recipient == address(0)) revert InvalidAddress();
        feeRecipient = _recipient;
    }

    // --- Core Functions ---

    /**
     * @dev Distribute reward to agent (called by TaskContract).
     *      Deducts platform fee, credits remainder to agent balance.
     *      Token must already be transferred to this contract by TaskContract.
     */
    function distributeReward(
        uint256 taskId,
        address agent,
        address token,
        uint256 amount
    ) external {
        if (msg.sender != taskContract) revert NotTaskContract();
        if (!supportedTokens[token]) revert UnsupportedToken();
        if (amount == 0) revert ZeroAmount();

        // Calculate platform fee
        uint256 fee = (amount * platformFeeBps) / 10000;
        uint256 agentAmount = amount - fee;

        // Credit agent balance
        balances[token][agent] += agentAmount;

        // Transfer fee to platform
        if (fee > 0) {
            IERC20(token).safeTransfer(feeRecipient, fee);
        }

        emit RewardDistributed(taskId, agent, token, agentAmount, fee);
    }

    /**
     * @dev Agent withdraws accumulated rewards for a specific token.
     */
    function withdrawReward(address token) external nonReentrant {
        if (!supportedTokens[token]) revert UnsupportedToken();

        uint256 amount = balances[token][msg.sender];
        if (amount == 0) revert InsufficientBalance();

        // Clear balance before transfer (CEI pattern)
        balances[token][msg.sender] = 0;

        // Transfer ERC20 to agent
        IERC20(token).safeTransfer(msg.sender, amount);

        emit RewardWithdrawn(msg.sender, token, amount);
    }

    /**
     * @dev Query agent balance for a specific token.
     */
    function getBalance(address agent, address token) external view returns (uint256) {
        return balances[token][agent];
    }
}
