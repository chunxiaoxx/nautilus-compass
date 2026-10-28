// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title PoWProof
 * @dev Proof-of-Work verification smart contract for Nautilus project
 *
 * Features:
 * - Submit PoW proofs on-chain
 * - Verify PoW validity
 * - Dynamic difficulty adjustment
 * - Immutable proof records
 */
contract PoWProof {
    struct Proof {
        address agent;           // Agent address
        bytes32 taskId;          // Task identifier
        bytes32 resultHash;      // Hash of task result
        uint256 nonce;           // PoW nonce
        bytes32 powHash;         // PoW hash (keccak256(resultHash || nonce))
        uint256 timestamp;       // Submission timestamp
        bool verified;           // Verification status
    }

    // Mapping from proof ID to Proof
    mapping(bytes32 => Proof) public proofs;

    // Current difficulty target (lower = harder)
    uint256 public difficulty;

    // Owner address (for difficulty adjustment)
    address public owner;

    // Events
    event ProofSubmitted(
        bytes32 indexed proofId,
        address indexed agent,
        bytes32 indexed taskId,
        uint256 timestamp
    );

    event ProofVerified(
        bytes32 indexed proofId,
        bool verified
    );

    event DifficultyAdjusted(
        uint256 oldDifficulty,
        uint256 newDifficulty
    );

    /**
     * @dev Constructor
     * @param _difficulty Initial difficulty target
     */
    constructor(uint256 _difficulty) {
        difficulty = _difficulty;
        owner = msg.sender;
    }

    /**
     * @dev Submit a PoW proof
     * @param taskId Task identifier
     * @param resultHash Hash of task result
     * @param nonce PoW nonce
     * @return proofId Unique proof identifier
     */
    function submitProof(
        bytes32 taskId,
        bytes32 resultHash,
        uint256 nonce
    ) external returns (bytes32 proofId) {
        // Compute PoW hash
        bytes32 powHash = keccak256(abi.encodePacked(resultHash, nonce));

        // Verify difficulty
        require(uint256(powHash) < difficulty, "PoW difficulty not met");

        // Generate unique proof ID
        proofId = keccak256(abi.encodePacked(
            msg.sender,
            taskId,
            block.timestamp,
            block.number
        ));

        // Store proof
        proofs[proofId] = Proof({
            agent: msg.sender,
            taskId: taskId,
            resultHash: resultHash,
            nonce: nonce,
            powHash: powHash,
            timestamp: block.timestamp,
            verified: false
        });

        emit ProofSubmitted(proofId, msg.sender, taskId, block.timestamp);

        return proofId;
    }

    /**
     * @dev Verify a PoW proof
     * @param proofId Proof identifier
     * @return isValid True if proof is valid
     */
    function verifyProof(bytes32 proofId) external returns (bool isValid) {
        Proof storage proof = proofs[proofId];
        require(proof.agent != address(0), "Proof does not exist");

        // Recompute PoW hash
        bytes32 computedHash = keccak256(abi.encodePacked(
            proof.resultHash,
            proof.nonce
        ));

        // Verify hash matches and meets difficulty
        isValid = (computedHash == proof.powHash) &&
                  (uint256(computedHash) < difficulty);

        // Update verification status
        proof.verified = isValid;

        emit ProofVerified(proofId, isValid);

        return isValid;
    }

    /**
     * @dev Set difficulty (owner only)
     * @param _difficulty New difficulty target
     */
    function setDifficulty(uint256 _difficulty) external {
        require(msg.sender == owner, "Only owner can adjust difficulty");
        require(_difficulty > 0, "Difficulty must be positive");

        uint256 oldDifficulty = difficulty;
        difficulty = _difficulty;

        emit DifficultyAdjusted(oldDifficulty, _difficulty);
    }

    /**
     * @dev Get proof details
     * @param proofId Proof identifier
     * @return Proof struct
     */
    function getProof(bytes32 proofId) external view returns (Proof memory) {
        require(proofs[proofId].agent != address(0), "Proof does not exist");
        return proofs[proofId];
    }

    /**
     * @dev Check if proof exists
     * @param proofId Proof identifier
     * @return exists True if proof exists
     */
    function proofExists(bytes32 proofId) external view returns (bool exists) {
        return proofs[proofId].agent != address(0);
    }

    /**
     * @dev Get current difficulty
     * @return Current difficulty target
     */
    function getDifficulty() external view returns (uint256) {
        return difficulty;
    }
}
