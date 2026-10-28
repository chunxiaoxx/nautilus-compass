// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title MEMEToken
 * @dev MEME Token for Nautilus AI Agent Mining Pool
 *
 * Features:
 * - ERC-20 standard token
 * - Mining rewards distribution
 * - PoW verification integration
 * - Value allocation mechanism
 */
contract MEMEToken is ERC20, Ownable {

    // PoW Proof contract address
    address public powProofContract;

    // Mining reward per successful PoW
    uint256 public miningReward;

    // Total tokens mined
    uint256 public totalMined;

    // Maximum supply (100 million tokens)
    uint256 public constant MAX_SUPPLY = 100_000_000 * 10**18;

    // Reward halving interval (blocks)
    uint256 public constant HALVING_INTERVAL = 210_000;

    // Initial mining reward (50 tokens)
    uint256 public constant INITIAL_REWARD = 50 * 10**18;

    // Block number when contract was deployed
    uint256 public deploymentBlock;

    // Mapping of agent addresses to their total mined tokens
    mapping(address => uint256) public agentMined;

    // Mapping of proof IDs to prevent double claiming
    mapping(bytes32 => bool) public claimedProofs;

    // Events
    event MiningRewardClaimed(address indexed agent, bytes32 indexed proofId, uint256 reward);
    event RewardUpdated(uint256 newReward);
    event PoWContractUpdated(address indexed newContract);

    /**
     * @dev Constructor
     * @param _powProofContract Address of PoW Proof contract
     */
    constructor(address _powProofContract) ERC20("MEME Token", "MEME") Ownable(msg.sender) {
        require(_powProofContract != address(0), "Invalid PoW contract address");

        powProofContract = _powProofContract;
        deploymentBlock = block.number;
        miningReward = INITIAL_REWARD;

        // Mint initial supply to owner (10% of max supply for liquidity)
        uint256 initialSupply = MAX_SUPPLY / 10;
        _mint(msg.sender, initialSupply);
        totalMined = initialSupply;
    }

    /**
     * @dev Claim mining reward for a verified PoW proof
     * @param proofId The ID of the verified proof
     * @param agent The agent who completed the work
     * @param taskId The task ID
     * @param resultHash The result hash
     * @param nonce The PoW nonce
     */
    function claimMiningReward(
        bytes32 proofId,
        address agent,
        bytes32 taskId,
        bytes32 resultHash,
        uint256 nonce
    ) external returns (uint256) {
        require(agent != address(0), "Invalid agent address");
        require(!claimedProofs[proofId], "Reward already claimed");
        require(totalMined + miningReward <= MAX_SUPPLY, "Max supply reached");

        // Verify proof exists and is verified in PoW contract
        (bool success, bytes memory data) = powProofContract.call(
            abi.encodeWithSignature("getProof(bytes32)", proofId)
        );
        require(success, "Failed to verify proof");

        // Decode proof data
        (
            address proofAgent,
            bytes32 proofTaskId,
            bytes32 proofResultHash,
            uint256 proofNonce,
            ,
            ,
            bool verified
        ) = abi.decode(data, (address, bytes32, bytes32, uint256, bytes32, uint256, bool));

        // Verify proof details match
        require(verified, "Proof not verified");
        require(proofAgent == agent, "Agent mismatch");
        require(proofTaskId == taskId, "Task ID mismatch");
        require(proofResultHash == resultHash, "Result hash mismatch");
        require(proofNonce == nonce, "Nonce mismatch");

        // Update reward based on halving schedule
        _updateMiningReward();

        // Mark proof as claimed
        claimedProofs[proofId] = true;

        // Mint reward to agent
        _mint(agent, miningReward);

        // Update statistics
        totalMined += miningReward;
        agentMined[agent] += miningReward;

        emit MiningRewardClaimed(agent, proofId, miningReward);

        return miningReward;
    }

    /**
     * @dev Update mining reward based on halving schedule
     */
    function _updateMiningReward() internal {
        uint256 blocksSinceDeployment = block.number - deploymentBlock;
        uint256 halvings = blocksSinceDeployment / HALVING_INTERVAL;

        if (halvings > 0) {
            uint256 newReward = INITIAL_REWARD / (2 ** halvings);

            // Minimum reward of 0.1 tokens
            if (newReward < 10**17) {
                newReward = 10**17;
            }

            if (newReward != miningReward) {
                miningReward = newReward;
                emit RewardUpdated(miningReward);
            }
        }
    }

    /**
     * @dev Get current mining reward
     */
    function getCurrentReward() external view returns (uint256) {
        uint256 blocksSinceDeployment = block.number - deploymentBlock;
        uint256 halvings = blocksSinceDeployment / HALVING_INTERVAL;

        if (halvings == 0) {
            return INITIAL_REWARD;
        }

        uint256 reward = INITIAL_REWARD / (2 ** halvings);

        // Minimum reward of 0.1 tokens
        if (reward < 10**17) {
            reward = 10**17;
        }

        return reward;
    }

    /**
     * @dev Check if a proof has been claimed
     */
    function isProofClaimed(bytes32 proofId) external view returns (bool) {
        return claimedProofs[proofId];
    }

    /**
     * @dev Get agent mining statistics
     */
    function getAgentStats(address agent) external view returns (
        uint256 mined,
        uint256 balance
    ) {
        return (agentMined[agent], balanceOf(agent));
    }

    /**
     * @dev Update PoW Proof contract address (owner only)
     */
    function updatePoWContract(address _newContract) external onlyOwner {
        require(_newContract != address(0), "Invalid contract address");
        powProofContract = _newContract;
        emit PoWContractUpdated(_newContract);
    }

    /**
     * @dev Get token statistics
     */
    function getTokenStats() external view returns (
        uint256 currentSupply,
        uint256 maxSupply,
        uint256 mined,
        uint256 currentReward,
        uint256 blocksUntilHalving
    ) {
        uint256 blocksSinceDeployment = block.number - deploymentBlock;
        uint256 blocksInCurrentPeriod = blocksSinceDeployment % HALVING_INTERVAL;

        return (
            totalSupply(),
            MAX_SUPPLY,
            totalMined,
            miningReward,
            HALVING_INTERVAL - blocksInCurrentPeriod
        );
    }
}
