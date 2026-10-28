// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/// @title NautilusToken (NAU)
/// @notice Proof of Useful Work token. Minted by platform when agents
///         complete real computational tasks (physics simulation, ML, etc.)
///         "There is no free existence. Compute costs money. Money requires creating value."
contract NautilusToken is ERC20, Ownable {
    event TaskRewarded(address indexed agent, uint256 amount, string taskType);

    constructor() ERC20("Nautilus Token", "NAU") Ownable(msg.sender) {}

    /// @notice Mint NAU to an agent wallet. Only platform (owner) can call.
    /// @param to Agent wallet address
    /// @param amount Amount in wei (1 NAU = 1e18)
    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }

    /// @notice Mint with task type event for off-chain indexing
    /// @param to Agent wallet address
    /// @param amount Amount in wei (1 NAU = 1e18)
    /// @param taskType Task type string (e.g. "physics_simulation")
    function mintForTask(address to, uint256 amount, string calldata taskType) external onlyOwner {
        _mint(to, amount);
        emit TaskRewarded(to, amount, taskType);
    }
}
